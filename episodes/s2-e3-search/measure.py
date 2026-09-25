"""Scoring for S2 E3, fixed before the run. Nothing here calls a model or the network."""

from collections.abc import Sequence

from lab.scoring import wilson_interval

METHODS = ("keyword", "vector", "hybrid")
TYPES = ("identifier", "paraphrase", "shared")


def rank_of(ranking: Sequence[str], article_id: str) -> int:
    """1-based position of an article in a full ranking."""
    return ranking.index(article_id) + 1


def recall(rows: Sequence[dict], method: str, k: int) -> dict:
    hits = sum(1 for row in rows if (r := row["ranks"][method]) is not None and r <= k)
    rate, low, high = wilson_interval(hits, len(rows))
    return {"hits": hits, "n": len(rows), "rate": rate, "low": low, "high": high}


def mrr(rows: Sequence[dict], method: str) -> float:
    """Mean reciprocal rank, counting an answer beyond the recorded depth as zero."""
    total = sum(1 / r for row in rows if (r := row["ranks"][method]) is not None)
    return total / len(rows) if rows else 0.0


def lookalike_errors(rows: Sequence[dict], method: str) -> dict:
    """Identifier questions where a look-alike article ranked above the correct one."""
    count = sum(1 for row in rows if row["lookalike_above"][method])
    rate, low, high = wilson_interval(count, len(rows))
    return {"hits": count, "n": len(rows), "rate": rate, "low": low, "high": high}


def of_type(results: dict, kind: str | None) -> list[dict]:
    return [q for q in results["questions"] if kind is None or q["type"] == kind]


def table(results: dict) -> dict:
    """Recall at k, recall at 1 and MRR for every method and question type, and all together."""
    k = results["top_k"]
    out = {}
    for kind in (*TYPES, None):
        rows = of_type(results, kind)
        out[kind or "all"] = {
            m: {"recall_k": recall(rows, m, k), "recall_1": recall(rows, m, 1), "mrr": mrr(rows, m)}
            for m in METHODS
        }
    return out


def _apart(a: dict, b: dict) -> bool:
    """Whether a is above b with 95% intervals that do not overlap."""
    return a["rate"] > b["rate"] and a["low"] > b["high"]


def assess(results: dict) -> dict:
    """The three claims, exactly as section 4 of the brief defines them."""
    t = table(results)
    paraphrase = {m: t["paraphrase"][m]["recall_k"] for m in METHODS}
    identifier = {m: t["identifier"][m]["recall_k"] for m in METHODS}
    overall = {m: t["all"][m]["recall_k"] for m in METHODS}
    per_type = []
    for kind in TYPES:
        cell = {m: t[kind][m]["recall_k"] for m in METHODS}
        better = max(("keyword", "vector"), key=lambda m: cell[m]["rate"])
        per_type.append(cell["hybrid"]["rate"] >= cell[better]["low"])
    top_single = max(overall["keyword"]["rate"], overall["vector"]["rate"])
    return {
        "claim1": {"holds": _apart(paraphrase["vector"], paraphrase["keyword"])},
        "claim2": {"holds": _apart(identifier["keyword"], identifier["vector"])},
        "claim3": {
            "beats_both_overall": overall["hybrid"]["rate"] > top_single,
            "within_better_on_every_type": all(per_type),
            "holds": overall["hybrid"]["rate"] > top_single and all(per_type),
        },
    }
