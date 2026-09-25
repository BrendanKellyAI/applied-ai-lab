"""Draws the S2 E3 charts from results/search.json alone: no API key, no model, no network.

Run from the repository root:

    uv run python episodes/s2-e3-search/chart.py

recall-by-question-type: recall at 5 by question type and overall, one bar per method. The acid
green bar is the method with the highest recall across all questions; on a tie, nothing is.

lookalikes: identifier questions where a look-alike article ranked above the right one, one bar
per method. The acid green bar is the method with the most such errors, and only if its 95%
interval does not overlap any other method's; otherwise nothing is highlighted.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from lab.charts import SLATE, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars, highlight
from lab.experiments import load_sibling

HERE = Path(__file__).parent
# Loaded by path, not by name: another episode also has a measure module.
measure = load_sibling(HERE / "measure.py")

RESULTS = HERE / "results" / "search.json"
OUT_DIR = HERE / "charts"
RECALL_CHART = "recall-by-question-type"
LOOKALIKE_CHART = "lookalikes"
METHOD_LABELS = {"keyword": "Keyword", "vector": "Vector", "hybrid": "Hybrid"}
GROUP_LABELS = {"identifier": "Identifier", "paraphrase": "Paraphrase",
                "shared": "Shared words", "all": "All"}
GROUP_WIDTH = 0.8
BAR_WIDTH = 0.6


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recall_cells(results: dict) -> dict[str, dict[str, dict]]:
    """Recall at k by group, then by method."""
    table = measure.table(results)
    return {g: {m: table[g][m]["recall_k"] for m in measure.METHODS} for g in GROUP_LABELS}


def lookalike_cells(results: dict) -> dict[str, dict]:
    rows = measure.of_type(results, "identifier")
    return {m: measure.lookalike_errors(rows, m) for m in measure.METHODS}


def best_overall(cells: dict[str, dict]) -> int | None:
    """Highlight rule for the recall chart: the single top method across all questions."""
    rates = [cells["all"][m]["rate"] for m in measure.METHODS]
    top = max(rates)
    return rates.index(top) if rates.count(top) == 1 else None


def most_lookalike_errors(cells: dict[str, dict]) -> int | None:
    """Highlight rule for the look-alike chart: the method with the most errors, only if its
    interval clears every other method's."""
    entries = [cells[m] for m in measure.METHODS]
    top = max(range(len(entries)), key=lambda i: entries[i]["rate"])
    others = [e for i, e in enumerate(entries) if i != top]
    if any(e["rate"] == entries[top]["rate"] for e in others):
        return None
    return top if all(entries[top]["low"] > e["high"] for e in others) else None


def _mark(ax: Axes, style: ChartStyle, centre: float, width: float, entry: dict,
          rotation: int = 0) -> None:
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
        fmt="none", ecolor=WHITE, elinewidth=style.line_width_pt / 2, capsize=5,
    )


def draw_recall(results: dict):
    cells = recall_cells(results)
    finding = best_overall(cells)
    groups = list(GROUP_LABELS)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[GROUP_LABELS[g] for g in groups],
            series=[(METHOD_LABELS[m], [cells[g][m]["rate"] for g in groups])
                    for m in measure.METHODS],
            style=style,
            highlight_bar=None if finding is None else (finding, groups.index("all")),
        )
        width = GROUP_WIDTH / len(measure.METHODS)
        for index, method in enumerate(measure.METHODS):
            centres = [p - GROUP_WIDTH / 2 + width * (index + 0.5) for p in range(len(groups))]
            entries = [cells[g][method] for g in groups]
            _errors(ax, style, centres, entries)
            for centre, entry in zip(centres, entries, strict=True):
                # Upright, because three counts side by side are wider than their bars.
                _mark(ax, style, centre, width, entry, rotation=90)
        ax.set_ylabel("Recall at 5")
        ax.set_ylim(0, 1.45)
        ax.set_yticks([tick / 5 for tick in range(6)])

    return draw


def draw_lookalikes(results: dict):
    cells = lookalike_cells(results)
    finding = most_lookalike_errors(cells)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        entries = [cells[m] for m in measure.METHODS]
        centres = list(range(len(entries)))
        bars = ax.bar(centres, [e["rate"] for e in entries], width=BAR_WIDTH, color=SLATE)
        if finding is not None:
            highlight(bars.patches[finding])
        _errors(ax, style, centres, entries)
        for centre, entry in zip(centres, entries, strict=True):
            _mark(ax, style, centre, BAR_WIDTH, entry)
        ax.set_xticks(centres, labels=[METHOD_LABELS[m] for m in measure.METHODS])
        ax.set_ylabel("Look-alike ranked above the answer")
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return draw


def _footnote(results: dict) -> str:
    return (
        f"{results['embedding_model_returned']}; BM25 splits codes on \\w+.\n"
        f"Run {results['run_date_utc']}. 95% Wilson intervals."
    )


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    total = len(results["questions"])
    identifiers = len(measure.of_type(results, "identifier"))
    recall_finding = best_overall(recall_cells(results))
    lookalike_finding = most_lookalike_errors(lookalike_cells(results))
    written = export_chart(
        draw_recall(results),
        out_dir,
        ChartSpec(
            name=RECALL_CHART,
            units="Recall at 5",
            sample_size=f"{total} questions, {total // 3} per type",
            footnote=_footnote(results),
            no_highlight_note=(
                None if recall_finding is not None
                else "Two methods tie overall; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_lookalikes(results),
        out_dir,
        ChartSpec(
            name=LOOKALIKE_CHART,
            units="Share of identifier questions",
            sample_size=f"{identifiers} identifier questions",
            footnote=_footnote(results),
            no_highlight_note=(
                None if lookalike_finding is not None
                else "No method stands clear; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
