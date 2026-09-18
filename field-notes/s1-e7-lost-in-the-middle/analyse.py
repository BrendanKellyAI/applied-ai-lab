"""Scores the S1 E7 results and builds its tables and charts.

Run through the harness, which needs no API key:

    uv run lab analyse field-notes/s1-e7-lost-in-the-middle/config.yaml

Scoring is deterministic (specification section 6.5): a response is correct if, once normalised,
it contains the exact inserted value. The facts are regenerated from the config seed, so the
analysis needs only the committed `raw.jsonl`, not the dataset.
"""

import csv
import importlib.util
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import (
    ARTICLE,
    LINE_STYLES,
    MIST,
    NAVY,
    SLATE,
    SLIDE,
    ChartSpec,
    ChartStyle,
    export_chart,
    heatmap,
    highlight,
)
from lab.config import ExperimentConfig
from lab.raw_log import RunRecord, latest_successful
from lab.scoring import contains_match, wilson_interval

SUMMARY_COLUMNS = (
    "model",
    "provider",
    "model_returned",
    "mode",
    "reasoning",
    "context_length_tokens",
    "position_percent",
    "fact_index",
    "correct",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "time_to_first_answer_token_ms",
    "total_latency_ms",
    "finish_reason",
)

# Charts are named after the finding, not the chart type, so a deck can use them directly.
HEATMAP_NAME = "accuracy-heatmap"
CURVE_NAME = "accuracy-by-position"
# The position curve is drawn at the longest context, where the effect should be strongest.
CURVE_LENGTH_TOKENS = 64000
# The "lost in the middle" dip is measured over the band between the 25% and 75% positions
# (section 6.6), which includes the middle of the document, where the dip is expected.
DIP_POSITIONS = (25, 50, 75)
EDGE_POSITIONS = (0, 100)
BASELINE_POSITION = 0
# Width of each position column in the printed accuracy table.
COLUMN_WIDTH = 15
# Smallest vertical gap between two direct labels on the position curve, in accuracy.
LABEL_GAP = 0.1
# How far below its line's lowest point each direct label sits, in points.
LABEL_OFFSET_POINTS = 12


class AnalysisError(RuntimeError):
    """The results cannot be analysed."""


@dataclass(frozen=True)
class Cell:
    """Accuracy for one model, context length, and position, over the facts in that cell."""

    model: str
    context_length_tokens: int
    position_percent: int
    correct: int
    trials: int
    point: float
    low: float
    high: float


def _facts(config: ExperimentConfig):
    """The same invented facts the dataset builder made, regenerated from the seed."""
    spec = importlib.util.spec_from_file_location(
        "s1_e7_facts", Path(__file__).parent / "build_dataset.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder.make_facts(config.seed, int(config.parameters["facts_per_cell"]))


def score(record: RunRecord, facts: Sequence) -> bool:
    """Whether the response contains the value of the fact that was inserted.

    A response cut short by the output limit is scored incorrect, which is why every one is
    flagged in the report rather than passed over.
    """
    if record.result is None:
        return False
    fact = facts[int(record.cell["fact_index"])]
    return contains_match(record.result.text, fact.value)


def _successful(records: Sequence[RunRecord]) -> list[RunRecord]:
    return list(latest_successful(list(records)).values())


def accuracy_by_cell(
    records: Sequence[RunRecord], facts: Sequence
) -> dict[tuple[str, int, int], Cell]:
    """Accuracy with a Wilson 95% interval for every model, length, and position."""
    tallies: dict[tuple[str, int, int], list[int]] = {}
    for record in _successful(records):
        key = (
            record.model_label,
            int(record.cell["context_length_tokens"]),
            int(record.cell["position_percent"]),
        )
        outcomes = tallies.setdefault(key, [])
        outcomes.append(1 if score(record, facts) else 0)

    cells = {}
    for key, outcomes in tallies.items():
        point, low, high = wilson_interval(sum(outcomes), len(outcomes))
        cells[key] = Cell(
            model=key[0],
            context_length_tokens=key[1],
            position_percent=key[2],
            correct=sum(outcomes),
            trials=len(outcomes),
            point=point,
            low=low,
            high=high,
        )
    return cells


def largest_drop_cell(
    cells: dict[tuple[str, int, int], Cell], model: str
) -> tuple[int, int] | None:
    """The cell with the largest accuracy drop from the 0% position at the same length.

    This is the documented highlight rule for the heatmap (section 6.6). Returns None when no
    cell is below its baseline, so the chart says nothing was highlighted.
    """
    drops: list[tuple[float, int, int]] = []
    for (label, length, position), cell in cells.items():
        if label != model or position == BASELINE_POSITION:
            continue
        baseline = cells.get((model, length, BASELINE_POSITION))
        if baseline is None:
            continue
        drop = baseline.point - cell.point
        if drop > 0:
            drops.append((drop, length, position))
    if not drops:
        return None
    # Largest drop first; ties settled by the longer context, then the earlier position.
    drop, length, position = max(drops, key=lambda item: (item[0], item[1], -item[2]))
    return length, position


def deepest_dip_model(cells: dict[tuple[str, int, int], Cell], length: int) -> str | None:
    """The model with the deepest accuracy dip between the 25% and 75% positions.

    The documented highlight rule for the position curve (section 6.6). The dip is measured
    from the better of the two edge positions down to the worst middle position.
    """
    dips: list[tuple[float, str]] = []
    for model in {label for label, _, _ in cells}:
        middle = [
            cells[(model, length, position)].point
            for position in DIP_POSITIONS
            if (model, length, position) in cells
        ]
        edges = [
            cells[(model, length, position)].point
            for position in EDGE_POSITIONS
            if (model, length, position) in cells
        ]
        if not middle or not edges:
            continue
        dip = max(edges) - min(middle)
        if dip > 0:
            dips.append((dip, model))
    if not dips:
        return None
    return max(dips, key=lambda item: (item[0], item[1]))[1]


def _reasoning_levels(config: ExperimentConfig) -> dict[str, str]:
    """The reasoning level each model ran with, so no reader has to open the config."""
    return {model.display_label: str(model.modes["standard"].reasoning) for model in config.models}


def _write_summary(
    path: Path, records: Sequence[RunRecord], facts: Sequence, config: ExperimentConfig
) -> int:
    levels = _reasoning_levels(config)
    rows = []
    for record in sorted(
        _successful(records),
        key=lambda r: (
            r.model_label,
            int(r.cell["context_length_tokens"]),
            int(r.cell["position_percent"]),
            int(r.cell["fact_index"]),
        ),
    ):
        result = record.result
        rows.append(
            {
                "model": record.model_label,
                "provider": result.provider,
                "model_returned": result.model_returned,
                "mode": record.mode,
                "reasoning": levels.get(record.model_label, ""),
                "context_length_tokens": record.cell["context_length_tokens"],
                "position_percent": record.cell["position_percent"],
                "fact_index": record.cell["fact_index"],
                "correct": score(record, facts),
                "input_tokens": result.input_tokens,
                "cached_input_tokens": result.cached_input_tokens,
                "output_tokens": result.output_tokens,
                "reasoning_tokens": result.reasoning_tokens,
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


def _draw_heatmap(
    cells: dict[tuple[str, int, int], Cell],
    model: str,
    lengths: Sequence[int],
    positions: Sequence[int],
    highlight_cell: tuple[int, int] | None,
):
    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        values = [
            [cells[(model, length, position)].point for position in positions] for length in lengths
        ]
        cell_index = None
        if highlight_cell is not None:
            cell_index = (lengths.index(highlight_cell[0]), positions.index(highlight_cell[1]))
        heatmap(
            ax,
            values,
            row_labels=[f"{length:,}" for length in lengths],
            col_labels=[f"{position}%" for position in positions],
            style=style,
            highlight_cell=cell_index,
        )
        ax.set_xlabel("Fact position in document")
        ax.set_ylabel("Context length (tokens)")

    return draw


def _label_anchors(
    series: Sequence[tuple[str, Sequence[float]]], positions: Sequence[int]
) -> dict[str, tuple[int, float]]:
    """Where to put each line's direct label: at its lowest point, where lines separate.

    Every model scores near 100% at the edges of the document, so labels placed at the last
    point would sit on top of each other. Labels sit below their line, and when two lines dip to
    nearly the same accuracy the lower label moves further down. Moving down rather than up
    matters when every line is at 100%: labels pushed upwards would leave the chart, and a
    reader would see one named line where there are three.
    """
    anchors = [
        [index, model, positions[list(points).index(min(points))], min(points)]
        for index, (model, points) in enumerate(series)
    ]
    anchors.sort(key=lambda anchor: (-anchor[3], anchor[0]))
    for earlier, later in zip(anchors, anchors[1:], strict=False):
        if earlier[3] - later[3] < LABEL_GAP:
            later[3] = earlier[3] - LABEL_GAP
    return {model: (x, y) for _, model, x, y in anchors}


def _draw_position_curve(
    cells: dict[tuple[str, int, int], Cell],
    models: Sequence[str],
    positions: Sequence[int],
    length: int,
    dip_model: str | None,
):
    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        series = [
            (model, [cells[(model, length, position)].point for position in positions])
            for model in models
        ]
        anchors = _label_anchors(series, positions)
        for index, (model, points) in enumerate(series):
            (line,) = ax.plot(
                positions,
                points,
                linestyle=LINE_STYLES[index % len(LINE_STYLES)],
                color=MIST if index == 0 else SLATE,
                linewidth=style.line_width_pt,
                marker="o",
                markersize=style.line_width_pt * 2,
            )
            if model == dip_model:
                highlight(line)
            # Direct labels rather than a legend, so colour never carries meaning alone. Each
            # label sits below its line's lowest point, which is clear space: the curve rises
            # on both sides of the dip.
            anchor_x, anchor_y = anchors[model]
            edge = anchor_x <= positions[0]
            ax.annotate(
                model,
                (anchor_x, anchor_y),
                textcoords="offset points",
                xytext=(10 if edge else 0, -LABEL_OFFSET_POINTS),
                ha="left" if edge else "center",
                va="top",
                color=MIST,
                # Navy backing, so a line crossing behind a label never cuts through the text.
                bbox={"facecolor": NAVY, "edgecolor": "none", "pad": 3},
            )
        ax.set_xticks(list(positions), labels=[f"{position}%" for position in positions])
        ax.set_ylim(-0.16, 1.08)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"])
        ax.set_xlabel("Fact position in document")
        ax.set_ylabel("Accuracy")
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return draw


def _slug(text: str) -> str:
    kept = [character.lower() if character.isalnum() else "-" for character in text]
    return "-".join(part for part in "".join(kept).split("-") if part)


def complete_grid(
    cells: dict[tuple[str, int, int], Cell],
    model: str,
    lengths: Sequence[int],
    positions: Sequence[int],
) -> bool:
    """Whether the model has a result in every length and position cell."""
    return all((model, length, position) in cells for length in lengths for position in positions)


def _grid_lines(cells: dict[tuple[str, int, int], Cell], models: Sequence[str]) -> list[str]:
    lengths = sorted({length for _, length, _ in cells})
    positions = sorted({position for _, _, position in cells})
    partial = [
        model
        for model in models
        if any(label == model for label, _, _ in cells)
        and not complete_grid(cells, model, lengths, positions)
    ]
    if not partial:
        return []
    return [
        f"Heatmaps not drawn for {', '.join(partial)}: the results do not cover every length and "
        "position yet, as in a pilot. They are drawn once the grid is complete."
    ]


def _charts(
    cells: dict[tuple[str, int, int], Cell],
    config: ExperimentConfig,
    out_dir: Path,
    facts_per_cell: int,
) -> list[Path]:
    models = [model.display_label for model in config.models]
    lengths = sorted({length for _, length, _ in cells})
    positions = sorted({position for _, _, position in cells})
    written: list[Path] = []

    for model in models:
        # A heatmap needs every cell. A pilot or a partial run has gaps, and a blank drawn as
        # 0% would read as a model failing every fact, so the heatmap is left out and the report
        # says why.
        if not complete_grid(cells, model, lengths, positions):
            continue
        drop = largest_drop_cell(cells, model)
        note = None
        if drop is None:
            note = "No cell scored below the 0% position; nothing highlighted."
        written += export_chart(
            _draw_heatmap(cells, model, lengths, positions, drop),
            out_dir,
            ChartSpec(
                name=f"{HEATMAP_NAME}-{_slug(model)}",
                units="Accuracy (%)",
                sample_size=f"n = {facts_per_cell} per cell",
                no_highlight_note=note,
            ),
        )

    if CURVE_LENGTH_TOKENS in lengths:
        drawable = [
            model
            for model in models
            if all((model, CURVE_LENGTH_TOKENS, position) in cells for position in positions)
        ]
        if drawable:
            dip_model = deepest_dip_model(cells, CURVE_LENGTH_TOKENS)
            note = None
            if dip_model is None:
                note = "No model dipped in the middle, so nothing is highlighted."
            written += export_chart(
                _draw_position_curve(cells, drawable, positions, CURVE_LENGTH_TOKENS, dip_model),
                out_dir,
                ChartSpec(
                    name=f"{CURVE_NAME}-{CURVE_LENGTH_TOKENS}",
                    units="Accuracy (%)",
                    sample_size=(
                        f"n = {facts_per_cell} per point, at {CURVE_LENGTH_TOKENS:,} tokens"
                    ),
                    no_highlight_note=note,
                ),
                layouts=(SLIDE, ARTICLE),
            )
    return written


def _accuracy_lines(cells: dict[tuple[str, int, int], Cell], models: Sequence[str]) -> list[str]:
    lengths = sorted({length for _, length, _ in cells})
    positions = sorted({position for _, _, position in cells})
    lines = ["Accuracy by model, context length, and fact position, with Wilson 95% intervals:"]
    for model in models:
        if not any(label == model for label, _, _ in cells):
            continue
        lines.append("")
        lines.append(f"  {model}")
        width = COLUMN_WIDTH
        lines.append(
            "    context   " + "".join(f"{f'{position}%':>{width}}" for position in positions)
        )
        for length in lengths:
            row = [f"    {length:>7,}   "]
            interval = [f"    {'':>7}   "]
            for position in positions:
                cell = cells.get((model, length, position))
                row.append(f"{'-' if cell is None else f'{cell.point:.0%}':>{width}}")
                interval.append(
                    f"{'-' if cell is None else f'{cell.low:.0%}-{cell.high:.0%}':>{width}}"
                )
            lines.append("".join(row))
            lines.append("".join(interval))
    return lines


def _finish_reason_lines(records: Sequence[RunRecord]) -> list[str]:
    truncated = [
        record
        for record in _successful(records)
        if record.result is not None and record.result.finish_reason == "length"
    ]
    if not truncated:
        return ["No response hit its output limit, so no answer was cut short."]
    lines = [
        f"{len(truncated)} response(s) hit the output limit and are scored incorrect. "
        "Raise max_output_tokens for that model and rerun those calls before drawing any "
        "conclusion:"
    ]
    for record in truncated[:10]:
        lines.append(
            f"  {record.model_label} at {record.cell['context_length_tokens']:,} tokens, "
            f"position {record.cell['position_percent']}%, fact {record.cell['fact_index']}"
        )
    return lines


def _reasoning_lines(records: Sequence[RunRecord], config: ExperimentConfig) -> list[str]:
    """Whether any model produced reasoning tokens, which matters for Gemini at `minimal`.

    A provider that leaves the reasoning count out is not the same as one reporting zero, so
    each model is described separately. Output tokens include any reasoning, so a model that
    reports nothing but used only a handful of output tokens per call cannot have reasoned.
    """
    levels = _reasoning_levels(config)
    by_model: dict[str, list] = {}
    for record in _successful(records):
        if record.result is not None:
            by_model.setdefault(record.model_label, []).append(record.result)

    lines = ["Reasoning, per model:"]
    for model, results in sorted(by_model.items()):
        level = levels.get(model, "unknown")
        reported = [r.reasoning_tokens for r in results if r.reasoning_tokens is not None]
        largest_output = max(r.output_tokens for r in results)
        if sum(reported) > 0:
            lines.append(
                f"  {model} (level {level}): {sum(reported):,} reasoning tokens, so reasoning "
                "was not fully off"
            )
        elif reported:
            lines.append(f"  {model} (level {level}): 0 reasoning tokens on every call")
        else:
            lines.append(
                f"  {model} (level {level}): reasoning not reported; at most "
                f"{largest_output:,} output tokens on any call, which includes any reasoning"
            )
    return lines


def _token_lines(records: Sequence[RunRecord]) -> list[str]:
    cached: dict[str, int] = {}
    inputs: dict[str, int] = {}
    for record in _successful(records):
        if record.result is None:
            continue
        inputs[record.model_label] = inputs.get(record.model_label, 0) + record.result.input_tokens
        cached[record.model_label] = cached.get(record.model_label, 0) + (
            record.result.cached_input_tokens or 0
        )
    lines = [
        "Input tokens, and how many the provider served from its own prompt cache. Automatic "
        "caching cannot be switched off and does not affect accuracy, so token and latency "
        "figures here are not a clean measure of cost:"
    ]
    for model in sorted(inputs):
        share = 100 * cached[model] / inputs[model] if inputs[model] else 0.0
        lines.append(
            f"  {model}: {inputs[model]:,} input tokens, {cached[model]:,} cached ({share:.0f}%)"
        )
    return lines


def _failure_lines(records: Sequence[RunRecord]) -> list[str]:
    """How many distinct calls failed. A call retried twice is one failed call, not two."""
    succeeded = {record.call_id for record in _successful(records)}
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
    facts = _facts(config)
    successful = _successful(records)
    if not successful:
        raise AnalysisError(
            "These results contain no successful calls, so there is nothing to score."
        )

    # Written beside the records they came from, so analysing a fresh run leaves the
    # published results/ folder untouched.
    results_folder = out_dir if out_dir is not None else folder / "results"
    rows = _write_summary(results_folder / "summary.csv", records, facts, config)
    cells = accuracy_by_cell(records, facts)
    charts = _charts(
        cells, config, results_folder / "charts", int(config.parameters["facts_per_cell"])
    )

    models = [model.display_label for model in config.models]
    lines = [
        f"{config.experiment}: {rows} scored call(s) across "
        f"{len({label for label, _, _ in cells})} model(s).",
        "",
        *_accuracy_lines(cells, models),
        "",
        *_finish_reason_lines(records),
        "",
        *_reasoning_lines(records, config),
        "",
        *_token_lines(records),
    ]
    grid = _grid_lines(cells, models)
    if grid:
        lines += ["", *grid]
    failures = _failure_lines(records)
    if failures:
        lines += ["", *failures]
    lines += [
        "",
        f"Written: {results_folder / 'summary.csv'}",
        f"Charts:  {len(charts)} file(s) in {results_folder / 'charts'}",
    ]
    return "\n".join(lines)
