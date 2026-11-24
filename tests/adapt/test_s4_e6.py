"""S4 E6: the learning-curve jobs are E5's job at smaller, nested sizes, and the configs read
E5's results for the points E6 reuses."""

import json
from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.tune import _files, _plan, load_record, train_subset
from lab.adapt.tune_config import TuneConfig
from lab.experiments import load_sibling

EPISODES = Path(__file__).parents[2] / "episodes"
E6 = EPISODES / "s4-e6-how-much-data-does-tuning-need"
E5_SHORT = EPISODES / "s4-e5-does-fine-tuning-beat-a-good-prompt" / "tune-short.yaml"
SIZES = (50, 200, 800)


@pytest.mark.parametrize("size", SIZES)
def test_job_is_e5s_short_job_at_a_smaller_size(size):
    job = TuneConfig.load(E6 / f"tune-{size}.yaml")
    e5 = TuneConfig.load(E5_SHORT)
    assert job.train_size == size and job.arm == f"e6-tuned-{size}"
    ignore = {"episode", "arm", "train_size", "folder"}
    assert job.model_dump(exclude=ignore) == e5.model_dump(exclude=ignore)


@pytest.mark.parametrize("size", SIZES)
def test_subsets_are_nested_inside_e5s_training_set(size):
    full = [i.id for i in train_subset(TuneConfig.load(E5_SHORT))]
    subset = [i.id for i in train_subset(TuneConfig.load(E6 / f"tune-{size}.yaml"))]
    assert subset == full[:size]


@pytest.mark.parametrize("size", SIZES)
def test_committed_job_record_matches_the_frozen_data(size):
    config = TuneConfig.load(E6 / f"tune-{size}.yaml")
    record = load_record(config.arm_folder)
    files, rows = _files(config)
    assert record is not None
    assert record["plan"] == json.loads(json.dumps(_plan(config, files, rows)))


@pytest.mark.parametrize(("name", "split"), [("config.dev.yaml", "dev"), ("config.yaml", "test")])
def test_configs_read_e5s_files_for_the_reused_points(name, split):
    experiment = Experiment.load(E6 / name)
    assert experiment.split == split and all(a.external for a in experiment.arms)
    reused = {"e6-reference", "e6-tuned-0", "e6-tuned-1600"}
    for arm in experiment.arms:
        path = experiment.path(arm.predictions)
        assert path.name == f"predictions-{split}.jsonl"
        if arm.name in reused:
            assert path.exists()


def test_preregistration_states_every_claim_and_mark():
    text = (E6 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E6 / "claims.yaml").read_text(encoding="utf-8"))
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text
    assert "800 or fewer" in text and spec["claims"]["C2"]["size_at_most"] == 800


claims = load_sibling(E6 / "claims.py")


def _by_item(split):
    files = claims.prediction_files(split)
    return files, {arm: claims.fully_right_by_item(path, split) for arm, path in files.items()}


def test_claims_on_the_test_results():
    spec = claims.load_claims_file()
    files, by_item = _by_item("test")
    recall_of = {arm: claims.safety_recall(files[arm], "test") for arm in spec["sizes"]}
    result = {c.id: c for c in claims.evaluate(by_item, recall_of, spec)}
    assert {k: c.held for k, c in result.items()} == {
        "C1": True,
        "C2": True,
        "C3": True,
        "C4": True,
    }
    assert result["C2"].detail["smallest_matching"] == "e6-tuned-800"
    assert claims.verdict(result["C1"]) == "Held"


def test_claims_fail_or_go_untested_on_the_far_side():
    spec = claims.load_claims_file()
    right = {f"i{n}": True for n in range(40)}
    wrong = {f"i{n}": n >= 30 for n in range(40)}
    by_item = {
        "e6-reference": right,
        "e6-tuned-50": right,
        "e6-tuned-200": wrong,
        "e6-tuned-800": wrong,
        "e6-tuned-1600": right,
    }
    recall = {"count": 1, "total": 2, "rate": 0.5}
    result = {c.id: c for c in claims.evaluate(by_item, {"e6-tuned-50": recall}, spec)}
    assert result["C1"].held is False
    assert result["C2"].detail["smallest_matching"] == "e6-tuned-50"
    assert result["C3"].held is False and result["C4"].held is False
    none_match = {**by_item, "e6-tuned-50": wrong, "e6-tuned-1600": wrong}
    untested = {c.id: c for c in claims.evaluate(none_match, {}, spec)}
    assert untested["C2"].held is False and untested["C4"].held is None
    assert claims.verdict(untested["C4"]) == "Not tested"
    assert claims.verdict(untested["C2"]) == "Failed"
