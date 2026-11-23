"""Write datasets/halvard-tasks/MANIFEST.json: the sha256 of every frozen file.

Run once, after the owner's hand checks; tests/adapt/test_halvard_tasks_frozen.py then fails if
any listed file changes.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "datasets" / "halvard-tasks"
FROZEN = [
    "routes.yaml",
    "style-guide.md",
    *[f"task-{t}/{s}.jsonl" for t in ("a", "b") for s in ("train", "dev", "test")],
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    files = {}
    for name in FROZEN:
        path = ROOT / name
        lines = path.read_text(encoding="utf-8").count("\n") if name.endswith(".jsonl") else None
        files[name] = {"sha256": sha256(path), **({"items": lines} if lines is not None else {})}
    manifest = {"dataset": "halvard-tasks", "frozen": "2026-11-23", "files": files}
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
