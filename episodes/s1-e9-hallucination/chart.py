"""Draws the S1 E9 chart from results/answers.json, so it needs no key, model or network.

Run from the repository root:

    uv run python episodes/s1-e9-hallucination/chart.py

error-rates: the two errors, each for the plain prompt and the prompt with the instruction, and for
each of those two bars side by side: what the fixed phrase rule counted, and what reading every
response found. The first pair of conditions is invented items described as real, the
hallucination rate. The second is real items flagged as doubtful, the over-caution rate.

The two measures are drawn next to each other because they disagree, and a chart that showed only
the rule would leave a reader with the wrong result. The acid green bar is the single highest
bar among the reading's invented-treated-as-real bars. If those are all 0, or the highest is
shared, nothing is highlighted and the chart says so. If the responses have not been read, the
chart has the rule's bars alone, says so, and highlights the highest of the rule's.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, SLATE, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.experiments import load_sibling

HERE = Path(__file__).parent
RESULTS = HERE / "results" / "answers.json"
OUT_DIR = HERE / "charts"
CHART = "error-rates"
CONDITIONS = ("plain", "instructed")
CONDITION_LABELS = {"plain": "Plain", "instructed": "Instructed"}
GROUPS = ("invented", "real")
GROUP_TITLES = {"invented": "Invented items treated as real", "real": "Real items flagged"}
RULE_LABEL = "By the rule"
READING_LABEL = "By reading each response"
# The bars, left to right: each group's conditions in turn.
CELLS = tuple((group, condition) for group in GROUPS for condition in CONDITIONS)
# Room above the tallest bar for its label, and above that for the group titles and the legend.
HEADROOM = 1.85
GROUP_WIDTH = 0.8
TITLE_HEIGHT = 0.985
LEGEND_TOP = 0.9
DIVIDER_TOP = 0.72

measure = load_sibling(HERE / "measure.py")


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rule_tallies(results: dict) -> dict[str, dict[str, dict]]:
    """For each group and condition, what the rule counted: the count and the number answered."""
    summary = results["summary"]
    return {
        group: {condition: summary[condition]["all"][group] for condition in CONDITIONS}
        for group in GROUPS
    }


def _rate(count: int, answered: int) -> float:
    return count / answered if answered else 0.0


def rate_of(tally: dict) -> float:
    """The rate as a bar height. A condition with no answers at all has nothing to draw."""
    return _rate(tally["count"], tally["answered"])


def reading_tallies(results: dict) -> dict[str, dict[str, dict]] | None:
    """The same counts from my reading of each response, or None unless every one was read.

    For invented items the count is those read as treated as real, and for real items those read
    as flagged, the same as for the rule. A response the rule could not score (incomplete or empty)
    is left out of both, so the two are counted over the same responses.
    """
    responses = results["responses"]
    if not responses or any(r.get("reading") is None for r in responses):
        return None
    counted = {"invented": measure.TREATED_AS_REAL, "real": measure.FLAGGED}
    tallies: dict[str, dict[str, dict]] = {}
    for group in GROUPS:
        tallies[group] = {}
        for condition in CONDITIONS:
            chosen = [
                r
                for r in responses
                if r["real"] == (group == "real")
                and r["condition"] == condition
                and r["label"] != measure.UNANSWERED
            ]
            tallies[group][condition] = {
                "count": sum(r["reading"] == counted[group] for r in chosen),
                "answered": len(chosen),
            }
    return tallies


def highest_invented(rates: list[float]) -> int | None:
    """Highlight rule: the index of the single highest invented-treated-as-real bar, or None if
    the highest is 0 or is shared, since neither picks out one bar."""
    highest = max(rates)
    if highest == 0 or rates.count(highest) > 1:
        return None
    return rates.index(highest)


def _invented_rates(tallies: dict[str, dict[str, dict]]) -> list[float]:
    return [rate_of(tallies["invented"][condition]) for condition in CONDITIONS]


def disagreements(results: dict) -> tuple[int, int]:
    """How many responses to invented items the rule and my reading disagree on, and how many."""
    invented = [r for r in results["responses"] if not r["real"] and r.get("reading")]
    return sum(r["label"] != r["reading"] for r in invented), len(invented)


def _no_highlight_note(rates: list[float], by_reading: bool) -> str | None:
    if highest_invented(rates) is not None:
        return None
    source = "Read by hand" if by_reading else "By the rule"
    if max(rates) == 0:
        return f"{source}, no invented item was treated as real; nothing highlighted."
    return f"{source}, the two are equal; nothing highlighted."


def _footnote(results: dict, by_reading: bool) -> str:
    lines = [f"Model: {results['model_returned']}. Each bar is out of 30."]
    if by_reading:
        differ, total = disagreements(results)
        lines.append(f"The rule and my reading differ on {differ} of {total} invented.")
    else:
        lines.append("Not yet read by hand: the rule's bars alone.")
    unanswered = sum(
        tally["unanswered"]
        for by_condition in rule_tallies(results).values()
        for tally in by_condition.values()
    )
    if unanswered:
        lines.append(f"{unanswered} incomplete responses are not counted.")
    return "\n".join(lines)


def _place_legend_under_titles(ax: Axes) -> None:
    """Moves the legend into the empty band at the top of the plot, below the group titles.

    Above the plot it runs into the titles when the chart is short, as it is at article size.
    Its keys are the fresh swatches the bar helper builds, so no key can pick up the acid green
    of a highlighted bar.
    """
    legend = ax.get_legend()
    if legend is None:
        return
    handles = list(legend.legend_handles)
    labels = [text.get_text() for text in legend.get_texts()]
    legend.remove()
    ax.legend(
        handles=handles,
        labels=labels,
        loc="upper left",
        bbox_to_anchor=(0.0, LEGEND_TOP),
        ncols=len(handles),
    )


def draw_error_rates(results: dict):
    rule = rule_tallies(results)
    reading = reading_tallies(results)
    measures = [(RULE_LABEL, rule)] + ([(READING_LABEL, reading)] if reading else [])
    finding_source = reading if reading else rule
    finding = highest_invented(_invented_rates(finding_source))
    finding_series = len(measures) - 1

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        rates = [[rate_of(tallies[g][c]) for g, c in CELLS] for _, tallies in measures]
        grouped_bars(
            ax,
            categories=[CONDITION_LABELS[c] for _, c in CELLS],
            series=[(label, values) for (label, _), values in zip(measures, rates, strict=True)],
            style=style,
            highlight_bar=None if finding is None else (finding_series, finding),
        )
        _place_legend_under_titles(ax)
        width = GROUP_WIDTH / len(measures)
        for series, (_, tallies) in enumerate(measures):
            for position, (group, condition) in enumerate(CELLS):
                tally = tallies[group][condition]
                centre = position - GROUP_WIDTH / 2 + width * (series + 0.5)
                ax.text(
                    centre,
                    rate_of(tally),
                    f"{tally['count']}/{tally['answered']}",
                    ha="center",
                    va="bottom",
                    color=WHITE,
                )
                if tally["count"] == 0:
                    # A bar of height zero draws nothing, and a reader would take a missing bar
                    # for missing data. A mark on the baseline says the count was zero.
                    ax.hlines(
                        0,
                        centre - width / 2,
                        centre + width / 2,
                        colors=WHITE,
                        linewidth=style.line_width_pt * 1.5,
                    )
        # Each group's title spans its two conditions, and a dotted line divides the groups.
        for index, group in enumerate(GROUPS):
            ax.text(
                index * len(CONDITIONS) + (len(CONDITIONS) - 1) / 2,
                TITLE_HEIGHT,
                GROUP_TITLES[group],
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                color=MIST,
            )
        divider = len(CONDITIONS) - 0.5
        # It stops below the legend, which spans both groups and would otherwise be cut through.
        ax.axvline(
            divider, ymax=DIVIDER_TOP, color=SLATE, linestyle=":", linewidth=style.line_width_pt / 2
        )
        ax.set_ylim(0, max(max(values) for values in rates) * HEADROOM or 1)
        # The band above the bars is for the titles and the legend, and a share cannot pass 100%.
        ax.set_yticks([tick / 5 for tick in range(6)])
        ax.set_ylabel("Share of answered responses")

    return draw


def render(results: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    results = results if results is not None else load()
    reading = reading_tallies(results)
    finding_source = reading if reading else rule_tallies(results)
    return export_chart(
        draw_error_rates(results),
        out_dir,
        ChartSpec(
            name=CHART,
            units="Share of answered responses",
            sample_size=f"{results['runs_per_item']} runs per item",
            footnote=_footnote(results, reading is not None),
            no_highlight_note=_no_highlight_note(
                _invented_rates(finding_source), reading is not None
            ),
        ),
    )


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
