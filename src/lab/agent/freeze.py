"""The frozen manifest for `datasets/halvard-cases`: a hash for every file.

Text files are hashed with LF line endings, so a Windows checkout and a Linux one agree (the
Season 4 manifest hashed CRLF files, which failed on fresh checkouts). Images are hashed as
bytes. Case files also record their line count.
"""

import hashlib
import json
from pathlib import Path

DATASET = Path(__file__).resolve().parents[3] / "datasets" / "halvard-cases"
MANIFEST = "MANIFEST.json"
BINARY = {".png"}


def file_hash(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix not in BINARY:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def manifest_entries(root: Path = DATASET) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != MANIFEST):
        entry: dict[str, object] = {"sha256": file_hash(path)}
        if path.suffix == ".jsonl":
            entry["lines"] = path.read_text(encoding="utf-8").count("\n")
        entries[path.relative_to(root).as_posix()] = entry
    return entries


def write_manifest(frozen: str, root: Path = DATASET) -> Path:
    path = root / MANIFEST
    payload = {"frozen": frozen, "files": manifest_entries(root)}
    path.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return path
