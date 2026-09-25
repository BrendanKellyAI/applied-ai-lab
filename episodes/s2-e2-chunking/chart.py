"""Draws the S2 E2 charts from results/chunking.json alone: no API key, no model, no network.

Run from the repository root:

    uv run python episodes/s2-e2-chunking/chart.py

recall-by-size: recall at 5 for one-sentence facts, 0% overlap. The acid green bar is the size
with the highest recall; if two or more sizes tie at the top, nothing is highlighted.

similarity-by-size: median similarity between each question and the chunk holding its answer,
with the ceiling and the floor. Nothing is highlighted.

two-sentence-overlap: recall at 5 for two-sentence facts, 0% against 25% overlap. The acid green
bar is the 25% bar at the size where overlap adds the most recall, and only if its 95% interval
clears the 0% bar's; otherwise nothing is highlighted.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from lab.charts import (
    MIST,
    SLATE,
    WHITE,
    ChartSpec,
    ChartStyle,
    export_chart,
    grouped_bars,
    highlight,
)
from lab.experiments import load_sibling

HERE = Path(__file__).parent
# Loaded by path, not by name: another episode also has a measure module.
measure = load_sibling(HERE / "measure.py")

RESULTS = HERE / "results" / "chunking.json"
OUT_DIR = HERE / "charts"
RECALL_CHART = "recall-by-size"
SIMILARITY_CHART = "similarity-by-size"
OVERLAP_CHART = "two-sentence-overlap"
BAR_WIDTH = 0.6
HEADROOM = 1.18


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recalls(results: dict, kind: str, overlap: float) -> list[dict]:
    conditions = [measure.find(results, size, overlap) for size in results["chunk_sizes"]]
    return [measure.recall(measure.rows_for(c, kind), results["top_k"]) for c in conditions]


def best_bar(entries: list[dict]) -> int | None:
    """Highlight rule for recall-by-size: the single top bar, or None on a tie."""
    top = max(entry["rate"] for entry in entries)
    winners = [index for index, entry in enumerate(entries) if entry["rate"] == top]
    return winners[0] if len(winners) == 1 else None


def overlap_gain_bar(without: list[dict], with_overlap: list[dict]) -> int | None:
    """Highlight rule for two-sentence-overlap: the size where overlap adds most recall, only
    if the 25% bar's interval sits wholly above the 0% bar's. None otherwise, or on a tie."""
    gains = [b["rate"] - a["rate"] for a, b in zip(without, with_overlap, strict=True)]
    top = max(gains)
    winners = [index for index, gain in enumerate(gains) if gain == top]
    if top <= 0 or len(winners) > 1:
        return None
    index = winners[0]
    return index if with_overlap[index]["low"] > without[index]["high"] else None


def _labels(results: dict) -> list[str]:
    return [f"{size:,}" for size in results["chunk_sizes"]]


def _footnote(results: dict, facts: str) -> str:
    return (
        f"Model: {results['model_returned']}, tokeniser {results['tokeniser']}.\n"
        f"{facts}. Run {results['run_date_utc']}. 95% Wilson intervals."
    )


def _mark(
    ax: Axes, style: ChartStyle, centre: float, width: float, entry: dict, rotation: int = 0
) -> None:
    """The count above each bar, and a stub on the baseline when the bar is zero."""
    ax.text(centre, entry["high"] + 0.02, f"{entry['hits']}/{entry['n']}",
            ha="center", va="bottom", color=WHITE, rotation=rotation)
    if entry["hits"] == 0:
        # A zero bar draws nothing, and a reader would take a missing bar for missing data.
        ax.hlines(0, centre - width / 2, centre + width / 2, colors=WHITE,
                  linewidth=style.line_width_pt * 1.5)


def _errors(ax: Axes, style: ChartStyle, centres, entries) -> None:
    ax.errorbar(
        centres,
        [e["rate"] for e in entries],
        # Clamped at zero: at 0% or 100% rounding can leave an interval a hair inside the rate.
        yerr=[
            [max(0.0, e["rate"] - e["low"]) for e in entries],
            [max(0.0, e["high"] - e["rate"]) for e in entries],
        ],
        fmt="none", ecolor=WHITE, elinewidth=style.line_width_pt / 2, capsize=6,
    )


def draw_recall(results: dict):
    entries = recalls(results, "one", 0.0)
    finding = best_bar(entries)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        centres = list(range(len(entries)))
        bars = ax.bar(centres, [e["rate"] for e in entries], width=BAR_WIDTH, color=SLATE)
        if finding is not None:
            highlight(bars.patches[finding])
        _errors(ax, style, centres, entries)
        for centre, entry in zip(centres, entries, strict=True):
            _mark(ax, style, centre, BAR_WIDTH, entry)
        ax.set_xticks(centres, labels=_labels(results))
        ax.set_xlabel("Chunk size (tokens)")
        ax.set_ylabel("Recall at 5")
        ax.set_ylim(0, HEADROOM)
        ax.set_yticks([tick / 5 for tick in range(6)])
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return draw


def similarity_series(results: dict) -> dict[str, list[float]]:
    summaries = [
        measure.similarity_summary(measure.rows_for(measure.find(results, size, 0.0), "one"))
        for size in results["chunk_sizes"]
    ]
    return {key: [s[f"{key}_median"] for s in summaries] for key in ("answer", "ceiling", "floor")}


def draw_similarity(results: dict):
    series = similarity_series(results)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        xs = list(range(len(results["chunk_sizes"])))
        ceiling = series["ceiling"][0]
        ax.axhline(ceiling, color=MIST, linestyle="--", linewidth=style.line_width_pt / 2)
        ax.text(xs[-1], ceiling + 0.02, f"Ceiling: fact alone {ceiling:.2f}",
                ha="right", va="bottom", color=MIST)
        # The floor is measured at each size, so it is drawn at each size rather than as one
        # value: random chunks grow slightly closer to a question as they grow longer.
        ax.plot(xs, series["floor"], color=SLATE, linestyle=":", linewidth=style.line_width_pt / 2)
        ax.text(xs[0], series["floor"][0] - 0.03, "Floor: random chunks",
                ha="left", va="top", color=SLATE)
        ax.plot(xs, series["answer"], color=WHITE, marker="o", linewidth=style.line_width_pt)
        for x, value in zip(xs, series["answer"], strict=True):
            ax.text(x, value + 0.03, f"{value:.2f}", ha="center", va="bottom", color=WHITE)
        ax.set_xticks(xs, labels=_labels(results))
        ax.set_xlabel("Chunk size (tokens)")
        ax.set_ylabel("Median similarity to answer chunk")
        ax.set_ylim(0, 1)
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return draw


def draw_overlap(results: dict):
    without = recalls(results, "two", 0.0)
    with_overlap = recalls(results, "two", 0.25)
    finding = overlap_gain_bar(without, with_overlap)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=_labels(results),
            series=[("0% overlap", [e["rate"] for e in without]),
                    ("25% overlap", [e["rate"] for e in with_overlap])],
            style=style,
            highlight_bar=None if finding is None else (1, finding),
        )
        width = 0.4
        for series_index, entries in enumerate((without, with_overlap)):
            centres = [i - 0.4 + width * (series_index + 0.5) for i in range(len(entries))]
            _errors(ax, style, centres, entries)
            for centre, entry in zip(centres, entries, strict=True):
                # Upright, because two counts side by side are wider than their bars.
                _mark(ax, style, centre, width, entry, rotation=90)
        ax.set_xlabel("Chunk size (tokens)")
        ax.set_ylabel("Recall at 5")
        ax.set_ylim(0, 1.3)
        ax.set_yticks([tick / 5 for tick in range(6)])

    return draw


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    one, two = results["facts"]["one"], results["facts"]["two"]
    recall_finding = best_bar(recalls(results, "one", 0.0))
    overlap_finding = overlap_gain_bar(recalls(results, "two", 0.0), recalls(results, "two", 0.25))
    written = export_chart(
        draw_recall(results),
        out_dir,
        ChartSpec(
            name=RECALL_CHART,
            units="Recall at 5, 0% overlap",
            sample_size=f"{one} one-sentence facts per size",
            footnote=_footnote(results, f"{one} one-sentence facts"),
            no_highlight_note=(
                None if recall_finding is not None
                else "Two or more sizes tie at the top; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_similarity(results),
        out_dir,
        ChartSpec(
            name=SIMILARITY_CHART,
            units="Cosine similarity, medians, 0% overlap",
            sample_size=f"{one} one-sentence facts per size",
            footnote=(
                f"Model: {results['model_returned']}, tokeniser {results['tokeniser']}.\n"
                f"{one} one-sentence facts. Run {results['run_date_utc']}."
            ),
            no_highlight_note="A trend, not one finding; nothing highlighted.",
        ),
    )
    written += export_chart(
        draw_overlap(results),
        out_dir,
        ChartSpec(
            name=OVERLAP_CHART,
            units="Recall at 5",
            sample_size=f"{two} two-sentence facts per bar",
            footnote=_footnote(results, f"{two} two-sentence facts"),
            no_highlight_note=(
                None if overlap_finding is not None
                else "No overlap gain clears its interval; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
