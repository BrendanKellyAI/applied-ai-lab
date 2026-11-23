"""S4 E3's pre-registered claims, applied to the test results. See PREREGISTRATION.md.

C1 and C2 read results/analysis-task-a-<split>.json. C3 and C4 compare two example arms item by
item, so they score each arm's saved replies against the frozen labels.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.adapt.definitions import Definitions
from lab.adapt.items import triage_items
from lab.adapt.score_a import score_items
from lab.rag.compare import paired

HERE = Path(__file__).parent
DATA = HERE.parents[1] / "datasets" / "halvard-tasks"


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


def fully_right_by_item(arm: str, split: str, results: Path = HERE / "results") -> dict[str, bool]:
    lines = (results / arm / f"predictions-{split}.jsonl").read_text(encoding="utf-8").splitlines()
    texts = {row["id"]: row["text"] for row in map(json.loads, lines)}
    scores = score_items(triage_items(DATA, split), texts, Definitions.load(DATA / "routes.yaml"))
    return {s.id: s.fully_right for s in scores}


def _count(analysis: Mapping[str, Any], arm: str) -> int:
    return analysis["arms"][arm]["fully_right"]["count"]


def c1(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    reference = _count(analysis, analysis["reference"])
    arms = {
        a: {"fully_right": _count(analysis, a), "p_holm": analysis["comparisons"][a]["p_holm"]}
        for a in mark["arms"]
    }
    held = any(
        r["fully_right"] > reference and r["p_holm"] < mark["p_below"] for r in arms.values()
    )
    return Claim(
        id="C1", title=mark["title"], held=held, detail={"reference": reference, "arms": arms}
    )


def c2(analysis: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    n0, r8, r32 = (_count(analysis, a) for a in ("e3-n0", "e3-random-8", "e3-random-32"))
    return Claim(
        id="C2",
        title=mark["title"],
        held=r32 - r8 < r8 - n0,
        detail={"n0_to_8": r8 - n0, "8_to_32": r32 - r8},
    )


def c3(similar: Mapping[str, bool], random: Mapping[str, bool], mark: Mapping[str, Any]) -> Claim:
    s, r = sum(similar.values()), sum(random.values())
    return Claim(
        id="C3",
        title=mark["title"],
        held=s > r,
        detail={"similar_8": s, "random_8": r, **paired(similar, random)},
    )


def c4(random: Mapping[str, bool], shuffled: Mapping[str, bool], mark: Mapping[str, Any]) -> Claim:
    pair = paired(random, shuffled)
    flips = pair["only_a"] + pair["only_b"]
    share = flips / len(random)
    return Claim(
        id="C4",
        title=mark["title"],
        held=share >= mark["flips_at_least"],
        detail={"flips": flips, "items": len(random), "share": round(share, 4), **pair},
    )


def evaluate(
    analysis: Mapping[str, Any], by_item: Mapping[str, Mapping[str, bool]], spec: Mapping[str, Any]
) -> list[Claim]:
    marks = spec["claims"]
    return [
        c1(analysis, marks["C1"]),
        c2(analysis, marks["C2"]),
        c3(by_item["e3-similar-8"], by_item["e3-random-8"], marks["C3"]),
        c4(by_item["e3-random-8"], by_item["e3-random-8-shuffled"], marks["C4"]),
    ]


def main(split: str = "test") -> None:
    arms = ("e3-similar-8", "e3-random-8", "e3-random-8-shuffled")
    by_item = {arm: fully_right_by_item(arm, split) for arm in arms}
    claims = evaluate(load_analysis(split), by_item, load_claims_file())
    out = HERE / "results" / f"claims-{split}.json"
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    out.write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {'Held' if claim.held else 'Failed'}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
