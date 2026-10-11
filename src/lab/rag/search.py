"""Stage 5, search: keyword (BM25), vector (cosine), or a hybrid of the two.

Ported from v1 S2 E3. Every search returns up to `depth` hits so the filter and reranker have
something to work with. Ties keep corpus order, so every run gives the same ranking.
"""

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from lab.rag.index import Index, unit, words


class SearchConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    method: Literal["keyword", "vector", "hybrid"]
    depth: int = Field(default=50, gt=0)
    # Hybrid only: how many of each ranking to fuse. None fuses the full rankings, as v1 did.
    fuse_depth: int | None = Field(default=None, gt=0)
    rrf_k: int = Field(default=60, gt=0)


class Hit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    score: float


# slide: S2 E5
def fuse(rankings, k=60):
    """Reciprocal rank fusion: each ranking gives a document
    1 / (k + rank), and the scores add up."""
    scores = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


# slide: S2 E8
def rank(scores, depth, keep=None):
    """Positions of the `depth` best scores. A position
    outside `keep` never takes a place: the filter runs
    before ranking, not after."""
    order = np.argsort(-scores, kind="stable")
    if keep is not None:
        order = order[keep[order]]
    return order[:depth].tolist()


def keyword_scores(index: Index, query: str) -> np.ndarray:
    return np.asarray(index.bm25.get_scores(words(query)), dtype=np.float64)


def vector_scores(index: Index, query_vector: np.ndarray) -> np.ndarray:
    return index.vectors @ unit(np.asarray(query_vector, dtype=np.float32))


def search(
    index: Index,
    query: str,
    query_vector: np.ndarray,
    config: SearchConfig,
    keep: np.ndarray | None = None,
) -> list[Hit]:
    """The best `config.depth` chunks for one query, restricted to `keep` if given."""
    if config.method == "keyword":
        scores = keyword_scores(index, query)
        return _hits(scores, rank(scores, config.depth, keep))
    if config.method == "vector":
        scores = vector_scores(index, query_vector)
        return _hits(scores, rank(scores, config.depth, keep))
    fuse_depth = config.fuse_depth or len(index.chunks)
    rankings = [
        rank(keyword_scores(index, query), fuse_depth, keep),
        rank(vector_scores(index, query_vector), fuse_depth, keep),
    ]
    fused = fuse(rankings, k=config.rrf_k)[: config.depth]
    places = [{position: r for r, position in enumerate(ranking, start=1)} for ranking in rankings]
    return [
        Hit(index=i, score=sum(1 / (config.rrf_k + p[i]) for p in places if i in p)) for i in fused
    ]


def _hits(scores: np.ndarray, positions: list[int]) -> list[Hit]:
    return [Hit(index=i, score=float(scores[i])) for i in positions]
