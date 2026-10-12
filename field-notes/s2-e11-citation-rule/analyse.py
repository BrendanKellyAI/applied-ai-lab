"""S2 E11 analysis: E9's allow-not-found run against E10's grounded-cite run, item by item.

Run with `uv run python field-notes/s2-e11-citation-rule/analyse.py`. No key, no call.
"""

import json
import statistics
from collections import Counter
from pathlib import Path

from lab.rag.analysis import below, load_condition
from lab.rag.episode import mcnemar
from lab.rag.score import Proportion

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
UNCITED = (ROOT / "episodes" / "s2-e9-building-the-prompt" / "results", "allow-not-found")
CITED = (ROOT / "episodes" / "s2-e10-grounding-and-citations" / "results", "grounded-cite")


def right(g) -> bool:
    return bool(g.verdict and g.verdict.correct and g.verdict.faithful)


def declined(logs) -> Proportion:
    group = [g for g in logs if not g.answerable]
    return Proportion.of(sum(1 for g in group if g.verdict and g.verdict.declined), len(group))


def main() -> dict:
    a, _ = load_condition(*UNCITED)
    b, _ = load_condition(*CITED)
    by_a = {g.item_id: g for g in a}
    same_passages = all(by_a[g.item_id].prompt_chunks == g.prompt_chunks for g in b)
    paired = mcnemar(a, b, right)
    na, nb = declined(a), declined(b)
    out_a = statistics.median(g.answer.output_tokens for g in a if g.answer)
    out_b = statistics.median(g.answer.output_tokens for g in b if g.answer)
    changed = Counter(g.type for g in b if right(g) != right(by_a[g.item_id]))
    import re

    uncited_citing = sum(1 for g in a if g.answer and re.search(r"\[P\d", g.answer.text))
    report = {
        "same_passages_every_item": same_passages,
        "claims": [
            {
                "id": "N1",
                "statement": "A citation rule does not change which answers are right.",
                "held": paired["p_value"] >= 0.05,
                "detail": paired,
            },
            {
                "id": "N2",
                "statement": "It does not change when the model declines.",
                "held": not below(na, nb) and not below(nb, na),
                "detail": {"uncited": na.model_dump(), "cited": nb.model_dump()},
            },
            {
                "id": "N3",
                "statement": "It makes answers longer.",
                "held": out_b >= 1.2 * out_a,
                "detail": {"uncited_median_output": out_a, "cited_median_output": out_b},
            },
        ],
        "verdict_changed_by_type": dict(changed),
        "uncited_run_citing_anyway": uncited_citing,
    }
    (HERE / "analysis.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
