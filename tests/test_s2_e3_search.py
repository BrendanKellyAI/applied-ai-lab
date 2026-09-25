"""The S2 E3 episode sample: identifiers, word checks, BM25 tokenising, fusion, results, charts.

No test calls the API, loads a model, or reaches the network.
"""

import json
import random
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import dotenv
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s2-e3-search"
SCRIPT = EPISODE / "search.py"
MARKER = "# Everything below this line matches the slides."
END_OF_LISTING = "\n# Not on the slides."
FORMAT = re.compile(r"^(E|KX)-\d{4}$")


@pytest.fixture(scope="module")
def modules():
    sys.path.insert(0, str(EPISODE))
    real = dotenv.load_dotenv
    dotenv.load_dotenv = lambda *_a, **_k: False  # never read a real .env in a test
    try:
        search = load_sibling(SCRIPT)
    finally:
        dotenv.load_dotenv = real
    return SimpleNamespace(
        search=search,
        plan=load_sibling(EPISODE / "plan.py"),
        generate=load_sibling(EPISODE / "generate.py"),
        measure=load_sibling(EPISODE / "measure.py"),
        chart=load_sibling(EPISODE / "chart.py"),
    )


@pytest.fixture(scope="module")
def config(modules):
    return modules.plan.load_config()


def _listing() -> str:
    source = SCRIPT.read_text(encoding="utf-8")
    return source.split(MARKER, 1)[1].split(END_OF_LISTING, 1)[0].strip("\n")


# The slide listing ---------------------------------------------------------------------------


def test_the_listing_fits_a_slide():
    lines = _listing().split("\n")
    assert len(lines) <= 16
    assert max(len(line) for line in lines) <= 64


def test_the_listing_is_standalone():
    assert "import" not in _listing()
    assert "lab" not in _listing().split()


def test_the_experiment_calls_the_listed_fusion():
    rest = SCRIPT.read_text(encoding="utf-8").split(END_OF_LISTING, 1)[1]
    assert 'fuse([keyword, vector_ids], k=config["rrf_k"])' in rest
    assert "def fuse" not in rest


# Reciprocal rank fusion ----------------------------------------------------------------------


def test_fusion_on_a_hand_worked_example(modules):
    # k = 1 keeps the sums readable:
    #   a: 1/2 + 1/4 = 0.75   b: 1/3 + 1/2 = 0.833   c: 1/4 + 1/3 = 0.583
    assert modules.search.fuse([["a", "b", "c"], ["b", "c", "a"]], k=1) == ["b", "a", "c"]


def test_fusion_with_one_ranking_keeps_its_order(modules):
    assert modules.search.fuse([["x", "y", "z"]]) == ["x", "y", "z"]


def test_a_document_in_only_one_ranking_still_scores(modules):
    assert set(modules.search.fuse([["a"], ["b"]])) == {"a", "b"}


# Identifiers and look-alikes -----------------------------------------------------------------


def test_identifiers_are_well_formed_and_deterministic(modules, config):
    groups = modules.plan.make_identifier_groups(config["seed"], 40)
    assert groups == modules.plan.make_identifier_groups(config["seed"], 40)
    assert groups != modules.plan.make_identifier_groups(config["seed"] + 1, 40)
    members = [m for g in groups for m in g.members]
    assert len(members) == len(set(members)) == 120
    assert all(FORMAT.match(m) for m in members)
    assert {g.kind for g in groups} == {"error code", "part number"}


def test_each_lookalike_is_one_digit_from_its_target_and_no_one_elses(modules, config):
    groups = modules.plan.make_identifier_groups(config["seed"], 40)
    apart = modules.plan.one_digit_apart
    for index, group in enumerate(groups):
        assert all(apart(group.target, other) for other in group.lookalikes)
        outsiders = [m for j, g in enumerate(groups) if j != index for m in g.members]
        assert not any(apart(m, o) for m in group.members for o in outsiders)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("E-4471", "E-4417", True),  # adjacent swap
        ("E-4471", "E-4474", True),  # one changed digit
        ("E-4471", "E-1474", False),  # two changed digits
        ("E-4471", "KX-4471", False),  # different kind
        ("E-4471", "E-4471", False),  # the same
    ],
)
def test_one_digit_apart(modules, a, b, expected):
    assert modules.plan.one_digit_apart(a, b) is expected


def test_the_committed_corpus_follows_the_identifier_rules(modules, config):
    corpus = json.loads((EPISODE / "corpus.json").read_text(encoding="utf-8"))
    groups = modules.plan.make_identifier_groups(config["seed"], 40)
    low, high = config["article_tokens"]
    assert len(corpus["articles"]) == 300
    expected = {m for g in groups for m in g.members}
    found = set()
    for article in corpus["articles"]:
        assert low <= article["tokens"] <= high
        ids = modules.plan.identifiers_in(article["text"])
        assert ids == ([article["identifier"]] if article["identifier"] else [])
        found |= set(ids)
    assert found == expected


# The word checks and BM25 tokenising ---------------------------------------------------------


def test_bm25_splits_an_identifier_into_letters_and_digits(modules):
    assert modules.plan.words("What does error E-4471 mean?") == [
        "what",
        "does",
        "error",
        "e",
        "4471",
        "mean",
    ]


def test_a_paraphrase_sharing_a_content_word_is_refused(modules, config):
    article = "Descale the Brio kettle every four weeks in hard water areas."
    problem = modules.generate.question_problem
    assert problem(config, "paraphrase", "How often should I descale my jug?", article)
    assert (
        problem(config, "paraphrase", "How often should I clear limescale from my jug?", article)
        is None
    )


def test_stop_words_do_not_count_as_shared(modules, config):
    stop = set(config["stop_words"])
    assert modules.plan.shared_words("How do I do it?", "How it is done.", stop) == set()


def test_a_shared_word_question_needs_enough_of_the_article(modules, config):
    article = "Descale the Brio kettle every four weeks in hard water areas."
    problem = modules.generate.question_problem
    assert problem(config, "shared", "How often should I descale my Brio kettle?", article) is None
    assert problem(config, "shared", "How often should I clean my jug?", article)


def test_the_committed_questions_pass_their_checks(modules, config):
    corpus = json.loads((EPISODE / "corpus.json").read_text(encoding="utf-8"))
    articles = {a["article_id"]: a for a in corpus["articles"]}
    questions = json.loads((EPISODE / "questions.json").read_text(encoding="utf-8"))["questions"]
    assert sorted(q["type"] for q in questions) == sorted(
        ["identifier", "paraphrase", "shared"] * 40
    )
    for q in questions:
        text = articles[q["article_id"]]["text"]
        assert modules.generate.question_problem(config, q["type"], q["question"], text) is None
    for q in (q for q in questions if q["type"] == "identifier"):
        assert articles[q["article_id"]]["role"] == "target"
        assert articles[q["article_id"]]["identifier"] in q["question"]


# The committed results -----------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed(modules):
    return modules.chart.load()


def test_the_results_match_their_schema(modules, committed):
    assert committed["embedding_model_returned"].startswith("text-embedding-3-small")
    assert committed["generation_model_returned"] == ["gpt-6-astra"]
    assert committed["tokeniser"] == "cl100k_base"
    assert committed["bm25"]["version"] == "0.2.2"
    assert committed["rrf_k"] == 60
    assert isinstance(committed["seed"], int)
    usage = committed["tokens_reported"]
    assert usage["generation"]["input_tokens"] > 0 and usage["generation"]["output_tokens"] > 0
    assert usage["embedding"] > 0
    assert "vector" not in json.dumps(committed).replace('"vector"', "")
    for row in committed["questions"]:
        assert set(row["ranks"]) == set(modules.measure.METHODS)
        assert all(r is None or 1 <= r <= committed["record_depth"] for r in row["ranks"].values())
        if row["type"] == "identifier":
            for method, ranks in row["lookalike_ranks"].items():
                assert len(ranks) == 2
                assert isinstance(row["lookalike_above"][method], bool)


def test_every_method_and_type_is_present(modules, committed):
    table = modules.measure.table(committed)
    assert set(table) == {"identifier", "paraphrase", "shared", "all"}
    for kind in ("identifier", "paraphrase", "shared"):
        assert all(table[kind][m]["recall_k"]["n"] == 40 for m in modules.measure.METHODS)


def test_the_claims_are_assessed(modules, committed):
    assert set(modules.measure.assess(committed)) == {"claim1", "claim2", "claim3"}


# The charts ----------------------------------------------------------------------------------


def _entry(hits: int, n: int = 40) -> dict:
    from lab.scoring import wilson_interval

    rate, low, high = wilson_interval(hits, n)
    return {"hits": hits, "n": n, "rate": rate, "low": low, "high": high}


def test_the_recall_highlight_is_the_single_best_method_overall(modules):
    rule = modules.chart.best_overall
    assert rule({"all": {"keyword": _entry(5), "vector": _entry(9), "hybrid": _entry(7)}}) == 1
    assert rule({"all": {"keyword": _entry(9), "vector": _entry(9), "hybrid": _entry(7)}}) is None


def test_the_lookalike_highlight_needs_clear_intervals(modules):
    rule = modules.chart.most_lookalike_errors
    assert rule({"keyword": _entry(0), "vector": _entry(20), "hybrid": _entry(3)}) == 1
    assert rule({"keyword": _entry(0), "vector": _entry(8), "hybrid": _entry(6)}) is None


def test_the_charts_rebuild_from_the_committed_results(modules, committed, tmp_path):
    written = modules.chart.render(committed, tmp_path)
    assert sorted(p.name for p in written) == sorted(
        f"{name}-{layout}"
        for name in ("recall-by-question-type", "lookalikes")
        for layout in ("slide.png", "slide.svg", "article.png")
    )


def test_a_tie_renders_with_nothing_highlighted(modules, committed, tmp_path):
    """Every question found first by every method: both notes are set, and the brand checks
    refuse a chart that highlights and carries a note, so rendering proves nothing is green."""
    tied = json.loads(json.dumps(committed))
    for row in tied["questions"]:
        row["ranks"] = {m: 1 for m in row["ranks"]}
        row["lookalike_above"] = {m: False for m in row["lookalike_above"]}
    assert modules.chart.render(tied, tmp_path)
    assert modules.chart.best_overall(modules.chart.recall_cells(tied)) is None


def test_the_sample_prints_questions_beside_their_articles(modules, capsys):
    random.seed(0)
    modules.search.print_sample(EPISODE, 1)
    out = capsys.readouterr().out
    assert out.count("[paraphrase]") == 20 and out.count("[identifier]") == 20


def test_every_stop_word_is_a_word(config):
    """YAML reads a bare on, off, or no as a boolean, which would silently drop it."""
    assert all(isinstance(word, str) for word in config["stop_words"])
    assert {"no", "off", "on"} <= set(config["stop_words"])
