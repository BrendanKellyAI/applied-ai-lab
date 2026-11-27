"""S4 E2's pre-registered claims, applied to the test analysis. See PREREGISTRATION.md.

`evaluate` reads the pass marks from claims.yaml, E2's best prompt from the dev analysis (by the
choice rule), and the numbers from results/analysis-task-a-<split>.json.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

HERE = Path(__file__).parent


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_analysis(split: str, results: Path = HERE / "results") -> dict[str, Any]:
    return json.loads((results / f"analysis-task-a-{split}.json").read_text(encoding="utf-8"))


def choose(analysis: Mapping[str, Any], order: list[str]) -> str:
    """The highest fully right; a tie goes to the arm earlier in `order`."""
    return max(order, key=lambda a: (analysis["arms"][a]["fully_right"]["count"], -order.index(a)))


def c1(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    reference = analysis["arms"][analysis["reference"]]["fully_right"]["count"]
    rungs = {
        arm: {
            "fully_right": analysis["arms"][arm]["fully_right"]["count"],
            "p_holm": analysis["comparisons"][arm]["p_holm"],
        }
        for arm in mark["arms"]
    }
    held = any(
        r["fully_right"] > reference and r["p_holm"] < mark["p_below"] for r in rungs.values()
    )
    return Claim(
        id="C1", title=mark["title"], held=held, detail={"reference": reference, "rungs": rungs}
    )


def c2(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    rate = analysis["arms"][mark["arm"]]["safety_false_alarms"]["rate"]
    reference = analysis["arms"][analysis["reference"]]["safety_false_alarms"]["rate"]
    ratio = rate / reference if reference else float("inf")
    return Claim(
        id="C2",
        title=mark["title"],
        held=ratio <= mark["ratio_at_most"],
        detail={"rate": rate, "reference_rate": reference, "ratio": round(ratio, 4)},
    )


def c3(analysis: Mapping[str, Any], best: str, mark: Mapping[str, Any]) -> Claim:
    recall = analysis["arms"][best]["safety_recall"]
    return Claim(
        id="C3",
        title=mark["title"],
        held=recall["rate"] >= mark["rate_at_least"],
        detail={"best": best, "safety_recall": recall},
    )


def evaluate(
    analysis: Mapping[str, Any], dev: Mapping[str, Any], spec: Mapping[str, Any]
) -> list[Claim]:
    marks = spec["claims"]
    best = choose(dev, spec["choose"]["order"])
    return [c1(analysis, marks["C1"]), c2(analysis, marks["C2"]), c3(analysis, best, marks["C3"])]


def main(split: str = "test") -> None:
    claims = evaluate(load_analysis(split), load_analysis("dev"), load_claims_file())
    out = HERE / "results" / f"claims-{split}.json"
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    out.write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {'Held' if claim.held else 'Failed'}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
