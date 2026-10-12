"""S2 E3 charts, from committed results only: no key, no call.

Run with `uv run python episodes/s2-e3-measuring/chart.py`.

- `agreement`: how often the judge and the second model give the same verdict, per field.
  Acid green marks each field below its 45-of-50 pass mark; the rule allows one, and if more
  than one fell short the chart highlights none and says so.
- `search-or-model`: E2's answers judged right, split by whether search put the right passage
  in the prompt. Acid green marks "Passage not in the prompt" when its interval sits below
  both others; otherwise nothing is highlighted and the chart says so.
"""

import json
from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.rag.log import read_log
from lab.rag.score import Proportion

HERE = Path(__file__).parent
E2_LOG = HERE.parent / "s2-e2-first-rag-system" / "results" / "baseline" / "log.jsonl"
PASS_MARK = 45
FIELDS = {"declined": "Declined", "correct": "Correct", "faithful": "Faithful",
          "right": "Correct and faithful"}


def _bars(ax: Axes, style: ChartStyle, labels, props: list[Proportion], highlight: int | None):
    grouped_bars(ax, categories=labels, series=[("Share", [p.rate for p in props])], style=style,
                 horizontal=True, highlight_bar=None if highlight is None else (0, highlight))
    positions = [len(props) - 1 - i for i in range(len(props))]
    ax.errorbar([p.rate for p in props], positions,
                xerr=[[p.rate - p.low for p in props], [p.high - p.rate for p in props]],
                fmt="none", ecolor=WHITE, elinewidth=style.line_width_pt,
                capsize=style.label_pt / 3)
    for p, y in zip(props, positions, strict=True):
        ax.text(p.high + 0.02, y, f"{p.count} of {p.total}", va="center", color=MIST)
    ax.set_xlim(0, 1.32)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])


def agreement_chart(models: dict[str, Any]):
    props = [Proportion(**models[f]) for f in FIELDS]
    short = [i for i, p in enumerate(props) if p.count < PASS_MARK]
    highlight = short[0] if len(short) == 1 else None

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(ax, style, list(FIELDS.values()), props, highlight)
        ax.axvline(PASS_MARK / 50, color=MIST, linestyle="--", linewidth=style.line_width_pt)

    note = None if highlight is not None else "No highlight: no single field missed its mark"
    return draw, note


def split_rates(logs) -> list[Proportion]:
    answerable = [g for g in logs if g.answerable]
    found = [g for g in answerable if g.evidence_rank is not None and g.evidence_rank <= 5]
    lost = [g for g in answerable if g not in found]
    plain = [g for g in found if g.type != "version"]

    def right(group):
        return Proportion.of(
            sum(1 for g in group if g.verdict and g.verdict.correct and g.verdict.faithful),
            len(group),
        )

    return [right(found), right(plain), right(lost)]


def split_chart(rates: list[Proportion]):
    found, plain, lost = rates
    clears = lost.high < found.low and lost.high < plain.low
    labels = ["Passage in the prompt", "In the prompt, no version Qs", "Passage not in the prompt"]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(ax, style, labels, rates, 2 if clears else None)

    return draw, None if clears else "No highlight: the intervals overlap"


def main() -> None:
    report = json.loads((HERE / "judge-check" / "agreement.json").read_text(encoding="utf-8"))
    out = HERE / "charts"
    draw, note = agreement_chart(report["models"])
    export_chart(draw, out, ChartSpec(
        name="agreement", units="Judge and Gemini agree", sample_size="n = 50 items",
        no_highlight_note=note, footnote="Dashed line: the 45 of 50 pass mark",
    ))
    draw, note = split_chart(split_rates(read_log(E2_LOG)))
    export_chart(draw, out, ChartSpec(
        name="search-or-model", units="Answers judged right", sample_size="n = 400 answerable",
        no_highlight_note=note, footnote="E2 baseline; judge verdicts",
    ))


if __name__ == "__main__":
    main()
