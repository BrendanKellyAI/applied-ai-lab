import pytest

from lab.rag.chunk import FixedChunker, StructureChunker, WholeChunker, chunk_library
from lab.rag.corpus import Span
from lab.rag.judge import Verdict
from lab.rag.score import (
    ItemScore,
    code_check,
    cut_spans,
    distractor_above,
    evidence_rank,
    first_lost_stage,
    leaks,
    season_numbers,
    span_rank,
)


def _item(library, item_id):
    return next(i for i in library.test if i.id == item_id)


def _chunks(library, chunker=None):
    return chunk_library(library.documents, chunker or WholeChunker())


def _by_id(chunks, *ids):
    found = {c.chunk_id: c for c in chunks}
    return [found[i] for i in ids]


def test_span_rank_is_the_first_chunk_holding_the_whole_span(library):
    chunks = _chunks(library)
    span = _item(library, "IDENT-000").evidence[0]
    ranked = _by_id(chunks, "A001@1#0", "A000@1#0")

    assert span_rank(span, ranked) == 2
    assert span_rank(span, ranked[:1]) is None


def test_a_chunk_holding_part_of_a_span_is_not_a_hit(library):
    span = _item(library, "POL-HEAD-000").evidence[0]
    tiny = [c for c in _chunks(library, FixedChunker(size=3)) if c.doc_key == "POL-WAR@2"]

    assert span_rank(span, tiny) is None
    assert cut_spans((span,), tiny) == (span,)


def test_a_wrong_version_never_counts(library):
    span = _item(library, "VERSION-000").evidence[0]
    old = [c for c in _chunks(library) if c.doc_key == "POL-WAR@1"]

    assert span_rank(span, old) is None


def test_evidence_rank_needs_every_span(library):
    chunks = _chunks(library)
    item = _item(library, "TWOPART-000")
    ranked = _by_id(chunks, "A005@1#0", "A000@1#0", "A004@1#0")

    assert evidence_rank(item, ranked) == 3
    assert evidence_rank(item, ranked[:2]) is None


def test_distractor_above_the_evidence(library):
    chunks = _chunks(library)
    item = _item(library, "IDENT-000")

    assert distractor_above(item, _by_id(chunks, "A001@1#0", "A000@1#0"))
    assert not distractor_above(item, _by_id(chunks, "A000@1#0", "A001@1#0"))


def test_leaks_count_staff_chunks_reaching_a_public_asker(library):
    chunks = _chunks(library)
    prompt = _by_id(chunks, "INT-PRC@1#0", "A000@1#0")

    assert leaks("public", prompt) == ("INT-PRC@1#0",)
    assert leaks("staff", prompt) == ()


def test_code_check_needs_every_key_value(library):
    item = _item(library, "TWOPART-000")

    assert code_check(item, "Hold it 3 seconds, and book a free collection.")
    assert not code_check(item, "Hold it 3 seconds.")
    assert code_check(_item(library, "ABSENT-000"), "anything") is None


def _verdict(declined=False, correct=True, faithful=True):
    return Verdict(declined=declined, correct=correct, faithful=faithful, reason="r")


@pytest.mark.parametrize(
    ("ranks", "verdict", "expected"),
    [
        ({"cut": True}, _verdict(correct=False), "chunk"),
        ({"searched": None}, _verdict(correct=False), "search"),
        ({"searched": 3, "filtered": None}, _verdict(correct=False), "filter"),
        ({"searched": 3, "filtered": 3, "reranked": 9}, _verdict(correct=False), "rerank"),
        (
            {"searched": 3, "filtered": 3, "reranked": 3},
            _verdict(declined=True, correct=False),
            "prompt",
        ),
        ({"searched": 3, "filtered": 3, "reranked": 3}, _verdict(correct=False), "answer"),
        ({"searched": 3, "filtered": 3, "reranked": 3}, _verdict(), None),
    ],
)
def test_first_lost_stage(ranks, verdict, expected):
    trace = {"cut": False, "searched": 1, "filtered": 1, "reranked": 1, **ranks}

    assert first_lost_stage(trace, k=5, verdict=verdict) == expected


def test_first_lost_stage_without_a_verdict():
    trace = {"cut": False, "searched": 1, "filtered": 1, "reranked": 1}

    assert first_lost_stage(trace, k=5, verdict=None) == "unjudged"


def _score(item_id, **fields):
    base = {
        "item_id": item_id,
        "type": "t",
        "asker": "public",
        "answerable": True,
        "evidence_rank": 1,
        "leaks": (),
        "verdict": _verdict(),
    }
    return ItemScore(**{**base, **fields})


def test_season_numbers():
    scores = [
        _score("a"),
        _score("b", evidence_rank=6, verdict=_verdict(correct=False)),
        _score("c", verdict=_verdict(faithful=False)),
        _score("d", answerable=False, evidence_rank=None, verdict=_verdict(declined=True)),
        _score(
            "e",
            answerable=False,
            evidence_rank=None,
            leaks=("INT-PRC@1#0",),
            verdict=_verdict(declined=False, correct=False),
        ),
        _score("f", asker="staff", leaks=()),
    ]
    numbers = season_numbers(scores, k=5)

    assert (numbers.search.count, numbers.search.total) == (3, 4)
    assert (numbers.answer.count, numbers.answer.total) == (2, 4)
    assert (numbers.not_found.count, numbers.not_found.total) == (1, 2)
    assert (numbers.leaks.count, numbers.leaks.total) == (1, 5)
    assert numbers.search.low < 0.75 < numbers.search.high


def test_unjudged_items_count_against_the_answer_score():
    numbers = season_numbers([_score("a", verdict=None)], k=5)

    assert (numbers.answer.count, numbers.answer.total) == (0, 1)


def test_structure_chunks_keep_a_heading_dependent_span_whole(library):
    span: Span = _item(library, "POL-HEAD-000").evidence[0]
    chunks = _chunks(library, StructureChunker(max_tokens=400))

    assert cut_spans((span,), chunks) == ()
