"""S4 E1's pre-registered claims, applied to the test analyses. See PREREGISTRATION.md.

`evaluate` reads the pass marks from claims.yaml and the numbers from
results/analysis-task-{a,b}-<split>.json, and returns C1 to C4 as Held or Failed.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

HERE = Path(__file__).parent
ARMS = {"a": "a-one-line", "b": "b-one-line"}


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool
    detail: dict[str, Any]


def load_marks(path: Path = HERE / "claims.yaml") -> dict[str, dict[str, Any]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["claims"]


def load_arm(task: str, split: str, results: Path = HERE / "results") -> dict[str, Any]:
    analysis = json.loads(
        (results / f"analysis-task-{task}-{split}.json").read_text(encoding="utf-8")
    )
    return analysis["arms"][ARMS[task]]


def c1(arm: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    fully = arm["fully_right"]
    return Claim(
        id="C1",
        title=mark["title"],
        held=fully["high"] < mark["upper_below"],
        detail={"fully_right": fully, "upper_below": mark["upper_below"]},
    )


def c2(arm: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    product = arm["field_accuracy"]["product"]["rate"]
    fully = arm["fully_right"]["rate"]
    gap = product - fully
    return Claim(
        id="C2",
        title=mark["title"],
        held=product >= mark["product_at_least"] and gap >= mark["gap_at_least"],
        detail={"product": product, "fully_right": fully, "gap": round(gap, 4)},
    )


def c3(arm: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    recall = arm["safety_recall"]
    return Claim(
        id="C3",
        title=mark["title"],
        held=recall["rate"] < mark["rate_below"],
        detail={"safety_recall": recall, "rate_below": mark["rate_below"]},
    )


def c4(arm: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    facts, checks = arm["facts_kept"]["rate"], arm["all_checks"]["rate"]
    return Claim(
        id="C4",
        title=mark["title"],
        held=facts >= mark["facts_at_least"] and checks <= mark["all_checks_at_most"],
        detail={"facts_kept": facts, "all_checks": checks},
    )


def evaluate(
    task_a: Mapping[str, Any], task_b: Mapping[str, Any], marks: Mapping[str, Any]
) -> list[Claim]:
    return [
        c1(task_a, marks["C1"]),
        c2(task_a, marks["C2"]),
        c3(task_a, marks["C3"]),
        c4(task_b, marks["C4"]),
    ]


def main(split: str = "test") -> None:
    marks = load_marks()
    claims = evaluate(load_arm("a", split), load_arm("b", split), marks)
    out = HERE / "results" / f"claims-{split}.json"
    out.write_text(json.dumps([c.model_dump() for c in claims], indent=2) + "\n", encoding="utf-8")
    for claim in claims:
        print(f"{claim.id} {'Held' if claim.held else 'Failed'}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
