"""S4 E8's slide charts, from the test analysis. No API calls.

    uv run python episodes/s4-e8-can-fine-tuning-teach-facts/charts.py

One chart per measure: right on the 400 answerable questions, correct declines on the 120 the
library cannot answer, and confident wrong answers on all 520. Each is written to
results/charts/ as a slide (PNG and SVG) and an article image.
"""

import json
from pathlib import Path

from lab.rag.fieldnote import interval_bars

HERE = Path(__file__).parent
LABELS = {
    "e8-base-closed": "Small model, untuned",
    "e8-tuned-closed": "Small model, tuned on the documents",
    "e8-reference": "Season 2 retrieval system",
}
MEASURES = {
    "right": ("Right", "400 answerable per arm"),
    "declined_unanswerable": ("Correct declines", "120 unanswerable per arm"),
    "confident_wrong": ("Confident wrong answers", "520 per arm"),
}


def main() -> None:
    analysis = json.loads((HERE / "results" / "analysis-facts-test.json").read_text("utf-8"))
    for measure, (what, sample) in MEASURES.items():
        rows = sorted(
            ((LABELS[name], arm[measure]) for name, arm in analysis["arms"].items()),
            key=lambda row: -row[1]["rate"],
        )
        tuned = [label for label, _ in rows].index(LABELS["e8-tuned-closed"])
        for path in interval_bars(
            HERE / "results" / "charts",
            f"s4-e8-can-fine-tuning-teach-facts-{measure}-test",
            rows=rows,
            units=f"{what}, share (95% Wilson)",
            sample_size=sample,
            highlight_index=tuned,
        ):
            print(path)


if __name__ == "__main__":
    main()
