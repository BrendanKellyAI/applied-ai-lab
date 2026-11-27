"""Builds the case world and the case facts, images and logs. No model calls.

The customer messages are written afterwards by a paid, gated step; this step writes
`cases/<split>.facts.jsonl`, which holds everything else, including each expected end state.
"""

import json
import random
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from lab.agent.case_draw import Drawer
from lab.agent.case_model import CaseFacts, Kind, Split
from lab.agent.cases import KIND_SIZES
from lab.agent.cases_media import DATASET, MediaBuilder
from lab.agent.cases_more import LongCaseBuilder, SequenceBuilder
from lab.agent.policy import load_policy
from lab.agent.world import build_world, write_csv

SEED = 20261127
TELEMETRY_SIZES: dict[Split, int] = {"dev": 15, "test": 45}
# Sequences (customers) and long cases per split: 40 of each in all.
SEQUENCE_SIZES: dict[Split, int] = {"dev": 10, "test": 30}
LONG_SIZES: dict[Split, int] = {"dev": 10, "test": 30}
ID_PREFIX = {("dev", False): "D", ("test", False): "T", ("dev", True): "LD", ("test", True): "LT"}


@dataclass(frozen=True)
class BuildSummary:
    cases: dict[str, int]
    kinds: dict[str, dict[str, int]]
    decisions: dict[str, dict[str, int]]
    images: int
    logs: int


def build_dataset(root: Path, seed: int = SEED) -> BuildSummary:
    """Write the world CSVs, case facts, images and logs under `root/datasets/halvard-cases`."""
    dataset = root / DATASET
    for folder in ("images", "telemetry"):
        shutil.rmtree(dataset / folder, ignore_errors=True)
    policy = load_policy()
    world = build_world(policy, seed)
    builder = MediaBuilder(Drawer(world, policy, random.Random(seed + 1)), root)
    order_rng = random.Random(seed + 2)
    files: dict[str, list[CaseFacts]] = {}
    for split in ("test", "dev"):
        slots = [(kind, i) for kind, n in KIND_SIZES[split].items() for i in range(n)]
        files[split] = _draw(builder, split, slots, order_rng, telemetry=False)
        telemetry_slots = [("telemetry", i) for i in range(TELEMETRY_SIZES[split])]
        files[f"telemetry-{split}"] = _draw(
            builder, split, telemetry_slots, order_rng, telemetry=True
        )
    sequences, long_cases = SequenceBuilder(builder), LongCaseBuilder(builder)
    for split in ("test", "dev"):
        files[f"sequences-{split}"] = [
            facts for n in range(SEQUENCE_SIZES[split]) for facts in sequences.sequence(n, split)
        ]
        files[f"long-{split}"] = [long_cases.long_case(n, split) for n in range(LONG_SIZES[split])]
    write_csv(world, dataset / "world")
    for name, cases in files.items():
        _write_jsonl(
            dataset / "cases" / f"{name}.facts.jsonl", [c.model_dump(mode="json") for c in cases]
        )
    _write_jsonl(dataset / "images" / "truth.jsonl", [asdict(t) for t in builder.image_truths])
    _write_jsonl(
        dataset / "telemetry" / "truth.jsonl", [asdict(t) for t in builder.telemetry_truths]
    )
    return _summary(files, len(builder.image_truths), len(builder.telemetry_truths))


def _draw(
    builder: MediaBuilder,
    split: Split,
    slots: list[tuple[Kind, int]],
    rng: random.Random,
    *,
    telemetry: bool,
) -> list[CaseFacts]:
    rng.shuffle(slots)
    cases = []
    for index, (kind, variant) in enumerate(slots, start=1):
        case_id = f"{ID_PREFIX[(split, telemetry)]}-{index:03d}"
        builder.case_id = case_id
        facts = getattr(builder, kind)(variant)
        cases.append(facts.model_copy(update={"case_id": case_id, "split": split}))
    return cases


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _summary(files: dict[str, list[CaseFacts]], images: int, logs: int) -> BuildSummary:
    return BuildSummary(
        cases={name: len(cases) for name, cases in files.items()},
        kinds={name: dict(Counter(c.kind for c in cases)) for name, cases in files.items()},
        decisions={
            name: dict(Counter(o.decision for c in cases for o in c.expected))
            for name, cases in files.items()
        },
        images=images,
        logs=logs,
    )


def load_facts(path: Path) -> list[CaseFacts]:
    with path.open(encoding="utf-8") as handle:
        return [CaseFacts.model_validate_json(line) for line in handle if line.strip()]
