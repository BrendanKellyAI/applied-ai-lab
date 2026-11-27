"""The Season 4 task definitions agree with the frozen Halvard corpus and with each other."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "datasets" / "halvard-tasks"
ROUTES = yaml.safe_load((TASKS / "routes.yaml").read_text(encoding="utf-8"))
HALVARD = yaml.safe_load(
    (ROOT / "datasets" / "halvard" / "config.yaml").read_text(encoding="utf-8")
)
DASHES = (chr(0x2013), chr(0x2014))


def test_every_product_is_a_halvard_product():
    assert ROUTES["products"] == HALVARD["products"]


def test_there_are_eight_routes_each_with_a_definition_and_team():
    assert len(ROUTES["routes"]) == 8
    for route in ROUTES["routes"].values():
        assert route["definition"].strip()
        assert route["team"].strip()


def test_fault_keys_are_unique_snake_case():
    keys = list(ROUTES["faults"])
    assert len(keys) == len(set(keys))
    assert all(key == key.lower() and " " not in key for key in keys)


def test_safety_share_is_ten_percent():
    assert ROUTES["safety"]["share"] == pytest.approx(0.10)


@pytest.mark.parametrize("name", ["routes.yaml", "style-guide.md", "GENERATION_PLAN.md"])
def test_no_dash_characters(name):
    text = (TASKS / name).read_text(encoding="utf-8")
    assert not any(dash in text for dash in DASHES)
