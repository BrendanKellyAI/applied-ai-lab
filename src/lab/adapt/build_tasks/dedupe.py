"""Near duplicate removal: character 5-gram Jaccard similarity against the train split.

An inverted index on shingles keeps this to pairs that share at least one shingle, so a test
item is compared only with train items that could be similar.
"""

import re
from collections import defaultdict
from collections.abc import Mapping

SHINGLE = 5


def shingles(text: str, size: int = SHINGLE) -> frozenset[str]:
    normal = re.sub(r"\s+", " ", text.lower()).strip()
    if len(normal) <= size:
        return frozenset({normal})
    return frozenset(normal[i : i + size] for i in range(len(normal) - size + 1))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class NearDuplicateIndex:
    def __init__(self, texts: Mapping[str, str]) -> None:
        self._sets = {key: shingles(text) for key, text in texts.items()}
        self._index: dict[str, set[str]] = defaultdict(set)
        for key, grams in self._sets.items():
            for gram in grams:
                self._index[gram].add(key)

    def closest(self, text: str) -> tuple[str | None, float]:
        """The most similar indexed text and its similarity, or (None, 0.0)."""
        grams = shingles(text)
        candidates: set[str] = set()
        for gram in grams:
            candidates |= self._index.get(gram, set())
        best_key, best = None, 0.0
        for key in sorted(candidates):
            score = jaccard(grams, self._sets[key])
            if score > best:
                best_key, best = key, score
        return best_key, best


def near_duplicates(
    items: Mapping[str, str], against: NearDuplicateIndex, threshold: float
) -> dict[str, tuple[str, float]]:
    """Items above the threshold, each with the indexed text it is close to."""
    found = {}
    for key, text in items.items():
        match, score = against.closest(text)
        if match is not None and score > threshold:
            found[key] = (match, score)
    return found
