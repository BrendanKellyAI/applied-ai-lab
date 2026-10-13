"""S2 E13 analysis: the long-context arm against the retrieval arm, on the same 120 items.

Run with `uv run python field-notes/s2-e13-long-context-or-retrieval/analyse.py`. No key, no
call. The retrieval arm is E12's `baseline` run (the same reference system, `0294479ba987`);
its seconds come from the raw call logs as first recorded.
"""

import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

from lab.rag.analysis import below
from lab.rag.corpus import load_library
from lab.rag.episode import mcnemar
from lab.rag.log import read_log
from lab.rag.score import Proportion, code_check

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
RETRIEVAL = ROOT / "field-notes" / "s2-e12-embedding-swap" / "results" / "baseline"
HARD = ("distractor", "two_part", "bridge")
SIMPLE = ("policy_single",)
TYPES = HARD + SIMPLE
# gpt-6-luna, USD per million tokens (prices.yaml, checked 12 October 2026).
PRICE = {"input": 0.10, "cached_input": 0.01, "output": 0.50}


def cost(input_tokens: int, cached: int, output: int) -> float:
    fresh = input_tokens - cached
    return (fresh * PRICE["input"] + cached * PRICE["cached_input"]
            + output * PRICE["output"]) / 1e6


def raw_calls(path: Path) -> dict[str, dict]:
    rows = (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
    return {r["cell"]["item"]: r["result"] for r in rows if r.get("result")}


def retrieval_rows(items: dict) -> list[dict]:
    answers = raw_calls(RETRIEVAL / "raw-answer.jsonl")
    reranks = raw_calls(RETRIEVAL / "raw-rerank.jsonl")
    rows = []
    for g in read_log(RETRIEVAL / "log.jsonl"):
        if g.item_id not in items or not g.answer:
            continue
        a, r = answers[g.item_id], reranks.get(g.item_id, {})
        rows.append({
            "item_id": g.item_id,
            "type": g.type,
            "correct": bool(g.verdict and g.verdict.correct),
            "code_check": code_check(items[g.item_id], g.answer.text),
            "input_tokens": a["input_tokens"] + r.get("input_tokens", 0),
            "answer_input_tokens": a["input_tokens"],
            "seconds": (a["total_latency_ms"] + r.get("total_latency_ms", 0)) / 1000,
            "answer_seconds": a["total_latency_ms"] / 1000,
            "cost": cost(a["input_tokens"], a.get("cached_input_tokens") or 0, a["output_tokens"])
            + cost(r.get("input_tokens", 0), r.get("cached_input_tokens") or 0,
                   r.get("output_tokens", 0)),
        })
    return rows


def long_rows(folder: Path, items: dict) -> list[dict]:
    rows = []
    for line in (folder / "log.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line) if line.strip() else None
        if not r or r["answer"] is None:
            continue
        cached = r["cached_input_tokens"] or 0
        rows.append({
            "item_id": r["item_id"],
            "type": r["type"],
            "correct": bool(r["verdict"] and r["verdict"]["correct"]),
            "code_check": code_check(items[r["item_id"]], r["answer"]),
            "input_tokens": r["input_tokens"],
            "cached_input_tokens": cached,
            "seconds": r["seconds"],
            "cost": cost(r["input_tokens"], cached, r["output_tokens"]),
            "cost_uncached": cost(r["input_tokens"], 0, r["output_tokens"]),
        })
    return rows


def rate(rows, types, field="correct") -> Proportion:
    group = [r for r in rows if r["type"] in types and r[field] is not None]
    return Proportion.of(sum(1 for r in group if r[field]), len(group))


def median(rows, field):
    return statistics.median(r[field] for r in rows)


def main(pilot: bool) -> dict:
    library = load_library(ROOT / "datasets" / "halvard")
    folder = HERE / "results" / ("pilot" if pilot else "") / "long-context"
    lc = long_rows(folder, {i.id: i for i in library.test})
    items = {i.id: i for i in library.test if i.id in {r["item_id"] for r in lc}}
    rt = retrieval_rows(items)
    lc_hard, rt_hard = rate(lc, HARD), rate(rt, HARD)
    lc_simple, rt_simple = rate(lc, SIMPLE), rate(rt, SIMPLE)
    tokens = {"long_context": median(lc, "input_tokens"), "retrieval": median(rt, "input_tokens"),
              "retrieval_answer_only": median(rt, "answer_input_tokens")}
    seconds = {"long_context": median(lc, "seconds"), "retrieval": median(rt, "seconds"),
               "retrieval_answer_only": median(rt, "answer_seconds")}
    as_obj = [SimpleNamespace(**r) for r in rt], [SimpleNamespace(**r) for r in lc]
    report = {
        "items": len(lc),
        "claims": [
            {"id": "L1", "statement": "On the hardest questions, sending everything beats retrieval.",
             "held": below(rt_hard, lc_hard),
             "detail": {"long_context": lc_hard.model_dump(), "retrieval": rt_hard.model_dump()}},
            {"id": "L2", "statement": "On simple questions, retrieval loses nothing.",
             "held": not below(rt_simple, lc_simple) and not below(lc_simple, rt_simple),
             "detail": {"long_context": lc_simple.model_dump(),
                        "retrieval": rt_simple.model_dump()}},
            {"id": "L3", "statement": "Long context costs many times more per question.",
             "held": tokens["long_context"] >= 20 * tokens["retrieval"],
             "detail": {"median_input_tokens": tokens,
                        "ratio": round(tokens["long_context"] / tokens["retrieval"], 1)}},
            {"id": "L4", "statement": "Long context is slower.",
             "held": seconds["long_context"] >= 3 * seconds["retrieval"],
             "detail": {"median_seconds": seconds,
                        "ratio": round(seconds["long_context"] / seconds["retrieval"], 2)}},
        ],
        "by_type": {
            t: {arm: {"judge": rate(rows, (t,)).model_dump(),
                      "code_check": rate(rows, (t,), "code_check").model_dump()}
                for arm, rows in (("long_context", lc), ("retrieval", rt))}
            for t in TYPES
        },
        "paired_correct": mcnemar(*as_obj, lambda g: g.correct),
        "cost_per_question_usd": {
            "long_context": round(statistics.mean(r["cost"] for r in lc), 5),
            "long_context_without_cache": round(statistics.mean(r["cost_uncached"] for r in lc), 5),
            "retrieval": round(statistics.mean(r["cost"] for r in rt), 5),
        },
        "long_context_cached_share": round(
            sum(r["cached_input_tokens"] for r in lc) / sum(r["input_tokens"] for r in lc), 3),
    }
    out = HERE / "results" / ("pilot" if pilot else "") / "analysis.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    print(json.dumps(main(pilot="--pilot" in sys.argv), indent=1))
