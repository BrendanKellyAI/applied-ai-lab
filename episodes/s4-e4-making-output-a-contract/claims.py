"""S4 E4's pre-registered claims, applied to the test analysis. See PREREGISTRATION.md."""

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


def c1(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    valid = analysis["arms"][mark["arm"]]["json_valid"]
    return Claim(
        id="C1",
        title=mark["title"],
        held=valid["rate"] >= mark["validity_at_least"],
        detail={"json_valid": valid},
    )


def c2(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    found = {
        arm: {
            "net": analysis["comparisons"][arm]["net"],
            "p_holm": analysis["comparisons"][arm]["p_holm"],
        }
        for arm in mark["arms"]
    }
    held = all(f["p_holm"] >= mark["p_below"] for f in found.values())
    return Claim(id="C2", title=mark["title"], held=held, detail={"against_text": found})


def evaluate(analysis: Mapping[str, Any], spec: Mapping[str, Any]) -> list[Claim]:
    marks = spec["claims"]
    return [c1(analysis, marks["C1"]), c2(analysis, marks["C2"])]


def main(split: str = "test") -> None:
    claims = evaluate(load_analysis(split), load_claims_file())
    out = HERE / "results" / f"claims-{split}.json"
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    out.write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {'Held' if claim.held else 'Failed'}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
