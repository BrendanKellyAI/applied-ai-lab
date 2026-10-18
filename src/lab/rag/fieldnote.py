"""Shared pieces for the Season 3 field notes: arms, prices, evidence checks and charts.

Prices come from the local, gitignored `prices.local.yaml`. Only ratios computed from them are
committed; when the file is missing, an analysis keeps the ratios already in its committed
`analysis.json`, so results rebuild with no key and no price list.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter, StrMethodFormatter

from lab.charts import MIST, NAVY, SLATE, ChartSpec, ChartStyle, export_chart, highlight
from lab.prices import load_prices
from lab.rag.corpus import Library
from lab.rag.judge_check import chunk_lookup
from lab.rag.log import ItemLog, read_log
from lab.rag.score import holds


def load_arms(results: Path, names: Sequence[str]) -> dict[str, list[ItemLog]]:
    """Each arm's log, for the arms that have one."""
    return {
        n: read_log(results / n / "log.jsonl")
        for n in names
        if (results / n / "log.jsonl").exists()
    }


def incomplete(arms: Mapping[str, Sequence[ItemLog]]) -> dict[str, int]:
    """Arms with items lacking an answer or a verdict, and how many. Claims are not stated
    for such arms: a missing answer would count as wrong."""
    out = {}
    for name, logs in arms.items():
        missing = sum(1 for g in logs if g.answer is None or g.verdict is None)
        if missing:
            out[name] = missing
    return out


def pipeline_of(results: Path, name: str) -> dict[str, Any]:
    return json.loads((results / name / "summary.json").read_text(encoding="utf-8"))["pipeline"]


def answer_prices(root: Path) -> dict[str, tuple[float, float]] | None:
    """Input and output price per million tokens for each model, or None with no prices file."""
    prices = load_prices(root / "prices.local.yaml")
    if prices is None:
        return None
    out = {}
    for provider in prices.prices.values():
        for model, price in provider.items():
            if price.input is not None and price.output is not None:
                out[model] = (price.input, price.output)
    return out


def kept_ratios(analysis: Path, key: str) -> dict[str, float] | None:
    """The cost ratios already committed, for a rebuild with no prices file."""
    if not analysis.exists():
        return None
    return json.loads(analysis.read_text(encoding="utf-8")).get(key)


def evidence_checker(
    library: Library, pipeline: Mapping[str, Any]
) -> Callable[[ItemLog, int], bool]:
    """Whether passage n of an item's prompt holds one of its evidence spans."""
    chunks = chunk_lookup(library, dict(pipeline))
    items = {i.id: i for i in library.test}

    def check(log: ItemLog, n: int) -> bool:
        chunk = chunks[log.prompt_chunks[n - 1]]
        return any(holds(chunk, span) for span in items[log.item_id].evidence)

    return check


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")


def slope_chart(
    out: Path,
    name: str,
    *,
    left: Mapping[str, float],
    right: Mapping[str, float],
    labels: Mapping[str, str],
    left_title: str,
    right_title: str,
    units: str,
    sample_size: str,
    highlight_key: str | None = None,
    footnote: str | None = None,
) -> list[Path]:
    """Two orders side by side: each model's rank on the left and on the right, joined by a
    line, so a reader sees which models move. Ties share a rank."""
    keys = list(labels)

    def ranks(values: Mapping[str, float]) -> dict[str, int]:
        ordered = sorted({values[k] for k in keys}, reverse=True)
        return {k: ordered.index(values[k]) for k in keys}

    left_rank, right_rank = ranks(left), ranks(right)
    rows = max(max(left_rank.values()), max(right_rank.values())) + 1

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        for k in keys:
            line = ax.plot(
                [0, 1],
                [left_rank[k], right_rank[k]],
                color=SLATE,
                linewidth=style.line_width_pt,
                marker="o",
                markersize=style.label_pt / 2,
            )[0]
            if k == highlight_key:
                highlight(line)
        for side, rank, values in ((0, left_rank, left), (1, right_rank, right)):
            by_rank: dict[int, list[str]] = {}
            for k in keys:
                by_rank.setdefault(rank[k], []).append(k)
            for r, group in by_rank.items():
                text = " / ".join(f"{labels[k]} {values[k]:g}" for k in group)
                ax.text(
                    -0.04 if side == 0 else 1.04,
                    r,
                    text,
                    ha="right" if side == 0 else "left",
                    va="center",
                    color=MIST,
                )
        ax.text(0, -1, left_title, ha="center", va="center", color=MIST)
        ax.text(1, -1, right_title, ha="center", va="center", color=MIST)
        ax.set_xlim(-1.3, 2.3)
        ax.set_ylim(rows - 0.5, -1.6)
        ax.axis("off")

    return export_chart(
        draw, out, ChartSpec(name=name, units=units, sample_size=sample_size, footnote=footnote)
    )


def interval_bars(
    out: Path,
    name: str,
    *,
    rows: Sequence[tuple[str, Mapping[str, Any]]],
    units: str,
    sample_size: str,
    highlight_index: int | None = None,
    footnote: str | None = None,
) -> list[Path]:
    """Horizontal bars of shares, best at the top, each with its 95% Wilson interval."""

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        positions = list(range(len(rows)))[::-1]
        rates = [p["rate"] for _, p in rows]
        bars = ax.barh(positions, rates, color=MIST, edgecolor=NAVY, height=0.7)
        lows = [max(0.0, p["rate"] - p["low"]) for _, p in rows]
        highs = [max(0.0, p["high"] - p["rate"]) for _, p in rows]
        ax.errorbar(
            rates,
            positions,
            xerr=[lows, highs],
            fmt="none",
            ecolor=NAVY,
            elinewidth=style.line_width_pt,
            capsize=style.label_pt / 3,
        )
        if highlight_index is not None:
            highlight(bars.patches[highlight_index])
        ax.set_yticks(positions, labels=[label for label, _ in rows])
        ax.tick_params(axis="y", length=0)
        low = max(0.0, min(p["low"] for _, p in rows) - 0.05)
        ax.set_xlim(low, 1)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return export_chart(
        draw, out, ChartSpec(name=name, units=units, sample_size=sample_size, footnote=footnote)
    )


def ratio_bars(
    out: Path,
    name: str,
    *,
    rows: Sequence[tuple[str, float]],
    units: str,
    sample_size: str,
    highlight_index: int | None = None,
    footnote: str | None = None,
) -> list[Path]:
    """Horizontal bars of multiples (1x is the cheapest), in the order given, top first."""

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        positions = list(range(len(rows)))[::-1]
        bars = ax.barh(positions, [v for _, v in rows], color=MIST, edgecolor=NAVY, height=0.7)
        if highlight_index is not None:
            highlight(bars.patches[highlight_index])
        ax.set_yticks(positions, labels=[label for label, _ in rows])
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:g}x"))
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return export_chart(
        draw, out, ChartSpec(name=name, units=units, sample_size=sample_size, footnote=footnote)
    )
