"""S4 E7: the tuning job, experiment configs and judge check match the pre-registration."""

from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.requests import arm_requests, load_inputs
from lab.adapt.tune import train_subset
from lab.adapt.tune_config import TuneConfig
from lab.experiments import load_sibling
from lab.providers.base import request_hash

EPISODES = Path(__file__).parents[2] / "episodes"
E7 = EPISODES / "s4-e7-teaching-a-house-style"
E1 = EPISODES / "s4-e1-baseline"
E5_SHORT = EPISODES / "s4-e5-does-fine-tuning-beat-a-good-prompt" / "tune-short.yaml"
ARMS = ["e7-one-line", "e7-style-guide", "e7-guide-4-examples", "e7-tuned-short"]


def test_job_is_e5s_settings_on_every_task_b_train_reply():
    job = TuneConfig.load(E7 / "tune-short.yaml")
    e5 = TuneConfig.load(E5_SHORT)
    assert (job.task, job.arm, job.train_size, job.instructions) == (
        "b",
        "e7-tuned-short",
        600,
        "short",
    )
    assert (job.base_model, job.base_revision) == (e5.base_model, e5.base_revision)
    assert job.lora == e5.lora and job.training == e5.training
    assert job.max_new_tokens == 320 and job.eval_splits == ("dev", "test")
    assert len(train_subset(job)) == 600


@pytest.mark.parametrize(
    ("name", "split", "size"), [("config.dev.yaml", "dev", 100), ("config.yaml", "test", 300)]
)
def test_configs_hold_the_four_arms(name, split, size):
    experiment = Experiment.load(E7 / name)
    assert experiment.split == split and len(load_inputs(experiment).items) == size
    assert [a.name for a in experiment.arms] == ARMS
    assert experiment.reference == "e7-style-guide"
    assert experiment.judge is not None and experiment.judge.model == "gemini-3.6-flash"
    examples = experiment.arm("e7-guide-4-examples").examples
    assert (examples.n, examples.selection, examples.seed) == (4, "random", 0)
    tuned = experiment.arm("e7-tuned-short")
    assert tuned.external
    assert tuned.predictions == Path(f"results/e7-tuned-short/predictions-{split}.jsonl")


@pytest.mark.parametrize("name", ["config.dev.yaml", "config.yaml"])
def test_one_line_arm_sends_e1s_requests_so_it_is_cached(name):
    e7 = Experiment.load(E7 / name)
    e1 = Experiment.load(E1 / name.replace("config", "config-b"))
    inputs = load_inputs(e7)
    ours = arm_requests(e7, e7.arm("e7-one-line"), inputs)
    theirs = arm_requests(e1, e1.arm("b-one-line"), inputs)
    assert [request_hash(r) for r in ours.values()] == [request_hash(r) for r in theirs.values()]


def test_judge_check_rejudges_the_main_runs_replies_with_haiku():
    check = Experiment.load(E7 / "judge-check" / "config.yaml")
    main = Experiment.load(E7 / "config.yaml")
    assert check.limit == 50 and check.split == "test"
    assert check.judge is not None and check.judge.model == "claude-haiku-5-5"
    assert check.reference == main.reference
    assert all(a.external for a in check.arms)
    for arm in check.arms:
        assert (
            check.path(arm.predictions).resolve()
            == (main.results / arm.name / "predictions-test.jsonl").resolve()
        )
    assert check.results != main.results


def test_preregistration_states_every_claim_and_the_choice_rule():
    text = (E7 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E7 / "claims.yaml").read_text(encoding="utf-8"))
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text
    assert spec["choose"]["order"] == ARMS[1:]
    assert spec["best_prompted"]["order"] == ARMS[1:3]
    assert spec["claims"]["C5"]["agree_at_least"] == 0.90 and "at least\n  90%" in text


claims = load_sibling(E7 / "claims.py")
KEPT = '{"all_facts_kept": true, "facts_added": []}'
LOST = '{"all_facts_kept": false, "facts_added": []}'


def test_best_prompted_is_the_dev_winner_ties_to_the_guide():
    order = ["e7-style-guide", "e7-guide-4-examples"]
    assert claims.best_prompted({"e7-style-guide": 5, "e7-guide-4-examples": 5}, order) == order[0]
    assert claims.best_prompted({"e7-style-guide": 5, "e7-guide-4-examples": 6}, order) == order[1]


def test_judges_agree_only_on_shared_verdicts():
    main = {"x": {"i1": KEPT, "i2": KEPT, "i3": LOST}}
    check = {"x": {"i1": KEPT, "i2": LOST, "i9": KEPT}, "y": {}}
    assert claims.agreement(main, check) == {"shared": 2, "same": 1, "rate": 0.5}
    assert claims.agreement({}, {})["rate"] == 0.0


def test_style_agreement_compares_combined_outcomes():
    one, two = '{"better": "1"}', '{"better": "2"}'
    main = {"x": {"i1:ar": one, "i1:ra": two, "i2:ar": one, "i2:ra": one}}
    check = {"x": {"i1:ar": one, "i1:ra": two, "i2:ar": two, "i2:ra": one, "i3:ar": "?"}}
    assert claims.style_agreement(main, check) == {"shared": 2, "same": 1, "rate": 0.5}


def _arm(primary, facts):
    return {"primary": primary, "facts_kept": facts}


def test_claims_hold_and_fail_on_synthetic_results():
    spec = claims.load_claims_file()
    good = {f"i{n}": True for n in range(40)}
    bad = {f"i{n}": n >= 30 for n in range(40)}
    test = {
        "e7-one-line": _arm(bad, good),
        "e7-style-guide": _arm(good, good),
        "e7-guide-4-examples": _arm(good, good),
        "e7-tuned-short": _arm(bad, bad),
    }
    facts = {"shared": 10, "same": 9, "rate": 0.9}
    result = {c.id: c for c in claims.evaluate(test, "e7-style-guide", facts, {}, spec)}
    assert [result[k].held for k in ("C1", "C2", "C3", "C4", "C5")] == [
        True,
        False,
        False,
        False,
        True,
    ]
    assert result["C3"].detail["best_prompted"] == "e7-style-guide"
    untested = claims.c5({"shared": 0}, {}, spec["claims"]["C5"])
    assert claims.verdict(untested) == "Not tested" and claims.verdict(result["C2"]) == "Failed"
