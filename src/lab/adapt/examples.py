"""Choosing worked examples from train for each item (E3).

Random examples are drawn once per arm, so every item sees the same ones. Similar examples are
the train items whose messages are nearest to the item's by cosine similarity of embeddings,
with the nearest shown last, next to the message. A shuffle seed reorders either set, to show
how much the order alone moves the score.
"""

import random
from collections.abc import Callable, Sequence

import numpy as np

from lab.adapt.experiment import Examples

Embed = Callable[[Sequence[str]], np.ndarray]


def _shuffled[T](chosen: list[T], shuffle_seed: int | None) -> list[T]:
    if shuffle_seed is None:
        return chosen
    out = list(chosen)
    random.Random(shuffle_seed).shuffle(out)
    return out


def fixed_examples[T](spec: Examples, train: Sequence[T]) -> list[T]:
    """The arm's random examples, the same for every item."""
    if spec.n == 0:
        return []
    if spec.n > len(train):
        raise ValueError(f"asked for {spec.n} examples from {len(train)} train items")
    return _shuffled(random.Random(spec.seed).sample(list(train), spec.n), spec.shuffle_seed)


def _unit(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


def similar_examples[T](
    spec: Examples,
    items: Sequence[str],
    train: Sequence[T],
    train_texts: Sequence[str],
    embed: Embed,
) -> list[list[T]]:
    """For each item text, its n nearest train items, nearest last."""
    if spec.n > len(train):
        raise ValueError(f"asked for {spec.n} examples from {len(train)} train items")
    if spec.n == 0:
        return [[] for _ in items]
    train_vectors = _unit(embed(list(train_texts)))
    item_vectors = _unit(embed(list(items)))
    scores = item_vectors @ train_vectors.T
    out = []
    for row in scores:
        # Ties break by train order, so the choice is reproducible.
        nearest = sorted(range(len(train)), key=lambda i: (-row[i], i))[: spec.n]
        chosen = [train[i] for i in reversed(nearest)]
        out.append(_shuffled(chosen, spec.shuffle_seed))
    return out
