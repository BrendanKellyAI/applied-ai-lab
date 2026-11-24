"""S4 E6's pre-registered claims, applied to the test results. See PREREGISTRATION.md.

Every claim compares arms item by item, so each arm's saved replies are scored against the
frozen labels. The arms' prediction files are the ones config.yaml names: three from this
episode's jobs and three from E5.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.adapt.definitions import Definitions
from lab.adapt.experiment import Experiment
from lab.adapt.items import triage_items
from lab.adapt.score_a import score_items
from lab.rag.compare import paired

HERE = Path(__file__).parent
DATA = HERE.parents[1] / "datasets" / "halvard-tasks"
CONFIGS = {"dev": "config.dev.yaml", "test": "config.yaml"}


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def prediction_files(split: str) -> dict[str, Path]:
    experiment = Experiment.load(HERE / CONFIGS[split])
    return {arm.name: experiment.path(arm.predictions) for arm in experiment.arms}


def _scores(path: Path, split: str) -> list[Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    texts = {row["id"]: row["text"] for row in map(json.loads, lines)}
    return score_items(triage_items(DATA, split), texts, Definitions.load(DATA / "routes.yaml"))


def fully_right_by_item(path: Path, split: str) -> dict[str, bool]:
    return {s.id: s.fully_right for s in _scores(path, split)}


def safety_recall(path: Path, split: str) -> dict[str, Any]:
    items = [s for s in _scores(path, split) if s.safety_item]
    found = sum(s.flagged for s in items)
    return {"count": found, "total": len(items), "rate": found / len(items)}


def against(a: Mapping[str, bool], b: Mapping[str, bool]) -> dict[str, Any]:
    return {"a": sum(a.values()), "b": sum(b.values()), **paired(a, b)}


def is_worse(pair: Mapping[str, Any], p_below: float) -> bool:
    return pair["a"] < pair["b"] and pair["p_value"] < p_below


def smallest_matching(
    by_item: Mapping[str, Mapping[str, bool]], spec: Mapping[str, Any]
) -> tuple[str | None, dict[str, dict[str, Any]]]:
    """The smallest size not worse than the reference, and every size's comparison."""
    reference = by_item[spec["reference"]]
    p_below = spec["matches"]["p_below"]
    pairs = {arm: against(by_item[arm], reference) for arm in spec["sizes"]}
    ordered = sorted(spec["sizes"], key=spec["sizes"].get)
    matching = [arm for arm in ordered if not is_worse(pairs[arm], p_below)]
    return (matching[0] if matching else None), pairs


def c1(pairs: Mapping[str, Mapping[str, Any]], mark: Mapping[str, Any]) -> Claim:
    pair = pairs[mark["arm"]]
    return Claim(
        id="C1", title=mark["title"], held=is_worse(pair, mark["p_below"]), detail=dict(pair)
    )


def c2(
    smallest: str | None,
    sizes: Mapping[str, int],
    pairs: Mapping[str, Any],
    mark: Mapping[str, Any],
) -> Claim:
    size = sizes[smallest] if smallest else None
    return Claim(
        id="C2",
        title=mark["title"],
        held=size is not None and size <= mark["size_at_most"],
        detail={"smallest_matching": smallest, "size": size, "against_reference": dict(pairs)},
    )


def c3(by_item: Mapping[str, Mapping[str, bool]], mark: Mapping[str, Any]) -> Claim:
    first, second = mark["arms"]
    pair = against(by_item[first], by_item[second])
    return Claim(
        id="C3", title=mark["title"], held=pair["p_value"] >= mark["p_at_least"], detail=pair
    )


def c4(smallest: str | None, recall: Mapping[str, Any] | None, mark: Mapping[str, Any]) -> Claim:
    if smallest is None or recall is None:
        return Claim(
            id="C4", title=mark["title"], held=None, detail={"not_tested": "no size matches"}
        )
    return Claim(
        id="C4",
        title=mark["title"],
        held=recall["rate"] >= mark["rate_at_least"],
        detail={"arm": smallest, "safety_recall": dict(recall)},
    )


def evaluate(
    by_item: Mapping[str, Mapping[str, bool]],
    recall_of: Mapping[str, Mapping[str, Any]],
    spec: Mapping[str, Any],
) -> list[Claim]:
    marks = spec["claims"]
    smallest, pairs = smallest_matching(by_item, spec)
    return [
        c1(pairs, marks["C1"]),
        c2(smallest, spec["sizes"], pairs, marks["C2"]),
        c3(by_item, marks["C3"]),
        c4(smallest, recall_of.get(smallest) if smallest else None, marks["C4"]),
    ]


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main(split: str = "test") -> None:
    spec = load_claims_file()
    files = prediction_files(split)
    by_item = {arm: fully_right_by_item(path, split) for arm, path in files.items()}
    recall_of = {arm: safety_recall(files[arm], split) for arm in spec["sizes"]}
    claims = evaluate(by_item, recall_of, spec)
    out = HERE / "results" / f"claims-{split}.json"
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    out.write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
