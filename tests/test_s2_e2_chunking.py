"""The S2 E2 episode sample: the chunker, the facts, the hit rules, the results, and the charts.

No test calls the API, loads a model, or reaches the network. The corpus tests build a novel
from repeated synthetic prose rather than downloading a book.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import dotenv
import numpy as np
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s2-e2-chunking"
SCRIPT = EPISODE / "chunking.py"
MARKER = "# Everything below this line matches the slides."
END_OF_LISTING = "\n# Not on the slides."
SIZES = [64, 128, 256, 512, 1024, 2048]
PROSE = "The lamp on the quay burned low and the tide drew out past the harbour wall. "


@pytest.fixture(scope="module")
def modules():
    sys.path.insert(0, str(EPISODE))
    real = dotenv.load_dotenv
    dotenv.load_dotenv = lambda *_a, **_k: False  # never read a real .env in a test
    try:
        chunking = load_sibling(SCRIPT)
    finally:
        dotenv.load_dotenv = real
    return SimpleNamespace(
        chunking=chunking,
        facts=load_sibling(EPISODE / "facts.py"),
        corpus=load_sibling(EPISODE / "corpus.py"),
        measure=load_sibling(EPISODE / "measure.py"),
        chart=load_sibling(EPISODE / "chart.py"),
    )


def _listing() -> str:
    source = SCRIPT.read_text(encoding="utf-8")
    return source.split(MARKER, 1)[1].split(END_OF_LISTING, 1)[0].strip("\n")


# The slide listing ---------------------------------------------------------------------------


def test_the_listing_fits_a_slide():
    lines = _listing().split("\n")
    assert len(lines) <= 16
    assert max(len(line) for line in lines) <= 64


def test_the_listing_uses_no_lab_helpers():
    assert "lab" not in _listing().split()
    assert "from lab" not in _listing()
    assert "import tiktoken" in _listing()


def test_the_experiment_calls_the_listed_chunker():
    source = SCRIPT.read_text(encoding="utf-8").split(END_OF_LISTING, 1)[1]
    assert "chunk(novel.text, size, overlap)" in source
    assert "def chunk" not in source


# The chunker ---------------------------------------------------------------------------------


def test_windows_are_the_chunk_size_with_a_shorter_last_one(modules):
    enc = modules.chunking.enc
    text = PROSE * 40
    total = len(enc.encode(text))
    chunks = modules.chunking.chunk(text, 64)
    lengths = [len(enc.encode(piece)) for piece in chunks]
    assert all(length == 64 for length in lengths[:-1])
    assert lengths[-1] == total - 64 * (len(chunks) - 1)
    assert 0 < lengths[-1] <= 64


def test_overlap_moves_each_window_on_by_size_minus_overlap(modules):
    enc = modules.chunking.enc
    tokens = enc.encode(PROSE * 40)
    chunks = modules.chunking.chunk(PROSE * 40, 64, 16)
    for index, piece in enumerate(chunks[:-1]):
        assert enc.encode(piece) == tokens[index * 48 : index * 48 + 64]
    assert enc.encode(chunks[-1]) == tokens[(len(chunks) - 1) * 48 :]
    # The last window reaches the end, and no window after it repeats only overlap.
    assert (len(chunks) - 1) * 48 + 64 >= len(tokens) > (len(chunks) - 2) * 48 + 64


def test_chunks_without_overlap_rebuild_the_original_tokens(modules):
    enc = modules.chunking.enc
    text = PROSE * 33 + "The end."
    assert enc.encode("".join(modules.chunking.chunk(text, 50))) == enc.encode(text)


def test_a_short_text_is_one_chunk(modules):
    assert modules.chunking.chunk("A short line.", 64, 16) == ["A short line."]


# The facts -----------------------------------------------------------------------------------


def test_facts_are_deterministic_from_the_seed(modules):
    config = modules.facts.load_config()
    first = modules.facts.facts_from_config(config)
    assert first == modules.facts.facts_from_config(config)
    assert first != modules.facts.make_facts(config["seed"] + 1, 6, 10, 5)


def test_the_committed_facts_match_the_seed(modules):
    config = modules.facts.load_config()
    assert modules.facts.load() == modules.facts.facts_from_config(config)


def test_there_are_60_one_and_30_two_sentence_facts_each_naming_its_own_place(modules):
    facts = modules.facts.load()
    assert sum(f.kind == "one" for f in facts) == 60
    assert sum(f.kind == "two" for f in facts) == 30
    assert all(len(f.sentences) == (1 if f.kind == "one" else 2) for f in facts)
    places = [f.place for f in facts]
    assert len(set(places)) == len(places)
    for fact in facts:
        assert fact.place in fact.question
        assert fact.place in fact.sentences[0]
        others = [p for p in places if p != fact.place]
        assert not any(other in fact.text or other in fact.question for other in others)


def test_facts_sit_at_least_2500_tokens_apart(modules):
    config = modules.facts.load_config()
    facts = [f for f in modules.facts.load() if f.novel_index == 0]
    raw = f"Title\n\n{'Front matter line.' * 10}\n\n" + PROSE * 5000
    novel = modules.corpus.build_novel(0, raw, facts, config, SimpleNamespace(id=1, title="Test"))
    enc = modules.corpus.encoding()
    starts = modules.corpus.fact_token_starts(novel.text, facts, enc)
    assert len(starts) == 15
    assert min(b - a for a, b in zip(starts, starts[1:], strict=False)) >= 2500
    for fact in facts:
        assert novel.text.count(fact.text) == 1


def test_spacing_below_the_minimum_is_refused(modules):
    with pytest.raises(modules.corpus.CorpusError):
        modules.corpus.check_spacing([0, 2600, 4000], 2500)


# The hit rules -------------------------------------------------------------------------------

ONE = ("The lighthouse at Carrigmore was painted by a woman named Orla Venn.",)
TWO = (
    "The harbourmaster at Kilrane kept a ledger of every ship.",
    "She stored it in a blue tin under the stairs.",
)


def test_a_one_sentence_fact_needs_the_whole_sentence(modules):
    holds = modules.measure.holds_fact
    assert holds(f"Rain fell. {ONE[0]} The sea rose.", ONE)
    assert not holds("The lighthouse at Carrigmore was painted by a woman", ONE)


def test_a_two_sentence_fact_split_across_two_chunks_is_a_miss(modules):
    chunks = [f"Earlier prose. {TWO[0]}", f"{TWO[1]} Later prose."]
    assert modules.measure.holders(chunks, TWO) == []
    assert modules.measure.holders([*chunks, " ".join(TWO)], TWO) == [2]


def test_rank_is_that_of_the_best_answer_chunk(modules):
    similarities = np.array([0.9, 0.2, 0.5, 0.7])
    assert modules.measure.first_hit_rank(similarities, [1, 2]) == 3
    assert modules.measure.first_hit_rank(similarities, [0]) == 1
    assert modules.measure.first_hit_rank(similarities, []) is None


def test_the_floor_never_samples_the_answer(modules):
    import random

    similarities = np.array([1.0] + [0.1] * 30)
    floor = modules.measure.floor_similarity(similarities, [0], 20, random.Random(1))
    assert floor == pytest.approx(0.1)


# The committed results -----------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed(modules):
    return modules.chart.load()


def test_every_condition_is_present(committed):
    found = {(c["chunk_size"], c["overlap_fraction"]) for c in committed["conditions"]}
    assert found == {(size, overlap) for size in SIZES for overlap in (0.0, 0.25)}
    for condition in committed["conditions"]:
        expected = int(condition["chunk_size"] * condition["overlap_fraction"])
        assert condition["overlap_tokens"] == expected


def test_the_results_match_their_schema(committed):
    assert committed["model_returned"].startswith("text-embedding-3-small")
    assert committed["tokeniser"] == "cl100k_base"
    assert len(committed["run_date_utc"]) == len("2026-09-25")
    assert isinstance(committed["seed"], int)
    assert committed["embedding_tokens_reported"] > 0
    assert committed["facts"] == {"one": 60, "two": 30}
    assert "vectors" not in json.dumps(committed)
    for condition in committed["conditions"]:
        assert condition["chunks"] > 0
        assert len(condition["questions"]) == 90
        for row in condition["questions"]:
            assert row["rank"] is None or row["rank"] >= 1
            assert (row["rank"] is None) == (row["answer_chunks"] == 0)
            assert (row["answer_similarity"] is None) == (row["answer_chunks"] == 0)
            assert -1 <= row["floor"] <= 1 and -1 <= row["ceiling"] <= 1


def test_the_claims_are_assessed_from_the_committed_results(modules, committed):
    claims = modules.measure.assess(committed)
    assert set(claims) == {"claim1", "claim2", "claim3"}
    assert claims["claim2"]["sizes"] == [64, 128]


# The charts ----------------------------------------------------------------------------------


def _entry(hits: int, n: int = 30) -> dict:
    from lab.scoring import wilson_interval

    rate, low, high = wilson_interval(hits, n)
    return {"hits": hits, "n": n, "rate": rate, "low": low, "high": high}


def test_the_recall_highlight_is_the_single_top_size(modules):
    assert modules.chart.best_bar([_entry(3), _entry(9), _entry(5)]) == 1
    assert modules.chart.best_bar([_entry(9), _entry(9), _entry(5)]) is None


def test_the_overlap_highlight_needs_intervals_apart(modules):
    rule = modules.chart.overlap_gain_bar
    assert rule([_entry(5), _entry(20)], [_entry(25), _entry(21)]) == 0
    assert rule([_entry(20), _entry(20)], [_entry(24), _entry(21)]) is None
    assert rule([_entry(20)], [_entry(18)]) is None


def test_the_charts_rebuild_from_the_committed_results(modules, committed, tmp_path):
    written = modules.chart.render(committed, tmp_path)
    assert sorted(path.name for path in written) == sorted(
        f"{name}-{layout}"
        for name in ("recall-by-size", "similarity-by-size", "two-sentence-overlap")
        for layout in ("slide.png", "slide.svg", "article.png")
    )


def test_a_tie_renders_with_nothing_highlighted(modules, committed, tmp_path):
    """Every question a hit at every size: the tie note is set, and the brand checks refuse a
    chart that both highlights and carries that note, so rendering proves nothing is green."""
    tied = json.loads(json.dumps(committed))
    for condition in tied["conditions"]:
        for row in condition["questions"]:
            row.update(rank=1, answer_chunks=1, answer_similarity=0.5)
    assert modules.chart.render(tied, tmp_path)
