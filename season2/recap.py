"""S2 E16 recap chart: the four season numbers, E2's baseline against the final reference system.

Run with `uv run python season2/recap.py`. No key, no call: it reads `scoreboard.json` and the
final reference run (E12's baseline, `0294479ba987`).
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import ChartSpec, ChartStyle, export_chart, grouped_bars

HERE = Path(__file__).parent
NUMBERS = {"search": "Search: right passage in top 5", "answer": "Answer: right answer",
           "not_found": "Not found: declines", "leaks": "Leaks: items leaking"}


def main() -> dict:
    rows = json.loads((HERE / "scoreboard.json").read_text(encoding="utf-8"))
    first = next(r for r in rows if r["episode"] == "s2-e2-first-rag-system")["after"]
    final = next(r for r in rows if r["episode"] == "s2-e12-embedding-swap")["before"]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(ax, categories=list(NUMBERS.values()), style=style, horizontal=True,
                     series=[("E2 baseline", [first[k]["rate"] for k in NUMBERS]),
                             ("Final system", [final[k]["rate"] for k in NUMBERS])])
        ax.legend(loc="lower right")

    export_chart(draw, HERE / "charts", ChartSpec(
        name="recap", units="Share of items", sample_size="400 answerable, 120 unanswerable, "
        "480 for leaks", footnote="E2 used a different answer model and judge"))
    summary = {"e2": {k: first[k]["count"] for k in NUMBERS},
               "final": {k: final[k]["count"] for k in NUMBERS}}
    (HERE / "charts" / "recap.json").write_text(json.dumps(summary, indent=1) + "\n",
                                                encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    print(main())
