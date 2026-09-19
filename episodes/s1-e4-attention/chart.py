"""Draws the S1 E4 charts from results/attention.json, needing neither the model nor a network.

Run from the repository root:

    uv run python episodes/s1-e4-attention/chart.py

word-attention: how much of the attention from "it" each earlier word receives, in both
sentences, renormalised without the first token. The acid green bar is the word whose weight
changes most between the sentences; if none changes, nothing is highlighted and the chart says so.

layer-shift: attention to "trophy" minus attention to "suitcase", layer by layer, for both
sentences. The acid green mark is the layer where the two sentences differ most; if they never
differ by more than 0.01, nothing is highlighted and the chart says so.
"""

import json
from collections.abc import Sequence
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import (
    LINE_STYLES,
    MIST,
    SLATE,
    ChartSpec,
    ChartStyle,
    export_chart,
    grouped_bars,
    highlight,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results" / "attention.json"
OUT_DIR = HERE / "charts"
WORD_CHART = "word-attention"
LAYER_CHART = "layer-shift"
SERIES = (("big", "too big"), ("small", "too small"))
# Below this, two layers' figures are the same for any purpose a slide could make of them.
LAYER_GAP = 0.01
# A change smaller than this is floating point noise.
TOLERANCE = 1e-9
MODEL_LINE = "GPT-2 small, averaged over all 12 layers and 12 heads."


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def charted_words(sentence: dict) -> list[dict]:
    """The earlier words that have a renormalised weight: every one but the first token."""
    return [word for word in sentence["words"] if word["renormalised"] is not None]


def most_changed_word(big: Sequence[dict], small: Sequence[dict]) -> int | None:
    """Highlight rule for the word chart, or None when no word's weight changes at all."""
    changes = [abs(b["renormalised"] - s["renormalised"]) for b, s in zip(big, small, strict=True)]
    largest = max(changes)
    return changes.index(largest) if largest > TOLERANCE else None


def widest_layer(big: Sequence[float], small: Sequence[float]) -> int | None:
    """Highlight rule for the layer chart, or None when the lines never separate by LAYER_GAP."""
    gaps = [abs(b - s) for b, s in zip(big, small, strict=True)]
    largest = max(gaps)
    return gaps.index(largest) if largest > LAYER_GAP else None


def _first_token_line(results: dict) -> str:
    shares = [results["sentences"][key]["first_token_share"] for key, _ in SERIES]
    if abs(shares[0] - shares[1]) <= TOLERANCE:
        return f"The first token took {shares[0]:.1%} of the attention, left out here."
    return f"The first token took {shares[0]:.1%} (big) and {shares[1]:.1%} (small)."


def draw_words(results: dict):
    big, small = (charted_words(results["sentences"][key]) for key, _ in SERIES)
    changed = most_changed_word(big, small)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[word["word"] for word in big],
            series=[
                (label, [word["renormalised"] for word in words])
                for (_, label), words in zip(SERIES, (big, small), strict=True)
            ],
            style=style,
            # The bar after the change, in the "small" sentence, carries the finding.
            highlight_bar=None if changed is None else (1, changed),
            horizontal=True,
        )
        ax.set_xlabel('Share of attention from "it"')

    return draw


def draw_layers(results: dict):
    lines = [
        results["sentences"][key]["trophy_minus_suitcase"]["per_layer"] for key, _ in SERIES
    ]
    widest = widest_layer(*lines)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        layers = list(range(1, len(lines[0]) + 1))
        for index, ((_, label), values) in enumerate(zip(SERIES, lines, strict=True)):
            ax.plot(
                layers,
                values,
                label=label,
                color=(MIST, SLATE)[index],
                linestyle=LINE_STYLES[index],
                linewidth=style.line_width_pt,
                marker="o",
                markersize=style.line_width_pt * 2,
            )
        if widest is not None:
            # A bar joining the two sentences at the layer where they differ most.
            (gap,) = ax.plot(
                [widest + 1, widest + 1],
                [lines[0][widest], lines[1][widest]],
                linewidth=style.line_width_pt * 2,
            )
            highlight(gap)
        ax.axhline(0, color=SLATE, linewidth=style.line_width_pt / 2, linestyle=":")
        ax.set_xticks(layers)
        ax.set_xlabel("Layer")
        ax.set_ylabel("Trophy minus suitcase")
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(loc="upper left", bbox_to_anchor=(0, 1.12), ncols=2)

    return draw


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    big, small = (charted_words(results["sentences"][key]) for key, _ in SERIES)
    lines = [
        results["sentences"][key]["trophy_minus_suitcase"]["per_layer"] for key, _ in SERIES
    ]
    written = export_chart(
        draw_words(results),
        out_dir,
        ChartSpec(
            name=WORD_CHART,
            units='Share of attention from "it"',
            sample_size="renormalised, one run",
            footnote=f"{MODEL_LINE}\n{_first_token_line(results)}",
            no_highlight_note=(
                None
                if most_changed_word(big, small) is not None
                else "No word's weight changed; nothing highlighted."
            ),
        ),
    )
    written += export_chart(
        draw_layers(results),
        out_dir,
        ChartSpec(
            name=LAYER_CHART,
            units="Attention to trophy minus suitcase",
            sample_size="12 heads per layer, one run",
            footnote='GPT-2 small, raw attention from "it".',
            no_highlight_note=(
                None
                if widest_layer(*lines) is not None
                else "Lines never differ by more than 0.01; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
