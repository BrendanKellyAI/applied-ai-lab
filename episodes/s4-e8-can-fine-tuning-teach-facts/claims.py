"""S4 E8's pre-registered claims, applied to results/analysis-facts-test.json.

Every claim compares two arms item by item with an exact McNemar test: on the 400 answerable
items for "right", the 120 unanswerable for "declined_unanswerable", and all 520 for
"confident_wrong". A claim holds when the arm named `more` has the higher count and p is below
the mark.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.rag.compare import paired

HERE = Path(__file__).parent

# Which items each measure counts over, and the per-item field that is the measure.
MEASURES = {
    "right": (lambda s: s["answerable"], lambda s: s["answerable"] and s["correct"]),
    "declined_unanswerable": (lambda s: not s["answerable"], lambda s: s["declined"]),
    "confident_wrong": (
        lambda s: True,
        lambda s: s["judged"] and not s["declined"] and not s["correct"],
    ),
}


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def by_item(per_item: list[dict], measure: str) -> dict[str, bool]:
    within, value = MEASURES[measure]
    return {s["id"]: bool(value(s)) for s in per_item if within(s)}


def check(cid: str, arms: Mapping[str, list[dict]], mark: Mapping[str, Any]) -> Claim:
    more = by_item(arms[mark["more"]], mark["measure"])
    than = by_item(arms[mark["than"]], mark["measure"])
    pair = {"more": sum(more.values()), "than": sum(than.values()), **paired(more, than)}
    held = pair["more"] > pair["than"] and pair["p_value"] < mark["p_below"]
    return Claim(id=cid, title=mark["title"], held=held, detail={**dict(mark), **pair})


def evaluate(arms: Mapping[str, list[dict]], spec: Mapping[str, Any]) -> list[Claim]:
    return [check(cid, arms, mark) for cid, mark in spec["claims"].items()]


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main() -> None:
    analysis = json.loads((HERE / "results" / "analysis-facts-test.json").read_text("utf-8"))
    arms = {name: arm["per_item"] for name, arm in analysis["arms"].items()}
    claims = evaluate(arms, load_claims_file())
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    (HERE / "results" / "claims-test.json").write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    main()
