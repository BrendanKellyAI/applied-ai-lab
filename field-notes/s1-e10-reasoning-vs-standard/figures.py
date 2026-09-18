"""Draws the four S1 E10 charts (specification section 7.6).

Kept apart from `analyse.py` so the statistics and the drawing can be read separately. Every
function here takes plain numbers, already aggregated, and returns the files it wrote.

The acid green element on each chart is chosen by the rule stated in that chart's docstring and
passed in by the analysis, never picked by hand. When nothing meets the rule, nothing is
highlighted and the chart says so in its footer.
"""

from collections.abc import Sequence
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from lab.charts import (
    MIST,
    SLATE,
    ChartSpec,
    ChartStyle,
    export_chart,
    grouped_bars,
    highlight,
)

# Marker shapes, so a model is never told apart by colour alone.
MARKERS = ("o", "s", "^")
POINT_COLOURS = (MIST, SLATE, MIST)
MILLISECONDS_PER_SECOND = 1000.0
# How far above its point each label sits. Wide enough to clear the marker itself.
LABEL_OFFSET_POINTS = 16
# Clear space kept around the plotted points, as a share of each axis range. The top gets more,
# because the highest point still needs room for its label.
AXIS_MARGIN = 0.1
TOP_MARGIN = 0.2

ACCURACY_BY_TASK = "accuracy-by-task"
TOKEN_MULTIPLE = "output-token-multiple-by-task"
COST_OF_ACCURACY = "cost-of-accuracy"
FIRST_TOKEN = "two-kinds-of-first-token"


def _tidy(ax: Axes) -> None:
    ax.grid(axis="y", alpha=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def accuracy_by_task(
    out_dir: Path,
    *,
    labels: Sequence[str],
    lowest: Sequence[float],
    high: Sequence[float],
    highlight_index: int | None,
    sample_size: str,
    footnote: str,
    no_highlight_note: str | None,
) -> list[Path]:
    """Accuracy per task in both modes.

    Highlight rule: the high reasoning bar for the task with the largest accuracy gain whose
    paired 95% confidence interval excludes zero.
    """

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=list(labels),
            series=[("Lowest reasoning", list(lowest)), ("High reasoning", list(high))],
            style=style,
            highlight_bar=None if highlight_index is None else (1, highlight_index),
        )
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Accuracy")

    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name=ACCURACY_BY_TASK,
            units="Accuracy (%)",
            sample_size=sample_size,
            footnote=footnote,
            no_highlight_note=no_highlight_note,
        ),
    )


def token_multiple_by_task(
    out_dir: Path,
    *,
    labels: Sequence[str],
    multiples: Sequence[float],
    highlight_index: int | None,
    sample_size: str,
    footnote: str,
    no_highlight_note: str | None,
) -> list[Path]:
    """How many times more output tokens high reasoning billed than the lowest setting.

    Highlight rule: the task with the largest multiple, as long as it is above one.
    """

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=list(labels),
            series=[("High reasoning", list(multiples))],
            style=style,
            highlight_bar=None if highlight_index is None else (0, highlight_index),
            value_formatter=FuncFormatter(lambda value, _: f"{value:g}x"),
        )
        ax.axhline(1, color=SLATE, linewidth=style.line_width_pt / 2, linestyle=":")
        ax.set_ylabel("Output tokens, high ÷ lowest")

    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name=TOKEN_MULTIPLE,
            units="Output tokens, high over lowest",
            sample_size=sample_size,
            footnote=footnote,
            no_highlight_note=no_highlight_note,
        ),
    )


def cost_of_accuracy(
    out_dir: Path,
    *,
    points: Sequence[tuple[str, str, float, float]],
    models: Sequence[str],
    highlight_key: tuple[str, str] | None,
    sample_size: str,
    footnote: str,
    no_highlight_note: str | None,
) -> list[Path]:
    """Extra output tokens against accuracy gained, one point per model and task.

    Each point is `(model, task code, extra output tokens per item, accuracy change in
    percentage points)`. Highlight rule: among points that gained accuracy, the one that gained
    the most accuracy per 1,000 extra output tokens.
    """

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        xs = [extra for _, _, extra, _ in points]
        ys = [change for _, _, _, change in points]
        span = (max(xs) - min(xs)) or 1.0
        reach = (max(ys) - min(ys)) or 1.0
        for model, task, extra, change in points:
            index = models.index(model)
            (marker,) = ax.plot(
                [extra],
                [change],
                marker=MARKERS[index % len(MARKERS)],
                markersize=style.line_width_pt * 2.5,
                linestyle="none",
                color=POINT_COLOURS[index % len(POINT_COLOURS)],
                markeredgecolor=SLATE,
            )
            if highlight_key == (model, task):
                highlight(marker)
            # Two-letter codes, centred directly above their own point, never nudged. Moving a
            # label to avoid a neighbour would either stretch the axis or separate the label
            # from the point it names, and both mislead. The key is in the chart's footnote.
            ax.annotate(
                task,
                (extra, change),
                textcoords="offset points",
                xytext=(0, LABEL_OFFSET_POINTS),
                ha="center",
                va="bottom",
                color=MIST,
            )
        ax.axhline(0, color=SLATE, linewidth=style.line_width_pt / 2, linestyle=":")
        ax.set_xlim(min(xs) - AXIS_MARGIN * span, max(xs) + AXIS_MARGIN * span)
        ax.set_ylim(min(ys) - AXIS_MARGIN * reach, max(ys) + TOP_MARGIN * reach)
        ax.set_xlabel("Extra output tokens per item")
        ax.set_ylabel("Accuracy change (points)")
        ax.legend(
            handles=[
                Line2D(
                    [],
                    [],
                    marker=MARKERS[index % len(MARKERS)],
                    color=POINT_COLOURS[index % len(POINT_COLOURS)],
                    markeredgecolor=SLATE,
                    linestyle="none",
                    markersize=style.line_width_pt * 2.5,
                    label=model,
                )
                for index, model in enumerate(models)
            ],
            loc="lower left",
            bbox_to_anchor=(0, 1.02),
            ncols=2,
            columnspacing=1.0,
            handletextpad=0.4,
        )
        _tidy(ax)

    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name=COST_OF_ACCURACY,
            units="Accuracy points vs extra tokens",
            sample_size=sample_size,
            footnote=footnote,
            no_highlight_note=no_highlight_note,
        ),
    )


def two_kinds_of_first_token(
    out_dir: Path,
    *,
    rows: Sequence[tuple[str, float | None, float]],
    highlight_index: int | None,
    sample_size: str,
    footnote: str,
    no_highlight_note: str | None,
) -> list[Path]:
    """Where a user sees thinking before any answer text arrives.

    Each row is `(label, median milliseconds to first thinking or None, median milliseconds to
    the first answer token)`. Highlight rule: the row with the longest stretch between the two,
    which is where a user waits longest with thinking on screen and no answer.
    """

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        for index, (_, thinking, answer) in enumerate(rows):
            height = len(rows) - index
            answer_seconds = answer / MILLISECONDS_PER_SECOND
            # A thinking median at or after the answer median is not a wait a user experiences,
            # so no span is drawn for it. The marker still shows when thinking was reported.
            if thinking is not None and thinking < answer:
                thinking_seconds = thinking / MILLISECONDS_PER_SECOND
                (connector,) = ax.plot(
                    [thinking_seconds, answer_seconds],
                    [height, height],
                    color=SLATE,
                    linewidth=style.line_width_pt,
                    solid_capstyle="butt",
                )
                if highlight_index == index:
                    highlight(connector)
            if thinking is not None:
                ax.plot(
                    [thinking / MILLISECONDS_PER_SECOND],
                    [height],
                    marker=MARKERS[0],
                    markersize=style.line_width_pt * 2.5,
                    linestyle="none",
                    color=MIST,
                )
            ax.plot(
                [answer_seconds],
                [height],
                marker=MARKERS[1],
                markersize=style.line_width_pt * 2.5,
                linestyle="none",
                color=SLATE,
                markeredgecolor=MIST,
            )
        ax.set_yticks(
            [len(rows) - index for index in range(len(rows))],
            labels=[label for label, _, _ in rows],
        )
        ax.set_ylim(0.4, len(rows) + 0.8)
        ax.set_xlim(left=0)
        ax.set_xlabel("Seconds from request")
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.legend(
            handles=[
                Line2D(
                    [],
                    [],
                    marker=MARKERS[0],
                    color=MIST,
                    linestyle="none",
                    markersize=style.line_width_pt * 2.5,
                    label="First thinking",
                ),
                Line2D(
                    [],
                    [],
                    marker=MARKERS[1],
                    color=SLATE,
                    markeredgecolor=MIST,
                    linestyle="none",
                    markersize=style.line_width_pt * 2.5,
                    label="First answer",
                ),
            ],
            loc="lower left",
            bbox_to_anchor=(0, 1.02),
            ncols=2,
            columnspacing=1.0,
            handletextpad=0.4,
        )

    return export_chart(
        draw,
        out_dir,
        ChartSpec(
            name=FIRST_TOKEN,
            units="Median seconds from request",
            sample_size=sample_size,
            footnote=footnote,
            no_highlight_note=no_highlight_note,
        ),
    )
