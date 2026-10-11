"""Stage 11, score (the code half): span hits, ranks, leaks, the code check, and the season's
four numbers.

A chunk hits a span when it is from the same document version and contains the whole span.
Recall at k needs every evidence span hit within the top k.
"""

from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.rag.chunk import Chunk
from lab.rag.corpus import Access, Item, Span
from lab.rag.judge import Verdict
from lab.scoring import contains_match, wilson_interval

Stage = Literal["chunk", "search", "filter", "rerank", "prompt", "answer", "unjudged"]


def holds(chunk: Chunk, span: Span) -> bool:
    return chunk.doc_key == span.doc_key and chunk.start <= span.start and span.end <= chunk.end


def span_rank(span: Span, ranked: Sequence[Chunk]) -> int | None:
    """1-based rank of the first chunk holding the whole span, or None."""
    for rank, chunk in enumerate(ranked, start=1):
        if holds(chunk, span):
            return rank
    return None


def evidence_rank(item: Item, ranked: Sequence[Chunk]) -> int | None:
    """The rank by which every evidence span is held, or None if one never is."""
    ranks = [span_rank(span, ranked) for span in item.evidence]
    if not ranks or any(r is None for r in ranks):
        return None
    return max(r for r in ranks if r is not None)


def cut_spans(spans: Sequence[Span], chunks: Sequence[Chunk]) -> tuple[Span, ...]:
    """Spans that no chunk in the index holds whole: the chunker cut them."""
    return tuple(span for span in spans if not any(holds(c, span) for c in chunks))


def distractor_above(item: Item, ranked: Sequence[Chunk]) -> bool:
    """Whether a look-alike passage ranks above the evidence (or the evidence is absent)."""
    target = evidence_rank(item, ranked)
    for span in item.distractor_spans:
        rank = span_rank(span, ranked)
        if rank is not None and (target is None or rank < target):
            return True
    return False


def leaks(asker: Access, prompt: Sequence[Chunk]) -> tuple[str, ...]:
    """Staff chunks that reached the prompt of a public asker."""
    if asker == "staff":
        return ()
    return tuple(chunk.chunk_id for chunk in prompt if chunk.access == "staff")


def code_check(item: Item, answer: str) -> bool | None:
    """Every key value appears in the answer as a whole token; None if the item has none."""
    if not item.key_values:
        return None
    return all(contains_match(answer, value) for value in item.key_values)


# slide: S2 E14
def first_lost_stage(trace, k, verdict):
    """The first stage that lost the right passage, or
    None if the answer came out right."""
    if trace["cut"]:
        return "chunk"
    if trace["searched"] is None:
        return "search"
    if trace["filtered"] is None:
        return "filter"
    if trace["reranked"] is None or trace["reranked"] > k:
        return "rerank"
    if verdict is None:
        return "unjudged"
    if verdict.correct:
        return None
    return "prompt" if verdict.declined else "answer"


class ItemScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    type: str
    asker: Access
    answerable: bool
    evidence_rank: int | None
    leaks: tuple[str, ...]
    verdict: Verdict | None


class Proportion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    count: int
    total: int
    rate: float
    low: float
    high: float

    @classmethod
    def of(cls, count: int, total: int) -> "Proportion":
        rate, low, high = wilson_interval(count, total) if total else (0.0, 0.0, 0.0)
        return cls(count=count, total=total, rate=rate, low=low, high=high)


class SeasonNumbers(BaseModel):
    """The four numbers on every scoreboard (corpus spec 6.5)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    search: Proportion
    answer: Proportion
    not_found: Proportion
    leaks: Proportion


def season_numbers(scores: Sequence[ItemScore], k: int) -> SeasonNumbers:
    answerable = [s for s in scores if s.answerable]
    unanswerable = [s for s in scores if not s.answerable]
    public = [s for s in scores if s.asker == "public"]
    return SeasonNumbers(
        search=Proportion.of(
            sum(1 for s in answerable if s.evidence_rank is not None and s.evidence_rank <= k),
            len(answerable),
        ),
        answer=Proportion.of(
            sum(1 for s in answerable if s.verdict and s.verdict.correct and s.verdict.faithful),
            len(answerable),
        ),
        not_found=Proportion.of(
            sum(1 for s in unanswerable if s.verdict and s.verdict.declined), len(unanswerable)
        ),
        leaks=Proportion.of(sum(1 for s in public if s.leaks), len(public)),
    )


def by_type(scores: Sequence[ItemScore], k: int) -> Mapping[str, SeasonNumbers]:
    types = sorted({s.type for s in scores})
    return {t: season_numbers([s for s in scores if s.type == t], k) for t in types}
