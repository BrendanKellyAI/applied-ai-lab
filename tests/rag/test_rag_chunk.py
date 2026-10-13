import pytest

from lab.rag.chunk import (
    ENCODING,
    FixedChunker,
    StructureChunker,
    WholeChunker,
    chunk_library,
    windows,
)


def _covers(text, ranges):
    covered = [False] * len(text)
    for start, end in ranges:
        for i in range(start, end):
            covered[i] = True
    return all(covered)


def test_windows_step_by_size_minus_overlap():
    text = " ".join(f"w{i}" for i in range(100))
    ranges = windows(text, size=20, overlap=5)
    tokens = [len(ENCODING.encode(text[s:e])) for s, e in ranges]

    assert ranges[0][0] == 0
    assert ranges[-1][1] == len(text)
    assert all(t <= 21 for t in tokens)
    assert _covers(text, ranges)
    # Consecutive windows overlap when overlap > 0.
    assert all(b[0] < a[1] for a, b in zip(ranges, ranges[1:], strict=False))


def test_windows_without_overlap_tile_the_text():
    text = " ".join(f"w{i}" for i in range(100))
    ranges = windows(text, size=20)

    assert all(a[1] == b[0] for a, b in zip(ranges, ranges[1:], strict=False))
    assert "".join(text[s:e] for s, e in ranges) == text


def test_windows_never_split_a_character():
    # Accented and non-Latin characters span several bytes and can straddle a token boundary.
    text = "Café crème brûlée, 東京の天気は晴れ。 " * 30
    for start, end in windows(text, size=7, overlap=2):
        piece = text[start:end]
        assert piece.encode("utf-8").decode("utf-8") == piece
    assert _covers(text, windows(text, size=7, overlap=2))


def test_short_text_is_one_window():
    assert windows("Short.", size=256) == [(0, 6)]


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError, match="overlap"):
        windows("text", size=10, overlap=10)


def test_every_chunker_gives_exact_substrings_covering_every_document(library):
    for chunker in (
        FixedChunker(size=8, overlap=2),
        StructureChunker(max_tokens=40),
        WholeChunker(),
    ):
        chunks = chunk_library(library.documents, chunker)
        for document in library.documents:
            own = [c for c in chunks if c.doc_key == document.key]
            assert own, f"{type(chunker).__name__} made no chunk for {document.key}"
            for chunk in own:
                assert chunk.text == document.body[chunk.start : chunk.end]
            assert _covers(document.body, [(c.start, c.end) for c in own])


def test_chunks_carry_document_metadata_and_stable_ids(library):
    chunks = chunk_library(library.documents, WholeChunker())
    staff = next(c for c in chunks if c.doc_id == "INT-PRC")

    assert staff.chunk_id == "INT-PRC@1#0"
    assert (staff.access, staff.status, staff.title) == (
        "staff",
        "current",
        "Goodwill and pricing rules",
    )


def test_article_shorter_than_the_size_is_one_chunk(library):
    chunks = chunk_library(library.documents, FixedChunker(size=256))

    assert [c.text for c in chunks if c.doc_id == "A000"] == [library.document("A000@1").body]


def test_structure_chunk_keeps_its_heading_path(library):
    chunks = chunk_library([library.document("POL-WAR@2")], StructureChunker(max_tokens=400))
    tessa = next(c for c in chunks if "36 months" in c.text)

    assert tessa.headings == ("Warranty", "Tessa dishwasher", "Cover period")
    # A heading with no text of its own joins the section below it.
    assert tessa.text.startswith("## Tessa dishwasher\n\n### Cover period")


def test_long_section_splits_at_paragraphs():
    from datetime import date

    from lab.rag.corpus import Document

    body = "## Long\n\n" + "\n\n".join(f"Paragraph {i} " + "word " * 30 for i in range(4))
    document = Document(
        doc_id="P",
        version=1,
        title="P",
        family="policy",
        access="public",
        status="current",
        effective_from=date(2026, 1, 1),
        body=body,
    )
    chunks = chunk_library([document], StructureChunker(max_tokens=50))

    assert len(chunks) >= 4
    assert all(len(ENCODING.encode(c.text)) <= 50 for c in chunks)
    assert all(c.headings == ("Long",) for c in chunks)
    assert all(c.text == body[c.start : c.end] for c in chunks)


def test_structure_chunker_on_an_article_without_headings(library):
    chunks = chunk_library([library.document("A002@1")], StructureChunker(max_tokens=400))

    assert len(chunks) == 1
    assert chunks[0].headings == ()
