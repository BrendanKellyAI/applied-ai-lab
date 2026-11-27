"""The Season 4 task data is frozen: every file in MANIFEST.json still has its recorded hash."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "datasets" / "halvard-tasks"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(MANIFEST["files"]))
def test_frozen_file_is_unchanged(name: str) -> None:
    path = ROOT / name
    entry = MANIFEST["files"][name]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    if "items" in entry:
        assert path.read_text(encoding="utf-8").count("\n") == entry["items"]


def test_every_split_is_frozen() -> None:
    splits = {f"task-{t}/{s}.jsonl" for t in "ab" for s in ("train", "dev", "test")}
    assert splits <= set(MANIFEST["files"])
