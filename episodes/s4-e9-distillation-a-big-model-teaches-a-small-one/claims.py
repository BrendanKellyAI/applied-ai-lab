"""S4 E9's pre-registered claims. See PREREGISTRATION.md.

C1 reads the teacher's fully right on train from results/analysis-task-a-train.json. C2 to C4
compare arms item by item on test, scoring each arm's saved replies against the frozen labels;
the arms' files are the ones config.yaml names.
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
from lab.adapt.run import predictions_path, read_texts
from lab.adapt.score_a import score_items
from lab.rag.compare import paired

HERE = Path(__file__).parent
DATA = HERE.parents[1] / "datasets" / "halvard-tasks"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fully_right_by_arm(config: Path = HERE / "config.yaml") -> dict[str, dict[str, bool]]:
    experiment = Experiment.load(config)
    items = triage_items(DATA, experiment.split)
    definitions = Definitions.load(DATA / "routes.yaml")
    out = {}
    for arm in experiment.arms:
        texts = read_texts(predictions_path(experiment, arm.name))
        out[arm.name] = {s.id: s.fully_right for s in score_items(items, texts, definitions)}
    return out


def c1(train_rate: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    held = train_rate["rate"] >= mark["rate_at_least"]
    return Claim(
        id="C1", title=mark["title"], held=held, detail={"teacher_on_train": dict(train_rate)}
    )


def beats(cid: str, by_arm: Mapping[str, Mapping[str, bool]], mark: Mapping[str, Any]) -> Claim:
    a, b = mark["arms"]
    pair = {
        "a": sum(by_arm[a].values()),
        "b": sum(by_arm[b].values()),
        **paired(by_arm[a], by_arm[b]),
    }
    held = pair["a"] > pair["b"] and pair["p_value"] < mark["p_below"]
    return Claim(id=cid, title=mark["title"], held=held, detail=pair)


def not_worse(cid: str, by_arm: Mapping[str, Mapping[str, bool]], mark: Mapping[str, Any]) -> Claim:
    a, b = mark["arms"]
    pair = {
        "a": sum(by_arm[a].values()),
        "b": sum(by_arm[b].values()),
        **paired(by_arm[a], by_arm[b]),
    }
    worse = pair["a"] < pair["b"] and pair["p_value"] < mark["p_below"]
    return Claim(id=cid, title=mark["title"], held=not worse, detail=pair)


def evaluate(
    train_rate: Mapping[str, Any], by_arm: Mapping[str, Mapping[str, bool]], spec: Mapping[str, Any]
) -> list[Claim]:
    marks = spec["claims"]
    return [
        c1(train_rate, marks["C1"]),
        beats("C2", by_arm, marks["C2"]),
        not_worse("C3", by_arm, marks["C3"]),
        not_worse("C4", by_arm, marks["C4"]),
    ]


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main() -> None:
    train = json.loads((HERE / "results" / "analysis-task-a-train.json").read_text("utf-8"))
    claims = evaluate(
        train["arms"]["e9-teacher"]["fully_right"], fully_right_by_arm(), load_claims_file()
    )
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    (HERE / "results" / "claims-test.json").write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    main()
