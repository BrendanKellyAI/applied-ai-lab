"""season4/scoreboard.json and reference_history.yaml match what scoreboard.py builds."""

import json
from pathlib import Path

import yaml

from lab.experiments import load_sibling

SEASON = Path(__file__).parents[2] / "season4"
scoreboard = load_sibling(SEASON / "scoreboard.py")


def test_files_on_disk_match_the_builder():
    board, history = scoreboard.build()
    assert json.loads((SEASON / "scoreboard.json").read_text(encoding="utf-8")) == board
    assert (
        yaml.safe_load((SEASON / "reference_history.yaml").read_text(encoding="utf-8")) == history
    )


def test_reference_matches_the_last_joined_row_per_task():
    _, history = scoreboard.build()
    reference = yaml.safe_load((SEASON / "reference.yaml").read_text(encoding="utf-8"))
    last = {row["task"]: row["reference_after"] for row in history}
    assert reference["task_a"]["arm"] == last["a"]
    assert reference["task_b"]["arm"] == last["b"]


def test_strict_bar_needs_the_intervals_apart():
    assert scoreboard.clears({"low": 0.9}, {"high": 0.89})
    assert not scoreboard.clears({"low": 0.9}, {"high": 0.9})
