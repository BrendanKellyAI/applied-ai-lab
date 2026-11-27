"""The Season 4 task data is frozen: every file in MANIFEST.json still has its recorded hash."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "datasets" / "halvard-tasks"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


def _as_recorded(data: bytes) -> bytes:
    """The manifest was written from a Windows checkout, so its hashes are of CRLF files.

    Git stores these files with LF (`.gitattributes`), so normalise to CRLF before hashing.
    The content check is unchanged; only line endings are made consistent.
    """
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


@pytest.mark.parametrize("name", sorted(MANIFEST["files"]))
def test_frozen_file_is_unchanged(name: str) -> None:
    path = ROOT / name
    entry = MANIFEST["files"][name]
    assert hashlib.sha256(_as_recorded(path.read_bytes())).hexdigest() == entry["sha256"]
    if "items" in entry:
        assert path.read_text(encoding="utf-8").count("\n") == entry["items"]


def test_every_split_is_frozen() -> None:
    splits = {f"task-{t}/{s}.jsonl" for t in "ab" for s in ("train", "dev", "test")}
    assert splits <= set(MANIFEST["files"])
