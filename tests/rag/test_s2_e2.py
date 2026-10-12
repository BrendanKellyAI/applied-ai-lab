import json
from pathlib import Path

import pytest
import yaml

from lab.cache import ResponseCache
from lab.experiments import load_sibling
from lab.providers.mock import MockProvider
from lab.rag.analysis import below, changed_value, gives_old_value
from lab.rag.config import load_episode
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.pipeline import RunContext, run_condition
from lab.rag.score import Proportion
from lab.runner import Runner, RunnerSettings
from tests.rag.conftest import condition_named
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mock_models import respond

E2 = Path(__file__).parents[2] / "episodes" / "s2-e2-first-rag-system"


@pytest.fixture(scope="module")
def e2_config():
    return load_episode(E2 / "config.yaml").config


def test_the_pre_registration_and_config_agree(e2_config):
    marks = e2_config.pass_marks
    text = (E2 / "PREREGISTRATION.md").read_text(encoding="utf-8")

    assert marks == {
        "h1_before_prompt_exceeds_inside": True,
        "h2_types_below_single": ["policy_two_sentence", "policy_heading"],
        "h3_identifier_below_paraphrase": True,
        "h4_followup_below_single": True,
        "h5a_restricted_leak_share": 0.5,
        "h5a_other_type_leaks_at_least": 1,
        "h5b_stale_in_prompt_share": 0.5,
        "h5b_old_value_answers_at_least": 1,
        "h6a_absent_not_found_at_least": 0.75,
        "h6b_leaked_or_deleted_not_found_at_most": 0.5,
    }
    for phrase in (
        "the before-prompt count is greater than the inside count",
        "both point estimates are lower",
        "on at least half of the 40",
        "on at least one item of another type",
        "at least one answer gives the old value",
        "not-found is at least 75%",
        "not-found is at most 50%",
    ):
        assert phrase in " ".join(text.split()), phrase


def test_the_e2_config_changes_nothing(e2_config):
    episode = load_episode(E2 / "config.yaml")

    assert [c.changed for c in episode.conditions] == [()]
    assert episode.config.items == "test"


def test_changed_value_widens_to_whole_tokens():
    assert changed_value("The period is 24 months.", "The period is 12 months.") == ("24", "12")
    assert changed_value("It costs £34.00 now.", "It costs £112.00 now.") == ("£34.00", "£112.00")
    assert changed_value("Charge of 21% applies.", "Charge of 9% applies.") == ("21%", "9%")


def test_gives_old_value_needs_the_old_without_the_new():
    assert gives_old_value("It is 12 months.", "24", "12")
    assert not gives_old_value("It was 12, now 24 months.", "24", "12")
    assert not gives_old_value("It is 112 months.", "24", "12")


def test_below_means_intervals_do_not_overlap():
    assert below(Proportion.of(2, 40), Proportion.of(38, 40))
    assert not below(Proportion.of(18, 40), Proportion.of(22, 40))


@pytest.fixture
def analysed(episode, library, tmp_path, e2_config):
    provider = MockProvider(respond=respond())
    runner = Runner(
        providers={"openai": provider, "anthropic": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    embedder = Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))
    results = episode.folder / "results"
    context = RunContext(
        episode=episode, library=library, embedder=embedder, runner=runner, results=results
    )
    run_condition(context, condition_named(episode, "baseline"), library.test)
    staged = episode.model_copy(
        update={
            "config": episode.config.model_copy(
                update={"pass_marks": e2_config.pass_marks, "episode": "s2-e2-first-rag-system"}
            )
        }
    )
    module = load_sibling(E2 / "analyse.py")
    text = module.analyse(staged, results, pilot=False)
    return episode, results, text


def test_analysis_writes_claims_examples_and_charts(analysed):
    episode, results, text = analysed
    report = json.loads((results / "analysis.json").read_text(encoding="utf-8"))

    assert [c["id"] for c in report["claims"]] == ["H1", "H2", "H3", "H4", "H5", "H6"]
    assert set(report["worked_examples"]) == {"right", "search_missed", "model_misread"}
    assert report["numbers"]["search"]["total"] == 7
    for chart in ("recall-by-type", "where-lost", "scoreboard"):
        assert (results / "charts" / f"{chart}-slide.png").exists()
    assert "H1" in text and "search:" in text


def test_analysis_records_the_first_scoreboard_row_and_reference(analysed):
    episode, *_ = analysed
    season = episode.folder.parents[1] / "season2"
    rows = json.loads((season / "scoreboard.json").read_text(encoding="utf-8"))
    history = yaml.safe_load((season / "reference_history.yaml").read_text(encoding="utf-8"))

    assert [r["episode"] for r in rows] == ["s2-e2-first-rag-system"]
    assert rows[0]["before"] is None and rows[0]["joined"] is True
    assert history[0]["stage_changed"] is None


def test_h5_finds_the_leak_and_the_stale_version(analysed):
    _, results, _ = analysed
    report = json.loads((results / "analysis.json").read_text(encoding="utf-8"))
    h5 = next(c for c in report["claims"] if c["id"] == "H5")

    assert h5["detail"]["restricted_leaked"] == 1
    assert h5["detail"]["version_items"] == 1
