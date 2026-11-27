"""`lab adapt run`: send every prompted arm's requests, and for Task B the judge's, then write
each arm's predictions. Every call goes through the runner, so it is cached and logged, and a
rerun sends nothing new.

Files, under the episode's results folder:
  <arm>/predictions-<split>.jsonl   one {"id", "text", token counts} per item
  <arm>/facts-<split>.jsonl         Task B: the facts judge's reply per answerable item
  <arm>/style-<split>.jsonl         Task B: the style judge's reply per item and order
  raw/                              the runner's raw logs
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from lab.adapt.examples import Embed
from lab.adapt.experiment import Experiment
from lab.adapt.requests import (
    Inputs,
    arm_requests,
    facts_requests,
    style_requests,
)
from lab.providers.base import GenerationRequest, GenerationResult
from lab.rag.waves import planned, run_wave
from lab.runner import Runner, RunSummary


def arm_folder(experiment: Experiment, arm: str) -> Path:
    return experiment.results / arm


def predictions_path(experiment: Experiment, arm: str) -> Path:
    """Where an arm's predictions live: its own file for an external arm."""
    spec = experiment.arm(arm)
    if spec.predictions is not None:
        return experiment.path(spec.predictions)
    return arm_folder(experiment, arm) / f"predictions-{experiment.split}.jsonl"


def write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_texts(path: Path) -> dict[str, str]:
    return {row["id"]: row["text"] for row in read_jsonl(path) if row.get("text") is not None}


def _row(key: str, result: GenerationResult) -> dict:
    return {
        "id": key,
        "text": result.text,
        "input_tokens": result.input_tokens,
        "cached_input_tokens": result.cached_input_tokens,
        "output_tokens": result.output_tokens,
        "model_returned": result.model_returned,
    }


def _wave(
    runner: Runner,
    experiment: Experiment,
    requests: Mapping[str, GenerationRequest],
    stage: str,
    condition: str,
) -> tuple[dict[str, GenerationResult], RunSummary]:
    calls = [
        planned(request, stage=stage, item_id=key, condition=condition)
        for key, request in requests.items()
    ]
    raw = experiment.results / "raw" / f"raw-{stage}-{experiment.split}.jsonl"
    return run_wave(runner, calls, raw)


def run_experiment(
    runner: Runner, experiment: Experiment, inputs: Inputs, embed: Embed | None = None
) -> dict[str, dict]:
    """Run every prompted arm, then the Task B judges. Returns the run summaries by stage."""
    summaries: dict[str, dict] = {}
    replies: dict[str, dict[str, str]] = {}
    for arm in experiment.arms:
        if arm.external:
            replies[arm.name] = read_texts(predictions_path(experiment, arm.name))
            continue
        requests = arm_requests(experiment, arm, inputs, embed)
        results, summary = _wave(runner, experiment, requests, f"answer-{arm.name}", arm.name)
        rows = [_row(item.id, results[item.id]) for item in inputs.items if item.id in results]
        write_jsonl(predictions_path(experiment, arm.name), rows)
        replies[arm.name] = {r["id"]: r["text"] for r in rows}
        summaries[f"answer-{arm.name}"] = summary_dict(summary)
    if experiment.task == "b":
        summaries |= _judge(runner, experiment, inputs, replies)
    return summaries


def _judge(
    runner: Runner, experiment: Experiment, inputs: Inputs, replies: Mapping[str, dict[str, str]]
) -> dict[str, dict]:
    summaries = {}
    reference = replies[experiment.reference]
    for arm in experiment.arms:
        folder = arm_folder(experiment, arm.name)
        facts = facts_requests(experiment, inputs, replies[arm.name], arm.name)
        results, summary = _wave(runner, experiment, facts, f"facts-{arm.name}", arm.name)
        write_jsonl(
            folder / f"facts-{experiment.split}.jsonl",
            [_row(k, v) for k, v in sorted(results.items())],
        )
        summaries[f"facts-{arm.name}"] = summary_dict(summary)
        if arm.name == experiment.reference:
            continue
        style = style_requests(experiment, inputs, replies[arm.name], reference, arm.name)
        results, summary = _wave(runner, experiment, style, f"style-{arm.name}", arm.name)
        write_jsonl(
            folder / f"style-{experiment.split}.jsonl",
            [_row(k, v) for k, v in sorted(results.items())],
        )
        summaries[f"style-{arm.name}"] = summary_dict(summary)
    return summaries


def summary_dict(summary: RunSummary) -> dict:
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
