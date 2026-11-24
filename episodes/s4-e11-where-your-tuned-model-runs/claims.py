"""S4 E11's pre-registered claims: the laptop's predictions and timing against E5's Colab run.

Run after results/laptop/ exists:

    uv run python episodes/s4-e11-where-your-tuned-model-runs/claims.py
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from lab.adapt.definitions import Definitions
from lab.adapt.items import triage_items
from lab.adapt.run import read_texts
from lab.adapt.score_a import score_items
from lab.rag.compare import paired

HERE = Path(__file__).parent
DATA = HERE.parents[1] / "datasets" / "halvard-tasks"
E5 = HERE.parent / "s4-e5-does-fine-tuning-beat-a-good-prompt" / "results" / "e5-tuned-short"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    held: bool | None
    detail: dict[str, Any]


def load_claims_file(path: Path = HERE / "claims.yaml") -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def colab_seconds_per_1000() -> float:
    record = json.loads((E5 / "job.json").read_text(encoding="utf-8"))
    test = [a for a in record["attempts"] if a["status"] == "succeeded"][-1]["result"]
    test = test["predictions"]["test"]
    return round(test["seconds"] / test["items"] * 1000, 1)


def fully_right(texts: Mapping[str, str]) -> dict[str, bool]:
    items = [i for i in triage_items(DATA, "test") if i.id in texts]
    scores = score_items(items, texts, Definitions.load(DATA / "routes.yaml"))
    return {s.id: s.fully_right for s in scores}


def evaluate(
    laptop: Mapping[str, str],
    colab: Mapping[str, str],
    laptop_per_1000: float,
    colab_per_1000: float,
    spec: Mapping[str, Any],
) -> list[Claim]:
    marks = spec["claims"]
    shared = [k for k in laptop if k in colab]
    same = sum(laptop[k] == colab[k] for k in shared)
    rate = same / len(shared)
    pair = paired(fully_right(laptop), fully_right({k: colab[k] for k in shared}))
    ratio = round(laptop_per_1000 / colab_per_1000, 1)
    per_message = round(laptop_per_1000 / 1000, 2)
    return [
        Claim(
            id="C1",
            title=marks["C1"]["title"],
            held=rate >= marks["C1"]["identical_at_least"],
            detail={"items": len(shared), "identical": same, "rate": round(rate, 4)},
        ),
        Claim(
            id="C2",
            title=marks["C2"]["title"],
            held=pair["p_value"] >= marks["C2"]["p_at_least"],
            detail=pair,
        ),
        Claim(
            id="C3",
            title=marks["C3"]["title"],
            held=ratio >= marks["C3"]["slower_at_least"],
            detail={
                "laptop_per_1000": laptop_per_1000,
                "colab_per_1000": colab_per_1000,
                "ratio": ratio,
            },  # fmt: skip
        ),
        Claim(
            id="C4",
            title=marks["C4"]["title"],
            held=per_message < marks["C4"]["seconds_per_message_below"],
            detail={"seconds_per_message": per_message},
        ),
    ]


def verdict(claim: Claim) -> str:
    return "Not tested" if claim.held is None else ("Held" if claim.held else "Failed")


def main() -> None:
    folder = HERE / "results" / "laptop"
    result = json.loads((folder / "local_result.json").read_text(encoding="utf-8"))
    claims = evaluate(
        read_texts(folder / "predictions-test.jsonl"),
        read_texts(E5 / "predictions-test.jsonl"),
        result["seconds_per_1000"],
        colab_seconds_per_1000(),
        load_claims_file(),
    )
    text = json.dumps([c.model_dump() for c in claims], indent=2) + "\n"
    (HERE / "results" / "claims.json").write_bytes(text.encode("utf-8"))
    for claim in claims:
        print(f"{claim.id} {verdict(claim)}: {claim.title}")


if __name__ == "__main__":
    main()
