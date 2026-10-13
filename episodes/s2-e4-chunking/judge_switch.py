"""Check the season's new judge before E4 uses it, as E4's pre-registration amendment requires.

A candidate judge marks the 50 items of E3's sample, reading exactly what the old judge read,
and is compared with `claude-sonnet-5-5` (the old judge) and the hand marks. Pass mark: at
least 45 of 50 with the old judge on `declined` and on `correct`, and at least 8 of 10 with the
hand marks on `correct`. Each candidate's results go in their own folder under judge-switch/.

Run with `uv run python episodes/s2-e4-chunking/judge_switch.py`, checking the judge in
season2/reference.yaml, or add `--judge provider:model:reasoning` to check another. The calls
are cached, so a rerun costs nothing; `--report` reads the saved verdicts and makes no call.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ProviderLimits
from lab.providers.registry import available_providers
from lab.rag.config import load_pipeline
from lab.rag.corpus import load_library
from lab.rag.judge_check import chunk_lookup, read_marks, read_record
from lab.rag.judge_second import read_second, run_second, second_prompts
from lab.rag.log import read_log
from lab.runner import Runner

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
E3 = ROOT / "episodes" / "s2-e3-measuring" / "judge-check"
E2_RUN = ROOT / "episodes" / "s2-e2-first-rag-system" / "results" / "baseline"
SWITCH = HERE / "judge-switch"
MODELS_AT_LEAST = 45
HAND_AT_LEAST = 8


def folder(spec) -> Path:
    """One folder per judge model and setting, so a failed candidate's results are kept."""
    return SWITCH / f"{spec.model}-{spec.reasoning}"


def candidate():
    """The judge to check: `--judge provider:model:reasoning`, or the reference's judge."""
    spec = load_pipeline(ROOT / "season2" / "reference.yaml").judge
    if "--judge" not in sys.argv:
        return spec
    provider, model, reasoning = sys.argv[sys.argv.index("--judge") + 1].split(":")
    return spec.model_copy(update={"provider": provider, "model": model, "reasoning": reasoning})


def run() -> None:
    # The main checkout's .env, also when run from a git worktree.
    load_dotenv(shared_cache_root(HERE).parent / ".env")
    spec = candidate()
    out = folder(spec)
    record = read_record(E3)
    library = load_library(ROOT / "datasets" / "halvard")
    logs = read_log(E2_RUN / "log.jsonl")
    summary = json.loads((E2_RUN / "summary.json").read_text(encoding="utf-8"))
    prompts = second_prompts(
        record["items"], logs, library, chunk_lookup(library, summary["pipeline"])
    )
    available = available_providers([spec.provider])
    if available.missing_keys:
        sys.exit(f"No API key for {spec.provider}")
    runner = Runner(
        providers=dict(available.providers),
        cache=ResponseCache(shared_cache_root(HERE)),
        limits={spec.provider: ProviderLimits(max_concurrency=4, requests_per_minute=60)},
    )
    out.mkdir(parents=True, exist_ok=True)
    run_second(runner, prompts, spec, out)


def report() -> dict:
    out = folder(candidate())
    record = read_record(E3)
    new = read_second(out)
    old = {g.item_id: g.verdict for g in read_log(E2_RUN / "log.jsonl")}
    gemini36 = read_second(E3 / "second")
    marks = {
        m.item_id: m
        for m in read_marks(E3 / "judge_check.csv", record["hand"], ("declined", "correct"))
    }
    items = record["items"]
    judged = [i for i in items if new.get(i)]

    def agree(other, field, ids):
        both = [i for i in ids if other.get(i) is not None]
        return {
            "count": sum(1 for i in both if getattr(new[i], field) == getattr(other[i], field)),
            "total": len(both),
        }

    result = {
        "no_verdict": [i for i in items if new.get(i) is None],
        "with_old_judge": {f: agree(old, f, judged) for f in ("declined", "correct", "faithful")},
        "with_gemini_3_6": {
            f: agree(gemini36, f, judged) for f in ("declined", "correct", "faithful")
        },
        "with_hand": {
            f: agree(marks, f, [i for i in judged if i in marks]) for f in ("declined", "correct")
        },
    }
    result["passed"] = (
        not result["no_verdict"]
        and result["with_old_judge"]["declined"]["count"] >= MODELS_AT_LEAST
        and result["with_old_judge"]["correct"]["count"] >= MODELS_AT_LEAST
        and result["with_hand"]["correct"]["count"] >= HAND_AT_LEAST
    )
    (out / "report.json").write_text(
        json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return result


if __name__ == "__main__":
    if "--report" not in sys.argv:
        run()
    print(json.dumps(report(), indent=1))
