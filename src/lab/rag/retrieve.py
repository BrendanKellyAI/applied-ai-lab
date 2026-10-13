"""Stages 2 to 8 for every item: chunk, index, search, filter, rerank and build the prompt.

Everything here is local once the vectors are cached. The rewrite stage's model calls are
made before (rewrite.py), and a reranker that needs model calls is passed in as `reorder`.
"""

from collections.abc import Callable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict

from lab.rag.chunk import Chunk, StructureChunker, chunk_library
from lab.rag.config import PipelineConfig
from lab.rag.corpus import Item, Library
from lab.rag.filter import Removed, apply_after, keep_mask, refusal
from lab.rag.index import Embed, Index, build_index
from lab.rag.prompt import BuiltPrompt, render
from lab.rag.search import Hit, fuse, search

# Stage 7: given the items, their queries and their filtered hits, a new order (positions
# into the filtered hits) for any item it reorders.
Reorder = Callable[..., dict[str, list[int]]]


class Retrieval(BaseModel):
    """What stages 4 to 8 did for one item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    queries: tuple[str, ...]
    searched: tuple[Hit, ...]
    removed: tuple[Removed, ...]
    filtered: tuple[Hit, ...]
    ranked: tuple[Hit, ...]
    prompt: BuiltPrompt


def build(library: Library, pipeline: PipelineConfig, embed: Embed) -> Index:
    chunks = chunk_library(library.documents, pipeline.chunk)
    headings = isinstance(pipeline.chunk, StructureChunker) and pipeline.chunk.embed_headings
    return build_index(chunks, embed, embed_headings=headings)


def queries_for(item: Item) -> tuple[str, ...]:
    """Stage 4 in passthrough: the last turn, as typed."""
    return (item.question,)


def retrieve(
    items: Sequence[Item],
    index: Index,
    pipeline: PipelineConfig,
    embed: Embed,
    queries: Mapping[str, tuple[str, ...]] | None = None,
    reorder: Reorder | None = None,
) -> dict[str, Retrieval]:
    """Stages 4 to 8 for every item. `queries` comes from stage 4 (the question as typed if
    None); `reorder` is stage 7 (the search order if None)."""
    queries = dict(queries) if queries else {item.id: queries_for(item) for item in items}
    texts = list(dict.fromkeys(q for qs in queries.values() for q in qs))
    vectors = dict(zip(texts, embed(texts), strict=True))
    found = {item.id: _find(item, queries[item.id], vectors, index, pipeline) for item in items}
    orders = reorder(items, queries, {i: f[2] for i, f in found.items()}) if reorder else {}
    out = {}
    for item in items:
        searched, removed, kept = found[item.id]
        order = orders.get(item.id)
        ranked = [kept[i] for i in order] if order is not None else kept
        passages: list[Chunk] = [index.chunks[hit.index] for hit in ranked]
        out[item.id] = Retrieval(
            item_id=item.id,
            queries=queries[item.id],
            searched=tuple(searched),
            removed=tuple(removed),
            filtered=tuple(kept),
            ranked=tuple(ranked),
            prompt=render(item.question, item.history, passages, pipeline.prompt),
        )
    return out


def _find(
    item: Item, queries: tuple[str, ...], vectors: dict, index: Index, pipeline: PipelineConfig
) -> tuple[list[Hit], list[Removed], list[Hit]]:
    """Search (each query, fused if more than one) and filter: searched, removed, kept."""
    keep = keep_mask(index.chunks, item.asker, pipeline.filter)
    runs = [search(index, q, vectors[q], pipeline.search, keep) for q in queries]
    searched = runs[0] if len(runs) == 1 else _fused(runs, pipeline.search.depth)
    if keep is None:
        kept, removed = apply_after(searched, index.chunks, item.asker, pipeline.filter)
    else:
        kept, removed = searched, _blocked(item, queries[0], vectors[queries[0]], index, pipeline)
    return searched, removed, kept


def _fused(runs: Sequence[Sequence[Hit]], depth: int, k: int = 60) -> list[Hit]:
    """Several queries' rankings merged by reciprocal rank fusion (search.fuse)."""
    order = fuse([[h.index for h in run] for run in runs], k=k)[:depth]
    places = [{h.index: r for r, h in enumerate(run, start=1)} for run in runs]
    return [Hit(index=i, score=sum(1 / (k + p[i]) for p in places if i in p)) for i in order]


def _blocked(
    item: Item, query: str, vector, index: Index, pipeline: PipelineConfig
) -> list[Removed]:
    """For a filter before ranking: the chunks it kept out of what an unfiltered search ranks."""
    unfiltered = search(index, query, vector, pipeline.search)
    blocked = []
    for hit in unfiltered:
        reason = refusal(index.chunks[hit.index], item.asker, pipeline.filter)
        if reason is not None:
            blocked.append(Removed(index=hit.index, reason=reason))
    return blocked
