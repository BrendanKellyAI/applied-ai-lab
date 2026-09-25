"""Builds the S2 E2 corpus: one excerpt per S1 E7 novel, with the invented facts inserted.

The novel text is fetched and checked exactly as in S1 E7, by that field note's own code, and
is never committed: rerun this to rebuild it. Only the facts and questions, which are ours, are
committed, in facts.json.
"""

import random
from bisect import bisect_right
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import tiktoken
import yaml

from lab.experiments import load_sibling

REPO = Path(__file__).parents[2]
S1_E7 = REPO / "field-notes" / "s1-e7-lost-in-the-middle"
GUTENBERG_CACHE = REPO / ".cache" / "gutenberg"


class CorpusError(RuntimeError):
    """The corpus cannot be built as the config describes."""


@dataclass(frozen=True)
class Novel:
    index: int
    book_id: int
    title: str
    text: str
    excerpt_tokens: int


@cache
def s1_e7():
    """The S1 E7 dataset builder, which knows how to fetch, check, and strip each book."""
    return load_sibling(S1_E7 / "build_dataset.py")


@cache
def encoding(name: str = "cl100k_base"):
    return tiktoken.get_encoding(name)


def books(config: dict) -> list:
    source = yaml.safe_load((REPO / config["books_from"]).read_text(encoding="utf-8"))
    return [s1_e7().Book.from_config(entry) for entry in source["parameters"]["filler_books"]]


def excerpt(text: str, tokens: int, enc) -> str:
    """The first `tokens` tokens of the novel's prose, cut back to the last whole sentence."""
    module = s1_e7()
    passage = module._passage(module._normalise(text))
    ids = enc.encode(passage, disallowed_special=())
    if len(ids) < tokens:
        raise CorpusError(f"Novel has {len(ids)} tokens of prose, fewer than {tokens}")
    candidate = enc.decode(ids[:tokens])
    ends = module.sentence_boundaries(candidate)
    return candidate[: ends[-1]].rstrip() if ends else candidate


def insertion_points(text: str, count: int, enc) -> list[int]:
    """`count` sentence boundaries spread evenly through the text, as character offsets.

    The targets sit at the middle of equal slices, measured in tokens, and each moves to the
    nearest sentence boundary, so no fact splits a sentence of the novel.
    """
    tokens = enc.encode(text, disallowed_special=())
    _, offsets = enc.decode_with_offsets(tokens)
    boundaries = s1_e7().sentence_boundaries(text)
    if len(boundaries) < count:
        raise CorpusError("Not enough sentence boundaries to place every fact")
    points = []
    for slot in range(count):
        target = offsets[int(len(tokens) * (slot + 0.5) / count)]
        nearest = min(boundaries, key=lambda boundary: (abs(boundary - target), boundary))
        points.append(nearest)
    if len(set(points)) != count:
        raise CorpusError("Two facts landed on the same sentence boundary")
    return points


def insert(text: str, points: list[int], facts: list) -> str:
    """The text with each fact placed at its point, in order, separated by single spaces."""
    pieces, previous = [], 0
    for point, fact in zip(points, facts, strict=True):
        pieces += [text[previous:point].strip(), fact.text]
        previous = point
    pieces.append(text[previous:].strip())
    return " ".join(piece for piece in pieces if piece)


def fact_token_starts(document: str, facts: list, enc) -> list[int]:
    """The token index at which each fact starts in the document, in document order."""
    tokens = enc.encode(document, disallowed_special=())
    _, offsets = enc.decode_with_offsets(tokens)
    starts = []
    for fact in facts:
        char = document.find(fact.text)
        if char < 0:
            raise CorpusError(f"Fact {fact.fact_id} is missing from its novel")
        starts.append(bisect_right(offsets, char) - 1)
    return sorted(starts)


def check_spacing(starts: list[int], minimum: int) -> None:
    gaps = [later - earlier for earlier, later in zip(starts, starts[1:])]
    if gaps and min(gaps) < minimum:
        raise CorpusError(f"Two facts are only {min(gaps)} tokens apart; {minimum} are needed")


def build_novel(index: int, raw_text: str, facts: list, config: dict, book) -> Novel:
    enc = encoding(config["tokeniser"])
    text = excerpt(raw_text, config["excerpt_tokens"], enc)
    for fact in facts:
        if fact.place.lower() in text.lower():
            raise CorpusError(f"{fact.place} already appears in {book.title}; change the seed")
    # The order of one- and two-sentence facts through the novel comes from the seed.
    ordered = list(facts)
    random.Random(config["seed"] * 100 + index).shuffle(ordered)
    document = insert(text, insertion_points(text, len(ordered), enc), ordered)
    check_spacing(fact_token_starts(document, ordered, enc), config["min_fact_spacing_tokens"])
    return Novel(index, book.id, book.title, document, len(enc.encode(document)))


def build(config: dict, facts: list, only: int | None = None) -> list[Novel]:
    """Every novel with its facts inserted, or just novel `only`."""
    module = s1_e7()
    novels = []
    for index, book in enumerate(books(config)):
        if only is not None and index != only:
            continue
        raw = module.load_book(book, GUTENBERG_CACHE)
        mine = [fact for fact in facts if fact.novel_index == index]
        novels.append(build_novel(index, raw, mine, config, book))
    return novels
