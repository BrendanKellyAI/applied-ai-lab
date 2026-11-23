"""S4 E5's pre-registered claims, applied to the test results. See PREREGISTRATION.md.

C1, C2 and C5 compare arms item by item, so they score each arm's saved replies against the
frozen labels. C3 counts input tokens with one tokeniser for every arm (o200k_base, plus the
chat template allowance in lab.adapt.tune), from the prompts each arm sends. C5 is not tested
(Amendment 1: the one-line tuned arm was not run).
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
from lab.adapt.tune import _files, message_tokens
from lab.adapt.tune_config import TuneConfig
from lab.rag.compare import paired

HERE = Path(__file__).parent
DATA = HERE.parents[1] / "datasets" / "halvard-tasks"
TUNED = "e5-tuned-short"
# The job whose eval prompts each arm sends: the reference sends E2's definitions prompt, which is
# exactly what the untuned job was given.
PROMPTS = {"e5-reference": "tune-untuned-0-6b.yaml", TUNED: "tune-short.yaml"}


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fully_right_by_item(arm: str, split: str, results: Path = HERE / "results") -> dict[str, bool]:
    lines = (results / arm / f"predictions-{split}.jsonl").read_text(encoding="utf-8").splitlines()
    texts = {row["id"]: row["text"] for row in map(json.loads, lines)}
    scores = score_items(triage_items(DATA, split), texts, Definitions.load(DATA / "routes.yaml"))
    return {s.id: s.fully_right for s in scores}


def safety_recall(arm: str, split: str, results: Path = HERE / "results") -> dict[str, Any]:
    lines = (results / arm / f"predictions-{split}.jsonl").read_text(encoding="utf-8").splitlines()
    texts = {row["id"]: row["text"] for row in map(json.loads, lines)}
    scores = score_items(triage_items(DATA, split), texts, Definitions.load(DATA / "routes.yaml"))
    items = [s for s in scores if s.safety_item]
    found = sum(s.flagged for s in items)
    return {"count": found, "total": len(items), "rate": found / len(items)}


def mean_input_tokens(job: str, split: str) -> float:
    """Mean o200k tokens of the system and user messages an arm sends on a split."""
    files, _ = _files(TuneConfig.load(HERE / job))
    rows = [json.loads(line) for line in files[f"eval-{split}.jsonl"].splitlines()]
    return round(sum(message_tokens(r["messages"]) for r in rows) / len(rows), 1)


def _beats(a: Mapping[str, bool], b: Mapping[str, bool]) -> dict[str, Any]:
    return {"a": sum(a.values()), "b": sum(b.values()), **paired(a, b)}


def c1(tuned: Mapping[str, bool], untuned: Mapping[str, bool], mark: Mapping[str, Any]) -> Claim:
    pair = _beats(tuned, untuned)
    held = pair["a"] > pair["b"] and pair["p_value"] < mark["p_below"]
    return Claim(id="C1", title=mark["title"], held=held, detail=pair)


def c2(tuned: Mapping[str, bool], reference: Mapping[str, bool], mark: Mapping[str, Any]) -> Claim:
    pair = _beats(tuned, reference)
    held = pair["p_value"] >= mark["p_at_least"]
    return Claim(id="C2", title=mark["title"], held=held, detail=pair)


def c3(tuned_tokens: float, reference_tokens: float, mark: Mapping[str, Any]) -> Claim:
    ratio = round(tuned_tokens / reference_tokens, 4)
    return Claim(
        id="C3",
        title=mark["title"],
        held=ratio <= mark["ratio_at_most"],
        detail={"tuned": tuned_tokens, "reference": reference_tokens, "ratio": ratio},
    )


def c4(recall: Mapping[str, Any], mark: Mapping[str, Any]) -> Claim:
    return Claim(
        id="C4",
        title=mark["title"],
        held=recall["rate"] >= mark["rate_at_least"],
        detail={"safety_recall": dict(recall)},
    )


def c5(mark: Mapping[str, Any]) -> Claim:
    return Claim(
        id="C5",
        title=mark["title"],
        held=None,
        detail={"not_tested": "e5-tuned-one-line was not run (PREREGISTRATION Amendment 1)"},
    )


def evaluate(
    by_item: Mapping[str, Mapping[str, bool]],
    tokens: Mapping[str, float],
    recall: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> list[Claim]:
    marks = spec["claims"]
    return [
        c1(by_item[TUNED], by_item["e5-untuned-0-6b"], marks["C1"]),
        c2(by_item[TUNED], by_item["e5-reference"], marks["C2"]),
        c3(tokens[TUNED], tokens["e5-reference"], marks["C3"]),
        c4(recall, marks["C4"]),
        c5(marks["C5"]),
    ]


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main(split: str = "test") -> None:
    arms = ("e5-reference", "e5-untuned-0-6b", TUNED)
    by_item = {arm: fully_right_by_item(arm, split) for arm in arms}
    tokens = {arm: mean_input_tokens(job, split) for arm, job in PROMPTS.items()}
    claims = evaluate(by_item, tokens, safety_recall(TUNED, split), load_claims_file())
    out = HERE / "results" / f"claims-{split}.json"
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    out.write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "test")
