"""Slide charts for the case: the scorecard as a heat table, and the sensitivity check.

The heat table puts candidates across and the rule's parts down, so it reads on a portrait
slide. Cells not yet introduced, or not scored because a gate failed, are left dark.
"""

from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

from lab.charts import (
    NAVY,
    ChartSpec,
    ChartStyle,
    export_chart,
    grouped_bars,
    highlight,
    sequential_colormap,
)
from lab.strategy.rule import Rule
from lab.strategy.scoring import Sensitivity

SHORT_CRITERIA = {
    "value": "Value",
    "task_fit": "Task fit",
    "error_tolerance": "Errors",
    "data_readiness": "Data",
    "durable_advantage": "Moat",
    "time_to_evidence": "Time",
}
AUTONOMY_SHORT = {"assist": "Assist", "automate": "Auto", "act": "Act"}
SOURCING_SHORT = {"build": "Build", "buy": "Buy", "none": "None"}


def _cell(row: dict[str, Any], part: str) -> tuple[float | None, str]:
    """A cell's shade (0 to 1, None for dark) and its text."""
    kind, _, name = part.partition(":")
    if kind == "gate":
        value = row[f"gate_{name}"]
        return (None, "") if not value else (1.0 if value == "pass" else 0.0, value.title())
    if kind == "criterion":
        value = row[name]
        return (None, "") if value == "" else ((int(value) - 1) / 4, str(value))
    if kind == "autonomy":
        design = row["design_autonomy"]
        if not design:
            return None, ""
        mark = "*" if row["autonomy_exceeded"] else ""
        return 0.5, AUTONOMY_SHORT[design] + mark
    if kind == "sourcing":
        value = row["application"]
        return (None, "") if not value else (0.5, SOURCING_SHORT.get(value, value.title()))
    total = row["total"]
    return (None, "") if total is None else ((total - 1) / 4, f"{total:.2f}")


def table_parts(rule: Rule, step: dict[str, Any]) -> list[tuple[str, str]]:
    """(part, label) for each row of the heat table, in the order the rule introduces them."""
    seen = step["columns"]
    parts: list[tuple[int, str, str]] = []
    for n, gate in enumerate(rule.gates, start=1):
        if seen[f"gate:{gate.id}"]:
            parts.append((gate.episode, f"gate:{gate.id}", f"G{n}"))
    for criterion in rule.criteria:
        if seen[f"criterion:{criterion.id}"]:
            parts.append(
                (
                    criterion.episode,
                    f"criterion:{criterion.id}",
                    SHORT_CRITERIA.get(criterion.id, criterion.label),
                )
            )
    if seen["autonomy"]:
        parts.append((rule.autonomy.episode, "autonomy:", "Autonomy"))
    if seen["sourcing"]:
        parts.append((rule.sourcing.episode, "sourcing:", "Sourcing"))
    out = [(p, label) for _, p, label in sorted(parts, key=lambda x: x[0])]
    if any(r["total"] is not None for r in step["rows"]):
        out.append(("total:", "Total"))
    return out


def draw_table(
    step: dict[str, Any], rule: Rule, *, highlight_label: str | None, highlight_pick: str | None
):
    rows = step["rows"]
    parts = table_parts(rule, step)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        shades = np.full((len(parts), len(rows)), np.nan)
        texts = [["" for _ in rows] for _ in parts]
        for i, (part, _) in enumerate(parts):
            for j, row in enumerate(rows):
                shade, text = _cell(row, part)
                shades[i, j] = np.nan if shade is None else shade
                texts[i][j] = text
        cmap = sequential_colormap().with_extremes(bad=NAVY)
        ax.imshow(np.ma.masked_invalid(shades), cmap=cmap, vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(rows)), labels=[r["id"] for r in rows])
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(parts)), labels=[label for _, label in parts])
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for i in range(len(parts)):
            for j in range(len(rows)):
                if texts[i][j]:
                    text = ax.text(j, i, texts[i][j], ha="center", va="center", color=NAVY)
                    if (
                        highlight_pick
                        and parts[i][0] == "total:"
                        and rows[j]["id"] == highlight_pick
                    ):
                        highlight(text)
        if highlight_label:
            for label in ax.get_yticklabels():
                if label.get_text() == highlight_label:
                    highlight(label)

    return draw


def export_table(
    step: dict[str, Any],
    rule: Rule,
    out_dir: Path,
    name: str,
    *,
    highlight_label: str | None = None,
    highlight_pick: str | None = None,
    footnote: str | None = None,
) -> list[Path]:
    spec = ChartSpec(
        name=name,
        units="Scores 1 to 5; gates pass or fail",
        sample_size=f"{len(step['rows'])} candidate use cases (invented)",
        footnote=footnote,
    )
    return export_chart(
        draw_table(step, rule, highlight_label=highlight_label, highlight_pick=highlight_pick),
        out_dir,
        spec,
    )


def export_sensitivity(result: Sensitivity, names: dict[str, str], out_dir: Path) -> list[Path]:
    ids = list(names)
    counts = [result.picks.get(i, 0) for i in ids]
    labels = [f"{i} {names[i]}" for i in ids]
    base_index = ids.index(result.base_pick) if result.base_pick in ids else None

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=labels,
            series=[("Weightings won", counts)],
            style=style,
            horizontal=True,
            value_formatter=StrMethodFormatter("{x:.0f}"),
            highlight_bar=(0, base_index) if base_index is not None else None,
        )
        ax.set_xlim(0, result.out_of)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    spec = ChartSpec(
        name="sensitivity",
        units="Weightings in which each candidate goes first",
        sample_size=f"{result.out_of} alternative weightings",
        footnote="Candidates that fail a gate cannot go first",
    )
    return export_chart(draw, out_dir, spec)
