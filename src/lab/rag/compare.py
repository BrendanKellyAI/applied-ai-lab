"""Paired comparisons of answer models on the same items, for the Season 3 field notes.

Every arm runs the same 520 test items, so models are compared item by item: exact McNemar
tests with Holm correction, tiers of models that cannot be told apart, Kendall's tau-b between
two orders with a bootstrap interval over items, per-item flips, and the format and behaviour
measures (citations, recognised declines, output tokens, latency, cost ratios).
"""

import re
import statistics
from collections.abc import Callable, Mapping, Sequence
from itertools import combinations
from math import comb
from pathlib import Path
from typing import Any

import numpy as np

from lab.rag.log import ItemLog
from lab.rag.score import Proportion
from lab.raw_log import latest_successful, load_records

# The answer's [Pn] markers, as S2 E10 parsed them: [P2], or a range such as [P2, P3].
MARKER = re.compile(r"\[P(\d+)(?:\s*[,\N{EN DASH}-]\s*P?(\d+))?\]")
# Wording the code recognises as "not found", for the format check on declines.
NOT_FOUND = re.compile(
    r"(could ?n[o']t|can ?n[o']t|cannot|unable to|did ?n[o']t|was ?n[o']t able to) "
    r"(find|locate|see)|not (found|in the passages|mentioned|provided|covered|stated)|"
    r"(passages|documents?) (do|does) not (contain|include|mention|say|cover|state)|"
    r"no information|does not specify|do not specify",
    re.IGNORECASE,
)


def handled(log: ItemLog) -> bool:
    """Handled right: an answerable item judged correct and faithful, or an unanswerable item
    declined. An item with no verdict counts as not handled."""
    v = log.verdict
    if v is None:
        return False
    return bool(v.correct and v.faithful) if log.answerable else bool(v.declined)


def answered_right(log: ItemLog) -> bool:
    v = log.verdict
    return bool(log.answerable and v and v.correct and v.faithful)


def hits(logs: Sequence[ItemLog], hit: Callable[[ItemLog], bool] = handled) -> dict[str, bool]:
    return {g.item_id: hit(g) for g in logs}


def proportion(logs: Sequence[ItemLog], hit: Callable[[ItemLog], bool] = handled) -> Proportion:
    return Proportion.of(sum(1 for g in logs if hit(g)), len(logs))


def exact_mcnemar(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts."""
    n, low = only_a + only_b, min(only_a, only_b)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(low + 1)) / 2**n)


def paired(a: Mapping[str, bool], b: Mapping[str, bool]) -> dict[str, Any]:
    """Items only a gets right, only b gets right, and the exact McNemar p-value."""
    shared = [i for i in a if i in b]
    only_a = sum(1 for i in shared if a[i] and not b[i])
    only_b = sum(1 for i in shared if b[i] and not a[i])
    return {"only_a": only_a, "only_b": only_b, "p_value": exact_mcnemar(only_a, only_b)}


def holm(pvalues: Mapping[Any, float]) -> dict[Any, float]:
    """Holm step-down adjusted p-values, monotone and capped at 1."""
    ordered = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(ordered)
    adjusted: dict[Any, float] = {}
    running = 0.0
    for rank, (key, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[key] = running
    return adjusted


def all_pairs(per_model: Mapping[str, Mapping[str, bool]]) -> dict[tuple[str, str], dict]:
    """Every pair of models, with raw and Holm-adjusted McNemar p-values."""
    pairs = {(a, b): paired(per_model[a], per_model[b]) for a, b in combinations(per_model, 2)}
    adjusted = holm({k: v["p_value"] for k, v in pairs.items()})
    return {k: {**v, "p_holm": adjusted[k]} for k, v in pairs.items()}


def distinguishable(pairs: Mapping[tuple[str, str], dict], a: str, b: str, alpha=0.05) -> bool:
    result = pairs.get((a, b)) or pairs.get((b, a))
    if result is None:
        raise KeyError(f"no comparison for {a} and {b}")
    return result["p_holm"] < alpha


def tiers(
    totals: Mapping[str, int], pairs: Mapping[tuple[str, str], dict], alpha: float = 0.05
) -> list[list[str]]:
    """Group models best first: each tier is the best remaining model and every remaining
    model the paired test cannot separate from it."""
    remaining = sorted(totals, key=lambda m: (-totals[m], m))
    out = []
    while remaining:
        best = remaining[0]
        tier = [m for m in remaining if m == best or not distinguishable(pairs, best, m, alpha)]
        out.append(tier)
        remaining = [m for m in remaining if m not in tier]
    return out


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float:
    """Kendall's tau-b, which allows for ties in either order."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("need two sequences of equal length, at least 2 long")
    concordant = discordant = ties_x = ties_y = 0
    for i, j in combinations(range(len(x)), 2):
        dx, dy = np.sign(x[i] - x[j]), np.sign(y[i] - y[j])
        if dx == 0 and dy == 0:
            continue
        if dx == 0:
            ties_x += 1
        elif dy == 0:
            ties_y += 1
        elif dx == dy:
            concordant += 1
        else:
            discordant += 1
    denominator = ((concordant + discordant + ties_x) * (concordant + discordant + ties_y)) ** 0.5
    return float((concordant - discordant) / denominator) if denominator else 0.0


def bootstrap_tau(
    board: Mapping[str, float],
    per_model: Mapping[str, Mapping[str, bool]],
    *,
    resamples: int = 2000,
    seed: int = 20261018,
) -> dict[str, float]:
    """Tau-b between board scores and items handled right, with a 95% percentile interval
    from resampling items with replacement."""
    models = list(board)
    items = sorted(next(iter(per_model.values())))
    matrix = np.array([[per_model[m][i] for i in items] for m in models], dtype=int)
    scores = [board[m] for m in models]
    point = kendall_tau_b(scores, matrix.sum(axis=1).tolist())
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(resamples):
        sample = rng.integers(0, len(items), len(items))
        draws.append(kendall_tau_b(scores, matrix[:, sample].sum(axis=1).tolist()))
    low, high = np.percentile(draws, [2.5, 97.5])
    return {"tau_b": round(point, 4), "low": round(float(low), 4), "high": round(float(high), 4)}


def flips(before: Mapping[str, bool], after: Mapping[str, bool]) -> dict[str, int]:
    """Items that change from right to wrong and from wrong to right."""
    shared = [i for i in before if i in after]
    lost = sum(1 for i in shared if before[i] and not after[i])
    gained = sum(1 for i in shared if after[i] and not before[i])
    return {
        "right_to_wrong": lost,
        "wrong_to_right": gained,
        "flipped": lost + gained,
        "net": gained - lost,
    }


def cited(answer: str, n_passages: int) -> list[int]:
    """The passage numbers an answer cites; numbers outside the prompt are ignored."""
    found: set[int] = set()
    for first, last in MARKER.findall(answer):
        lo, hi = int(first), int(last or first)
        found.update(range(lo, hi + 1))
    return sorted(n for n in found if 1 <= n <= n_passages)


def format_measures(logs: Sequence[ItemLog]) -> dict[str, Any]:
    """Citations on answers that are not declines, and declines worded as "not found"."""
    answers = [g for g in logs if g.answer and g.verdict and not g.verdict.declined]
    citing = [g for g in answers if cited(g.answer.text, len(g.prompt_chunks))]
    declines = [g for g in logs if g.answer and g.verdict and g.verdict.declined]
    recognised = [g for g in declines if NOT_FOUND.search(g.answer.text)]
    return {
        "citing": Proportion.of(len(citing), len(answers)).model_dump(),
        "declines_recognised": Proportion.of(len(recognised), len(declines)).model_dump(),
    }


def citation_validity(logs: Sequence[ItemLog], evidence_holds: Callable[[ItemLog, int], bool]):
    """Share of citations, on answerable items answered (not declined), whose cited passage
    holds the evidence. `evidence_holds(log, n)` says whether passage n holds it."""
    total = good = 0
    for g in logs:
        if not (g.answerable and g.answer and g.verdict and not g.verdict.declined):
            continue
        numbers = cited(g.answer.text, len(g.prompt_chunks))
        total += len(numbers)
        good += sum(1 for n in numbers if evidence_holds(g, n))
    return Proportion.of(good, total).model_dump()


def behaviour(logs: Sequence[ItemLog], raw_answer: Path | None = None) -> dict[str, Any]:
    """Median output tokens, errors and refusals, and median latency from the raw call log."""
    outputs = [g.answer.output_tokens for g in logs if g.answer]
    missing = sum(1 for g in logs if g.answer is None)
    empty = sum(1 for g in logs if g.answer and not g.answer.text.strip())
    refused = sum(1 for g in logs if g.answer and g.answer.finish_reason in {"refusal", "safety"})
    out: dict[str, Any] = {
        "median_output_tokens": statistics.median(outputs) if outputs else None,
        "median_input_tokens": statistics.median(g.answer.input_tokens for g in logs if g.answer)
        if outputs
        else None,
        "errors": missing,
        "empty_answers": empty,
        "refusals": refused,
    }
    if raw_answer is not None and raw_answer.exists():
        latest = latest_successful(load_records(raw_answer))
        latencies = [r.result.total_latency_ms for r in latest.values() if r.result is not None]
        out["median_latency_ms"] = statistics.median(latencies) if latencies else None
    return out


def answer_cost(logs: Sequence[ItemLog], price_in: float, price_out: float) -> float:
    """Cost of the answer calls, from the tokens each provider reported."""
    return (
        sum(
            g.answer.input_tokens * price_in + g.answer.output_tokens * price_out
            for g in logs
            if g.answer
        )
        / 1_000_000
    )


def ratios(costs: Mapping[str, float], handled_counts: Mapping[str, int]) -> dict[str, float]:
    """Cost per item handled right, as a ratio to the cheapest arm's."""
    per = {k: costs[k] / handled_counts[k] for k in costs if handled_counts.get(k)}
    cheapest = min(per.values())
    return {k: round(v / cheapest, 2) for k, v in per.items()}
