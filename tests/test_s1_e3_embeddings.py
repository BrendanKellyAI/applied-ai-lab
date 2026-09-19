"""The S1 E3 episode sample: embedding similarity, run against a fake client, and its charts.

No network calls are made. The script runs from a copy in a temporary folder, because it writes
its results beside itself, and the committed results must never be overwritten by fake vectors.
"""

import json
import random
import runpy
import shutil
from pathlib import Path
from types import SimpleNamespace

import dotenv
import numpy as np
import openai
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e3-embeddings"
SCRIPT = EPISODE / "similarity.py"
MARKER = "# Everything below this line matches the slides."

# Exactly as shown on the slide.
SLIDE_LISTING = """import numpy as np
from openai import OpenAI

client = OpenAI()
query = "How do I get my money back?"
phrases = ["refund policy", "money back", "return an item",
           "reset password", "can't log in", "locked account",
           "Dublin weather"]
result = client.embeddings.create(
    model="text-embedding-3-small", input=[query, *phrases])
vectors = np.array([item.embedding for item in result.data])
q, rows = vectors[0], vectors[1:]
norms = np.linalg.norm(rows, axis=1) * np.linalg.norm(q)
scores = rows @ q / norms
for score, phrase in sorted(zip(scores, phrases), reverse=True):
    print(f"{score:.3f}  {phrase}")
"""

PHRASES = [
    "refund policy",
    "money back",
    "return an item",
    "reset password",
    "can't log in",
    "locked account",
    "Dublin weather",
]
PAIR_KINDS = ["negation", "numbers", "paraphrase", "unrelated"]
FAKE_DIMENSIONS = 8


def fake_vector(text: str) -> list[float]:
    """The same text always gets the same vector, so a test can work the scores out itself."""
    rng = random.Random(text)
    return [rng.uniform(-1, 1) for _ in range(FAKE_DIMENSIONS)]


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            model="text-embedding-3-small",
            data=[
                SimpleNamespace(index=index, embedding=fake_vector(text))
                for index, text in enumerate(kwargs["input"])
            ],
        )


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self) -> None:
        self.embeddings = FakeEmbeddings()
        FakeOpenAI.instances.append(self)


class EnvLoads:
    """Stands in for load_dotenv, so tests never read a real .env file."""

    def __init__(self) -> None:
        self.count = 0
        self.clients_before_first_load = None

    def __call__(self, *_args, **_kwargs) -> bool:
        if self.count == 0:
            self.clients_before_first_load = len(FakeOpenAI.instances)
        self.count += 1
        return False


@pytest.fixture
def env_loads(monkeypatch):
    loads = EnvLoads()
    monkeypatch.setattr(dotenv, "load_dotenv", loads)
    return loads


@pytest.fixture
def run(monkeypatch, tmp_path, env_loads, capsys):
    """Run a copy of the script against the fake client. Returns its output and results."""
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    copy = tmp_path / "similarity.py"
    shutil.copy(SCRIPT, copy)
    runpy.run_path(str(copy), run_name="__main__")
    results = json.loads((tmp_path / "results" / "embeddings.json").read_text(encoding="utf-8"))
    return SimpleNamespace(
        output=capsys.readouterr().out,
        results=results,
        calls=FakeOpenAI.instances[0].embeddings.calls,
    )


def _cosine(a: str, b: str) -> float:
    x, y = np.array(fake_vector(a)), np.array(fake_vector(b))
    return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y)))


# The slide listing ---------------------------------------------------------------------------


def test_the_script_contains_the_slide_listing_exactly():
    assert SLIDE_LISTING in SCRIPT.read_text(encoding="utf-8")


def test_only_the_env_loading_sits_between_the_marker_and_the_listing():
    source = SCRIPT.read_text(encoding="utf-8")
    between = source.split(MARKER, 1)[1].split(SLIDE_LISTING, 1)[0]
    assert between == "\nload_dotenv()\n\n"


def test_the_listing_fits_a_slide():
    lines = SLIDE_LISTING.rstrip("\n").split("\n")
    assert len(lines) <= 16
    assert max(len(line) for line in lines) <= 64


def test_the_listing_uses_no_lab_helpers_and_writes_no_results():
    assert "lab" not in SLIDE_LISTING.split()
    assert "from lab" not in SLIDE_LISTING
    assert "json" not in SLIDE_LISTING
    assert "write" not in SLIDE_LISTING


def test_env_loading_sits_above_the_marker_and_the_listing():
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.index("load_dotenv()") < source.index(SLIDE_LISTING)
    assert source.index(MARKER) < source.index(SLIDE_LISTING)


def test_env_is_loaded_before_the_client_is_created(run, env_loads):
    assert env_loads.count == 1
    assert env_loads.clients_before_first_load == 0


# Running against the fake client ------------------------------------------------------------


def test_the_query_and_phrases_are_embedded_in_one_call(run):
    assert run.calls[0] == {
        "model": "text-embedding-3-small",
        "input": ["How do I get my money back?", *PHRASES],
    }


def test_the_pairs_use_the_same_model_as_the_slide(run):
    assert run.calls[1]["model"] == run.calls[0]["model"]


def test_phrases_print_highest_score_first(run):
    query = "How do I get my money back?"
    expected = sorted(PHRASES, key=lambda phrase: -_cosine(query, phrase))
    printed = [line.split("  ", 1)[1] for line in run.output.splitlines()[: len(PHRASES)]]
    assert printed == expected


def test_printed_scores_match_cosine_similarity(run):
    query = "How do I get my money back?"
    for line in run.output.splitlines()[: len(PHRASES)]:
        score, phrase = line.split("  ", 1)
        assert float(score) == pytest.approx(_cosine(query, phrase), abs=0.0005)


def test_every_pair_is_scored_and_printed(run):
    assert [pair["kind"] for pair in run.results["pairs"]] == PAIR_KINDS
    for pair in run.results["pairs"]:
        assert pair["score"] == pytest.approx(_cosine(pair["first"], pair["second"]))
        assert f"{pair['kind']}: {pair['first']} / {pair['second']}" in run.output


def test_the_results_record_every_text_vector_score_and_the_run(run):
    results = run.results
    assert results["model_requested"] == "text-embedding-3-small"
    assert results["model_returned"] == "text-embedding-3-small"
    assert results["vector_length"] == FAKE_DIMENSIONS
    assert len(results["run_date_utc"]) == len("2026-09-19")
    assert [entry["phrase"] for entry in results["search"]["scores"]] == PHRASES
    texts = {"How do I get my money back?", *PHRASES}
    texts |= {text for pair in results["pairs"] for text in (pair["first"], pair["second"])}
    assert set(results["vectors"]) == texts
    for text, vector in results["vectors"].items():
        assert vector == pytest.approx(fake_vector(text))


# The committed results ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def chart():
    return load_sibling(EPISODE / "chart.py")


@pytest.fixture(scope="module")
def committed(chart):
    return chart.load()


def test_the_committed_results_name_a_model(committed):
    assert committed["model_returned"].startswith("text-embedding")


def test_the_committed_results_have_one_vector_per_text_all_the_same_length(committed):
    texts = {committed["search"]["query"], *PHRASES}
    for pair in committed["pairs"]:
        texts |= {pair["first"], pair["second"]}
    assert set(committed["vectors"]) == texts
    assert {len(vector) for vector in committed["vectors"].values()} == {committed["vector_length"]}


def test_the_committed_scores_are_the_cosine_of_the_committed_vectors(committed):
    vectors = {text: np.array(vector) for text, vector in committed["vectors"].items()}

    def cosine(a: str, b: str) -> float:
        return float(
            vectors[a] @ vectors[b] / (np.linalg.norm(vectors[a]) * np.linalg.norm(vectors[b]))
        )

    query = committed["search"]["query"]
    for entry in committed["search"]["scores"]:
        assert entry["score"] == pytest.approx(cosine(query, entry["phrase"]))
    for pair in committed["pairs"]:
        assert pair["score"] == pytest.approx(cosine(pair["first"], pair["second"]))


# The charts ---------------------------------------------------------------------------------


def _pairs(negation: float, numbers: float, paraphrase: float, unrelated: float) -> list[dict]:
    scores = dict(zip(PAIR_KINDS, (negation, numbers, paraphrase, unrelated), strict=True))
    return [{"kind": kind, "first": "a", "second": "b", "score": scores[kind]} for kind in scores]


def test_the_search_highlight_is_the_highest_phrase(chart):
    scores = [{"phrase": "a", "score": 0.2}, {"phrase": "b", "score": 0.7}]
    assert chart.top_phrase(scores) == "b"


def test_the_highest_warning_pair_is_flagged_when_it_beats_the_paraphrase(chart):
    assert chart.flagged_pair(_pairs(0.81, 0.86, 0.59, 0.10)) == "numbers"
    assert chart.flagged_pair(_pairs(0.90, 0.70, 0.59, 0.10)) == "negation"


def test_nothing_is_flagged_when_no_warning_pair_beats_the_paraphrase(chart):
    assert chart.flagged_pair(_pairs(0.50, 0.55, 0.60, 0.10)) is None


def test_the_committed_charts_apply_both_rules(chart, committed):
    assert (
        chart.top_phrase(committed["search"]["scores"])
        == max(committed["search"]["scores"], key=lambda entry: entry["score"])["phrase"]
    )
    paraphrase = next(p["score"] for p in committed["pairs"] if p["kind"] == "paraphrase")
    flagged = chart.flagged_pair(committed["pairs"])
    if flagged is not None:
        flagged_score = next(p["score"] for p in committed["pairs"] if p["kind"] == flagged)
        assert flagged_score > paraphrase


def test_both_charts_render_from_the_committed_results(chart, committed, tmp_path):
    written = chart.render(committed, tmp_path)
    assert sorted(path.name for path in written) == [
        "pairs-article.png",
        "pairs-slide.png",
        "pairs-slide.svg",
        "similarity-to-query-article.png",
        "similarity-to-query-slide.png",
        "similarity-to-query-slide.svg",
    ]


def _specs(chart, monkeypatch) -> dict:
    """Records the spec of every chart drawn, while still drawing it through the brand checks."""
    specs = {}
    real = chart.export_chart

    def recording(draw, out_dir, spec, *args, **kwargs):
        specs[spec.name] = spec
        return real(draw, out_dir, spec, *args, **kwargs)

    monkeypatch.setattr(chart, "export_chart", recording)
    return specs


def test_the_pairs_chart_says_so_when_nothing_is_highlighted(
    chart, committed, tmp_path, monkeypatch
):
    """Synthetic scores where no warning pair beats the paraphrase. The brand checks refuse a
    chart that both highlights something and carries this note, so it rendering at all proves
    nothing is in acid green."""
    specs = _specs(chart, monkeypatch)
    synthetic = {**committed, "pairs": _pairs(0.50, 0.55, 0.60, 0.10)}

    chart.render(synthetic, tmp_path)

    assert "nothing highlighted" in specs["pairs"].no_highlight_note
    assert (tmp_path / "pairs-slide.png").exists()


def test_the_pairs_chart_has_no_note_when_a_pair_is_highlighted(
    chart, committed, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render({**committed, "pairs": _pairs(0.81, 0.86, 0.59, 0.10)}, tmp_path)

    assert specs["pairs"].no_highlight_note is None


def test_both_footnotes_name_the_model(chart, committed, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(committed, tmp_path)

    for spec in specs.values():
        assert committed["model_returned"] in spec.footnote
    assert "Cosine similarity to: How do I get my money back?" in (
        specs["similarity-to-query"].footnote
    )
