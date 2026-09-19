"""Draws the S1 E2 chart: one sentence per language, and how many tokens each costs.

Run from the repository root:

    uv run python episodes/s1-e2-tokens/chart.py

Counts come from the tokeniser, never typed in by hand, so the chart always matches what
count_tokens.py prints. The acid green bar is the language whose sentence costs the most tokens.
"""

from pathlib import Path

import tiktoken
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, SLATE, ChartSpec, ChartStyle, export_chart, highlight

TOKENISER = "o200k_base"
SENTENCES = {
    "English": "My name is Brendan.",
    "French": "Je m'appelle Brendan.",
    "Amharic": "ስሜ ብሬንዳን ነው።",
}
CHART_NAME = "tokens-by-language"
OUT_DIR = Path(__file__).parent / "charts"
# Space between the end of a bar and its count, in points.
VALUE_OFFSET_POINTS = 12


def token_counts(tokeniser: str = TOKENISER) -> dict[str, int]:
    encoding = tiktoken.get_encoding(tokeniser)
    return {language: len(encoding.encode(sentence)) for language, sentence in SENTENCES.items()}


def most_tokens(counts: dict[str, int]) -> str:
    """The highlight rule: the language whose sentence costs the most tokens."""
    return max(counts, key=lambda language: (counts[language], language))


def _draw(counts: dict[str, int]):
    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        languages = list(SENTENCES)
        rows = range(len(languages))[::-1]
        bars = ax.barh(
            list(rows),
            [counts[language] for language in languages],
            height=0.55,
            color=SLATE,
        )
        for bar, language in zip(bars.patches, languages, strict=True):
            if language == most_tokens(counts):
                highlight(bar)
            ax.annotate(
                f"{counts[language]}",
                (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                textcoords="offset points",
                xytext=(VALUE_OFFSET_POINTS, 0),
                va="center",
                color=MIST,
            )
        # The sentence sits under its language, so every bar is labelled with what was counted.
        ax.set_yticks(
            list(rows), labels=[f"{language}\n{SENTENCES[language]}" for language in languages]
        )
        ax.set_xlim(0, max(counts.values()) * 1.2)
        ax.set_xlabel("Tokens")
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)

    return draw


def render(out_dir: Path = OUT_DIR) -> list[Path]:
    counts = token_counts()
    return export_chart(
        _draw(counts),
        out_dir,
        ChartSpec(
            name=CHART_NAME,
            units=f"Tokens, counted with {TOKENISER}",
            sample_size="One sentence per language",
            footnote="The same sentence in each language.",
        ),
    )


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
