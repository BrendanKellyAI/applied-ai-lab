"""S4 E13 recap: the two task ladders as charts, and the season's numbers in one file.

    uv run python season4/recap.py

No key, no call. Task A's ladder comes from `scoreboard.json`. Task B's adds E7's two prompted
arms from E7's test analysis, because only joined rungs and the tuned model are on the
scoreboard. The claim tally reads every episode's test claims. Writes charts and `recap.json`
to `season4/charts/`.
"""

import json
from collections import Counter
from pathlib import Path

from lab.rag.fieldnote import interval_bars

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "charts"
LABELS_A = {
    "a-one-line": "E1 one-line prompt",
    "e2-definitions": "E2 + definitions (reference)",
    "e3-similar-8": "E3 + 8 similar examples",
    "e4-json-mode": "E4 + JSON mode",
    "e5-tuned-short": "E5 small model, tuned",
    "e9-student-teacher-labels": "E9 tuned on big model's labels",
}
E7 = ROOT / "episodes" / "s4-e7-teaching-a-house-style" / "results" / "analysis-task-b-test.json"
LABELS_B = {
    "e7-one-line": "One-line prompt",
    "e7-style-guide": "E7 + style guide",
    "e7-guide-4-examples": "E7 + guide and 4 examples",
    "e7-tuned-short": "E7 small model, tuned (reference)",
}


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def ladder_a() -> list[tuple[str, dict]]:
    rows = {r["candidate"]: r["score"] for r in read(HERE / "scoreboard.json") if r["task"] == "a"}
    return [(label, rows[name]) for name, label in LABELS_A.items()]


def ladder_b() -> list[tuple[str, dict]]:
    arms = read(E7)["arms"]
    return [(label, arms[name]["primary"]) for name, label in LABELS_B.items()]


def claim_tally() -> dict[str, dict[str, int]]:
    tally = {}
    for episode in sorted((ROOT / "episodes").glob("s4-e*")):
        files = [p for p in episode.glob("results/claims*.json") if "dev" not in p.name]
        counts = Counter()
        for path in files:
            for claim in read(path):
                held = claim.get("held")
                counts["held" if held is True else "failed" if held is False else "not tested"] += 1
        tally[episode.name] = dict(counts)
    return tally


def main() -> dict:
    charts = [
        ("task-a", ladder_a(), "Fully right", "600 test messages", 1),
        ("task-b", ladder_b(), "Passes every rule", "300 test replies", 3),
    ]
    for name, rows, what, sample, reference in charts:
        interval_bars(
            OUT,
            f"s4-recap-{name}",
            rows=rows,
            units=f"{what}, share (95% Wilson)",
            sample_size=sample,
            highlight_index=reference,
        )
    tally = claim_tally()
    total = Counter()
    for counts in tally.values():
        total.update(counts)
    summary = {
        "task_a": {label: score["count"] for label, score in charts[0][1]},
        "task_b": {label: score["count"] for label, score in charts[1][1]},
        "claims": tally,
        "claims_total": dict(total),
    }
    (OUT / "recap.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
