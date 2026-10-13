"""Stage 3, index: chunks, their unit vectors, and a BM25 model, held in memory.

Nothing here is saved: with the vectors in the embedding cache, building an index is free.
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from lab.rag.chunk import Chunk

_WORD = re.compile(r"\w+")

Embed = Callable[[Sequence[str]], np.ndarray]


def words(text: str) -> list[str]:
    """Lower-cased words split on \\w+, as v1 S2 E3: "E-2194" becomes "e" and "2194"."""
    return _WORD.findall(text.lower())


def embed_text(chunk: Chunk, embed_headings: bool) -> str:
    """The text embedded and keyword-indexed for a chunk."""
    if embed_headings and chunk.headings:
        return " > ".join(chunk.headings) + "\n\n" + chunk.text
    return chunk.text


def unit(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


@dataclass(frozen=True)
class Index:
    chunks: tuple[Chunk, ...]
    vectors: np.ndarray
    bm25: BM25Okapi
    embed_headings: bool


def build_index(chunks: Sequence[Chunk], embed: Embed, embed_headings: bool = False) -> Index:
    texts = [embed_text(chunk, embed_headings) for chunk in chunks]
    return Index(
        chunks=tuple(chunks),
        vectors=unit(np.asarray(embed(texts), dtype=np.float32)),
        bm25=BM25Okapi([words(text) for text in texts]),
        embed_headings=embed_headings,
    )
