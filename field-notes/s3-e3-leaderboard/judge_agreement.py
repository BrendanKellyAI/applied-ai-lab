"""S3 E3's judge agreement: two judges mark one shared sample, as the pre-registration requires.

E3 uses two judges: gemini-3.6-flash for OpenAI and Anthropic answers, claude-sonnet-5-5 for
Google answers. Both mark the same 100 items of the gpt-6-luna arm, reading the identical judge
prompt, and their agreement is reported per field. Gemini's verdicts come from the arm's log;
Sonnet's are new calls, cached like every other.

Run with `uv run python field-notes/s3-e3-leaderboard/judge_agreement.py`; `--report` reads the
saved verdicts and makes no call.
"""

import json
import random
import sys
from pathlib import Path

from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ProviderLimits
from lab.providers.registry import available_providers
from lab.rag.config import ModelSpec
from lab.rag.corpus import load_library
from lab.rag.judge import judge_prompt
from lab.rag.judge_check import chunk_lookup
from lab.rag.log import read_log
from lab.rag.score import Proportion
from lab.rag.waves import judge
from lab.runner import Runner

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results" / "2026-10"
ARM = RESULTS / "gpt-6-luna"
OUT = RESULTS / "judge-agreement"
SIZE = 100
SEED = 20261018
SECOND = ModelSpec(
    provider="anthropic", model="claude-sonnet-5-5", reasoning="off", max_output_tokens=400
)
FIELDS = ("declined", "correct", "faithful")


def sample(logs) -> list[str]:
    ids = sorted(g.item_id for g in logs if g.verdict is not None)
    return sorted(random.Random(SEED).sample(ids, SIZE))


def run() -> None:
    load_dotenv(shared_cache_root(HERE).parent / ".env")
    logs = {g.item_id: g for g in read_log(ARM / "log.jsonl")}
    chosen = sample(logs.values())
    library = load_library(ROOT / "datasets" / "halvard")
    items = {i.id: i for i in library.test}
    pipeline = json.loads((ARM / "summary.json").read_text(encoding="utf-8"))["pipeline"]
    chunks = chunk_lookup(library, pipeline)
    prompts = {
        i: judge_prompt(items[i], [chunks[c] for c in logs[i].prompt_chunks], logs[i].answer.text)
        for i in chosen
    }
    providers = available_providers(["anthropic"])
    if providers.missing_keys:
        sys.exit(f"Missing keys: {providers.missing_keys}")
    runner = Runner(
        providers=dict(providers.providers),
        cache=ResponseCache(shared_cache_root(HERE)),
        limits={"anthropic": ProviderLimits(max_concurrency=4, requests_per_minute=50)},
    )
    OUT.mkdir(parents=True, exist_ok=True)
    judged, _ = judge(
        runner,
        prompts,
        SECOND,
        episode="s3-e3-leaderboard",
        condition="judge-agreement",
        folder=OUT,
    )
    rows = [
        {"item_id": i, "verdict": judged[i].verdict.model_dump() if judged[i].verdict else None}
        for i in chosen
        if i in judged
    ]
    (OUT / "verdicts.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n"
    )


def report() -> dict:
    logs = {g.item_id: g for g in read_log(ARM / "log.jsonl")}
    second = [
        json.loads(line)
        for line in (OUT / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    pairs = [(logs[r["item_id"]].verdict, r["verdict"]) for r in second if r["verdict"]]
    out = {
        "sample": SIZE,
        "seed": SEED,
        "first_judge": "gemini-3.6-flash",
        "second_judge": SECOND.model,
        "both_gave_a_verdict": len(pairs),
        "agree": {
            f: Proportion.of(
                sum(1 for a, b in pairs if getattr(a, f) == b[f]), len(pairs)
            ).model_dump()
            for f in FIELDS
        },
        "handled_right": {
            "first": sum(
                1
                for (a, _), r in zip(pairs, second, strict=False)
                if (a.correct and a.faithful if logs[r["item_id"]].answerable else a.declined)
            ),
            "second": sum(
                1
                for (_, b), r in zip(pairs, second, strict=False)
                if (
                    b["correct"] and b["faithful"]
                    if logs[r["item_id"]].answerable
                    else b["declined"]
                )
            ),
        },
    }
    (OUT / "report.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return out


if __name__ == "__main__":
    if "--report" not in sys.argv:
        run()
    print(json.dumps(report(), indent=1))
