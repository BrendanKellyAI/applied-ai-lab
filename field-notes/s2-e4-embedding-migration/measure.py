"""Measures and pass marks for S2 E4, fixed before the run. Nothing here calls a model or the
network, so every function can be tested on hand-made arrays.
"""

import math
import random
from collections.abc import Sequence

import numpy as np

from lab.scoring import wilson_interval

# S2 E3's question types. The brief calls identifier questions "code" questions.
TYPES = ("identifier", "paraphrase", "shared")
TYPE_LABELS = {
    "identifier": "Code",
    "paraphrase": "Paraphrase",
    "shared": "Shared words",
    "all": "All 120",
}


# Vectors -------------------------------------------------------------------------------------


def shorten(vectors: np.ndarray, dimensions: int) -> np.ndarray:
    """Keep the first `dimensions` values of each vector and rescale it to length 1."""
    cut = np.asarray(vectors, dtype=np.float64)[..., :dimensions]
    return (cut / np.linalg.norm(cut, axis=-1, keepdims=True)).astype(np.float32)


def row_cosines(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine between each row of `a` and the same row of `b`."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return (a * b).sum(axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))


def index_bytes(vectors: int, dimensions: int) -> int:
    """Size of an index at float32: vectors x dimensions x 4 bytes."""
    return vectors * dimensions * 4


# Recall --------------------------------------------------------------------------------------


def entry(hits: int, n: int) -> dict:
    rate, low, high = wilson_interval(hits, n)
    return {"hits": hits, "n": n, "rate": rate, "low": low, "high": high}


def recall(hits: Sequence[bool]) -> dict:
    return entry(sum(bool(h) for h in hits), len(hits))


def recall_by_type(types: Sequence[str], hits: Sequence[bool]) -> dict:
    """Recall for each question type and for all questions together."""
    out = {
        kind: recall([h for t, h in zip(types, hits, strict=True) if t == kind]) for kind in TYPES
    }
    out["all"] = recall(hits)
    return out


def random_floor(k: int, articles: int, questions: int) -> float:
    """Expected hits if the top k were drawn at random: questions x k / articles."""
    return questions * k / articles


# Claim 1 and the control: two rankings of the same questions ---------------------------------


def overlap(first: Sequence[str], second: Sequence[str]) -> int:
    """How many articles appear in both top-k lists, in any order."""
    return len(set(first) & set(second))


def compare(
    tops_a: Sequence[Sequence[str]],
    tops_b: Sequence[Sequence[str]],
    hits_a: Sequence[bool],
    hits_b: Sequence[bool],
    k: int,
) -> dict:
    """Top-k overlap per question, and the questions each side found that the other missed.

    A loss is a question side a found and side b missed; a gain is the reverse.
    """
    overlaps = [overlap(a, b) for a, b in zip(tops_a, tops_b, strict=True)]
    pairs = list(zip(hits_a, hits_b, strict=True))
    losses = [i for i, (a, b) in enumerate(pairs) if a and not b]
    gains = [i for i, (a, b) in enumerate(pairs) if b and not a]
    return {
        "overlaps": overlaps,
        "mean_overlap": sum(overlaps) / len(overlaps),
        "distribution": [overlaps.count(n) for n in range(k + 1)],
        "losses": losses,
        "gains": gains,
        "flips": len(losses) + len(gains),
    }


# Claim 3: a threshold carried across models --------------------------------------------------


def threshold(right_scores: Sequence[float], percentile: float) -> float:
    """The given percentile of the right articles' scores, linear interpolation."""
    return float(np.percentile(np.asarray(right_scores, dtype=np.float64), percentile))


def keep_and_wrong(scores: np.ndarray, answers: Sequence[int], t: float) -> dict:
    """K: the share of right articles scoring at or above t.
    W: the mean number of wrong articles per question scoring at or above t.

    `scores` has one row per question and one column per article; `answers` gives each
    question's right column.
    """
    scores = np.asarray(scores, dtype=np.float64)
    rows = np.arange(len(answers))
    right = scores[rows, answers]
    above = scores >= t
    wrong = above.sum(axis=1) - above[rows, answers]
    return {"t": t, "K": float((right >= t).mean()), "W": float(wrong.mean())}


def w_factor(w_old: float, w_new: float) -> float:
    """How many times larger the bigger W is than the smaller one."""
    low, high = sorted((w_old, w_new))
    if low == 0:
        return 1.0 if high == 0 else math.inf
    return high / low


# Claim 2c: the half-migrated index -----------------------------------------------------------


def migrated_split(articles: Sequence[dict], questions: Sequence[dict], seed: int) -> list[str]:
    """Half of all articles, chosen with the seed, stratified so that each question type has
    half its answer articles migrated. Articles no question asks about are split by role too,
    so half the look-alikes move and half stay.
    """
    rng = random.Random(seed)
    answer_type = {q["article_id"]: q["type"] for q in questions}
    strata: dict[str, list[str]] = {}
    for article in articles:
        aid = article["article_id"]
        key = answer_type.get(aid) or f"unasked-{article.get('role') or 'plain'}"
        strata.setdefault(key, []).append(aid)
    chosen: list[str] = []
    carry = 0
    for key in sorted(strata):
        members = strata[key]
        # An odd stratum rounds down and up in turn, so the total is exactly half.
        take = (len(members) + carry) // 2
        carry = (len(members) + carry) % 2
        chosen += rng.sample(members, take)
    order = {a["article_id"]: i for i, a in enumerate(articles)}
    return sorted(chosen, key=order.__getitem__)


def split_report(questions: Sequence[dict], migrated: Sequence[str]) -> dict:
    """Answer articles migrated and not, by question type."""
    moved = set(migrated)
    return {
        kind: {
            "migrated": sum(1 for q in questions if q["type"] == kind and q["article_id"] in moved),
            "old": sum(1 for q in questions if q["type"] == kind and q["article_id"] not in moved),
        }
        for kind in TYPES
    }


# The pilot -----------------------------------------------------------------------------------


def pilot_selection(
    articles: Sequence[dict], questions: Sequence[dict], seed: int, per_type: int, others: int
) -> tuple[list[str], list[int]]:
    """Article ids and question positions for the pilot: `per_type` questions of each type,
    their right articles, and `others` more articles, all chosen with one seeded generator."""
    rng = random.Random(seed)
    picked: list[int] = []
    for kind in TYPES:
        positions = [i for i, q in enumerate(questions) if q["type"] == kind]
        picked += sorted(rng.sample(positions, per_type))
    right = {questions[i]["article_id"] for i in picked}
    rest = [a["article_id"] for a in articles if a["article_id"] not in right]
    chosen = right | set(rng.sample(rest, others))
    return [a["article_id"] for a in articles if a["article_id"] in chosen], picked


# Verdicts, computed from the pass marks in config.yaml ---------------------------------------


def points(difference: float) -> float:
    """A difference of two rates in percentage points, rounded so that a gap sitting exactly
    on a pass mark, such as 0.8 - 0.7, is not pushed over it by floating-point error."""
    return round(abs(difference) * 100, 9)


def verdict(holds: bool) -> str:
    return "held" if holds else "failed"


def claim1(mean_overlap: float, losses: int, marks: dict) -> dict:
    holds = (
        mean_overlap <= marks["claim1_max_mean_overlap"] and losses >= marks["claim1_min_losses"]
    )
    return {"mean_overlap": mean_overlap, "losses": losses, "verdict": verdict(holds)}


def claim2a(hits: int, raised: bool, marks: dict) -> dict:
    holds = not raised and hits <= marks["claim2a_max_hits"]
    return {"hits": hits, "raised": raised, "verdict": verdict(holds)}


def claim2c(old_half_rate: float, migrated_rate: float, full_rate: float, marks: dict) -> dict:
    gap = points(migrated_rate - full_rate)
    holds = (
        old_half_rate <= marks["claim2c_max_old_half_recall"]
        and gap <= marks["claim2c_max_gap_points"]
    )
    return {
        "old_half_rate": old_half_rate,
        "migrated_rate": migrated_rate,
        "full_rate": full_rate,
        "gap_points": gap,
        "verdict": verdict(holds),
    }


def claim3(k_old: float, k_new: float, w_old: float, w_new: float, marks: dict) -> dict:
    k_points = points(k_new - k_old)
    factor = w_factor(w_old, w_new)
    w_change = abs(w_new - w_old)
    by_k = k_points >= marks["claim3_min_k_points"]
    by_w = factor >= marks["claim3_min_w_factor"] and w_change >= marks["claim3_min_w_articles"]
    return {
        "k_points": k_points,
        "w_factor": factor if math.isfinite(factor) else None,
        "w_change": w_change,
        "by_k": by_k,
        "by_w": by_w,
        "verdict": verdict(by_k or by_w),
    }


def claim4(gaps_percent: dict[str, float], marks: dict) -> dict:
    """`gaps_percent` maps each model to |API - local| / local x 100 for a full corpus embed."""
    holds = all(abs(g) <= marks["claim4_max_gap_percent"] for g in gaps_percent.values())
    return {"gaps_percent": gaps_percent, "verdict": verdict(holds)}


def control(mean_overlap: float, flips: int, marks: dict) -> dict:
    holds = (
        mean_overlap >= marks["control_min_mean_overlap"] and flips <= marks["control_max_flips"]
    )
    return {"mean_overlap": mean_overlap, "flips": flips, "verdict": verdict(holds)}
