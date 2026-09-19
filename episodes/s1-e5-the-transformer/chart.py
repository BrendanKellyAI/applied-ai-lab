"""Draws the S1 E5 charts from results/timing.json, needing neither the model nor a network.

Run from the repository root:

    uv run python episodes/s1-e5-the-transformer/chart.py

per-token: milliseconds per token for reading a 512-token prompt and for writing 512 tokens, as
the median of 5 runs with the minimum and maximum as whiskers. The acid green bar is the slower
of the two; if they are within 10% of each other, nothing is highlighted and the chart says so.

sweep: total time against the number of tokens, one line for reading and one for writing. The
acid green line is the one with the steeper slope; if the two slopes are within 10% of each
other, nothing is highlighted and the chart says so.
"""

import json
import re
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from lab.charts import (
    LINE_STYLES,
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
RESULTS = HERE / "results" / "timing.json"
OUT_DIR = HERE / "charts"
PER_TOKEN_CHART = "per-token"
SWEEP_CHART = "sweep"
READING = "reading"
WRITING = "writing"
KINDS = (READING, WRITING)
SAMPLE = "median of 5 runs"
# Room above the tallest whisker for its value label.
HEADROOM = 1.18

measure = load_sibling(HERE / "measure.py")


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def condition(results: dict, kind: str, tokens: int, kv_cache: bool = True) -> dict:
    for entry in results["conditions"]:
        if (entry["kind"], entry["tokens"], entry["kv_cache"]) == (kind, tokens, kv_cache):
            return entry
    raise ValueError(f"No {kind} condition of {tokens} tokens with kv_cache={kv_cache}")


def headline(results: dict) -> dict[str, dict[str, float]]:
    """Per-token milliseconds as median, minimum and maximum, for reading and for writing."""
    tokens = results["method"]["headline_tokens"]
    return {
        kind: measure.summarise(condition(results, kind, tokens)["seconds"], tokens)[
            "per_token_ms"
        ]
        for kind in KINDS
    }


def sweep(results: dict, kind: str) -> tuple[list[int], list[float]]:
    """Token counts, and the median total seconds at each."""
    counts = results["method"]["sweep_tokens"]
    medians = [
        measure.spread(condition(results, kind, count)["seconds"])["median"] for count in counts
    ]
    return list(counts), medians


def slower_bar(reading_ms: float, writing_ms: float) -> int | None:
    """Highlight rule for the per-token chart: 0 for reading, 1 for writing, or None."""
    if measure.same_within(reading_ms, writing_ms):
        return None
    return 0 if reading_ms > writing_ms else 1


def steeper_line(reading_slope: float, writing_slope: float) -> int | None:
    """Highlight rule for the sweep chart: 0 for reading, 1 for writing, or None."""
    if measure.same_within(reading_slope, writing_slope):
        return None
    return 0 if reading_slope > writing_slope else 1


def slopes(results: dict) -> tuple[float, float]:
    """Seconds per token of the reading line and of the writing line."""
    return tuple(measure.slope(*sweep(results, kind)) for kind in KINDS)


def short_cpu(name: str | None) -> str:
    """A CPU's name without its trademark marks, so it fits on one footer line."""
    if not name:
        return "an unnamed CPU"
    return re.sub(r"\s+", " ", re.sub(r"\((?:R|TM)\)|\bCPU\b", "", name)).strip()


def _machine_line(results: dict) -> str:
    machine = results["machine"]
    return f"GPT-2 small on {short_cpu(machine['cpu'])}, {machine['threads_used']} threads"


def _ms(value: float) -> str:
    return f"{value:.1f}"


def draw_per_token(results: dict):
    figures = headline(results)
    medians = [figures[kind]["median"] for kind in KINDS]
    slower = slower_bar(*medians)
    tokens = results["method"]["headline_tokens"]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[f"Reading\n({tokens}-token prompt)", f"Writing\n({tokens} new tokens)"],
            series=[("Milliseconds per token", medians)],
            style=style,
            highlight_bar=None if slower is None else (0, slower),
            value_formatter=FuncFormatter(lambda value, _: f"{value:g}"),
        )
        low = [figures[kind]["median"] - figures[kind]["min"] for kind in KINDS]
        high = [figures[kind]["max"] - figures[kind]["median"] for kind in KINDS]
        ax.errorbar(range(len(KINDS)), medians, yerr=[low, high], fmt="none", ecolor=WHITE)
        for position, kind in enumerate(KINDS):
            ax.text(
                position,
                figures[kind]["max"],
                f"{_ms(figures[kind]['median'])} ms",
                ha="center",
                va="bottom",
                color=WHITE,
            )
        ax.set_ylim(0, max(figures[kind]["max"] for kind in KINDS) * HEADROOM)
        ax.set_ylabel("Milliseconds per token")

    return draw


def draw_sweep(results: dict):
    lines = [sweep(results, kind) for kind in KINDS]
    steeper = steeper_line(*slopes(results))

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        for index, (kind, (counts, seconds)) in enumerate(zip(KINDS, lines)):
            (line,) = ax.plot(
                counts,
                seconds,
                color=(MIST, SLATE)[index],
                linestyle=LINE_STYLES[index],
                linewidth=style.line_width_pt,
                marker="o",
                markersize=style.line_width_pt * 2,
            )
            if steeper == index:
                highlight(line)
            # Named at the line's end rather than in a legend, because a legend key copies the
            # line's colour and would show the acid green finding a second time.
            ax.annotate(
                kind.capitalize(),
                (counts[-1], seconds[-1]),
                xytext=(-12, 12),
                textcoords="offset points",
                ha="right",
                va="bottom",
            )
        ax.set_xticks(lines[0][0])
        ax.set_ylim(0, max(max(seconds) for _, seconds in lines) * HEADROOM)
        ax.set_xlabel("Tokens read, or tokens written")
        ax.set_ylabel("Total time (seconds)")
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    return draw


def _ratio_line(reading_ms: float, writing_ms: float) -> str:
    slower, faster = (WRITING, READING) if writing_ms >= reading_ms else (READING, WRITING)
    times = measure.ratio(max(reading_ms, writing_ms), min(reading_ms, writing_ms))
    return f"{slower.capitalize()} takes {times:.1f} times as long per token as {faster}."


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    figures = headline(results)
    medians = [figures[kind]["median"] for kind in KINDS]
    reading_slope, writing_slope = slopes(results)
    written = export_chart(
        draw_per_token(results),
        out_dir,
        ChartSpec(
            name=PER_TOKEN_CHART,
            units="Milliseconds per token",
            sample_size=SAMPLE,
            footnote="\n".join(
                [
                    _machine_line(results),
                    _ratio_line(*medians),
                    "Bars are medians; whiskers run from minimum to maximum.",
                ]
            ),
            no_highlight_note=(
                None
                if slower_bar(*medians) is not None
                else "Within 10% of each other; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_sweep(results),
        out_dir,
        ChartSpec(
            name=SWEEP_CHART,
            units="Total time in seconds",
            sample_size=SAMPLE,
            footnote=(
                f"{_machine_line(results)}\n"
                f"Slopes: writing {_ms(writing_slope * 1000)}, "
                f"reading {_ms(reading_slope * 1000)} ms per token."
            ),
            no_highlight_note=(
                None
                if steeper_line(reading_slope, writing_slope) is not None
                else "Slopes within 10% of each other; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
