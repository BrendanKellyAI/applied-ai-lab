"""S4 E10's pre-registered claims, applied to results/analysis-regression.json.

Each claim compares both tuned models with the untuned base, item by item, on one check; it
holds only when both comparisons go the stated way with p below the mark.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.rag.compare import paired

HERE = Path(__file__).parent


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def one(tuned: Mapping[str, bool], base: Mapping[str, bool], mark: Mapping[str, Any]) -> dict:
    pair = {"tuned": sum(tuned.values()), "base": sum(base.values()), **paired(tuned, base)}
    goes = (
        pair["tuned"] < pair["base"]
        if mark["direction"] == "fewer"
        else pair["tuned"] > pair["base"]
    )
    return {**pair, "passes": goes and pair["p_value"] < mark["p_below"]}


def evaluate(
    per_item: Mapping[str, Mapping[str, Mapping[str, bool]]], spec: Mapping[str, Any]
) -> list[Claim]:
    out = []
    for cid, mark in spec["claims"].items():
        base = per_item[spec["baseline"]][mark["check"]]
        tests = {arm: one(per_item[arm][mark["check"]], base, mark) for arm in spec["tuned"]}
        held = all(t["passes"] for t in tests.values())
        out.append(
            Claim(id=cid, title=mark["title"], held=held, detail={"check": mark["check"], **tests})
        )
    return out


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main() -> None:
    analysis = json.loads((HERE / "results" / "analysis-regression.json").read_text("utf-8"))
    per_item = {name: arm["per_item"] for name, arm in analysis["arms"].items()}
    claims = evaluate(per_item, load_claims_file())
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    (HERE / "results" / "claims.json").write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    main()
