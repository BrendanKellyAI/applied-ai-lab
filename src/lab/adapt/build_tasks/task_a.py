"""Build Task A: generate a message for every seed, check it in code, label it blind, drop
disagreements and near duplicates, and keep the first items to pass in seed order.

Every call goes through the harness runner, so it is cached and logged, and a rebuild from the
same seeds sends nothing.
"""

import json
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from lab.adapt.build_tasks.checks import ReplyError, check_message, message_of, parse_object
from lab.adapt.build_tasks.config import SPLITS, Split, TaskBuildConfig
from lab.adapt.build_tasks.dedupe import NearDuplicateIndex, near_duplicates
from lab.adapt.build_tasks.prompts import (
    GENERATOR_SYSTEM,
    generation_prompt,
    labeller_prompt,
    labeller_system,
)
from lab.adapt.build_tasks.seeds import Seed, draw_seeds, seed_count
from lab.adapt.definitions import Definitions, Label
from lab.rag.build_corpus.generate import Generated, Outcome, Task, generate
from lab.rag.waves import planned, request_for, run_wave
from lab.runner import Runner, RunSummary

RETRY_TEMPLATE = "That draft does not meet the brief: {problem} Reply again with the JSON object."
EPISODE = "s4-task-data"
REVIEW_SAMPLE = 50


@dataclass(frozen=True)
class Kept:
    seed: Seed
    message: str


def plan_seeds(config: TaskBuildConfig, definitions: Definitions, *, pilot: bool) -> list[Seed]:
    task = config.task_a
    if pilot:
        return draw_seeds("dev", task.pilot_seeds, task, definitions, config.seed)
    seeds: list[Seed] = []
    for split in SPLITS:
        n = seed_count(task.splits[split], task.overgenerate)
        seeds += draw_seeds(split, n, task, definitions, config.seed)
    return seeds


def generation_tasks(seeds: Sequence[Seed], definitions: Definitions) -> list[Task]:
    return [
        Task(id=s.id, system=GENERATOR_SYSTEM, prompt=generation_prompt(s, definitions))
        for s in seeds
    ]


def parse_label(text: str, definitions: Definitions) -> Label:
    try:
        label = Label.model_validate(parse_object(text))
        label.check_against(definitions)
    except (ReplyError, ValueError) as exc:
        raise ReplyError(f"unparsed label: {exc}") from exc
    return label


def build_task_a(
    runner: Runner,
    config: TaskBuildConfig,
    definitions: Definitions,
    folder: Path,
    *,
    pilot: bool,
) -> dict:
    """Run the build and write the splits, the build log and the review sample to `folder`."""
    seeds = plan_seeds(config, definitions, pilot=pilot)
    by_id = {s.id: s for s in seeds}
    raw = folder / "raw"
    generated = generate(
        runner,
        generation_tasks(seeds, definitions),
        config.generator,
        lambda seed_id, text: check_message(by_id[seed_id], text, definitions),
        stage="task-a-generate",
        folder=raw,
        max_attempts=config.max_attempts,
        retry_template=RETRY_TEMPLATE,
    )
    messages = {
        seed_id: message_of(outcome.text)
        for seed_id, outcome in generated.outcomes.items()
        if outcome.text is not None
    }
    labels, label_summary = _label(runner, config, definitions, messages, raw)
    disagreed = _disagreements(by_id, labels, messages, definitions)
    agreed = {k: v for k, v in messages.items() if k not in disagreed}
    removed = _remove_near_duplicates(by_id, agreed, config.task_a.near_duplicate_threshold)
    kept = _keep(seeds, agreed, removed, config, pilot=pilot)
    _write_splits(folder, kept)
    log = _build_log(
        config, seeds, generated.failed(), disagreed, removed, kept, generated, label_summary
    )
    (folder / "build_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    if not pilot:
        _write_review_sample(folder, kept.get("test", []), config.seed)
    return log


def _label(
    runner: Runner,
    config: TaskBuildConfig,
    definitions: Definitions,
    messages: Mapping[str, str],
    raw: Path,
) -> tuple[dict[str, str], RunSummary]:
    system = labeller_system(definitions)
    calls = [
        planned(
            request_for(
                config.labeller,
                system=system,
                prompt=labeller_prompt(message),
                episode=EPISODE,
                stage="task-a-label",
            ),
            stage="task-a-label",
            item_id=seed_id,
            condition="blind",
        )
        for seed_id, message in messages.items()
    ]
    results, summary = run_wave(runner, calls, raw / "raw-task-a-label.jsonl")
    return {seed_id: result.text for seed_id, result in results.items()}, summary


def _disagreements(
    by_id: Mapping[str, Seed],
    labels: Mapping[str, str],
    messages: Mapping[str, str],
    definitions: Definitions,
) -> dict[str, tuple[str, ...]]:
    """Each discarded item and why: the fields that differ, or why it has no label."""
    discarded: dict[str, tuple[str, ...]] = {}
    for seed_id in messages:
        text = labels.get(seed_id)
        if text is None:
            discarded[seed_id] = ("no label",)
            continue
        try:
            label = parse_label(text, definitions)
        except ReplyError:
            discarded[seed_id] = ("unparsed",)
            continue
        fields = by_id[seed_id].label.disagreements(label)
        if fields:
            discarded[seed_id] = fields
    return discarded


def _remove_near_duplicates(
    by_id: Mapping[str, Seed], agreed: Mapping[str, str], threshold: float
) -> dict[str, tuple[str, float]]:
    train = {k: v for k, v in agreed.items() if by_id[k].split == "train"}
    if not train:
        return {}
    held_out = {k: v for k, v in agreed.items() if by_id[k].split != "train"}
    return near_duplicates(held_out, NearDuplicateIndex(train), threshold)


def _keep(
    seeds: Sequence[Seed],
    agreed: Mapping[str, str],
    removed: Mapping[str, tuple[str, float]],
    config: TaskBuildConfig,
    *,
    pilot: bool,
) -> dict[Split, list[Kept]]:
    kept: dict[Split, list[Kept]] = {}
    seen: set[str] = set()
    for seed in seeds:
        if seed.id not in agreed or seed.id in removed:
            continue
        # Two seeds can still get the same text; keep only the first, in any split.
        text = " ".join(agreed[seed.id].lower().split())
        if text in seen:
            continue
        target = config.task_a.pilot_seeds if pilot else config.task_a.splits[seed.split]
        bucket = kept.setdefault(seed.split, [])
        if len(bucket) < target:
            bucket.append(Kept(seed=seed, message=agreed[seed.id]))
            seen.add(text)
    return kept


def item_record(item: Kept) -> dict:
    seed = item.seed
    return {
        "id": seed.id,
        "message": item.message,
        "label": seed.label.model_dump(),
        "kind": seed.kind,
        "channel": seed.channel,
        "name": seed.name,
        "tone": seed.tone,
        "habit": seed.habit,
    }


def _write_splits(folder: Path, kept: Mapping[Split, list[Kept]]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for split, items in kept.items():
        lines = [json.dumps(item_record(i), ensure_ascii=False) for i in items]
        (folder / f"{split}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_log(
    config: TaskBuildConfig,
    seeds: Sequence[Seed],
    failed: Sequence[Outcome],
    disagreed: Mapping[str, tuple[str, ...]],
    removed: Mapping[str, tuple[str, float]],
    kept: Mapping[Split, list[Kept]],
    generated: Generated,
    label_summary: RunSummary,
) -> dict:
    by_id = {s.id: s for s in seeds}
    return {
        "dataset_version": config.dataset_version,
        "generator": config.generator.model_dump(),
        "labeller": config.labeller.model_dump(),
        "seeds": dict(Counter(s.split for s in seeds)),
        "generation_failed": sorted(o.id for o in failed),
        "label_disagreements": {
            "total": len(disagreed),
            "by_field": dict(Counter(f for fields in disagreed.values() for f in fields)),
            "by_route": dict(Counter(by_id[k].label.route for k in disagreed)),
            "by_kind": dict(Counter(by_id[k].kind for k in disagreed)),
            "items": {k: list(v) for k, v in sorted(disagreed.items())},
        },
        "near_duplicates_removed": {
            k: {"train_item": m, "similarity": round(s, 3)} for k, (m, s) in sorted(removed.items())
        },
        "kept": {split: len(items) for split, items in kept.items()},
        "safety_items_kept": {
            split: sum(i.seed.label.safety for i in items) for split, items in kept.items()
        },
        "generation_attempts": [_summary(s) for s in generated.summaries],
        "label_calls": _summary(label_summary),
    }


def _summary(summary: RunSummary) -> dict:
    return {
        "planned": summary.planned,
        "made": summary.made,
        "cached": summary.cached,
        "failed": summary.failed,
        "tokens": {
            provider: {"input": t.input_tokens, "output": t.output_tokens}
            for provider, t in summary.tokens_by_provider.items()
        },
    }


def _write_review_sample(folder: Path, test: Sequence[Kept], seed: int) -> None:
    """The items Brendan checks by hand before the test set is frozen."""
    sample = random.Random(f"{seed}:review").sample(list(test), min(REVIEW_SAMPLE, len(test)))
    lines = [
        "# Task A test items for hand checking",
        "",
        "For each item, mark whether the label is right. Any wrong label is reported in the "
        "dataset README.",
        "",
    ]
    for item in sorted(sample, key=lambda i: i.seed.id):
        label = item.seed.label
        lines += [
            f"## {item.seed.id} ({item.seed.kind})",
            "",
            item.message,
            "",
            f"route `{label.route}`, safety `{str(label.safety).lower()}`, product "
            f"`{label.product}`, fault `{label.fault}`",
            "",
            "- [ ] label is right",
            "",
        ]
    review = folder.parent / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "task-a-test-sample.md").write_text("\n".join(lines), encoding="utf-8")
