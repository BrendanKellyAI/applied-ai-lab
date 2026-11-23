"""S4 E2 to E4: configs load, arms match the pre-registration, and each claim is stated."""

from pathlib import Path

import pytest
import yaml

from lab.adapt.experiment import Experiment
from lab.adapt.requests import arm_requests, load_inputs
from lab.providers.base import request_hash

EPISODES = Path(__file__).parents[2] / "episodes"
E2 = EPISODES / "s4-e2-instructions-first"
E3 = EPISODES / "s4-e3-how-many-examples"
E4 = EPISODES / "s4-e4-making-output-a-contract"
CONFIGS = [
    (E2 / "config.dev.yaml", 200),
    (E2 / "config.yaml", 600),
    (E3 / "ceiling.dev.yaml", 200),
    (E3 / "ceiling.yaml", 600),
    (E4 / "ceiling.dev.yaml", 200),
    (E4 / "ceiling.yaml", 600),
]


@pytest.mark.parametrize(("path", "size"), CONFIGS, ids=lambda v: str(v)[-30:])
def test_configs_load_on_the_cheapest_model(path, size):
    experiment = Experiment.load(path)
    assert experiment.answer.model == "gpt-6-luna" and experiment.answer.reasoning == "off"
    assert all(arm.model is None for arm in experiment.arms)
    assert len(load_inputs(experiment).items) == size


def test_e2_reference_sends_e1s_requests_so_it_is_cached():
    e1 = Experiment.load(EPISODES / "s4-e1-baseline" / "config-a.dev-all.yaml")
    e2 = Experiment.load(E2 / "config.dev.yaml")
    old = arm_requests(e1, e1.arm("a-one-line"), load_inputs(e1))
    new = arm_requests(e2, e2.arm("e2-one-line"), load_inputs(e2))
    assert [request_hash(r) for r in old.values()] == [request_hash(r) for r in new.values()]


@pytest.mark.parametrize("folder", [E2, E3, E4], ids=lambda p: p.name)
def test_every_claim_and_choice_arm_is_in_the_preregistration(folder):
    text = (folder / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((folder / "claims.yaml").read_text(encoding="utf-8"))
    for claim in spec["claims"]:
        assert f"**{claim}." in text
    for arm in spec["choose"]["order"]:
        assert f"`{arm}`" in text


def test_ceilings_differ_from_a_real_config_only_in_the_base_prompt():
    for folder in (E3, E4):
        arms = Experiment.load(folder / "ceiling.yaml").arms
        assert {arm.instructions for arm in arms} == {"unsure"}
