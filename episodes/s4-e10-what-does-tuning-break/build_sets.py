"""Write S4 E10's three prompt sets to data/, from their frozen sources. No calls.

uv run python episodes/s4-e10-what-does-tuning-break/build_sets.py
"""

from pathlib import Path

from lab.adapt.regression import bleed_rows, decline_rows, general_rows, write_rows
from lab.rag.corpus import load_library

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
S1 = ROOT / "field-notes" / "s1-e10-reasoning-vs-standard" / "tasks" / "items.jsonl"
S2 = ROOT / "field-notes" / "s2-e12-embedding-swap" / "results" / "baseline"


def main() -> None:
    library = load_library(ROOT / "datasets" / "halvard")
    write_rows(HERE / "data" / "general.jsonl", general_rows(S1))
    write_rows(HERE / "data" / "bleed-prompts.jsonl", bleed_rows(HERE / "data" / "bleed.jsonl"))
    rows = decline_rows(library, S2 / "log.jsonl", S2 / "raw-answer.jsonl")
    write_rows(HERE / "data" / "declines.jsonl", rows)


if __name__ == "__main__":
    main()
