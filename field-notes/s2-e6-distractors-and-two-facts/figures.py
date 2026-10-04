"""S2 E6 charts, drawn with `lab.charts` at slide and article size.

Each chart has one documented highlight rule. When nothing meets it, the chart says so in its
footer rather than colouring anything.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, PercentFormatter, ScalarFormatter

from lab.charts import (
    LINE_STYLES,
    MIST,
    NAVY,
    SERIES_COLOURS,
    WHITE,
    ChartSpec,
    ChartStyle,
    export_chart,
    grouped_bars,
    highlight,
)

SHORT_LABELS = {
    "single": "Single",
    "distractors": "Distractors",
    "two-fact": "Two-fact",
    "two-fact-distractors": "Two-fact +\ndistractors",
}
HARDEST = "two-fact-distractors"
LONGEST = 128000
SHORTEST = 16000


def _stack_legend(ax: Axes) -> None:
    """One legend entry per line above the plot: three model names side by side do not fit a
    slide."""
    legend = ax.get_legend()
    ax.legend(
        handles=legend.legend_handles,
        labels=[text.get_text() for text in legend.texts],
        loc="lower left",
        bbox_to_anchor=(0, 1.0),
        ncols=1,
    )


def _accuracy_axis(ax: Axes) -> None:
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))


# 1. Accuracy by shape at 128,000 ------------------------------------------------------------


def lowest_shape_clearing_single(cells) -> str | None:
    """The lowest pooled shape whose interval sits wholly below Single's, at 128,000."""
    single = cells.pooled("single", LONGEST)
    clearing = []
    for shape in SHORT_LABELS:
        pooled = cells.pooled(shape, LONGEST)
        if shape == "single" or pooled is None or single is None:
            continue
        if pooled.interval[2] < single.interval[1]:
            clearing.append((pooled.correct, list(SHORT_LABELS).index(shape), shape))
    return min(clearing)[2] if clearing else None


def shapes_chart(cells, out_dir: Path) -> list[Path]:
    shapes = list(SHORT_LABELS)
    chosen = lowest_shape_clearing_single(cells)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[SHORT_LABELS[shape] for shape in shapes],
            series=[
                (model, [cells.model(model, shape, LONGEST).interval[0] for shape in shapes])
                for model in cells.models
            ],
            style=style,
            horizontal=True,
        )
        _stack_legend(ax)
        for index, shape in enumerate(shapes):
            # Horizontal bars put the first shape at the top.
            (marker,) = ax.plot(
                [cells.pooled(shape, LONGEST).interval[0]],
                [len(shapes) - 1 - index],
                marker="D",
                markersize=style.label_pt * 0.8,
                markeredgecolor=NAVY,
                color=WHITE,
                linestyle="none",
            )
            if shape == chosen:
                highlight(marker)
        ax.set_xlim(0, 1.05)
        ax.set_xlabel("Accuracy at 128,000 tokens")

    note = None if chosen else "No shape's pooled interval clears Single; nothing highlighted."
    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name="shapes-128k",
            units="Accuracy (%)",
            sample_size=f"n = {cells.items} per bar, {cells.items * len(cells.models)} per diamond",
            footnote="Diamond: the three models pooled",
            no_highlight_note=note,
        ),
    )


# 2. The hardest shape at each length ---------------------------------------------------------


def largest_drop_model(cells, lengths: Sequence[int]) -> str | None:
    """The model whose shape 4 accuracy falls most from 16,000 to 128,000, if its two
    intervals do not overlap."""
    drops = []
    for model in cells.models:
        short = cells.model(model, HARDEST, SHORTEST)
        long = cells.model(model, HARDEST, LONGEST)
        drops.append((short.correct - long.correct, -cells.models.index(model), model))
    drop, _, model = max(drops)
    short = cells.model(model, HARDEST, SHORTEST)
    long = cells.model(model, HARDEST, LONGEST)
    if drop > 0 and long.interval[2] < short.interval[1]:
        return model
    return None


def length_chart(cells, lengths: Sequence[int], out_dir: Path) -> list[Path]:
    chosen = largest_drop_model(cells, lengths)
    xs = list(range(len(lengths)))

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        handles = []
        for index, model in enumerate(cells.models):
            colour = SERIES_COLOURS[index]
            values = [cells.model(model, HARDEST, length).interval[0] for length in lengths]
            (line,) = ax.plot(
                xs,
                values,
                linestyle=LINE_STYLES[index % len(LINE_STYLES)],
                color=colour,
                linewidth=style.line_width_pt,
                marker="o",
                markersize=style.line_width_pt * 2,
            )
            if model == chosen:
                highlight(line)
            # Fresh legend keys, so a highlighted line does not put acid green in the legend.
            handles.append(
                Line2D(
                    [],
                    [],
                    color=colour,
                    linestyle=LINE_STYLES[index % len(LINE_STYLES)],
                    linewidth=style.line_width_pt,
                    label=model,
                )
            )
        ax.set_xticks(xs, labels=[f"{length:,}" for length in lengths])
        ax.set_xlim(-0.2, len(lengths) - 0.8)
        _accuracy_axis(ax)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Context length (tokens)")
        ax.set_ylabel("Accuracy, hardest shape")
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=1)

    note = None
    if chosen is None:
        note = "No model's 16,000 and 128,000 intervals separate; nothing highlighted."
    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name="length-hardest",
            units="Accuracy (%)",
            sample_size=f"n = {cells.items} per point",
            no_highlight_note=note,
        ),
    )


# 3. Wrong replies by type ---------------------------------------------------------------------


def distractor_leads(wrong: Mapping[str, Mapping[str, int]]) -> str | None:
    """Shape 2 or 4, where a distractor value is the most common wrong reply.

    When both qualify, the shape with more distractor replies, shape 4 on a tie.
    """
    leading = []
    for order, shape in enumerate(("distractors", HARDEST)):
        counts = wrong[shape]
        top = counts["distractor value"]
        if top > 0 and all(top > n for kind, n in counts.items() if kind != "distractor value"):
            leading.append((top, order, shape))
    return max(leading)[2] if leading else None


def wrong_types_chart(
    wrong: Mapping[str, Mapping[str, int]], types: Sequence[str], out_dir: Path, calls: int
) -> list[Path]:
    shapes = list(SHORT_LABELS)
    chosen = distractor_leads(wrong)
    total = sum(sum(counts.values()) for counts in wrong.values())

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        formatter = ScalarFormatter()
        grouped_bars(
            ax,
            categories=[SHORT_LABELS[shape] for shape in shapes],
            series=[
                (kind.capitalize(), [wrong[shape][kind] for shape in shapes]) for kind in types
            ],
            style=style,
            highlight_bar=(0, shapes.index(chosen)) if chosen else None,
            value_formatter=formatter,
        )
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        top = max((wrong[shape][kind] for shape in shapes for kind in types), default=0)
        ax.set_ylim(0, max(top * 1.15, 4))
        ax.set_ylabel("Wrong replies")

    note = None
    if chosen is None:
        note = "Distractor value is not the top wrong type; nothing highlighted."
    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name="wrong-types",
            units="Wrong replies (count)",
            sample_size=f"{total} wrong of {calls} calls, {calls // len(shapes)} per shape",
            no_highlight_note=note,
        ),
    )


# 4. Models on the hardest shape at 128,000 ---------------------------------------------------


def lowest_model_clearing_highest(cells) -> str | None:
    """The lowest model on shape 4 at 128,000, if its interval sits below the highest's."""
    ranked = sorted(
        cells.models,
        key=lambda m: (cells.model(m, HARDEST, LONGEST).correct, cells.models.index(m)),
    )
    lowest = cells.model(ranked[0], HARDEST, LONGEST)
    highest = cells.model(ranked[-1], HARDEST, LONGEST)
    return ranked[0] if lowest.interval[2] < highest.interval[1] else None


def models_chart(cells, out_dir: Path) -> list[Path]:
    chosen = lowest_model_clearing_highest(cells)
    counts = [cells.model(model, HARDEST, LONGEST) for model in cells.models]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        points = [count.interval[0] for count in counts]
        grouped_bars(
            ax,
            categories=[model.replace(" ", "\n", 1) for model in cells.models],
            series=[("Two-fact + distractors at 128,000", points)],
            style=style,
        )
        # The finding is marked on the count above each interval, not on the bar: a model at
        # 0 of n has no bar to colour.
        for index, (model, count) in enumerate(zip(cells.models, counts, strict=True)):
            label = ax.text(
                index,
                count.interval[2] + 0.03,
                f"{count.correct} of {count.trials}",
                ha="center",
                va="bottom",
                color=MIST,
            )
            if model == chosen:
                highlight(label)
        ax.errorbar(
            range(len(counts)),
            points,
            yerr=[
                # Clamped at zero: at 0 of n the Wilson bound sits a rounding error above 0.
                [max(0.0, count.interval[0] - count.interval[1]) for count in counts],
                [max(0.0, count.interval[2] - count.interval[0]) for count in counts],
            ],
            fmt="none",
            ecolor=MIST,
            elinewidth=style.line_width_pt,
            capsize=style.label_pt * 0.6,
            capthick=style.line_width_pt,
        )
        _accuracy_axis(ax)
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Accuracy, hardest shape")

    note = None if chosen else "No model's interval clears another's; nothing highlighted."
    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name="models-hardest",
            units="Accuracy (%)",
            sample_size=f"n = {cells.items} per model",
            footnote="At 128,000 tokens, with Wilson 95% intervals",
            no_highlight_note=note,
        ),
    )
