"""S4 E10's slide charts, from the regression analysis. No API calls.

    uv run python episodes/s4-e10-what-does-tuning-break/charts.py

One chart per check: general ability (120 Season 1 items), format bleed (100 ordinary
requests) and declines (120 unanswerable questions with the reference system's prompt). Each is
written to results/charts/ as a slide (PNG and SVG) and an article image. The reply writer is
highlighted: it is the model whose habits leaked.
"""

import json
from pathlib import Path

from lab.rag.fieldnote import interval_bars

HERE = Path(__file__).parent
LABELS = {
    "e10-base": "Small model, untuned",
    "e10-tuned-triage": "Tuned for triage (E5)",
    "e10-tuned-replies": "Tuned for replies (E7)",
}
CHECKS = {
    "general": ("Right", "120 items each"),
    "bleed": ("Tuned format", "100 requests each"),
    "declines": ("Declined", "120 unanswerable each"),
}


def main() -> None:
    analysis = json.loads((HERE / "results" / "analysis-regression.json").read_text("utf-8"))
    names = list(LABELS)
    for check, (what, sample) in CHECKS.items():
        rows = [(LABELS[name], analysis["arms"][name]["checks"][check]) for name in names]
        for path in interval_bars(
            HERE / "results" / "charts",
            f"s4-e10-what-does-tuning-break-{check}",
            rows=rows,
            units=f"{what}, share (95% Wilson)",
            sample_size=sample,
            highlight_index=names.index("e10-tuned-replies"),
        ):
            print(path)


if __name__ == "__main__":
    main()
