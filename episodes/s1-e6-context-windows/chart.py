"""Draws the S1 E6 chart from results/edge.json, so it needs no API key.

Run from the repository root:

    uv run python episodes/s1-e6-context-windows/chart.py

french-replies: how many of the replies to the final English question came back in French, out
of the runs made, for each way of trimming the conversation. The acid green bar is the strategy
with fewer French replies, the one that lost the instruction; if the two are equal, nothing is
highlighted and the chart says so. A bar with no replies has no height to colour, so its label
is the acid green element instead.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from lab.charts import WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars, highlight

HERE = Path(__file__).parent
RESULTS = HERE / "results" / "edge.json"
OUT_DIR = HERE / "charts"
CHART = "french-replies"
STRATEGIES = ("naive", "pinned")
LABELS = {
    "naive": "Naive\n(oldest dropped first)",
    "pinned": "Pinned\n(instruction kept)",
}
# Room above the tallest bar for its value label.
HEADROOM = 1.15


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def french_counts(results: dict) -> list[int]:
    strategies = results["truncated"]["strategies"]
    return [strategies[name]["french_replies"] for name in STRATEGIES]


def fewer_french(counts: list[int]) -> int | None:
    """Highlight rule: the index of the strategy with fewer French replies, or None if equal."""
    naive, pinned = counts
    if naive == pinned:
        return None
    return 0 if naive < pinned else 1


def draw_french(results: dict):
    counts = french_counts(results)
    runs = results["truncated"]["runs_per_strategy"]
    finding = fewer_french(counts)
    # A bar of zero height has nothing to colour, so a strategy that got no French replies at all
    # is marked by its label instead. Either way there is exactly one acid green element.
    mark_bar = finding is not None and counts[finding] > 0

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        # The bars are counts out of the runs made, not shares, so the axis is whole numbers.
        grouped_bars(
            ax,
            categories=[LABELS[name] for name in STRATEGIES],
            series=[("Replies in French", counts)],
            style=style,
            highlight_bar=(0, finding) if mark_bar else None,
            value_formatter=FuncFormatter(lambda value, _: f"{value:g}"),
        )
        for position, count in enumerate(counts):
            label = ax.text(
                position,
                count,
                f"{count} of {runs}",
                ha="center",
                va="bottom",
                color=WHITE,
            )
            if position == finding and not mark_bar:
                highlight(label)
        ax.set_ylim(0, runs * HEADROOM)
        ax.set_yticks(range(runs + 1))
        ax.set_ylabel(f"Replies in French, out of {runs}")

    return draw


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    truncated = results["truncated"]
    counts = french_counts(results)
    return export_chart(
        draw_french(results),
        out_dir,
        ChartSpec(
            name=CHART,
            units="Replies in French",
            sample_size=f"{truncated['runs_per_strategy']} runs each",
            footnote=(
                f"Model: {results['model_returned']}.\n"
                f"Budget: {truncated['budget_tokens']:,} tokens, counted with o200k_base."
            ),
            no_highlight_note=(
                None
                if fewer_french(counts) is not None
                else "Both strategies scored the same; nothing highlighted."
            ),
        ),
    )


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
