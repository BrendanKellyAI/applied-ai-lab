"""Draws the S2 E4 charts from results/results.json alone: no API key, no model, no network.

Run from the repository root:

    uv run python field-notes/s2-e4-embedding-migration/chart.py

recall-by-model: recall at 5 by question type and for all 120, old model beside new. The acid
green bar is the better model's all-120 bar, only if the two all-120 intervals do not overlap.

top5-overlap: how many of the same articles each question's two top 5s share, for the swap
(old against new) and the control (two passes of the old model). The acid green element is the
swap's mean line, only if claim 1's overlap condition holds.

mixing: recall at 5 when vectors from two models meet, against the random floor. The acid green
bar is the half-migrated index with new queries, answers in the old half, only if claim 2c holds.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
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
measure = load_sibling(HERE / "measure.py")

RESULTS = HERE / "results" / "results.json"
OUT_DIR = HERE / "results" / "charts"
GROUPS = ("identifier", "paraphrase", "shared", "all")
MODELS = {"old": "Old: 3-small", "new": "New: 3-large"}
MIXING = (
    ("Old on old", "recall", "old"),
    ("Cross (2a)", "recall", "cross"),
    ("Half, new q: migrated", "half_new_queries", "migrated"),
    ("Half, new q: old half", "half_new_queries", "old"),
    ("Half, old q: migrated", "half_old_queries", "migrated"),
    ("Half, old q: old half", "half_old_queries", "old"),
)
MIXING_FINDING = 3
BAR_WIDTH = 0.6


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def label(entry: dict) -> str:
    return f"{entry['hits']} of {entry['n']}"


def recall_winner(results: dict) -> int | None:
    """Index of the model whose all-120 interval sits clear above the other's, else None."""
    old, new = (results["recall"][m]["all"] for m in MODELS)
    if old["low"] > new["high"]:
        return 0
    if new["low"] > old["high"]:
        return 1
    return None


def overlap_holds(results: dict) -> bool:
    return results["swap"]["mean_overlap"] <= results["pass_marks"]["claim1_max_mean_overlap"]


def mixing_entries(results: dict) -> list[dict]:
    splits = results["half_migrated"]["splits"]
    return [
        results["recall"][key]["all"] if source == "recall" else splits[source][key]["all"]
        for _, source, key in MIXING
    ]


def _mark(
    ax: Axes, style: ChartStyle, x: float, width: float, entry: dict, rotation: int = 0
) -> Line2D | None:
    """The count above each bar, and a stub on the baseline when the bar is zero. Returns the
    stub, so a zero bar that carries the finding can be highlighted through it."""
    ax.text(
        x,
        entry["high"] + 0.02,
        label(entry),
        ha="center",
        va="bottom",
        color=WHITE,
        rotation=rotation,
    )
    if entry["hits"] > 0:
        return None
    # A zero bar draws nothing, and a reader would take a missing bar for missing data.
    (stub,) = ax.plot(
        [x - width / 2, x + width / 2],
        [0, 0],
        color=WHITE,
        linewidth=style.line_width_pt * 1.5,
        solid_capstyle="butt",
        clip_on=False,
    )
    return stub


def _errors(ax: Axes, style: ChartStyle, xs, entries) -> None:
    ax.errorbar(
        xs,
        [e["rate"] for e in entries],
        # Clamped at zero: at 0% or 100% rounding can leave an interval a hair inside the rate.
        yerr=[
            [max(0.0, e["rate"] - e["low"]) for e in entries],
            [max(0.0, e["high"] - e["rate"]) for e in entries],
        ],
        fmt="none",
        ecolor=WHITE,
        elinewidth=style.line_width_pt / 2,
        capsize=5,
    )


def _plain_axes(ax: Axes) -> None:
    ax.grid(axis="y", alpha=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def draw_recall(results: dict):
    cells = {m: results["recall"][m] for m in MODELS}
    winner = recall_winner(results)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[measure.TYPE_LABELS[g] for g in GROUPS],
            series=[(name, [cells[m][g]["rate"] for g in GROUPS]) for m, name in MODELS.items()],
            style=style,
            highlight_bar=None if winner is None else (winner, GROUPS.index("all")),
        )
        width = 0.8 / len(MODELS)
        for index, model in enumerate(MODELS):
            xs = [p - 0.4 + width * (index + 0.5) for p in range(len(GROUPS))]
            entries = [cells[model][g] for g in GROUPS]
            _errors(ax, style, xs, entries)
            for x, entry in zip(xs, entries, strict=True):
                _mark(ax, style, x, width, entry, rotation=90)
        ax.set_ylabel("Recall at 5")
        ax.set_ylim(0, 1.6)
        ax.set_yticks([tick / 5 for tick in range(6)])

    return draw


def draw_overlap(results: dict):
    k = results["top_k"]
    total = results["questions"]
    swap, control = results["swap"], results["control"]
    finding = overlap_holds(results)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[str(n) for n in range(k + 1)],
            series=[
                ("Swap: old vs new", [c / total for c in swap["distribution"]]),
                ("Control: old vs old", [c / total for c in control["distribution"]]),
            ],
            style=style,
        )
        for name, data, y, colour, dash in (
            ("Swap", swap, 0.95, WHITE, "--"),
            ("Control", control, 0.8, MIST, ":"),
        ):
            line = ax.axvline(
                data["mean_overlap"], color=colour, linestyle=dash, linewidth=style.line_width_pt
            )
            if name == "Swap" and finding:
                highlight(line)
            ax.text(
                data["mean_overlap"] - 0.08,
                y,
                f"{name} mean {data['mean_overlap']:.2f}",
                ha="right",
                va="top",
                color=WHITE,
            )
        ax.set_xlabel("Articles shared by the two top 5s")
        ax.set_ylabel("Share of questions")
        ax.set_ylim(0, 1.05)

    return draw


def draw_mixing(results: dict):
    entries = mixing_entries(results)
    floor = results["random_floor"]
    finding = results["verdicts"]["claim2c"]["verdict"] == "held"

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        xs = list(range(len(entries)))
        bars = ax.bar(xs, [e["rate"] for e in entries], width=BAR_WIDTH, color=SLATE)
        _errors(ax, style, xs, entries)
        stubs = [
            _mark(ax, style, x, BAR_WIDTH, entry, rotation=90)
            for x, entry in zip(xs, entries, strict=True)
        ]
        if finding:
            # A zero bar has no face to colour, so its stub carries the highlight instead.
            highlight(stubs[MIXING_FINDING] or bars.patches[MIXING_FINDING])
        floor_line = ax.axhline(
            floor["rate"], color=MIST, linestyle="--", linewidth=style.line_width_pt / 2
        )
        ax.legend(
            handles=[floor_line],
            loc="upper right",
            labels=[f"Random floor, {floor['hits']:.0f} of {floor['n']}"],
        )
        ax.set_xticks(xs, labels=[name for name, _, _ in MIXING], rotation=90)
        ax.set_ylabel("Recall at 5")
        ax.set_ylim(0, 1.45)
        ax.set_yticks([tick / 5 for tick in range(6)])
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        _plain_axes(ax)

    return draw


def _models(results: dict) -> str:
    return "text-embedding-3-small vs text-embedding-3-large"


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    sample = f"{results['questions']} questions, {results['articles']} articles"
    date = f"Run {results['run_date_utc']}."
    written = export_chart(
        draw_recall(results),
        out_dir,
        ChartSpec(
            name="recall-by-model",
            units="Recall at 5",
            sample_size=sample,
            footnote=f"{_models(results)} (3,072).\n{date} 95% Wilson intervals.",
            no_highlight_note=(
                None
                if recall_winner(results) is not None
                else "Intervals overlap; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_overlap(results),
        out_dir,
        ChartSpec(
            name="top5-overlap",
            units="Share of questions",
            sample_size=sample,
            footnote=f"Swap: {_models(results)} (3,072).\n{date} Control: two 3-small passes.",
            no_highlight_note=(
                None if overlap_holds(results) else "Swap mean above 3.5 of 5; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_mixing(results),
        out_dir,
        ChartSpec(
            name="mixing",
            units="Recall at 5",
            sample_size=sample,
            footnote=(
                f"3-small index; 3-large queries cut to 1,536. Half: 150 migrated.\n"
                f"{date} 95% Wilson intervals."
            ),
            no_highlight_note=(
                None
                if results["verdicts"]["claim2c"]["verdict"] == "held"
                else "Claim 2c failed; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
