import json
from pathlib import Path

import pytest
import yaml

from lab.cache import ResponseCache
from lab.experiments import load_sibling
from lab.providers.mock import MockProvider
from lab.rag.chunk import FixedChunker, StructureChunker
from lab.rag.cli import results_folder
from lab.rag.config import load_episode
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.judge import Verdict
from lab.rag.pipeline import RunContext, run_condition
from lab.rag.score import Proportion, SeasonNumbers
from lab.runner import Runner, RunnerSettings
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mini_corpus import REFERENCE
from tests.rag.mock_models import respond
from tests.rag.test_rag_judge_check import _log

E4 = Path(__file__).parents[2] / "episodes" / "s2-e4-chunking"
claims = load_sibling(E4 / "claims.py")


@pytest.fixture(scope="module")
def e4():
    return load_episode(E4 / "config.yaml")


def test_every_condition_changes_the_chunker_only(e4):
    assert [c.changed for c in e4.conditions][0] == ()
    assert all(c.changed == ("chunk",) for c in e4.conditions[1:])
    assert len(e4.conditions) == 16
    assert {c.name for c in e4.conditions if c.measure == "full"} == {
        "baseline",
        "fixed-512-0",
        "structure-1024",
    }


def test_the_dev_config_matches_the_test_config(e4):
    dev = load_episode(E4 / "config.dev.yaml")

    assert dev.config.items == "dev" and all(c.measure == "search" for c in dev.conditions)
    assert [c.pipeline for c in dev.conditions] == [c.pipeline for c in e4.conditions]


def test_pass_marks_name_real_conditions_and_match_the_pre_registration(e4):
    marks = e4.config.pass_marks
    names = {c.name for c in e4.conditions}
    text = " ".join((E4 / "PREREGISTRATION.md").read_text(encoding="utf-8").split())

    assert {marks["c1_long"], marks["c1_reference"]} <= names
    assert {n for pair in marks["c3_pairs"] for n in pair} <= names
    for phrase in (
        "fixed 1,024 with no overlap sits below fixed 256 with no overlap",
        "25% overlap leaves fewer cut evidence spans than no overlap",
        "at each of the three sizes",
        "its search number (recall at 5 on the 400",
        "its answer number is not lower",
    ):
        assert phrase in text, phrase


def test_dev_results_never_land_on_test_results(e4):
    dev = load_episode(E4 / "config.dev.yaml")

    assert results_folder(e4, pilot=False).name == "results"
    assert results_folder(dev, pilot=False).name == "results-dev"
    assert results_folder(dev, pilot=True).parent.name == "results-dev"


def _hits(found: list[bool], kind="policy_single"):
    return [
        _log(
            f"I{i}", kind, Verdict(declined=False, correct=f, faithful=True, reason="r")
        ).model_copy(update={"evidence_rank": 1 if f else None})
        for i, f in enumerate(found)
    ]


def test_choice_takes_the_best_dev_recall_then_the_smaller_chunk():
    marks = {"policy_types": ["policy_single"]}
    chunkers = {
        "baseline": FixedChunker(size=256),
        "fixed-128-0": FixedChunker(size=128),
        "fixed-512-0": FixedChunker(size=512),
        "structure-512": StructureChunker(max_tokens=512),
        "structure-1024": StructureChunker(max_tokens=1024),
    }
    dev = {
        "baseline": _hits([True, True, False]),
        "fixed-128-0": _hits([True, True, False]),
        "fixed-512-0": _hits([True, False, False]),
        "structure-512": _hits([True, False, False]),
        "structure-1024": _hits([True, True, True]),
    }

    assert claims.choose_full(dev, chunkers, marks, 5) == {
        "fixed": "fixed-128-0",
        "structure": "structure-1024",
    }


def _numbers(search: int, answer: int) -> SeasonNumbers:
    return SeasonNumbers(
        search=Proportion.of(search, 400),
        answer=Proportion.of(answer, 400),
        not_found=Proportion.of(56, 120),
        leaks=Proportion.of(51, 480),
    )


def test_join_needs_search_clear_of_the_reference_and_answers_not_lower():
    full = {
        "baseline": _numbers(239, 217),
        "a": _numbers(285, 216),
        "b": _numbers(280, 230),
        "c": _numbers(276, 240),
    }

    assert claims.join(full) == {"passed": ["b"], "joined": "b"}
    assert claims.join({"baseline": _numbers(239, 217), "c": _numbers(276, 240)})["joined"] is None


def test_c5_needs_answers_to_move_with_search():
    assert claims.c5({"baseline": _numbers(239, 217), "a": _numbers(260, 230)}).held
    assert not claims.c5({"baseline": _numbers(239, 217), "a": _numbers(260, 210)}).held


def test_mcnemar_counts_items_found_by_only_one():
    ref = _hits([True, True, False, False, False])
    other = _hits([True, False, True, True, True])
    result = claims.mcnemar(ref, other, 5)

    assert (result["only_other"], result["only_reference"]) == (3, 1)
    assert result["p_value"] == pytest.approx(0.625)


@pytest.fixture
def analysed(tmp_path, library_dir, e4):
    season = tmp_path / "season2"
    season.mkdir()
    (season / "reference.yaml").write_text(yaml.safe_dump(REFERENCE), encoding="utf-8")
    folder = tmp_path / "episodes" / "s2-e4-chunking"
    folder.mkdir(parents=True)
    raw = yaml.safe_load((E4 / "config.yaml").read_text(encoding="utf-8"))
    raw.update(base="../../season2/reference.yaml", library=str(library_dir))
    (folder / "config.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    episode = load_episode(folder / "config.yaml")
    provider = MockProvider(respond=respond())
    runner = Runner(
        providers={"openai": provider, "anthropic": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    from lab.rag.corpus import load_library

    library = load_library(library_dir)
    embedder = Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))
    results = folder / "results"
    context = RunContext(
        episode=episode, library=library, embedder=embedder, runner=runner, results=results
    )
    for condition in episode.conditions:
        run_condition(context, condition, library.test)
    text = load_sibling(E4 / "analyse.py").analyse(episode, results, pilot=False)
    return folder, results, text


def test_analysis_reports_every_condition_the_claims_and_the_join(analysed):
    folder, results, text = analysed
    report = json.loads((results / "analysis.json").read_text(encoding="utf-8"))

    assert len(report["conditions"]) == 16
    assert set(report["full"]) == {"baseline", "fixed-512-0", "structure-1024"}
    assert [c["id"] for c in report["claims"]] == ["C1", "C2", "C3", "C4", "C5"]
    assert set(report["join"]) == {"passed", "joined"}
    assert set(report["paired"]) == {"fixed-512-0", "structure-1024"}
    for chart in ("policy-recall", "headings", "cut-evidence", "scoreboard"):
        assert (results / "charts" / f"{chart}-slide.png").exists(), chart
    assert "Structure 1024 +heads" in text


def test_analysis_records_the_e4_scoreboard_row(analysed):
    folder, *_ = analysed
    rows = json.loads((folder.parents[1] / "season2" / "scoreboard.json").read_text("utf-8"))

    assert rows[-1]["episode"] == "s2-e4-chunking" and rows[-1]["stage_changed"] == "chunk"
    assert rows[-1]["before"] is not None
