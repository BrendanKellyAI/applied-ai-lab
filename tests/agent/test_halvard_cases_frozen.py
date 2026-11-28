"""The Season 5 case data is frozen: every file in MANIFEST.json is unchanged, and none is added."""

import json

import pytest

from lab.agent.freeze import DATASET, MANIFEST, file_hash, manifest_entries

RECORDED = json.loads((DATASET / MANIFEST).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(RECORDED["files"]))
def test_frozen_file_is_unchanged(name):
    path = DATASET / name
    entry = RECORDED["files"][name]
    assert file_hash(path) == entry["sha256"]
    if "lines" in entry:
        assert path.read_text(encoding="utf-8").count("\n") == entry["lines"]


def test_no_file_was_added_or_removed():
    assert set(manifest_entries()) == set(RECORDED["files"])


def test_every_case_file_is_frozen():
    for split in ("test", "dev", "telemetry-test", "telemetry-dev", "sequences-test", "long-test"):
        assert f"cases/{split}.jsonl" in RECORDED["files"]
    assert RECORDED["files"]["cases/test.jsonl"]["lines"] == 236
