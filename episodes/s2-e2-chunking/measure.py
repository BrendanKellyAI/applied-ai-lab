"""Scoring for S2 E2: what counts as a hit, the ranks, and the claims, all fixed before the run.

Nothing here calls a model or the network, so chart.py and the tests can use all of it.
"""

import random
from collections.abc import Sequence
from statistics import median

import numpy as np

from lab.scoring import wilson_interval


def holds_fact(chunk: str, sentences: Sequence[str]) -> bool:
    """A chunk holds a fact only if it contains every sentence of it, whole.

    For a two-sentence fact, two chunks that each hold one sentence do not count: neither alone
    can answer the question.
    """
    return all(sentence in chunk for sentence in sentences)


def holders(chunks: Sequence[str], sentences: Sequence[str]) -> list[int]:
    return [index for index, chunk in enumerate(chunks) if holds_fact(chunk, sentences)]


def unit(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def first_hit_rank(similarities: np.ndarray, answer: Sequence[int]) -> int | None:
    """1-based rank of the best-ranked chunk holding the answer, or None if no chunk holds it."""
    if not answer:
        return None
    best = max(similarities[index] for index in answer)
    return int(np.sum(similarities > best)) + 1


def floor_similarity(
    similarities: np.ndarray, answer: Sequence[int], sample: int, rng: random.Random
) -> float:
    """Median similarity to `sample` random chunks that do not hold the answer."""
    others = sorted(set(range(len(similarities))) - set(answer))
    picked = rng.sample(others, min(sample, len(others)))
    return float(median(float(similarities[index]) for index in picked))


def score_condition(
    question_vectors: np.ndarray,
    chunk_vectors: np.ndarray,
    answers: Sequence[Sequence[int]],
    ceilings: Sequence[float],
    *,
    floor_sample: int,
    seed: int,
) -> list[dict]:
    """One row per question: rank of first hit, similarity to its answer chunk, ceiling, floor."""
    matrix = unit(question_vectors) @ unit(chunk_vectors).T
    rows = []
    for index, (similarities, answer) in enumerate(zip(matrix, answers, strict=True)):
        rng = random.Random(seed * 1000 + index)
        rows.append(
            {
                "rank": first_hit_rank(similarities, answer),
                "answer_chunks": len(answer),
                # With overlap a fact can sit in two chunks; the closer one is its answer chunk.
                "answer_similarity": (
                    max(float(similarities[i]) for i in answer) if answer else None
                ),
                "ceiling": float(ceilings[index]),
                "floor": floor_similarity(similarities, answer, floor_sample, rng),
            }
        )
    return rows


# Summaries ----------------------------------------------------------------------------------


def recall(rows: Sequence[dict], k: int) -> dict:
    hits = sum(1 for row in rows if row["rank"] is not None and row["rank"] <= k)
    rate, low, high = wilson_interval(hits, len(rows))
    return {"hits": hits, "n": len(rows), "rate": rate, "low": low, "high": high}


def _median(values) -> float | None:
    values = [value for value in values if value is not None]
    return float(median(values)) if values else None


def similarity_summary(rows: Sequence[dict]) -> dict:
    return {
        "answer_median": _median(row["answer_similarity"] for row in rows),
        "ceiling_median": _median(row["ceiling"] for row in rows),
        "floor_median": _median(row["floor"] for row in rows),
        "no_answer_chunk": sum(1 for row in rows if row["answer_chunks"] == 0),
        "n": len(rows),
    }


def rows_for(condition: dict, kind: str) -> list[dict]:
    return [row for row in condition["questions"] if row["kind"] == kind]


def find(results: dict, size: int, overlap: float) -> dict | None:
    for condition in results["conditions"]:
        if condition["chunk_size"] == size and condition["overlap_fraction"] == overlap:
            return condition
    return None


def best_sizes(recalls: dict[int, dict]) -> list[int]:
    """Every size sharing the top recall, so a tie is visible rather than broken silently."""
    top = max(entry["rate"] for entry in recalls.values())
    return [size for size, entry in recalls.items() if entry["rate"] == top]


def _recall_by_size(results: dict, kind: str, overlap: float, k: int) -> dict[int, dict]:
    return {
        size: recall(rows_for(find(results, size, overlap), kind), k)
        for size in results["chunk_sizes"]
        if find(results, size, overlap) is not None
    }


def assess(results: dict) -> dict:
    """The three claims, tested exactly as section 4 of the brief defines them."""
    k = results["top_k"]
    sizes = results["chunk_sizes"]
    one = _recall_by_size(results, "one", 0.0, k)
    two = _recall_by_size(results, "two", 0.0, k)
    two_overlap = _recall_by_size(results, "two", 0.25, k)
    medians = [
        similarity_summary(rows_for(find(results, size, 0.0), "one"))["answer_median"]
        for size in sizes
    ]
    falls = all(a is not None and b is not None and b < a for a, b in zip(medians, medians[1:]))
    best_one = best_sizes(one)
    top = one[best_one[0]]
    largest = one[sizes[-1]]
    separated = sizes[-1] not in best_one and largest["high"] < top["low"]
    claim2_sizes = [size for size in (64, 128) if size in two and size in two_overlap]
    claim2 = bool(claim2_sizes) and all(
        two_overlap[size]["rate"] > two[size]["rate"] for size in claim2_sizes
    )
    best_two = best_sizes(two)
    return {
        "claim1": {
            "median_falls_every_step": falls,
            "largest_below_best_intervals_apart": separated,
            "holds": falls and separated,
            "medians": dict(zip(sizes, medians, strict=True)),
        },
        "claim2": {"holds": claim2, "sizes": claim2_sizes},
        "claim3": {
            "best_one": best_one,
            "best_two": best_two,
            "holds": set(best_one).isdisjoint(best_two),
        },
    }
