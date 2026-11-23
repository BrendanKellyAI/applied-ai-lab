"""S4 E1's configs load, and its pre-registration states the pass marks claims.yaml holds."""

from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.requests import load_inputs

EPISODE = Path(__file__).parents[2] / "episodes" / "s4-e1-baseline"
CONFIGS = ("config-a.dev", "config-a", "config-b.dev", "config-b")


@pytest.mark.parametrize("name", CONFIGS)
def test_configs_load_with_one_arm_on_the_cheapest_model(name):
    experiment = Experiment.load(EPISODE / f"{name}.yaml")
    assert experiment.answer.model == "gpt-6-luna" and experiment.answer.reasoning == "off"
    assert [a.instructions for a in experiment.arms] == ["one_line"]
    assert experiment.split == ("dev" if name.endswith(".dev") else "test")
    inputs = load_inputs(experiment)
    expected = {"config-a.dev": 40, "config-a": 600, "config-b.dev": 20, "config-b": 300}
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
