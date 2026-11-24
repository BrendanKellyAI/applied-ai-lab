"""S4 E7's pre-registered claims, applied to the test results. See PREREGISTRATION.md.

C1 to C4 compare arms item by item on the primary (every code check passed and the facts kept)
or on facts kept, scored from each arm's saved replies and facts verdicts. The best prompted arm
is chosen on dev. C5 compares the judge check's facts verdicts (claude-haiku-5-5) with the main
run's (gemini-3.6-flash) on the same replies; style agreement is reported, not claimed.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.task_b import facts_verdict
from lab.adapt.experiment import Experiment
from lab.adapt.requests import load_inputs
from lab.adapt.run import predictions_path, read_texts
from lab.adapt.score_b import _choice, score_replies, style_outcome
from lab.rag.compare import paired

HERE = Path(__file__).parent
CONFIGS = {"dev": HERE / "config.dev.yaml", "test": HERE / "config.yaml"}
CHECK = HERE / "judge-check" / "config.yaml"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def judged(path: Path) -> dict[str, str]:
    return read_texts(path) if path.exists() else {}


def by_item(config: Path) -> dict[str, dict[str, dict[str, bool]]]:
    """Per arm: {"primary": {id: bool}, "facts_kept": {id: bool}}."""
    experiment = Experiment.load(config)
    items = load_inputs(experiment).items
    out = {}
    for arm in experiment.arms:
        texts = read_texts(predictions_path(experiment, arm.name))
        facts = judged(experiment.results / arm.name / f"facts-{experiment.split}.jsonl")
        scores = score_replies(items, texts, facts)
        out[arm.name] = {
            "primary": {s.id: s.primary for s in scores},
            "facts_kept": {s.id: s.facts_kept for s in scores},
        }
    return out


def best_prompted(dev_counts: Mapping[str, int], order: list[str]) -> str:
    return max(order, key=lambda a: (dev_counts[a], -order.index(a)))


def against(a: Mapping[str, bool], b: Mapping[str, bool]) -> dict[str, Any]:
    return {"a": sum(a.values()), "b": sum(b.values()), **paired(a, b)}


def beats(a: Mapping[str, bool], b: Mapping[str, bool], mark: Mapping[str, Any]) -> Claim:
    pair = against(a, b)
    held = pair["a"] > pair["b"] and pair["p_value"] < mark["p_below"]
    return Claim(id="", title=mark["title"], held=held, detail=pair)


def not_worse(
    a: Mapping[str, bool], b: Mapping[str, bool], best: str, mark: Mapping[str, Any]
) -> Claim:
    pair = against(a, b)
    worse = pair["a"] < pair["b"] and pair["p_value"] < mark["p_below"]
    return Claim(id="", title=mark["title"], held=not worse, detail={"best_prompted": best, **pair})


def agreement(
    main: Mapping[str, Mapping[str, str]], check: Mapping[str, Mapping[str, str]]
) -> dict[str, Any]:
    """Facts verdicts the two judges share, and how many match, over every arm."""
    shared = same = 0
    for arm, verdicts in check.items():
        for item_id, text in verdicts.items():
            if item_id not in main.get(arm, {}):
                continue
            shared += 1
            same += facts_verdict(text) == facts_verdict(main[arm][item_id])
    return {"shared": shared, "same": same, "rate": same / shared if shared else 0.0}


def style_agreement(
    main: Mapping[str, Mapping[str, str]], check: Mapping[str, Mapping[str, str]]
) -> dict[str, Any]:
    """Pairs both judges read in both orders, and how many get the same win, tie or loss."""
    shared = same = 0
    for arm, verdicts in check.items():
        ids = {key.split(":")[0] for key in verdicts}
        for item_id in ids:
            keys = (f"{item_id}:ar", f"{item_id}:ra")
            ours, theirs = [verdicts.get(k) for k in keys], [main.get(arm, {}).get(k) for k in keys]
            if any(_choice(v) is None for v in (*ours, *theirs)):
                continue
            shared += 1
            same += style_outcome(*ours) == style_outcome(*theirs)
    return {"shared": shared, "same": same, "rate": same / shared if shared else 0.0}


def c5(facts: Mapping[str, Any], style: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    if not facts["shared"]:
        return Claim(id="C5", title=mark["title"], held=None, detail={"not_tested": "no verdicts"})
    return Claim(
        id="C5",
        title=mark["title"],
        held=facts["rate"] >= mark["agree_at_least"],
        detail={"facts": dict(facts), "style_reported": dict(style)},
    )


def evaluate(
    test: Mapping[str, Mapping[str, Mapping[str, bool]]],
    best: str,
    facts_agreement: Mapping[str, Any],
    style: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> list[Claim]:
    marks = spec["claims"]
    out = []
    for cid in ("C1", "C2"):
        first, second = marks[cid]["arms"]
        metric = marks[cid]["metric"]
        claim = beats(test[first][metric], test[second][metric], marks[cid])
        out.append(claim.model_copy(update={"id": cid}))
    for cid in ("C3", "C4"):
        arm, metric = marks[cid]["arm"], marks[cid]["metric"]
        claim = not_worse(test[arm][metric], test[best][metric], best, marks[cid])
        out.append(claim.model_copy(update={"id": cid}))
    out.append(c5(facts_agreement, style, marks["C5"]))
    return out


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def _judge_files(config: Path, stage: str) -> dict[str, dict[str, str]]:
    experiment = Experiment.load(config)
    folder = experiment.results
    return {a.name: judged(folder / a.name / f"{stage}-test.jsonl") for a in experiment.arms}


def main() -> None:
    spec = load_claims_file()
    dev = json.loads((HERE / "results" / "analysis-task-b-dev.json").read_text(encoding="utf-8"))
    dev_counts = {arm: dev["arms"][arm]["primary"]["count"] for arm in dev["arms"]}
    best = best_prompted(dev_counts, spec["best_prompted"]["order"])
    facts = agreement(_judge_files(CONFIGS["test"], "facts"), _judge_files(CHECK, "facts"))
    style = style_agreement(_judge_files(CONFIGS["test"], "style"), _judge_files(CHECK, "style"))
    claims = evaluate(by_item(CONFIGS["test"]), best, facts, style, spec)
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    (HERE / "results" / "claims-test.json").write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    main()
