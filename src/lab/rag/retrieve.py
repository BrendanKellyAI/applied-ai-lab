"""Stages 2 to 8 for every item: chunk, index, search, filter, rerank and build the prompt.

Everything here is local once the vectors are cached. The rewrite and rerank stages are
passthrough until E6 and E7 switch them on.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from lab.rag.chunk import Chunk, StructureChunker, chunk_library
from lab.rag.config import PipelineConfig
from lab.rag.corpus import Item, Library
from lab.rag.filter import Removed, apply_after, keep_mask, refusal
from lab.rag.index import Embed, Index, build_index
from lab.rag.prompt import BuiltPrompt, render
from lab.rag.search import Hit, search


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
    items: Sequence[Item], index: Index, pipeline: PipelineConfig, embed: Embed
) -> dict[str, Retrieval]:
    queries = {item.id: queries_for(item) for item in items}
    texts = list(dict.fromkeys(q for qs in queries.values() for q in qs))
    vectors = dict(zip(texts, embed(texts), strict=True))
    return {
        item.id: _retrieve_one(item, queries[item.id], vectors, index, pipeline) for item in items
    }


def _retrieve_one(
    item: Item,
    queries: tuple[str, ...],
    vectors: dict,
    index: Index,
    pipeline: PipelineConfig,
) -> Retrieval:
    query = queries[0]
    keep = keep_mask(index.chunks, item.asker, pipeline.filter)
    searched = search(index, query, vectors[query], pipeline.search, keep)
    if keep is None:
        kept, removed = apply_after(searched, index.chunks, item.asker, pipeline.filter)
    else:
        kept, removed = searched, _blocked(item, query, vectors[query], index, pipeline)
    ranked = kept
    passages: list[Chunk] = [index.chunks[hit.index] for hit in ranked]
    return Retrieval(
        item_id=item.id,
        queries=queries,
        searched=tuple(searched),
        removed=tuple(removed),
        filtered=tuple(kept),
        ranked=tuple(ranked),
        prompt=render(item.question, item.history, passages, pipeline.prompt),
    )


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
