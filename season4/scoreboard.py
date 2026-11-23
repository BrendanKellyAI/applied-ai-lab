"""Build season4/scoreboard.json and reference_history.yaml from the episodes' test analyses.

Each episode's candidate is chosen on dev by its own pre-registered rule (claims.yaml `choose`),
then judged on test by the strict bar: it joins the reference only if the low end of its Wilson
interval on the primary metric sits above the high end of the current reference's. Run after
every episode's analysis:

    uv run python season4/scoreboard.py
"""

import json
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).parent
EPISODES = HERE.parent / "episodes"
STRICT_BAR = "candidate's interval on the primary metric sits clear above the reference's"

# (episode, task, arm or None): None means the candidate is chosen by claims.yaml's rule on dev.
LADDER: list[tuple[str, str, str | None]] = [
    ("s4-e1-baseline", "a", "a-one-line"),
    ("s4-e1-baseline", "b", "b-one-line"),
    ("s4-e2-instructions-first", "a", None),
    ("s4-e3-how-many-examples", "a", None),
    ("s4-e4-making-output-a-contract", "a", None),
    # E5 Amendment 1: the one-line tuned arm was not run, so the short arm is the only candidate.
    ("s4-e5-does-fine-tuning-beat-a-good-prompt", "a", "e5-tuned-short"),
]
PRIMARY = {"a": "fully_right", "b": "primary"}


def load_analysis(episode: str, task: str, split: str) -> dict[str, Any]:
    path = EPISODES / episode / "results" / f"analysis-task-{task}-{split}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def choose(episode: str, task: str) -> str:
    """The dev winner by the episode's rule: the highest primary count; ties go to `order`."""
    rule = yaml.safe_load((EPISODES / episode / "claims.yaml").read_text(encoding="utf-8"))
    order = rule["choose"]["order"]
    dev = load_analysis(episode, task, "dev")["arms"]
    return max(order, key=lambda a: (dev[a][PRIMARY[task]]["count"], -order.index(a)))


def clears(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    return candidate["low"] > reference["high"]


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    board: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    current: dict[str, dict[str, Any]] = {}
    for episode, task, fixed in LADDER:
        arm = fixed or choose(episode, task)
        analysis = load_analysis(episode, task, "test")
        score = analysis["arms"][arm][PRIMARY[task]]
        before = current.get(task)
        joined = before is None or clears(score, before["score"])
        row = {
            "episode": episode,
            "task": task,
            "candidate": arm,
            "metric": PRIMARY[task],
            "score": score,
            "reference_before": None if before is None else before["arm"],
            "reference_score_before": None if before is None else before["score"],
            "joined": joined,
        }
        board.append(row)
        history.append(
            {
                "episode": episode,
                "task": task,
                "candidate": arm,
                "reference_before": row["reference_before"],
                "reference_after": arm if joined else row["reference_before"],
                "pass_mark": "none: the baseline sets the reference"
                if before is None
                else STRICT_BAR,
                "joined": joined,
            }
        )
        if joined:
            current[task] = {"arm": arm, "score": score}
    return board, history


def main() -> None:
    board, history = build()
    (HERE / "scoreboard.json").write_bytes((json.dumps(board, indent=1) + "\n").encode("utf-8"))
    text = yaml.safe_dump(history, sort_keys=False, allow_unicode=True)
    (HERE / "reference_history.yaml").write_bytes(text.encode("utf-8"))
    for row in board:
        s = row["score"]
        print(
            f"{row['task']} {row['candidate']}: {s['count']} of {s['total']},"
            f" joined {row['joined']}"
        )


if __name__ == "__main__":
    main()
