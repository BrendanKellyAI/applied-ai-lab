"""S4 E5: the tuning jobs and experiment configs match the pre-registration."""

import json
from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.requests import arm_requests, load_inputs
from lab.adapt.tune import _files, _plan, load_record
from lab.adapt.tune_config import TuneConfig
from lab.experiments import load_sibling
from lab.providers.base import request_hash

EPISODES = Path(__file__).parents[2] / "episodes"
E5 = EPISODES / "s4-e5-does-fine-tuning-beat-a-good-prompt"
E2 = EPISODES / "s4-e2-instructions-first"
QWEN_06 = ("Qwen/Qwen3-0.6B", "c1899de289a04d12100db370d81485cdf75e47ca")
STATUS = {
    "tune-untuned-0-6b.yaml": "succeeded",
    "tune-short.yaml": "succeeded",
    "tune-one-line.yaml": "cancelled",
}
JOBS = {
    "tune-untuned-0-6b.yaml": ("e5-untuned-0-6b", 0, "definitions"),
    "tune-short.yaml": ("e5-tuned-short", 1600, "short"),
    "tune-one-line.yaml": ("e5-tuned-one-line", 1600, "one_line"),
}


@pytest.mark.parametrize("name", sorted(JOBS))
def test_jobs_are_pinned_and_use_the_defaults(name):
    config = TuneConfig.load(E5 / name)
    arm, size, instructions = JOBS[name]
    assert (config.arm, config.train_size, config.instructions) == (arm, size, instructions)
    assert (config.base_model, config.base_revision) == QWEN_06
    assert config.eval_splits == ("dev", "test")
    assert config.lora == type(config.lora)() and config.training == type(config.training)()


@pytest.mark.parametrize("name", sorted(JOBS))
def test_committed_job_record_matches_the_frozen_data(name):
    config = TuneConfig.load(E5 / name)
    record = load_record(config.arm_folder)
    assert record is not None
    assert [a["status"] for a in record["attempts"]] == [STATUS[name]]
    files, rows = _files(config)
    assert record["plan"] == json.loads(json.dumps(_plan(config, files, rows)))


@pytest.mark.parametrize(("name", "size"), [("config.dev.yaml", 200), ("config.yaml", 600)])
def test_experiments_point_at_each_jobs_predictions(name, size):
    experiment = Experiment.load(E5 / name)
    assert len(load_inputs(experiment).items) == size
    external = {a.name: a.predictions for a in experiment.arms if a.external}
    # Amendment 1: the one-line tuned arm was not run.
    assert set(external) == {"e5-untuned-0-6b", "e5-tuned-short"}
    for arm, path in external.items():
        assert path == Path(f"results/{arm}/predictions-{experiment.split}.jsonl")


def test_reference_sends_e2s_definitions_requests_so_it_is_cached():
    e5 = Experiment.load(E5 / "config.yaml")
    e2 = Experiment.load(E2 / "config.yaml")
    inputs = load_inputs(e5)
    ours = arm_requests(e5, e5.arm("e5-reference"), inputs)
    theirs = arm_requests(e2, e2.arm("e2-definitions"), inputs)
    assert [request_hash(r) for r in ours.values()] == [request_hash(r) for r in theirs.values()]


def test_preregistration_states_the_pilot_rule_and_every_claim():
    text = (E5 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E5 / "claims.yaml").read_text(encoding="utf-8"))
    assert f"at least {spec['pilot']['json_valid_at_least']} of 200" in text
    assert spec["pilot"]["fallback_revision"] in text
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text


claims = load_sibling(E5 / "claims.py")


def test_claims_on_the_test_results():
    spec = claims.load_claims_file()
    by_item = {
        arm: claims.fully_right_by_item(arm, "test")
        for arm in ("e5-reference", "e5-untuned-0-6b", "e5-tuned-short")
    }
    assert sum(by_item["e5-tuned-short"].values()) == 592
    tokens = {"e5-reference": 945.1, "e5-tuned-short": 112.1}
    recall = claims.safety_recall("e5-tuned-short", "test")
    result = {c.id: c.held for c in claims.evaluate(by_item, tokens, recall, spec)}
    assert result == {"C1": True, "C2": True, "C3": True, "C4": True, "C5": None}


def test_claims_fail_on_the_far_side():
    spec = claims.load_claims_file()
    ids = [f"i{n}" for n in range(100)]
    good = {i: True for i in ids}
    bad = {i: n >= 50 for n, i in enumerate(ids)}
    by_item = {"e5-tuned-short": bad, "e5-untuned-0-6b": bad, "e5-reference": good}
    tokens = {"e5-reference": 100.0, "e5-tuned-short": 50.0}
    recall = {"count": 9, "total": 10, "rate": 0.9}
    result = {c.id: c.held for c in claims.evaluate(by_item, tokens, recall, spec)}
    assert result == {"C1": False, "C2": False, "C3": False, "C4": False, "C5": None}
    assert claims.verdict(claims.c5(spec["claims"]["C5"])) == "Not tested"


def test_input_tokens_use_one_tokeniser_for_every_arm():
    assert claims.mean_input_tokens("tune-short.yaml", "dev") < 0.2 * claims.mean_input_tokens(
        "tune-untuned-0-6b.yaml", "dev"
    )
