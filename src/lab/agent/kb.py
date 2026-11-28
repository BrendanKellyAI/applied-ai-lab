"""The knowledge base the agent searches: the Season 2 Halvard corpus.

Two backends behind one interface:
  reference  the Season 2 reference retrieval (season2/reference.yaml): vector search over
             the reference chunks, the public and current filter, and the gpt-6-luna rerank.
             Each new query costs one embedding and one rerank call, both cached.
  keyword    BM25 over the same chunks and filter, with no model calls. For tests, dry runs
             and token estimates.
"""

import hashlib
import threading
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Protocol

from rank_bm25 import BM25Okapi

from lab.rag.chunk import Chunk, chunk_library
from lab.rag.config import PipelineConfig, load_pipeline
from lab.rag.corpus import Item, Library, load_library
from lab.rag.filter import allowed
from lab.rag.index import words

REPO = Path(__file__).resolve().parents[3]
CORPUS = REPO / "datasets" / "halvard"
REFERENCE = REPO / "season2" / "reference.yaml"
TOP_K = 5
PASSAGE_CHARS = 1200


class KnowledgeBase(Protocol):
    def search(self, query: str) -> list[dict[str, str]]: ...


def _passage(chunk: Chunk) -> dict[str, str]:
    text = chunk.text if len(chunk.text) <= PASSAGE_CHARS else chunk.text[:PASSAGE_CHARS] + " ..."
    return {"document": chunk.doc_id, "title": chunk.title, "text": text}


class KeywordKB:
    """BM25 over the reference chunks a public asker may see. No model calls."""

    def __init__(self, library: Library | None = None, pipeline: PipelineConfig | None = None):
        self._library = library
        self._pipeline = pipeline

    @cached_property
    def _chunks(self) -> list[Chunk]:
        library = self._library or load_library(CORPUS)
        pipeline = self._pipeline or load_pipeline(REFERENCE)
        chunks = chunk_library(library.documents, pipeline.chunk)
        return [c for c in chunks if allowed(c, "public", pipeline.filter)]

    @cached_property
    def _bm25(self) -> BM25Okapi:
        return BM25Okapi([words(chunk.text) for chunk in self._chunks])

    def search(self, query: str) -> list[dict[str, str]]:
        scores = self._bm25.get_scores(words(query))
        best = sorted(range(len(scores)), key=lambda i: -scores[i])[:TOP_K]
        return [_passage(self._chunks[i]) for i in best if scores[i] > 0]


class ReferenceKB:
    """The Season 2 reference retrieval, one query at a time."""

    def __init__(self, *, runner: object, cache_root: Path, folder: Path) -> None:
        self._runner = runner
        self._cache_root = cache_root
        self._folder = folder
        # Searches from parallel cases share the rerank log, so they run one at a time.
        self._lock = threading.Lock()

    @cached_property
    def _parts(self) -> tuple:
        from lab.rag.embed import Embedder, EmbeddingStore, openai_client
        from lab.rag.rerank import make_reorder
        from lab.rag.retrieve import build

        library = load_library(CORPUS)
        pipeline = load_pipeline(REFERENCE)
        store = EmbeddingStore(self._cache_root / "embeddings" / "s2.sqlite")
        embedder = Embedder(openai_client(), pipeline.embed.model, store)
        index = build(library, pipeline, embedder)
        reorder, _ = make_reorder(
            pipeline.rerank,
            runner=self._runner,
            cache_root=self._cache_root,
            index=index,
            episode="s5-agent-kb",
            condition="reference",
            folder=self._folder,
        )
        return pipeline, embedder, index, reorder

    def search(self, query: str) -> list[dict[str, str]]:
        from lab.rag.retrieve import retrieve

        with self._lock:
            pipeline, embedder, index, reorder = self._parts
            item = _query_item(query)
            retrieval = retrieve([item], index, pipeline, embedder, reorder=reorder)[item.id]
        return [_passage(index.chunks[hit.index]) for hit in retrieval.ranked[:TOP_K]]


def _query_item(query: str) -> Item:
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
    return Item(
        id=f"agent-{digest}",
        type="agent",
        asker="public",
        question=query,
        answerable=True,
        answer="",
    )


def passages_text(passages: Sequence[dict[str, str]]) -> str:
    return "\n\n".join(f"[{p['document']}] {p['title']}\n{p['text']}" for p in passages)
