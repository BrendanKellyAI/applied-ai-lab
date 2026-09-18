"""Scores the S1 E10 results and builds its tables and charts.

Run through the harness, which needs no API key:

    uv run lab analyse field-notes/s1-e10-reasoning-vs-standard/config.yaml

The questions and their correct answers are committed in `tasks/items.jsonl`, so this analysis
reads them straight from the repository. The statistics live in `metrics.py` and the drawing in
`figures.py`; this module writes `summary.csv`, prints the report, and applies each chart's
highlight rule.
"""

import csv
from collections.abc import Sequence
from functools import cache
from pathlib import Path

from lab.config import ExperimentConfig
from lab.experiments import load_sibling
from lab.raw_log import RunRecord

HIGH_MODE = "high"
LOWEST_MODE = "lowest"
MODES = (LOWEST_MODE, HIGH_MODE)

SUMMARY_COLUMNS = (
    "model",
    "provider",
    "model_returned",
    "mode",
    "reasoning",
    "show_thinking",
    "task",
    "item_index",
    "answer_expected",
    "answer_given",
    "parsed",
    "correct",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "time_to_first_thinking_ms",
    "time_to_first_answer_token_ms",
    "total_latency_ms",
    "finish_reason",
)

# Two-letter codes for the scatter, where twelve full task names would not fit. The key is in
# the chart's own footnote, so the chart is readable on its own.
TASK_CODES = {
    "extraction": "Ex",
    "arithmetic": "Ar",
    "state-tracking": "St",
    "constraint-puzzle": "Pz",
}
# The footnote every chart carries, because "lowest" does not mean the same thing on all three.
MODE_FOOTNOTE = (
    "Lowest reasoning is off for Terra and Sonnet 5, and minimal\n"
    "for Gemini 3.6 Flash, which cannot turn thinking off."
)
# The scatter has no room for a third footer line, so its key and the caveat share two.
SCATTER_FOOTNOTE = (
    "Ex extraction, Ar arithmetic, St state tracking, Pz puzzles.\n"
    "Lowest reasoning is minimal on Gemini 3.6 Flash, off elsewhere."
)
COLUMN_WIDTH = 16
# Width of the "model / task" column in the printed comparison table.
PAIR_WIDTH = 36
# How many unparsed or truncated responses to name before the report just gives the count.
EXAMPLES_SHOWN = 10


class AnalysisError(RuntimeError):
    """The results cannot be analysed."""


@cache
def _module(name: str):
    return load_sibling(Path(__file__).parent / name)


def _metrics():
    return _module("metrics.py")


def _figures():
    return _module("figures.py")


def _items(folder: Path):
    return _module("build_dataset.py").read_items(folder)


def _settings(config: ExperimentConfig) -> dict[tuple[str, str], tuple[str, bool]]:
    """The reasoning level and thinking setting each model ran with, per mode.

    Published in summary.csv so no reader has to open the config to see what "lowest" meant for
    a given model.
    """
    return {
        (model.display_label, mode): (str(settings.reasoning), settings.show_thinking)
        for model in config.models
        for mode, settings in model.modes.items()
    }


def _write_summary(
    path: Path, records: Sequence[RunRecord], items, config: ExperimentConfig
) -> int:
    metrics = _metrics()
    expected = {(item.task, item.index): item for item in items}
    settings = _settings(config)
    rows = []
    for record in sorted(
        metrics.successful(records),
        key=lambda r: (r.model_label, str(r.cell["task"]), int(r.cell["item_index"]), r.mode),
    ):
        result = record.result
        item = expected.get((str(record.cell["task"]), int(record.cell["item_index"])))
        if item is None:
            continue
        correct, answer = metrics.score(result.text, item.answer, item.answer_kind)
        reasoning, show_thinking = settings.get((record.model_label, record.mode), ("", False))
        rows.append(
            {
                "model": record.model_label,
                "provider": result.provider,
                "model_returned": result.model_returned,
                "mode": record.mode,
                "reasoning": reasoning,
                "show_thinking": show_thinking,
                "task": item.task,
                "item_index": item.index,
                "answer_expected": item.answer,
                "answer_given": "" if answer is None else answer,
                "parsed": answer is not None,
                "correct": correct,
                "input_tokens": result.input_tokens,
                "cached_input_tokens": result.cached_input_tokens,
                "output_tokens": result.output_tokens,
                "reasoning_tokens": result.reasoning_tokens,
                "time_to_first_thinking_ms": result.time_to_first_thinking_ms,
                "time_to_first_answer_token_ms": result.time_to_first_answer_token_ms,
                "total_latency_ms": result.total_latency_ms,
                "finish_reason": result.finish_reason,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# --------------------------------------------------------------------------------------------
# Highlight rules. Each returns the element to colour acid green, or None when nothing
# qualifies, in which case the chart says so.
# --------------------------------------------------------------------------------------------


def best_gain_task(scored, tasks: Sequence[str], models: Sequence[str]) -> int | None:
    """The task with the largest accuracy gain that is clear of chance.

    Two conditions, not one. The pooled interval over all three models treats its pairs as
    independent, and they are not: the same 30 items are put to every model, so item difficulty
    is shared and the interval is a little narrower than the data warrants. Every model must
    therefore also have moved the same way before the bar is painted.
    """
    metrics = _metrics()
    qualifying = []
    for index, task in enumerate(tasks):
        pooled = metrics.gain(
            metrics.select(scored, task=task), lowest_mode=LOWEST_MODE, high_mode=HIGH_MODE
        )
        if pooled is None or pooled.change <= 0 or not pooled.significant:
            continue
        per_model = [
            metrics.gain(
                metrics.select(scored, task=task, model=model),
                lowest_mode=LOWEST_MODE,
                high_mode=HIGH_MODE,
            )
            for model in models
        ]
        if any(found is None or found.change <= 0 for found in per_model):
            continue
        qualifying.append((pooled.change, -index, index))
    return max(qualifying)[2] if qualifying else None


def largest_multiple_task(multiples: Sequence[float | None]) -> int | None:
    """The task where high reasoning billed the most extra output tokens, if any did."""
    above_one = [
        (value, -index, index)
        for index, value in enumerate(multiples)
        if value is not None and value > 1
    ]
    return max(above_one)[2] if above_one else None


def best_value_point(points: Sequence[tuple[str, str, float, float]]) -> tuple[str, str] | None:
    """Among points that gained accuracy, the most accuracy per 1,000 extra output tokens."""
    candidates = [
        (change / (extra / 1000.0), model, task)
        for model, task, extra, change in points
        if change > 0 and extra > 0
    ]
    if not candidates:
        return None
    _, model, task = max(candidates)
    return model, task


def longest_thinking_gap(rows: Sequence[tuple[str, float | None, float]]) -> int | None:
    """The row where a user waits longest with thinking on screen and no answer yet."""
    gaps = [
        (answer - thinking, -index, index)
        for index, (_, thinking, answer) in enumerate(rows)
        if thinking is not None and answer > thinking
    ]
    return max(gaps)[2] if gaps else None


# --------------------------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------------------------


def drawable_tasks(scored, tasks: Sequence[str]) -> list[str]:
    """Tasks with calls in both modes.

    A task answered in only one mode is left off the bar charts rather than drawn as zero, which
    would read as "the model got everything wrong" instead of "this was not run".
    """
    metrics = _metrics()
    return [
        task
        for task in tasks
        if all(metrics.select(scored, task=task, mode=mode) for mode in MODES)
    ]


def _accuracies(scored, tasks: Sequence[str], mode: str) -> list[float]:
    metrics = _metrics()
    return [metrics.accuracy(metrics.select(scored, task=task, mode=mode)).point for task in tasks]


def _scatter_points(scored, tasks: Sequence[str], models: Sequence[str]):
    """One point per model and task: extra output tokens against accuracy points gained."""
    metrics = _metrics()
    points = []
    for model in models:
        for task in tasks:
            comparison = metrics.compare(
                scored, model=model, task=task, lowest_mode=LOWEST_MODE, high_mode=HIGH_MODE
            )
            change = comparison.accuracy_change_points
            if change is None or comparison.extra_output_tokens is None:
                continue
            points.append(
                (model, TASK_CODES.get(task, task), comparison.extra_output_tokens, change)
            )
    return points


def _first_token_rows(scored, models: Sequence[str]) -> list[tuple[str, float | None, float]]:
    """One row per model and mode, dropping any with no measured first answer token.

    Where a model streamed thinking, both medians are taken over the calls that reported
    thinking. Taking the answer median over every call instead would put the two ends of the
    span on different populations, and the gap drawn between them would mean nothing.
    """
    metrics = _metrics()
    rows = []
    for model in models:
        for mode in MODES:
            chosen = metrics.select(scored, model=model, mode=mode)
            thought = [outcome for outcome in chosen if outcome.first_thinking_ms is not None]
            measured = thought or chosen
            answer = metrics.median([outcome.first_answer_ms for outcome in measured])
            if answer is None:
                continue
            thinking = metrics.median([outcome.first_thinking_ms for outcome in thought])
            rows.append((f"{model}\n{mode}", thinking, answer))
    return rows


def _charts(
    scored, config: ExperimentConfig, out_dir: Path, tasks: Sequence[str], models: Sequence[str]
) -> list[Path]:
    figures = _figures()
    metrics = _metrics()
    names = _module("generators.py").TASK_NAMES
    items_per_task = int(config.parameters["items_per_task"])
    sample = f"n = {items_per_task} items x {len(models)} models"
    written: list[Path] = []

    drawable = drawable_tasks(scored, tasks)
    if drawable:
        labels = [names.get(task, task) for task in drawable]
        gain_index = best_gain_task(scored, drawable, models)
        written += figures.accuracy_by_task(
            out_dir,
            labels=labels,
            lowest=_accuracies(scored, drawable, LOWEST_MODE),
            high=_accuracies(scored, drawable, HIGH_MODE),
            highlight_index=gain_index,
            sample_size=sample,
            footnote=MODE_FOOTNOTE,
            no_highlight_note=(
                None
                if gain_index is not None
                else "No gain was clear of chance, so nothing is highlighted."
            ),
        )

        # Only tasks with a token multiple: a task with none has no calls to compare, and a
        # zero bar would read as "high reasoning billed nothing", which is the opposite.
        measured = [
            (names.get(task, task), value)
            for task in drawable
            if (
                value := metrics.token_multiple(
                    scored, task=task, lowest_mode=LOWEST_MODE, high_mode=HIGH_MODE
                )
            )
            is not None
        ]
        multiples = [value for _, value in measured]
        multiple_index = largest_multiple_task(multiples)
        written += figures.token_multiple_by_task(
            out_dir,
            labels=[label for label, _ in measured],
            multiples=multiples,
            highlight_index=multiple_index,
            sample_size=sample,
            footnote=MODE_FOOTNOTE,
            no_highlight_note=(
                None
                if multiple_index is not None
                else "High reasoning billed no extra tokens; nothing highlighted."
            ),
        )

    points = _scatter_points(scored, tasks, models)
    if points:
        best = best_value_point(points)
        written += figures.cost_of_accuracy(
            out_dir,
            points=points,
            models=list(models),
            highlight_key=best,
            sample_size=f"n = {items_per_task} items per point",
            footnote=SCATTER_FOOTNOTE,
            no_highlight_note=(
                None
                if best is not None
                else "No model and task gained accuracy; nothing highlighted."
            ),
        )

    rows = _first_token_rows(scored, models)
    if rows:
        gap_index = longest_thinking_gap(rows)
        written += figures.two_kinds_of_first_token(
            out_dir,
            rows=rows,
            highlight_index=gap_index,
            sample_size=f"n = {items_per_task * len(tasks)} per model and mode",
            footnote=MODE_FOOTNOTE,
            no_highlight_note=(
                None
                if gap_index is not None
                else "No provider streamed thinking first; nothing highlighted."
            ),
        )
    return written


# --------------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------------


def _cell(found) -> tuple[str, str]:
    """The accuracy and its interval, as two strings, or dashes when a cell has no calls."""
    if found is None:
        return "-", "-"
    return f"{found.point:.0%}", f"{found.low:.0%}-{found.high:.0%}"


def _accuracy_lines(scored, models: Sequence[str], tasks: Sequence[str]) -> list[str]:
    metrics = _metrics()
    lines = ["Accuracy by model, task, and mode, with Wilson 95% intervals:"]
    header = "".join(f"{mode:>{COLUMN_WIDTH}}" for mode in MODES)
    for model in models:
        if not metrics.select(scored, model=model):
            continue
        lines += ["", f"  {model}", f"    {'task':<18}{header}"]
        for task in tasks:
            cells = [
                _cell(metrics.accuracy(metrics.select(scored, model=model, task=task, mode=mode)))
                for mode in MODES
            ]
            lines.append(
                f"    {task:<18}" + "".join(f"{point:>{COLUMN_WIDTH}}" for point, _ in cells)
            )
            lines.append(
                f"    {'':<18}" + "".join(f"{spread:>{COLUMN_WIDTH}}" for _, spread in cells)
            )
    return lines


def _gain_lines(scored, tasks: Sequence[str]) -> list[str]:
    metrics = _metrics()
    lines = [
        "Accuracy change from lowest to high reasoning, paired over the same items, with a "
        "95% interval:"
    ]
    for task in tasks:
        found = metrics.gain(
            metrics.select(scored, task=task), lowest_mode=LOWEST_MODE, high_mode=HIGH_MODE
        )
        if found is None:
            lines.append(f"  {task:<20} no items answered in both modes")
            continue
        verdict = "excludes zero" if found.significant else "includes zero"
        lines.append(
            f"  {task:<20} {found.change_points:+6.1f} points "
            f"({found.low * 100:+.1f} to {found.high * 100:+.1f}, {verdict}), "
            f"{found.pairs} pairs"
        )
    lines += [
        "  An interval that includes zero is not a finding: the change is within what chance "
        "would produce.",
        "  The pairs pool three models over the same 30 items, so item difficulty is shared and "
        "these",
        "  intervals are slightly optimistic. The per-model figures in the next table do not pool.",
    ]
    return lines


def _cost_lines(scored, models: Sequence[str], tasks: Sequence[str]) -> list[str]:
    metrics = _metrics()
    lines = [
        "What high reasoning cost and bought, per model and task:",
        f"  {'model / task':<{PAIR_WIDTH}}  tokens   latency   accuracy   points per 1k tokens",
    ]
    for model in models:
        for task in tasks:
            comparison = metrics.compare(
                scored, model=model, task=task, lowest_mode=LOWEST_MODE, high_mode=HIGH_MODE
            )
            if comparison.output_token_multiple is None:
                continue
            lines.append(
                f"  {f'{model} / {task}':<{PAIR_WIDTH}}"
                f"{_multiple(comparison.output_token_multiple):>7}"
                f"{_multiple(comparison.latency_multiple):>10}"
                f"{_points(comparison.accuracy_change_points):>11}"
                f"{_points_per_thousand(comparison.points_per_thousand_tokens):>23}"
            )
    return lines


def _multiple(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}x"


def _points(value: float | None) -> str:
    return "-" if value is None else f"{value:+.1f}"


def _points_per_thousand(value: float | None) -> str:
    return "-" if value is None else f"{value:+.1f}"


def _usage_lines(scored, models: Sequence[str]) -> list[str]:
    metrics = _metrics()
    lines = [
        "Billed output tokens, reasoning tokens where the provider reports them, and latency. "
        "Median and 90th percentile:"
    ]
    for model in models:
        for mode in MODES:
            chosen = metrics.select(scored, model=model, mode=mode)
            if not chosen:
                continue
            reasoning = [o.reasoning_tokens for o in chosen if o.reasoning_tokens is not None]
            output = _pair(metrics, [o.output_tokens for o in chosen], _number)
            thought = "not reported" if not reasoning else _pair(metrics, reasoning, _number)
            total = _pair(metrics, [o.total_latency_ms for o in chosen], _ms)
            first_answer = _pair(metrics, [o.first_answer_ms for o in chosen], _ms)
            first_thinking = _ms(metrics.median([o.first_thinking_ms for o in chosen]))
            lines.append(f"  {f'{model} [{mode}]':<28}output {output}   reasoning {thought}")
            lines.append(
                f"  {'':<28}total {total}   first answer token {first_answer}"
                f"   first thinking {first_thinking}"
            )
    return lines


def _pair(metrics, values, render) -> str:
    """Median and 90th percentile of a measurement, as one string."""
    return f"{render(metrics.median(values))} / {render(metrics.percentile_90(values))}"


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:,.0f}"


def _ms(value: float | None) -> str:
    return "-" if value is None else f"{value / 1000:.1f}s"


def _parse_lines(scored) -> list[str]:
    unparsed = [outcome for outcome in scored if not outcome.parsed]
    if not unparsed:
        return [
            f"Answer parse rate: 100%. Every one of the {len(scored)} scored responses ended "
            "with an ANSWER line."
        ]
    rate = 100 * (len(scored) - len(unparsed)) / len(scored)
    lines = [
        f"Answer parse rate: {rate:.1f}%. {len(unparsed)} response(s) had no ANSWER line and "
        "are scored incorrect. Read them before drawing any conclusion:"
    ]
    for outcome in unparsed[:EXAMPLES_SHOWN]:
        lines.append(f"  {outcome.model} [{outcome.mode}] {outcome.task} item {outcome.item_index}")
    return lines


def _truncation_lines(scored) -> list[str]:
    truncated = [outcome for outcome in scored if outcome.finish_reason == "length"]
    if not truncated:
        return ["No response hit its output limit, so no reasoning was cut short."]
    lines = [
        f"{len(truncated)} response(s) hit the output limit and are scored incorrect. Raise "
        "max_output_tokens for that model and mode and rerun those calls:"
    ]
    for outcome in truncated[:EXAMPLES_SHOWN]:
        lines.append(f"  {outcome.model} [{outcome.mode}] {outcome.task} item {outcome.item_index}")
    return lines


def _failure_lines(records: Sequence[RunRecord]) -> list[str]:
    """How many distinct calls failed. A call retried twice is one failed call, not two."""
    metrics = _metrics()
    succeeded = {record.call_id for record in metrics.successful(records)}
    failed = {
        record.call_id
        for record in records
        if record.result is None and record.call_id not in succeeded
    }
    if not failed:
        return []
    return [f"{len(failed)} call(s) failed and are not scored. Run `lab run` again to retry them."]


def analyse(
    config: ExperimentConfig,
    folder: Path,
    records: Sequence[RunRecord],
    out_dir: Path | None = None,
) -> str:
    """Score the results, write summary.csv and the charts, and return the report text."""
    metrics = _metrics()
    items = _items(folder)
    scored = metrics.outcomes(records, items)
    if not scored:
        raise AnalysisError(
            "These results contain no successful calls for any committed item, so there is "
            "nothing to score."
        )

    tasks = tuple(str(task) for task in config.parameters["tasks"])
    models = [model.display_label for model in config.models]
    # Written beside the records they came from, so analysing a fresh run leaves the
    # published results/ folder untouched.
    results_folder = out_dir if out_dir is not None else folder / "results"
    rows = _write_summary(results_folder / "summary.csv", records, items, config)
    charts = _charts(scored, config, results_folder / "charts", tasks, models)

    lines = [
        f"{config.experiment}: {rows} scored call(s) across {len(models)} model(s) and "
        f"{len(tasks)} task(s).",
        "",
        *_accuracy_lines(scored, models, tasks),
        "",
        *_gain_lines(scored, tasks),
        "",
        *_cost_lines(scored, models, tasks),
        "",
        *_usage_lines(scored, models),
        "",
        *_parse_lines(scored),
        "",
        *_truncation_lines(scored),
    ]
    failures = _failure_lines(records)
    if failures:
        lines += ["", *failures]
    lines += [
        "",
        f"Written: {results_folder / 'summary.csv'}",
        f"Charts:  {len(charts)} file(s) in {results_folder / 'charts'}",
    ]
    return "\n".join(lines)
