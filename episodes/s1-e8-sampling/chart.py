"""Draws the S1 E8 charts from results/local.json and results/api.json, so it needs no key,
no model and no network.

Run from the repository root:

    uv run python episodes/s1-e8-sampling/chart.py

next-token: GPT-2's most likely next tokens for "The capital of Ireland is" at temperature 1.0.
The acid green bar is the single most likely token, whichever it is.

temperature: the four most likely next tokens for "My favourite colour is", each at temperatures
0.3, 1.0 and 1.8. The acid green bar is the top token at 0.3.

distinct-answers: how many different answers came back from 20 identical calls, for each API
condition that was run. The acid green bar is the condition with the most distinct answers. If
all conditions are equal, or the most is shared, nothing is highlighted and the chart says so.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, PercentFormatter

from lab.charts import (
    MIST,
    NAVY,
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
LOCAL = HERE / "results" / "local.json"
API = HERE / "results" / "api.json"
OUT_DIR = HERE / "charts"
NEXT_TOKEN_CHART = "next-token"
TEMPERATURE_CHART = "temperature"
DISTINCT_CHART = "distinct-answers"
TOP_TOKENS = 4
# The order the conditions are shown in: the one-answer prompt first, then the many-answer prompt.
CONDITION_ORDER = ("capital-default", "coffee-default", "coffee-temperature-0")
CONDITION_LABELS = {
    "capital-default": "One answer\n(defaults)",
    "coffee-default": "Many answers\n(defaults)",
    "coffee-temperature-0": "Many answers\n(temperature 0)",
}
# Three series need three looks, and the shared bar helper offers two, so this chart draws its
# own. Each is told apart by colour and by hatching, never colour alone.
SERIES_STYLES = ((MIST, ""), (SLATE, "//"), (WHITE, ".."))
# Room above the tallest bar for its value label.
HEADROOM = 1.15
BAR_HEIGHT = 0.6

measure = load_sibling(HERE / "measure.py")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def top_entries(local: dict, prompt: str, temperature: float, count: int) -> list[dict]:
    return local["prompts"][prompt]["distributions"][str(temperature)]["top"][:count]


def most_likely_token(entries: list[dict]) -> int:
    """Highlight rule for the next-token chart: the index of the single most likely token."""
    return max(range(len(entries)), key=lambda index: entries[index]["probability"])


def token_label(entry: dict) -> str:
    """The token in quotation marks, so the space that GPT-2 puts before a word can be seen."""
    return f'"{entry["text"]}"'


def most_distinct(counts: list[int]) -> int | None:
    """Highlight rule for the answers chart: the condition with the most distinct answers.

    None when every condition is equal, and also when the most is shared, because choosing one of
    two tied conditions would say something the results do not.
    """
    largest = max(counts)
    if counts.count(largest) > 1:
        return None
    return counts.index(largest)


def api_conditions(api: dict) -> list[dict]:
    by_name = {condition["name"]: condition for condition in api["conditions"]}
    return [by_name[name] for name in CONDITION_ORDER if name in by_name]


def _percent(value: float) -> str:
    return f"{value:.1%}"


def draw_next_token(local: dict):
    entries = top_entries(local, "capital", 1.0, measure.TOP_K)
    finding = most_likely_token(entries)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        rows = list(range(len(entries)))[::-1]
        bars = ax.barh(rows, [e["probability"] for e in entries], height=BAR_HEIGHT, color=SLATE)
        for index, bar in enumerate(bars.patches):
            if index == finding:
                highlight(bar)
            ax.annotate(
                _percent(entries[index]["probability"]),
                (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                textcoords="offset points",
                xytext=(12, 0),
                va="center",
                color=MIST,
            )
        ax.set_yticks(rows, labels=[token_label(e) for e in entries])
        ax.set_xlim(0, max(e["probability"] for e in entries) * 1.3)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.set_xlabel("Probability of the next token")
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)

    return draw


def draw_temperature(local: dict):
    temperatures = local["temperatures"]
    tops = [top_entries(local, "colour", t, TOP_TOKENS) for t in temperatures]
    # Temperature never reorders tokens, so the same four are on top at every temperature. If a
    # file ever said otherwise, the bars would be labelled wrongly, so refuse to draw.
    if len({tuple(e["token_id"] for e in entries) for entries in tops}) != 1:
        raise ValueError("The top tokens differ between temperatures, so they cannot share bars")
    categories = [e["text"].strip() for e in tops[0]]
    finding_series = temperatures.index(min(temperatures))

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        width = 0.8 / len(temperatures)
        for series, entries in enumerate(tops):
            colour, hatch = SERIES_STYLES[series]
            offsets = [c - 0.4 + width * (series + 0.5) for c in range(len(categories))]
            bars = ax.bar(
                offsets,
                [e["probability"] for e in entries],
                width=width,
                color=colour,
                hatch=hatch,
                edgecolor=NAVY,
            )
            if series == finding_series:
                highlight(bars.patches[0])
            # Only the top token is labelled: twelve labels would run into each other.
            ax.annotate(
                f"{entries[0]['probability']:.0%}",
                (offsets[0], entries[0]["probability"]),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                color=WHITE,
            )
        ax.set_xticks(range(len(categories)), labels=categories)
        ax.set_ylim(0, max(e["probability"] for entries in tops for e in entries) * HEADROOM)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.set_ylabel("Probability of the next token")
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        # Built from fresh swatches, because a legend key copies the colour of the bar it stands
        # for, and the highlighted bar would turn its key acid green as well.
        ax.legend(
            handles=[
                Patch(
                    facecolor=SERIES_STYLES[i][0],
                    hatch=SERIES_STYLES[i][1],
                    edgecolor=NAVY,
                    label=str(t),
                )
                for i, t in enumerate(temperatures)
            ],
            title="Temperature",
            loc="upper right",
            ncols=len(temperatures),
        )

    return draw


def draw_distinct(api: dict):
    conditions = api_conditions(api)
    counts = [condition["distinct_count"] for condition in conditions]
    finding = most_distinct(counts)
    runs = api["runs_per_condition"]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        # Whole numbers out of the calls made, not shares, so the axis is plain counts.
        grouped_bars(
            ax,
            categories=[CONDITION_LABELS[c["name"]] for c in conditions],
            series=[("Distinct answers", counts)],
            style=style,
            highlight_bar=None if finding is None else (0, finding),
            value_formatter=FuncFormatter(lambda value, _: f"{value:g}"),
        )
        for position, condition in enumerate(conditions):
            ax.text(
                position,
                condition["distinct_count"],
                f"{condition['distinct_count']} of {condition['answered']}",
                ha="center",
                va="bottom",
                color=WHITE,
            )
        ax.set_ylim(0, runs * HEADROOM)
        ax.set_yticks(range(0, runs + 1, 5))
        ax.set_ylabel(f"Distinct answers from {runs} calls")

    return draw


def _distinct_footnote(api: dict) -> str:
    lines = [f"Model: {api['model_returned']}. Same prompt every time."]
    unanswered = sum(condition["unanswered"] for condition in api_conditions(api))
    if unanswered:
        lines.append(f"{unanswered} incomplete responses are not counted.")
    if api["probe"]["outcome"] == "rejected":
        lines.append("Temperature 0 was rejected by the model, so has no bar.")
    return "\n".join(lines)


def render(
    local: dict | None = None, api: dict | None = None, out_dir: Path = OUT_DIR
) -> list[Path]:
    local = local if local is not None else load(LOCAL)
    api = api if api is not None else load(API)
    capital = local["prompts"]["capital"]
    colour = local["prompts"]["colour"]
    dublin = capital["dublin"]
    written = export_chart(
        draw_next_token(local),
        out_dir,
        ChartSpec(
            name=NEXT_TOKEN_CHART,
            units="Probability of the next token",
            sample_size="exact, one forward pass",
            footnote=(
                f'GPT-2 small. Prompt: "{capital["prompt"]}"\n'
                f'" Dublin" ranks {dublin["rank"]}, with {_percent(dublin["probability"])}.'
            ),
        ),
    )
    written += export_chart(
        draw_temperature(local),
        out_dir,
        ChartSpec(
            name=TEMPERATURE_CHART,
            units="Probability of the next token",
            sample_size="exact, one forward pass",
            footnote=f'GPT-2 small. Prompt: "{colour["prompt"]}"',
        ),
    )
    counts = [condition["distinct_count"] for condition in api_conditions(api)]
    written += export_chart(
        draw_distinct(api),
        out_dir,
        ChartSpec(
            name=DISTINCT_CHART,
            units="Distinct answers",
            sample_size=f"{api['runs_per_condition']} calls per condition",
            footnote=_distinct_footnote(api),
            no_highlight_note=(
                None
                if most_distinct(counts) is not None
                else "The most distinct answers is shared; nothing highlighted."
            ),
        ),
    )
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
