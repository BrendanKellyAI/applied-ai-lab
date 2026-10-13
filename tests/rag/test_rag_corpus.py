import json
from datetime import date

import pytest
from pydantic import ValidationError

from lab.rag.corpus import CorpusError, Item, Span, load_items, load_library, parse_document
from tests.rag.mini_corpus import CORPUS_VERSION


def test_loads_every_document_version(library):
    assert library.corpus_version == CORPUS_VERSION
    assert len(library.documents) == 10
    assert {d.key for d in library.documents if d.doc_id == "POL-WAR"} == {
        "POL-WAR@1",
        "POL-WAR@2",
    }


def test_front_matter_becomes_metadata(library):
    old = library.document("POL-WAR@1")

    assert old.status == "superseded"
    assert old.effective_to == date(2026, 2, 28)
    assert old.superseded_by == "POL-WAR@2"
    assert library.document("INT-PRC@1").access == "staff"
    assert library.document("DEL-00@1").deleted_on == date(2026, 6, 30)


def test_body_excludes_front_matter_exactly():
    text = (
        "---\ndoc_id: A9\nversion: 1\ntitle: T\nfamily: article\nproducts: []\n"
        "access: public\nstatus: current\n---\nLine one.\n\nLine two.\n"
    )

    assert parse_document(text).body == "Line one.\n\nLine two.\n"


def test_span_text_reads_the_labelled_characters(library):
    item = next(i for i in library.test if i.id == "IDENT-000")

    assert library.span_text(item.evidence[0]) == "Error E-2194 means the drain pump is blocked."


def test_items_load_with_history_and_spans(library):
    followup = next(i for i in library.test if i.id == "FOLLOW-000")

    assert [t.role for t in followup.history] == ["user", "assistant"]
    assert followup.resolved_question == "How long is the Tessa dishwasher warranty?"
    assert len(library.test) == 10
    assert len(library.dev) == 1


def test_changed_file_stops_the_load_and_names_it(library_dir):
    path = library_dir / "documents" / "A000@1.md"
    path.write_text(path.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")

    with pytest.raises(CorpusError, match="A000@1.md"):
        load_library(library_dir)


def test_file_missing_from_manifest_stops_the_load(library_dir):
    (library_dir / "documents" / "A999@1.md").write_text("---\n---\n", encoding="utf-8")

    with pytest.raises(CorpusError, match="A999@1.md"):
        load_library(library_dir)


def test_file_in_manifest_but_absent_stops_the_load(library_dir):
    (library_dir / "documents" / "A001@1.md").unlink()

    with pytest.raises(CorpusError, match="A001@1.md"):
        load_library(library_dir)


def test_span_must_lie_inside_its_document(library_dir):
    rows = (library_dir / "test.jsonl").read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["evidence"][0]["end"] = 10_000
    rows[0] = json.dumps(first)
    (library_dir / "test.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

    with pytest.raises(CorpusError, match="IDENT-000"):
        load_library(library_dir)


def test_span_needs_a_positive_length():
    with pytest.raises(ValidationError):
        Span(doc_id="A000", version=1, start=5, end=5)


def test_answerable_item_needs_evidence():
    with pytest.raises(ValidationError, match="evidence"):
        Item(id="X", type="t", asker="public", question="q", answerable=True, answer="a")


def test_unanswerable_item_needs_a_reason():
    with pytest.raises(ValidationError, match="reason"):
        Item(id="X", type="t", asker="public", question="q", answerable=False, answer="a")


def test_bad_json_line_names_the_line(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")

    with pytest.raises(CorpusError, match="line 1"):
        load_items(path)


def test_document_without_front_matter_is_refused():
    with pytest.raises(CorpusError, match="front matter"):
        parse_document("No front matter here.\n")
