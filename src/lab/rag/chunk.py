"""Stage 2, chunk: cut every document into chunks that search can rank.

Every chunk is an exact substring of its document's body, with its character offsets. A span
label is scored by whether some chunk contains it whole, so labels work under any chunker.
"""

import re
from bisect import bisect_left, bisect_right
from collections.abc import Iterable
from itertools import accumulate
from typing import Literal

import tiktoken
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.rag.corpus import Access, Document, Status

# The embedding model's tokeniser: chunk sizes are counted in the tokens the embedder sees.
ENCODING = tiktoken.get_encoding("cl100k_base")

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    doc_id: str
    version: int
    start: int
    end: int
    text: str
    headings: tuple[str, ...] = ()
    title: str
    access: Access
    status: Status

    @property
    def doc_key(self) -> str:
        return f"{self.doc_id}@{self.version}"


class FixedChunker(BaseModel):
    """Windows of `size` tokens, each starting `size - overlap` tokens after the last."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["fixed"] = "fixed"
    size: int = Field(gt=0)
    overlap: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _overlap_below_size(self) -> "FixedChunker":
        if self.overlap >= self.size:
            raise ValueError("overlap must be smaller than size")
        return self


class StructureChunker(BaseModel):
    """One chunk per lowest-level section, split at paragraphs if over `max_tokens`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["structure"] = "structure"
    max_tokens: int = Field(gt=0)
    # Whether the heading path is put in front of the text that is embedded. The chunk text,
    # and so its offsets, never change.
    embed_headings: bool = False


class WholeChunker(BaseModel):
    """One chunk per document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["whole"] = "whole"


Chunker = FixedChunker | StructureChunker | WholeChunker


# slide: S2 E4
def windows(text, size, overlap=0):
    """Character ranges of windows `size` tokens long,
    each starting `size - overlap` tokens after the
    one before. Every range is a slice of `text`."""
    if not 0 <= overlap < size:
        raise ValueError("overlap must be from 0 to size - 1")
    starts, ends = token_bounds(text)
    n = len(starts) - 1
    step = size - overlap
    ranges = []
    for first in range(0, max(n, 1), step):
        last = min(first + size, n)
        ranges.append((starts[first], ends[last]))
        if last == n:
            break
    return ranges


def token_bounds(text: str) -> tuple[list[int], list[int]]:
    """Character offsets of every token boundary in `text`, n + 1 of them for n tokens.

    A token can end partway through a character that takes several bytes. `starts` rounds such
    a boundary down to the character's start and `ends` rounds it up past its end, so a window
    from starts[i] to ends[j] always holds whole characters and every token in it.
    """
    token_bytes = [len(ENCODING.decode_single_token_bytes(t)) for t in _encode(text)]
    byte_bounds = list(accumulate(token_bytes, initial=0))
    char_bytes = list(accumulate((len(c.encode("utf-8")) for c in text), initial=0))
    starts = [bisect_right(char_bytes, b) - 1 for b in byte_bounds]
    ends = [bisect_left(char_bytes, b) for b in byte_bounds]
    return starts, ends


def count_tokens(text: str) -> int:
    return len(_encode(text))


def _encode(text: str) -> list[int]:
    # Documents are plain text, so a string such as "<|endoftext|>" is ordinary text here.
    return ENCODING.encode(text, disallowed_special=())


def chunk_library(documents: Iterable[Document], chunker: Chunker) -> tuple[Chunk, ...]:
    """Every chunk of every document, in document order."""
    return tuple(chunk for document in documents for chunk in chunk_document(document, chunker))


def chunk_document(document: Document, chunker: Chunker) -> list[Chunk]:
    if isinstance(chunker, FixedChunker):
        pieces = [((), r) for r in windows(document.body, chunker.size, chunker.overlap)]
    elif isinstance(chunker, StructureChunker):
        pieces = _structure_pieces(document.body, chunker.max_tokens)
    else:
        pieces = [((), (0, len(document.body)))]
    return [
        Chunk(
            chunk_id=f"{document.key}#{n}",
            doc_id=document.doc_id,
            version=document.version,
            start=start,
            end=end,
            text=document.body[start:end],
            headings=headings,
            title=document.title,
            access=document.access,
            status=document.status,
        )
        for n, (headings, (start, end)) in enumerate(pieces)
    ]


def _structure_pieces(body: str, max_tokens: int) -> list[tuple[tuple[str, ...], tuple[int, int]]]:
    pieces = []
    for headings, (start, end) in _sections(body):
        for piece_start, piece_end in _fit(body, start, end, max_tokens):
            pieces.append((headings, (piece_start, piece_end)))
    return pieces


def _sections(body: str) -> list[tuple[tuple[str, ...], tuple[int, int]]]:
    """Sections from each heading to the next, with their heading paths.

    A heading with no text of its own before the next heading starts the section below it,
    so a parent heading stays with the first text under it.
    """
    matches = list(_HEADING.finditer(body))
    bounds = [0, *(m.start() for m in matches), len(body)]
    path: list[tuple[int, str]] = []
    paths: list[tuple[str, ...]] = [()]
    for match in matches:
        level = len(match.group(1))
        path = [(lvl, title) for lvl, title in path if lvl < level] + [(level, match.group(2))]
        paths.append(tuple(title for _, title in path))

    sections = []
    pending_start: int | None = None
    for index, (start, end) in enumerate(zip(bounds, bounds[1:], strict=False)):
        if start == end:
            continue
        heading_end = matches[index - 1].end() if index > 0 else start
        if not body[heading_end:end].strip() and index < len(matches):
            pending_start = start if pending_start is None else pending_start
            continue
        first = start if pending_start is None else pending_start
        sections.append((paths[index], (first, end)))
        pending_start = None
    if pending_start is not None:
        sections.append((paths[-1], (pending_start, len(body))))
    return sections


def _fit(body: str, start: int, end: int, max_tokens: int) -> list[tuple[int, int]]:
    """The section as one range if it fits, else split at paragraph breaks, else by tokens."""
    if count_tokens(body[start:end]) <= max_tokens:
        return [(start, end)]
    cuts = [start, *(m.end() + start for m in _PARAGRAPH_BREAK.finditer(body[start:end])), end]
    paragraphs = [(a, b) for a, b in zip(cuts, cuts[1:], strict=False) if a < b]
    ranges: list[tuple[int, int]] = []
    current: tuple[int, int] | None = None
    for a, b in paragraphs:
        if current is not None and count_tokens(body[current[0] : b]) <= max_tokens:
            current = (current[0], b)
            continue
        if current is not None:
            ranges.append(current)
        if count_tokens(body[a:b]) <= max_tokens:
            current = (a, b)
        else:
            ranges.extend((a + s, a + e) for s, e in windows(body[a:b], max_tokens))
            current = None
    if current is not None:
        ranges.append(current)
    return ranges
