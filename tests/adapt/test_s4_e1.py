"""S4 E1's configs load, and its pre-registration states the pass marks claims.yaml holds."""

from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.requests import load_inputs
from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[2] / "episodes" / "s4-e1-baseline"
CONFIGS = ("config-a.dev", "config-a.dev-all", "config-a", "config-b.dev", "config-b")


@pytest.mark.parametrize("name", CONFIGS)
def test_configs_load_with_one_arm_on_the_cheapest_model(name):
    experiment = Experiment.load(EPISODE / f"{name}.yaml")
    assert experiment.answer.model == "gpt-6-luna" and experiment.answer.reasoning == "off"
    assert [a.instructions for a in experiment.arms] == ["one_line"]
    assert experiment.split == ("dev" if ".dev" in name else "test")
    inputs = load_inputs(experiment)
    expected = {
        "config-a.dev": 40,
        "config-a.dev-all": 200,
        "config-a": 600,
        "config-b.dev": 20,
        "config-b": 300,
    }
    assert len(inputs.items) == expected[name]


def test_preregistration_states_every_pass_mark():
    text = " ".join((EPISODE / "PREREGISTRATION.md").read_text(encoding="utf-8").split())
    claims = yaml.safe_load((EPISODE / "claims.yaml").read_text(encoding="utf-8"))["claims"]
    marks = {
        "C1": ["below 85%"],
        "C2": ["at least 90%", "at least 15 points lower"],
        "C3": ["below 95%"],
        "C4": ["at least 80%", "at most 20%"],
    }
    values = {
        "C1": [claims["C1"]["upper_below"]],
        "C2": [claims["C2"]["product_at_least"], claims["C2"]["gap_at_least"]],
        "C3": [claims["C3"]["rate_below"]],
        "C4": [claims["C4"]["facts_at_least"], claims["C4"]["all_checks_at_most"]],
    }
    assert set(claims) == set(marks)
    for claim, phrases in marks.items():
        assert f"**{claim}." in text
        for phrase, value in zip(phrases, values[claim], strict=True):
            assert phrase in text
            assert f"{round(value * 100)}" in phrase


claims = load_sibling(EPISODE / "claims.py")


def _arm_a(fully: float, high: float, product: float, recall: float) -> dict:
    return {
        "fully_right": {"rate": fully, "high": high},
        "field_accuracy": {"product": {"rate": product}},
        "safety_recall": {"rate": recall},
    }


def test_claims_hold_when_every_pass_mark_is_met():
    marks = claims.load_marks()
    a = _arm_a(fully=0.70, high=0.74, product=0.99, recall=0.90)
    b = {"facts_kept": {"rate": 0.90}, "all_checks": {"rate": 0.05}}
    assert [c.held for c in claims.evaluate(a, b, marks)] == [True, True, True, True]


def test_claims_fail_on_the_far_side_of_each_mark():
    marks = claims.load_marks()
    a = _arm_a(fully=0.85, high=0.89, product=0.99, recall=1.0)
    b = {"facts_kept": {"rate": 0.90}, "all_checks": {"rate": 0.25}}
    held = {c.id: c.held for c in claims.evaluate(a, b, marks)}
    assert held == {"C1": False, "C2": False, "C3": False, "C4": False}


def test_claims_read_the_dev_analyses_on_disk():
    result = claims.evaluate(
        claims.load_arm("a", "dev"), claims.load_arm("b", "dev"), claims.load_marks()
    )
    held = {c.id: c.held for c in result}
    # Dev: 170 of 200 (upper 0.893), product 1.0, recall 25 of 25; Task B 0 of 20 all checks.
    assert held == {"C1": False, "C2": True, "C3": False, "C4": True}
