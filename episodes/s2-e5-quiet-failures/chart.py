"""Draws the S2 E5 charts from results/summary.json alone: no API key, no model, no network.

Run from the repository root:

    uv run python episodes/s2-e5-quiet-failures/chart.py

stale: fresh against stale index; recall at 5, current value, old value.
versions: answers giving only the old value, for B-plain, B-dated and B-latest.
scores: each question's top-1 cosine score, answerable against unanswerable, and the best
hindsight cut-off as a dashed line.
prompts: asserted answers on unanswerable questions, and the current value on answerable ones,
under P1 and P2.
scope: leaks and recall at 5 for D-none, D-post and D-pre.

A bar is acid green only when its 95% interval clears every other bar it is compared with;
otherwise nothing is, and the chart says so.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, NAVY, SLATE, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars

HERE = Path(__file__).parent
RESULTS = HERE / "results" / "summary.json"
OUT_DIR = HERE / "charts"
NOTHING_CLEARS = "No interval clears the others; nothing highlighted."


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clears(entries: list[dict], index: int) -> bool:
    """Whether one bar's interval sits wholly above, or wholly below, every other bar's."""
    me = entries[index]
    others = [e for n, e in enumerate(entries) if n != index]
    return all(me["low"] > o["high"] for o in others) or all(me["high"] < o["low"] for o in others)


def _errors(ax: Axes, style: ChartStyle, xs: list[float], entries: list[dict]) -> None:
    ax.errorbar(xs, [e["rate"] for e in entries],
                yerr=[[max(0.0, e["rate"] - e["low"]) for e in entries],
                      [max(0.0, e["high"] - e["rate"]) for e in entries]],
                fmt="none", ecolor=WHITE, elinewidth=style.line_width_pt / 2, capsize=5)
    for x, e in zip(xs, entries, strict=True):
        ax.text(x, e["high"] + 0.02, f"{e['hits']} of {e['n']}", ha="center", va="bottom",
                color=WHITE, rotation=90)


def grouped(categories: list[str], series: list[tuple[str, list[dict]]], finding):
    """Grouped bars of counts with intervals. `finding` is (series, category) or None."""

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(ax, categories=categories,
                     series=[(name, [e["rate"] for e in entries]) for name, entries in series],
                     style=style, highlight_bar=finding)
        width = 0.8 / len(series)
        for index, (_, entries) in enumerate(series):
            xs = [p - 0.4 + width * (index + 0.5) for p in range(len(categories))]
            _errors(ax, style, xs, entries)
        ax.set_ylim(0, 1.5)
        ax.set_yticks([tick / 5 for tick in range(6)])

    return draw


def _spec(name: str, units: str, summ: dict, n: str, highlighted: bool,
          extra: str = "") -> ChartSpec:
    models = f"{summ['chat_model_requested']}; {summ['embedding_model_requested']}"
    return ChartSpec(name=name, units=units, sample_size=n,
                     footnote=f"{models}.{extra}\nRun {summ['run_date_utc']}. 95% Wilson "
                              "intervals.",
                     no_highlight_note=None if highlighted else NOTHING_CLEARS)


def stale_chart(summ: dict) -> tuple:
    a = summ["A"]
    measures = [("Recall at 5", "recall"), ("Current value", "current"), ("Old value", "old")]
    series = [(name, [a[key][m] for _, m in measures]) for name, key in
              (("Fresh index", "fresh"), ("Stale index", "stale"))]
    old = [a["fresh"]["old"], a["stale"]["old"]]
    finding = (1, 2) if clears(old, 1) else None
    n = a["fresh"]["recall"]["n"]
    return (grouped([m for m, _ in measures], series, finding),
            _spec("stale", "Share of questions", summ, f"{n} revised articles",
                  finding is not None))


def versions_chart(summ: dict) -> tuple:
    b = summ["B"]
    names = ("B-plain", "B-dated", "B-latest")
    entries = [b[name]["old_only"] for name in names]
    found = next((i for i in range(len(names)) if clears(entries, i)), None)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(ax, categories=["Plain", "Dated", "Latest only"],
                     series=[("Old value only", [e["rate"] for e in entries])], style=style,
                     highlight_bar=None if found is None else (0, found))
        _errors(ax, style, [0, 1, 2], entries)
        ax.set_ylabel("Answers giving only the old value")
        ax.set_ylim(0, 1.3)
        ax.set_yticks([tick / 5 for tick in range(6)])

    n = entries[0]["n"]
    return draw, _spec("versions", "Share of questions", summ, f"{n} questions, both versions",
                       found is not None)


def scores_chart(summ: dict) -> tuple:
    scores, cut = summ["C_scores"], summ["C"]["cutoff"]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        for row, (group, colour, marker) in enumerate((("answerable", MIST, "o"),
                                                       ("unanswerable", SLATE, "s"))):
            values = scores[group]
            # A fixed jitter by position, so the same results always draw the same chart.
            ys = [row + ((n % 7) - 3) * 0.05 for n in range(len(values))]
            ax.scatter(values, ys, s=style.label_pt * 6, color=colour, marker=marker,
                       edgecolors="none", alpha=0.85)
        ax.axvline(cut["cutoff"], color=WHITE, linestyle="--", linewidth=style.line_width_pt)
        ax.text(cut["cutoff"], 1.55, f"Best cut-off {cut['cutoff']:.2f}:\n"
                f"{cut['misclassified']} of {cut['n']} wrong", ha="center", va="bottom",
                color=WHITE, bbox={"facecolor": NAVY, "edgecolor": "none", "pad": 6})
        ax.set_yticks([0, 1], labels=["Answerable", "Unanswer-\nable"])
        ax.set_ylim(-0.6, 2.3)
        ax.set_xlabel("Top-1 cosine score")
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    n = len(scores["answerable"]) + len(scores["unanswerable"])
    return draw, ChartSpec(
        name="scores", units="Cosine similarity", sample_size=f"{n} questions",
        footnote=(f"{summ['embedding_model_requested']}. Cut-off chosen with hindsight.\n"
                  f"Run {summ['run_date_utc']}."))


def prompts_chart(summ: dict) -> tuple:
    c = summ["C"]
    series = [(name, [c[name]["unanswerable_asserted_for_c3"], c[name]["answerable_current"]])
              for name in ("P1", "P2")]
    asserted = [c["P1"]["unanswerable_asserted_for_c3"], c["P2"]["unanswerable_asserted_for_c3"]]
    finding = (1, 0) if clears(asserted, 1) else None
    n = asserted[0]["n"]
    return (grouped(["Asserted,\nunanswerable", "Current value,\nanswerable"], series, finding),
            _spec("prompts", "Share of questions", summ, f"{n} of each group",
                  finding is not None, " P2 adds NOT_FOUND."))


def scope_chart(summ: dict) -> tuple:
    d = summ["D"]
    names = ("D-none", "D-post", "D-pre")
    labels = {"D-none": "No filter", "D-post": "Filter after", "D-pre": "Filter before"}
    series = [(labels[name], [d[name]["leaks"], d[name]["recall"]]) for name in names]
    leaks = [d[name]["leaks"] for name in names]
    finding = (0, 0) if clears(leaks, 0) else None
    n = leaks[0]["n"]
    return (grouped(["Leaks", "Recall at 5"], series, finding),
            _spec("scope", "Share of questions", summ, f"{n} questions, 360 entries",
                  finding is not None))


CHARTS = (stale_chart, versions_chart, scores_chart, prompts_chart, scope_chart)


def render(summ: dict | None = None, out_dir: Path = OUT_DIR) -> list[Path]:
    summ = summ if summ is not None else load()
    written = []
    for make in CHARTS:
        draw, spec = make(summ)
        written += export_chart(draw, out_dir, spec)
    return written


if __name__ == "__main__":
    for path in render():
        print(f"Written: {path}")
