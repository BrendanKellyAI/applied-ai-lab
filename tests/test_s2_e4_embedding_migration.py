"""The S2 E4 field note: the slide listing, the measures, the pass marks, the committed results,
the charts, and the README's verdicts.

No test calls the API, loads a model, or reaches the network. Hand-made arrays stand in for
vectors, except where a test rechecks the committed results against the committed vectors.
"""

import json
import re
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import dotenv
import numpy as np
import pytest

from lab.experiments import load_sibling
from lab.scoring import wilson_interval

NOTE = Path(__file__).parents[1] / "field-notes" / "s2-e4-embedding-migration"
SCRIPT = NOTE / "migrate.py"
MARKER = "# Everything below this line matches the slides."
END_OF_LISTING = "\n# Not on the slides."
LISTING = '''import numpy as np


def top_k(query, index, k=5):
    """Rank stored vectors by cosine similarity to the query.
    Nothing here checks which model made either vector."""
    q = query / np.linalg.norm(query)
    m = index / np.linalg.norm(index, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return best, scores[best]'''
MARKS = {
    "claim1_max_mean_overlap": 3.5,
    "claim1_min_losses": 5,
    "claim2a_max_hits": 10,
    "claim2c_max_old_half_recall": 0.10,
    "claim2c_max_gap_points": 10,
    "claim3_min_k_points": 15,
    "claim3_min_w_factor": 2,
    "claim3_min_w_articles": 5,
    "claim4_max_gap_percent": 1,
    "control_min_mean_overlap": 4.9,
    "control_max_flips": 2,
}


@pytest.fixture(scope="module")
def modules():
    sys.path.insert(0, str(NOTE))
    real = dotenv.load_dotenv
    dotenv.load_dotenv = lambda *_a, **_k: False  # never read a real .env in a test
    try:
        migrate = load_sibling(SCRIPT)
    finally:
        dotenv.load_dotenv = real
    return SimpleNamespace(
        migrate=migrate,
        measure=load_sibling(NOTE / "measure.py"),
        chart=load_sibling(NOTE / "chart.py"),
    )


@pytest.fixture(scope="module")
def config(modules):
    return modules.migrate.load_config()


@pytest.fixture(scope="module")
def committed(modules):
    return modules.chart.load()


def _listing() -> str:
    source = SCRIPT.read_text(encoding="utf-8")
    return source.split(MARKER, 1)[1].split(END_OF_LISTING, 1)[0].strip("\n")


# The slide listing ---------------------------------------------------------------------------


def test_the_listing_matches_the_pinned_text():
    assert _listing() == LISTING


def test_the_listing_fits_a_slide():
    lines = _listing().split("\n")
    assert len(lines) <= 16
    assert max(len(line) for line in lines) <= 64


def test_the_listing_imports_nothing_from_lab():
    assert "lab" not in re.findall(r"\w+", _listing())


def test_every_retrieval_condition_ranks_through_top_k():
    rest = SCRIPT.read_text(encoding="utf-8").split(END_OF_LISTING, 1)[1]
    assert "def top_k" not in rest
    assert "argsort" not in rest and "@" not in rest.replace("@ q", "")
    body = rest.split("def rank(", 1)[1].split("\ndef ", 1)[0]
    assert "top_k(query, index, k)" in body
    scores = rest.split("def all_scores(", 1)[1].split("\ndef ", 1)[0]
    assert "top_k(query, index, len(index))" in scores


def test_top_k_on_a_hand_made_example(modules):
    index = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.0]])
    best, scores = modules.migrate.top_k(np.array([2.0, 0.1]), index, k=3)
    assert best.tolist() == [0, 2, 1]
    assert scores[0] == pytest.approx(2 / np.linalg.norm([2.0, 0.1]))


def test_top_k_ignores_vector_length(modules):
    index = np.array([[10.0, 0.0], [0.0, 0.1]])
    assert modules.migrate.top_k(np.array([0.0, 5.0]), index, k=1)[0].tolist() == [1]


def test_a_query_of_the_wrong_length_raises(modules):
    """Claim 2b, the loud failure: 3,072 values against a 1,536-dimension index."""
    with pytest.raises(ValueError):
        modules.migrate.top_k(np.ones(3072), np.ones((4, 1536)))
    assert modules.migrate.loud_failure() == "builtins.ValueError"


def test_the_same_length_from_another_model_raises_nothing(modules):
    """Claim 2a, the silent failure: any 1,536 values are accepted."""
    rng = np.random.default_rng(1)
    best, _ = modules.migrate.top_k(rng.normal(size=1536), rng.normal(size=(4, 1536)))
    assert len(best) == 4


# Shortening ----------------------------------------------------------------------------------


def test_shortening_keeps_the_first_values_and_rescales_to_length_one(modules):
    vectors = np.array([[3.0, 4.0, 12.0], [1.0, 0.0, 9.0]])
    short = modules.measure.shorten(vectors, 2)
    assert short.shape == (2, 2)
    assert np.allclose(short, [[0.6, 0.8], [1.0, 0.0]])
    assert np.allclose(np.linalg.norm(short, axis=1), 1)


def test_row_cosines(modules):
    a = np.array([[1.0, 0.0], [1.0, 1.0]])
    b = np.array([[2.0, 0.0], [-1.0, -1.0]])
    assert modules.measure.row_cosines(a, b).tolist() == pytest.approx([1.0, -1.0])


def test_index_bytes(modules):
    assert modules.measure.index_bytes(300, 1536) == 1_843_200
    assert modules.measure.index_bytes(300, 3072) == 3_686_400


# Overlap, losses and gains -------------------------------------------------------------------


def test_overlap_losses_and_gains_on_a_hand_made_example(modules):
    tops_a = [["a", "b", "c"], ["a", "b", "c"], ["d", "e", "f"]]
    tops_b = [["c", "b", "a"], ["a", "x", "y"], ["x", "y", "z"]]
    out = modules.measure.compare(tops_a, tops_b, [True, True, False], [True, False, True], k=3)
    assert out["overlaps"] == [3, 1, 0]
    assert out["mean_overlap"] == pytest.approx(4 / 3)
    assert out["distribution"] == [1, 1, 0, 1]
    assert out["losses"] == [1]
    assert out["gains"] == [2]
    assert out["flips"] == 2


def test_random_floor_is_two_of_120(modules):
    assert modules.measure.random_floor(5, 300, 120) == 2


# The threshold -------------------------------------------------------------------------------


def test_the_threshold_is_the_tenth_percentile(modules):
    scores = [float(n) for n in range(11)]  # 0 to 10: the 10th percentile is exactly 1
    assert modules.measure.threshold(scores, 10) == pytest.approx(1.0)


def test_k_and_w_on_a_hand_made_example(modules):
    scores = np.array(
        [
            [0.9, 0.5, 0.2],  # right is column 0: kept, one wrong at or above 0.5
            [0.4, 0.6, 0.5],  # right is column 0: missed, two wrong at or above 0.5
        ]
    )
    out = modules.measure.keep_and_wrong(scores, [0, 0], 0.5)
    assert out["K"] == 0.5
    assert out["W"] == 1.5


def test_w_factor(modules):
    assert modules.measure.w_factor(2, 6) == 3
    assert modules.measure.w_factor(6, 2) == 3
    assert modules.measure.w_factor(0, 0) == 1
    assert modules.measure.w_factor(0, 3) == float("inf")


# Verdicts, at and on either side of each pass mark -------------------------------------------


@pytest.mark.parametrize(
    ("overlap", "losses", "expected"),
    [
        (3.5, 5, "held"),
        (3.4, 6, "held"),
        (3.6, 9, "failed"),
        (2.0, 4, "failed"),
    ],
)
def test_claim1_verdict(modules, overlap, losses, expected):
    assert modules.measure.claim1(overlap, losses, MARKS)["verdict"] == expected


@pytest.mark.parametrize(
    ("hits", "raised", "expected"),
    [
        (10, False, "held"),
        (9, False, "held"),
        (11, False, "failed"),
        (0, True, "failed"),
    ],
)
def test_claim2a_verdict(modules, hits, raised, expected):
    assert modules.measure.claim2a(hits, raised, MARKS)["verdict"] == expected


@pytest.mark.parametrize(
    ("old_half", "migrated", "full", "expected"),
    [
        (0.10, 0.80, 0.70, "held"),  # both marks exactly met
        (0.05, 0.75, 0.80, "held"),
        (0.11, 0.80, 0.80, "failed"),  # old half too high
        (0.00, 0.80, 0.69, "failed"),  # gap of 11 points
    ],
)
def test_claim2c_verdict(modules, old_half, migrated, full, expected):
    assert modules.measure.claim2c(old_half, migrated, full, MARKS)["verdict"] == expected


@pytest.mark.parametrize(
    ("k_old", "k_new", "w_old", "w_new", "expected"),
    [
        (0.90, 0.75, 10, 10, "held"),  # K moves exactly 15 points
        (0.90, 0.76, 10, 10, "failed"),  # K moves 14 points
        (0.90, 0.90, 5, 10, "held"),  # W doubles and rises by 5
        (0.90, 0.90, 10, 5, "held"),  # W halves and falls by 5
        (0.90, 0.90, 2, 6, "failed"),  # W triples but rises by only 4
        (0.90, 0.90, 10, 19, "failed"),  # W rises by 9 but less than double
    ],
)
def test_claim3_verdict(modules, k_old, k_new, w_old, w_new, expected):
    assert modules.measure.claim3(k_old, k_new, w_old, w_new, MARKS)["verdict"] == expected


@pytest.mark.parametrize(
    ("gaps", "expected"),
    [
        ({"old": 1.0, "new": -1.0}, "held"),
        ({"old": 0.0, "new": 1.01}, "failed"),
    ],
)
def test_claim4_verdict(modules, gaps, expected):
    assert modules.measure.claim4(gaps, MARKS)["verdict"] == expected


@pytest.mark.parametrize(
    ("overlap", "flips", "expected"),
    [
        (4.9, 2, "held"),
        (5.0, 0, "held"),
        (4.89, 0, "failed"),
        (5.0, 3, "failed"),
    ],
)
def test_control_verdict(modules, overlap, flips, expected):
    assert modules.measure.control(overlap, flips, MARKS)["verdict"] == expected


# The migrated split and the pilot ------------------------------------------------------------


def _toy_corpus():
    articles = [
        {"article_id": f"A{i:03d}", "role": "lookalike" if i >= 16 else None} for i in range(24)
    ]
    types = ["identifier"] * 4 + ["paraphrase"] * 4 + ["shared"] * 4
    questions = [{"article_id": f"A{i:03d}", "type": t} for i, t in enumerate(types)]
    return articles, questions


def test_the_split_is_seeded_half_and_balanced_by_type(modules):
    articles, questions = _toy_corpus()
    split = modules.measure.migrated_split
    first = split(articles, questions, 7)
    assert first == split(articles, questions, 7)
    assert first != split(articles, questions, 8)
    assert len(first) == 12
    report = modules.measure.split_report(questions, first)
    assert all(cell == {"migrated": 2, "old": 2} for cell in report.values())
    lookalikes = [a for a in first if int(a[1:]) >= 16]
    assert len(lookalikes) == 4


def test_the_committed_split_is_150_and_balanced(modules, config):
    articles, questions = modules.migrate.load_corpus(config)
    committed = json.loads((NOTE / "results" / "migrated_articles.json").read_text("utf-8"))
    assert committed["seed"] == config["seed"] == 20260929
    assert committed["article_ids"] == modules.measure.migrated_split(
        articles, questions, config["seed"]
    )
    assert len(committed["article_ids"]) == 150
    assert all(
        cell == {"migrated": 20, "old": 20} for cell in committed["answers_by_type"].values()
    )


def test_the_pilot_takes_four_of_each_type_and_twenty_articles(modules, config):
    articles, questions = modules.migrate.load_corpus(config)
    chosen, picked = modules.measure.pilot_selection(articles, questions, config["seed"], 4, 8)
    assert len(chosen) == 20 and len(picked) == 12
    assert sorted(questions[i]["type"] for i in picked) == sorted(
        ["identifier", "paraphrase", "shared"] * 4
    )
    assert {questions[i]["article_id"] for i in picked} <= set(chosen)


# The estimate --------------------------------------------------------------------------------


def test_the_estimate_matches_the_committed_counts_with_no_network(modules, config, monkeypatch):
    def refuse(*_a, **_k):
        raise AssertionError("The estimate must not reach the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    counts = modules.migrate.estimate(config)
    committed = json.loads((NOTE / "results" / "local_token_counts.json").read_text("utf-8"))
    assert counts == committed
    assert counts["full_run_total"] == sum(counts["full_run_calls"].values())
    assert counts["corpus_tokens"] == sum(counts["articles"].values())


def test_the_estimate_prints_no_prices(modules, config, capsys):
    modules.migrate.print_estimate(modules.migrate.estimate(config))
    out = capsys.readouterr().out
    assert "tokens" in out
    assert not re.search(r"[$£€]|\bcost\b|\bprice\b|\bUSD\b", out, re.IGNORECASE)


# The committed results -----------------------------------------------------------------------


def test_the_results_record_models_route_seed_and_date(committed):
    assert committed["route"] == "B"
    assert committed["seed"] == 20260929
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", committed["run_date_utc"])
    for name, rows in committed["models"].items():
        for row in rows:
            assert row["model_returned"].startswith(row["model_requested"]), name
            assert row["vector_length"] in (1536, 3072)


def test_recall_recomputes_from_the_stored_hits(modules, committed):
    types = committed["question_types"]
    for name, rows in committed["conditions"].items():
        if rows:
            hits = [r["hit"] for r in rows]
            assert modules.measure.recall_by_type(types, hits) == committed["recall"][name]
            assert all(
                r["hit"] == (a in r["top"]) for r, a in zip(rows, committed["answers"], strict=True)
            )


def test_every_verdict_recomputes_from_its_stored_measures(modules, committed):
    m, marks, v = modules.measure, committed["pass_marks"], committed["verdicts"]
    old, new, ctrl = (committed["conditions"][c] for c in ("old", "new", "control"))
    swap = modules.migrate.pair(old, new, committed["top_k"])
    assert swap["mean_overlap"] == committed["swap"]["mean_overlap"]
    assert m.claim1(swap["mean_overlap"], len(swap["losses"]), marks) == v["claim1"]
    control = modules.migrate.pair(old, ctrl, committed["top_k"])
    assert m.control(control["mean_overlap"], control["flips"], marks) == v["control"]
    cross = committed["recall"]["cross"]["all"]["hits"]
    assert m.claim2a(cross, committed["claim2a_raised"], marks) == v["claim2a"]
    splits = committed["half_migrated"]["splits"]
    assert (
        m.claim2c(
            splits["half_new_queries"]["old"]["all"]["rate"],
            splits["half_new_queries"]["migrated"]["all"]["rate"],
            splits["new_short"]["migrated"]["all"]["rate"],
            marks,
        )
        == v["claim2c"]
    )
    t = committed["claim3"]
    assert (
        m.claim3(t["old"]["K"], t["new_same_t"]["K"], t["old"]["W"], t["new_same_t"]["W"], marks)
        == v["claim3"]
    )
    tokens = committed["tokens"]
    assert m.claim4(tokens["corpus_gap_percent"], marks) == v["claim4"]


def test_the_threshold_and_k_recompute_from_the_stored_scores(modules, committed):
    t = committed["claim3"]
    scores = t["right_scores"]
    assert modules.measure.threshold(scores["old"], 10) == pytest.approx(t["old"]["t"])
    assert modules.measure.threshold(scores["new"], 10) == pytest.approx(t["new_retuned"]["t"])
    for side, key in (("old", "old"), ("new", "new_same_t"), ("new", "new_retuned")):
        kept = np.mean([s >= t[key]["t"] for s in scores[side]])
        assert kept == pytest.approx(t[key]["K"])


def test_the_pipeline_check_reads_the_committed_e3_figure(committed):
    e3 = json.loads(
        (NOTE.parents[1] / "episodes" / "s2-e3-search" / "results" / "search.json").read_text(
            "utf-8"
        )
    )
    hits = sum(1 for q in e3["questions"] if (r := q["ranks"]["vector"]) and r <= 5)
    assert committed["pipeline_check"]["e3_hits"] == hits


def test_the_results_contain_no_prices(committed):
    text = json.dumps(committed)
    assert not re.search(r"[$£€]|\"cost|\"price|usd", text, re.IGNORECASE)


@pytest.fixture(scope="module")
def vectors(committed):
    path = NOTE / "results" / "vectors.npz"
    if not committed["vectors"]["committed"]:
        pytest.skip("vectors were not committed")
    with np.load(path) as data:
        return {name: data[name] for name in data.files}


def test_the_committed_vectors_reproduce_old_and_new_rankings(modules, committed, vectors):
    ids = vectors["article_ids"].tolist()
    k = committed["top_k"]
    for name, q, a in (("old", "old_q", "old_a"), ("new", "new_q", "new_a")):
        rows = modules.migrate.rank(vectors[q], vectors[a], ids, committed["answers"], k)
        assert [r["top"] for r in rows] == [r["top"] for r in committed["conditions"][name]]


def test_the_committed_vectors_reproduce_w(modules, committed, vectors):
    ids = vectors["article_ids"].tolist()
    answers = [ids.index(a) for a in committed["answers"]]
    config = {"threshold_percentile": 10}
    out = modules.migrate.claim3_measures(vectors, answers, config)
    for key in ("old", "new_same_t", "new_retuned"):
        assert out[key]["W"] == pytest.approx(committed["claim3"][key]["W"])


def test_the_committed_vectors_have_the_recorded_shapes(committed, vectors):
    assert vectors["old_a"].shape == (300, 1536) and vectors["new_a"].shape == (300, 3072)
    assert vectors["old_q"].shape == (120, 1536) and vectors["new_q"].shape == (120, 3072)
    assert vectors["dimension_check"].shape == (5, 1536)
    total = sum(vectors[n].nbytes for n in committed["vectors"]["arrays"])
    assert total == committed["vectors"]["bytes"] <= 10_000_000


# The charts ----------------------------------------------------------------------------------


def _entry(hits: int, n: int = 120) -> dict:
    rate, low, high = wilson_interval(hits, n)
    return {"hits": hits, "n": n, "rate": rate, "low": low, "high": high}


def test_the_recall_highlight_needs_intervals_apart(modules):
    rule = modules.chart.recall_winner
    assert rule({"recall": {"old": {"all": _entry(60)}, "new": {"all": _entry(100)}}}) == 1
    assert rule({"recall": {"old": {"all": _entry(95)}, "new": {"all": _entry(91)}}}) is None


def test_the_charts_rebuild_from_the_committed_results(modules, committed, tmp_path):
    written = modules.chart.render(committed, tmp_path)
    assert sorted(p.name for p in written) == sorted(
        f"{name}-{layout}"
        for name in ("recall-by-model", "top5-overlap", "mixing")
        for layout in ("slide.png", "slide.svg", "article.png")
    )


def test_failed_claims_render_with_nothing_highlighted(modules, committed, tmp_path):
    """The brand checks refuse a chart that highlights and carries a note, so rendering with
    every rule unmet proves nothing is green."""
    unmet = json.loads(json.dumps(committed))
    unmet["swap"]["mean_overlap"] = 4.0
    unmet["verdicts"]["claim2c"]["verdict"] = "failed"
    assert modules.chart.render(unmet, tmp_path)


def test_no_text_anywhere_uses_an_em_dash():
    for path in [*NOTE.glob("*.py"), *NOTE.glob("*.yaml"), NOTE / "README.md", Path(__file__)]:
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path.name


# The README agrees with the results ----------------------------------------------------------

README_CLAIMS = {
    "claim1": "Claim 1",
    "claim2a": "Claim 2a",
    "claim2c": "Claim 2c",
    "claim3": "Claim 3",
    "claim4": "Claim 4",
    "control": "The re-embed control",
}


@pytest.mark.parametrize("key", list(README_CLAIMS))
def test_the_readme_states_each_verdict_once_and_matches_the_results(committed, key):
    readme = (NOTE / "README.md").read_text(encoding="utf-8")
    name = re.escape(README_CLAIMS[key])
    stated = re.findall(rf"{name}(?![0-9a-z]) (held|failed)", readme)
    assert stated, f"The README gives no verdict for {README_CLAIMS[key]}"
    assert set(stated) == {committed["verdicts"][key]["verdict"]}
