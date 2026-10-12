"""S2 E13's long-context arm: every current public document in one prompt, then the question.

Run with `uv run python field-notes/s2-e13-long-context-or-retrieval/longcontext.py`, or
`--pilot` for 2 items per type. Calls go through the harness runner, so they are cached and
logged. The library comes first and the question last, so the model provider can cache the
shared prefix; the cached tokens are reported.

The judge reads the same instructions as everywhere else this season, but the passages are
replaced by a note that the whole library was given: a judge prompt of 161,000 tokens per item
would cost more than the experiment. So this arm is scored on correctness only, by the judge and
by the code check, and the retrieval arm is compared on the same two measures.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ProviderLimits
from lab.providers.registry import available_providers
from lab.rag.chunk import count_tokens
from lab.rag.config import load_pipeline
from lab.rag.corpus import load_library
from lab.rag.judge import judge_prompt
from lab.rag.prompt import conversation, instruction
from lab.rag.score import code_check
from lab.rag.waves import judge, planned, request_for, run_wave
from lab.runner import Runner

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
TYPES = ("distractor", "two_part", "bridge", "policy_single")
EPISODE = "s2-e13-long-context-or-retrieval"
ARM = "long-context"


def pack_text(library) -> str:
    """Every current public document, policies first, each headed with its title and id."""
    docs = [d for d in library.documents if d.status == "current" and d.access == "public"]
    docs.sort(key=lambda d: (not d.doc_id.startswith("POL"), d.doc_id))
    return "\n\n".join(
        f"[Document: {d.title} ({d.doc_id}@{d.version})]\n{d.body.strip()}" for d in docs
    )


# slide: S2 E13
def long_prompt(library_text, item):
    """Everything first, so the provider can cache it,
    then any earlier turns, then the question."""
    parts = [f"Documents:\n\n{library_text}"]
    if item.history:
        parts.append(conversation(item.history))
    parts.append(f"Question: {item.question}")
    return "\n\n".join(parts)


def main(pilot: bool) -> None:
    load_dotenv(shared_cache_root(HERE).parent / ".env")
    reference = load_pipeline(ROOT / "season2" / "history" / f"{EPISODE}.yaml")
    library = load_library(ROOT / "datasets" / "halvard")
    items = [i for i in library.test if i.type in TYPES]
    if pilot:
        items = [
            i
            for t in TYPES
            for i in sorted((x for x in items if x.type == t), key=lambda x: x.id)[:2]
        ]
    text = pack_text(library)
    folder = HERE / "results" / ("pilot" if pilot else "") / ARM
    folder.mkdir(parents=True, exist_ok=True)
    providers = available_providers([reference.answer.provider, reference.judge.provider])
    if providers.missing_keys:
        sys.exit(f"Missing keys: {providers.missing_keys}")
    runner = Runner(
        providers=dict(providers.providers),
        cache=ResponseCache(shared_cache_root(HERE)),
        limits={
            "openai": ProviderLimits(max_concurrency=4, requests_per_minute=60),
            "google": ProviderLimits(max_concurrency=8, requests_per_minute=300),
        },
    )
    calls = [
        planned(
            request_for(
                reference.answer,
                system=instruction(reference.prompt.instruction),
                prompt=long_prompt(text, item),
                episode=EPISODE,
                stage="answer",
            ),
            stage="answer",
            item_id=item.id,
            condition=ARM,
        )
        for item in items
    ]
    answers, answer_summary = run_wave(runner, calls, folder / "raw-answer.jsonl")
    note = (
        f"(the whole library, {count_tokens(text):,} tokens in cl100k_base, was given; "
        "it is not repeated here)"
    )
    prompts = {
        item.id: judge_prompt(item, (), answers[item.id].text).replace(
            "Passages given to the system:\n(none)", f"Passages given to the system:\n{note}"
        )
        for item in items
        if item.id in answers
    }
    judged, judge_summaries = judge(
        runner, prompts, reference.judge, episode=EPISODE, condition=ARM, folder=folder
    )
    rows = []
    for item in items:
        result, verdict = answers.get(item.id), judged.get(item.id)
        rows.append(
            {
                "item_id": item.id,
                "type": item.type,
                "answer": result.text if result else None,
                "input_tokens": result.input_tokens if result else None,
                "cached_input_tokens": result.cached_input_tokens if result else None,
                "output_tokens": result.output_tokens if result else None,
                "seconds": round(result.total_latency_ms / 1000, 2) if result else None,
                "verdict": verdict.verdict.model_dump() if verdict and verdict.verdict else None,
                "code_check": code_check(item, result.text) if result else None,
            }
        )
    (folder / "log.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8", newline="\n"
    )
    (folder / "summary.json").write_text(
        json.dumps(
            {
                "items": len(items),
                "library_tokens_cl100k": count_tokens(text),
                "answer_model": reference.answer.model,
                "judge_model": reference.judge.model,
                "answer_calls": vars(answer_summary)
                if hasattr(answer_summary, "__dict__")
                else None,
            },
            indent=1,
            default=str,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(rows)} items; judged {sum(1 for r in rows if r['verdict'])}")


if __name__ == "__main__":
    main(pilot="--pilot" in sys.argv)
