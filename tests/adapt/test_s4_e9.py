"""S4 E9: the teacher's configs, the teacher-label tuning option and the claims."""

import json
from pathlib import Path

import pytest
import yaml

from lab.adapt.definitions import Definitions
from lab.adapt.experiment import Experiment
from lab.adapt.items import triage_items
from lab.adapt.prompts import label_json
from lab.adapt.requests import arm_requests, load_inputs
from lab.adapt.run import predictions_path, write_jsonl
from lab.adapt.tune import _files, _plan, teacher_labelled, train_subset
from lab.adapt.tune_config import TuneConfig
from lab.experiments import load_sibling
from lab.providers.base import request_hash

ROOT = Path(__file__).parents[2]
EPISODES = ROOT / "episodes"
E9 = EPISODES / "s4-e9-distillation-a-big-model-teaches-a-small-one"
E2 = EPISODES / "s4-e2-instructions-first"
DATA = ROOT / "datasets" / "halvard-tasks"
claims = load_sibling(E9 / "claims.py")


@pytest.mark.parametrize("name", ["config.dev.yaml", "config.yaml"])
def test_teacher_sends_e2s_definitions_requests_so_it_is_cached(name):
    e9 = Experiment.load(E9 / name)
    e2 = Experiment.load(E2 / name)
    inputs = load_inputs(e9)
    ours = arm_requests(e9, e9.arm("e9-teacher"), inputs)
    theirs = arm_requests(e2, e2.arm("e2-definitions"), inputs)
    assert [request_hash(r) for r in ours.values()] == [request_hash(r) for r in theirs.values()]


def test_train_config_labels_every_train_message_with_the_teacher():
    experiment = Experiment.load(E9 / "config.train.yaml")
    assert experiment.split == "train" and len(load_inputs(experiment).items) == 1600
    assert [a.name for a in experiment.arms] == ["e9-teacher"]
    assert experiment.arm("e9-teacher").instructions == "definitions"


def test_reused_arms_read_e5s_files():
    experiment = Experiment.load(E9 / "config.yaml")
    for arm in ("e9-student-untuned", "e9-student-true-labels"):
        assert predictions_path(experiment, arm).exists()


def _teacher_job(tmp_path: Path, replies: dict[str, str]) -> TuneConfig:
    teacher = tmp_path / "teacher.jsonl"
    write_jsonl(teacher, [{"id": k, "text": v} for k, v in replies.items()])
    raw = {"episode": "s4-test", "task": "a", "arm": "e9-x", "base_model": "Qwen/Qwen3-0.6B",
           "train_size": 2, "teacher": "teacher.jsonl", "data": str(DATA),
           "eval_splits": ["dev"]}  # fmt: skip
    path = tmp_path / "tune.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return TuneConfig.load(path)


def test_teacher_labels_replace_the_true_ones_and_bad_replies_are_dropped(tmp_path):
    train = triage_items(DATA, "train")
    wrong = train[0].label.model_copy(update={"route": "other"})
    replies = {train[0].id: label_json(wrong), train[1].id: "not json"}
    replies |= {i.id: label_json(i.label) for i in train[2:]}
    job = _teacher_job(tmp_path, replies)
    kept, dropped = teacher_labelled(train, job)
    assert dropped == [train[1].id] and len(kept) == 1599
    assert kept[0].label.route == "other"
    files, rows = _files(job)
    assert len(rows) == 2 and len(train_subset(job)) == 2
    plan = _plan(job, files, rows)
    assert plan["teacher"]["dropped"] == 1 and plan["teacher"]["file"] == "teacher.jsonl"
    labels = Definitions.load(DATA / "routes.yaml")
    assert labels is not None


def test_teacher_labels_are_for_task_a_only():
    with pytest.raises(ValueError, match="Task A"):
        TuneConfig.model_validate(
            {
                "episode": "e",
                "task": "b",
                "arm": "a",
                "base_model": "m",
                "train_size": 0,
                "teacher": "t.jsonl",
            }  # fmt: skip
        )


def test_preregistration_states_every_claim_and_the_terms():
    text = (E9 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E9 / "claims.yaml").read_text(encoding="utf-8"))
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text
    assert "Permitted Exception" in text and "services-agreement" in text


def test_claims_on_synthetic_arms():
    spec = claims.load_claims_file()
    right = {f"i{n}": True for n in range(40)}
    wrong = {f"i{n}": n >= 30 for n in range(40)}
    arms = {
        "e9-teacher": right,
        "e9-student-untuned": wrong,
        "e9-student-teacher-labels": right,
        "e9-student-true-labels": right,
    }
    held = [c.held for c in claims.evaluate({"rate": 0.97}, arms, spec)]
    assert held == [True, True, True, True]
    worse = {**arms, "e9-student-teacher-labels": wrong}
    result = claims.evaluate({"rate": 0.90}, worse, spec)
    assert [c.held for c in result] == [False, False, False, False]
    assert claims.verdict(result[0]) == "Failed"
    assert json.dumps([c.model_dump() for c in result])
