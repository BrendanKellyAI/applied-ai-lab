"""Draws the S1 E3 charts from results/embeddings.json, so it needs no API key.

Run from the repository root:

    uv run python episodes/s1-e3-embeddings/chart.py

similarity-to-query: how close each stored phrase is to "How do I get my money back?". The acid
green bar is the phrase that scores highest.

pairs: the negation and numbers pairs beside a paraphrase and an unrelated sentence. The acid
green bar is whichever of negation or numbers scores highest, and only if it beats the
paraphrase: a warning pair that scores below a true paraphrase shows nothing worth flagging.
"""

import json
from collections.abc import Sequence
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter

from lab.charts import MIST, NAVY, SLATE, ChartSpec, ChartStyle, export_chart, highlight

HERE = Path(__file__).parent
RESULTS = HERE / "results" / "embeddings.json"
OUT_DIR = HERE / "charts"
SEARCH_CHART = "similarity-to-query"
PAIRS_CHART = "pairs"
# The two pairs the episode warns about. Paraphrase and unrelated are yardsticks, not findings.
WARNING_KINDS = ("negation", "numbers")
PAIR_LABELS = {
    "negation": "Negation",
    "numbers": "Numbers",
    "paraphrase": "Paraphrase",
    "unrelated": "Unrelated",
}
# Space between the end of a bar and its score, in points.
VALUE_OFFSET_POINTS = 12
BAR_HEIGHT = 0.4
TEXT_GAP = 0.06


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def top_phrase(scores: Sequence[dict]) -> str:
    """Highlight rule for the search chart: the single highest-scoring phrase."""
    return max(scores, key=lambda entry: entry["score"])["phrase"]


def flagged_pair(pairs: Sequence[dict]) -> str | None:
    """Highlight rule for the pairs chart, or None when no warning pair beats the paraphrase."""
    paraphrase = next(pair["score"] for pair in pairs if pair["kind"] == "paraphrase")
    warnings = [pair for pair in pairs if pair["kind"] in WARNING_KINDS]
    best = max(warnings, key=lambda pair: pair["score"])
    return best["kind"] if best["score"] > paraphrase else None


def _bars(
    ax: Axes,
    style: ChartStyle,
    *,
    labels: Sequence[str],
    scores: Sequence[float],
    texts: Sequence[str] | None,
    finding: int | None,
) -> None:
    """Horizontal bars, first at the top, each score printed at the end of its bar."""
    rows = list(range(len(labels)))[::-1]
    bars = ax.barh(rows, list(scores), height=BAR_HEIGHT, color=SLATE)
    for index, bar in enumerate(bars.patches):
        if index == finding:
            highlight(bar)
        ax.annotate(
            f"{scores[index]:.3f}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            textcoords="offset points",
            xytext=(VALUE_OFFSET_POINTS, 0),
            va="center",
            color=MIST,
        )
        if texts is not None:
            # The sentences go above the bar: they are too long to sit beside it as a label.
            ax.text(
                0,
                bar.get_y() + bar.get_height() + TEXT_GAP,
                texts[index],
                ha="left",
                va="bottom",
                color=MIST,
                bbox={"facecolor": NAVY, "edgecolor": "none", "pad": 2},
            )
    ax.set_yticks(rows, labels=list(labels))
    if texts is not None:
        ax.set_ylim(-0.5, len(labels) - 0.2)
    # Scores are cosine similarities, which never exceed 1.
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.set_xlabel("Cosine similarity")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", alpha=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)


def draw_search(results: dict):
    ranked = sorted(results["search"]["scores"], key=lambda entry: -entry["score"])
    finding = [entry["phrase"] for entry in ranked].index(top_phrase(ranked))

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(
            ax,
            style,
            labels=[entry["phrase"] for entry in ranked],
            scores=[entry["score"] for entry in ranked],
            texts=None,
            finding=finding,
        )

    return draw


def draw_pairs(results: dict):
    pairs = results["pairs"]
    kind = flagged_pair(pairs)
    finding = None if kind is None else [pair["kind"] for pair in pairs].index(kind)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(
            ax,
            style,
            labels=[PAIR_LABELS[pair["kind"]] for pair in pairs],
            scores=[pair["score"] for pair in pairs],
            texts=[f"{pair['first']} / {pair['second']}" for pair in pairs],
            finding=finding,
        )

    return draw


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    model = results["model_returned"]
    query = results["search"]["query"]
    written = export_chart(
        draw_search(results),
        out_dir,
        ChartSpec(
            name=SEARCH_CHART,
            units="Cosine similarity",
            sample_size=f"{len(results['search']['scores'])} stored phrases, one run",
            footnote=f"Model: {model}.\nCosine similarity to: {query}",
        ),
    )
    flagged = flagged_pair(results["pairs"])
    written += export_chart(
        draw_pairs(results),
        out_dir,
        ChartSpec(
            name=PAIRS_CHART,
            units="Cosine similarity",
            sample_size=f"{len(results['pairs'])} pairs, one run",
            footnote=f"Model: {model}.",
            no_highlight_note=(
                None
                if flagged is not None
                else "No warning pair beat the paraphrase; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
