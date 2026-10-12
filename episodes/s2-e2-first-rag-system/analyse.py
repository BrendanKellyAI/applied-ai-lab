"""S2 E2 analysis: claims, worked examples, charts and the first scoreboard row.

Run with `uv run lab rag analyse episodes/s2-e2-first-rag-system/config.yaml`. Reads the
committed results only, so it needs no key and makes no call.
"""

import json
from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from lab.charts import MIST, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.experiments import load_sibling
from lab.rag.analysis import (
    STAGE_ORDER,
    evidence_in_prompt,
    first,
    is_right,
    is_wrong,
    load_condition,
    lost_at_counts,
    numbers,
    recall_by_type,
)
from lab.rag.config import Episode
from lab.rag.corpus import load_library
from lab.rag.log import ItemLog
from lab.rag.scoreboard import Row, export_scoreboard, record, record_history

HERE = Path(__file__).parent
CONDITION = "baseline"
NEW_TYPES = {
    "policy_single", "policy_two_sentence", "policy_heading", "distractor", "two_part",
    "bridge", "followup", "version", "restricted_staff",
}


def worked_examples(logs: list[ItemLog]) -> dict[str, str | None]:
    """The three examples, by the rules fixed in PREREGISTRATION.md."""
    right = first(logs, lambda g: g.type == "policy_single" and is_right(g))
    missed = first(
        logs,
        lambda g: g.type == "policy_single" and not evidence_in_prompt(g)
        and g.verdict is not None and not g.verdict.correct,
    )
    misread = first(
        logs,
        lambda g: g.type in NEW_TYPES and evidence_in_prompt(g) and g.verdict is not None
        and not g.verdict.correct and not g.verdict.declined,
    )
    return {
        "right": right.item_id if right else None,
        "search_missed": missed.item_id if missed else None,
        "model_misread": misread.item_id if misread else None,
    }


# Chart labels for the item types, in reading order: the v1 search types, the policy facts,
# then the types later episodes address.
TYPE_LABELS = {
    "shared": "Shared words",
    "paraphrase": "Paraphrase",
    "identifier": "Identifier",
    "policy_single": "Policy, one sentence",
    "policy_two_sentence": "Policy, two sentences",
    "policy_heading": "Policy, needs heading",
    "distractor": "Look-alike",
    "version": "Version",
    "restricted_staff": "Staff asker",
    "two_part": "Two-part",
    "bridge": "Bridge",
    "followup": "Follow-up",
}
# What each first-lost stage means in a run with no rewrite, filter or reranker.
STAGE_LABELS = {
    "chunk": "Cut by a chunk edge",
    "search": "Not in the top 50",
    "filter": "Removed by the filter",
    "rerank": "Ranked below 5th",
    "prompt": "Declined despite passage",
    "answer": "Wrong despite passage",
    "unjudged": "Not judged",
}


def _count_labels(ax: Axes, ends: list[float], positions: list[int], text: list[str]) -> None:
    """A count beside every bar, so a zero bar still shows as a result."""
    for end, y, label in zip(ends, positions, text, strict=True):
        ax.text(end + 0.02, y, label, va="center", color=MIST)


def _recall_chart(by_type: dict[str, Any]):
    names = [t for t in TYPE_LABELS if t in by_type] + [t for t in by_type if t not in TYPE_LABELS]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax, categories=[TYPE_LABELS.get(n, n) for n in names],
            series=[("Recall at 5", [by_type[n].rate for n in names])],
            style=style, horizontal=True,
        )
        positions = [len(names) - 1 - i for i in range(len(names))]
        rates = [by_type[n].rate for n in names]
        errors = [
            [r - by_type[n].low for r, n in zip(rates, names, strict=True)],
            [by_type[n].high - r for r, n in zip(rates, names, strict=True)],
        ]
        ax.errorbar(rates, positions, xerr=errors, fmt="none", ecolor=WHITE,
                    elinewidth=style.line_width_pt, capsize=style.label_pt / 3)
        _count_labels(ax, [by_type[n].high for n in names], positions,
                      [f"{by_type[n].count} of {by_type[n].total}" for n in names])
        ax.set_xlim(0, 1.32)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])

    return draw


def _lost_chart(lost: dict[str, int]):
    stages = [s for s in STAGE_ORDER if lost.get(s)]
    total = sum(lost.values()) or 1
    shares = [lost[s] / total for s in stages]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax, categories=[STAGE_LABELS.get(s, s) for s in stages],
            series=[("Wrong answers", shares)], style=style, horizontal=True,
            value_formatter=PercentFormatter(xmax=1, decimals=0),
        )
        positions = [len(stages) - 1 - i for i in range(len(stages))]
        _count_labels(ax, shares, positions, [str(lost[s]) for s in stages])
        ax.set_xlim(0, max(shares, default=1) * 1.25)

    return draw


def analyse(episode: Episode, results: Path, *, pilot: bool) -> str:
    claims_module = load_sibling(HERE / "claims.py")
    library = load_library(episode.library)
    logs, summary = load_condition(results, CONDITION)
    k = summary["pipeline"]["prompt"]["k"]
    claims = claims_module.evaluate(logs, library, episode.config.pass_marks, k)
    after = numbers(logs, k)
    by_type = recall_by_type(logs, k)
    lost = lost_at_counts(logs)
    examples = worked_examples(logs)
    report = {
        "condition": CONDITION,
        "config_id": summary["config_id"],
        "items": len(logs),
        "numbers": after.model_dump(),
        "recall_by_type": {t: p.model_dump() for t, p in by_type.items()},
        "lost_at": dict(lost),
        "wrong_answerable": sum(1 for g in logs if is_wrong(g)),
        "cut_evidence_items": sum(
            1 for g in logs if any(t.kind == "evidence" and t.cut for t in g.spans)
        ),
        "distractor_above": sum(1 for g in logs if g.type == "distractor" and g.distractor_above),
        "claims": [c.model_dump() for c in claims],
        "worked_examples": examples,
        "models_returned": summary["models_returned"],
        "code_check_disagrees_with_judge": summary["code_check_disagrees_with_judge"],
    }
    (results / "analysis.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    charts = results / "charts"
    answerable = sum(1 for g in logs if g.answerable)
    export_chart(_recall_chart(by_type), charts, ChartSpec(
        name="recall-by-type", units="Recall at 5", sample_size=f"n = {answerable} answerable",
        no_highlight_note="No highlight: E2 measures, it does not compare",
    ))
    export_chart(_lost_chart(lost), charts, ChartSpec(
        name="where-lost", units="Share of wrong answers",
        sample_size=f"n = {report['wrong_answerable']} wrong answerable items",
        no_highlight_note="No highlight: E2 measures, it does not compare",
    ))
    row = Row(
        episode=episode.config.episode, stage_changed=None, config_before=None,
        config_after=summary["config_id"], before=None, after=after, joined=True,
        models_returned=summary["models_returned"], corpus_version=library.corpus_version,
    )
    export_scoreboard(row, charts, f"n = {len(logs)} test items")
    if not pilot:
        season = episode.folder.parents[1] / "season2"
        record(season / "scoreboard.json", row)
        record_history(season / "reference_history.yaml", {
            "episode": episode.config.episode,
            "stage_changed": None,
            "reference_before": None,
            "reference_after": summary["config_id"],
            "pass_mark": "none: the baseline sets the reference",
            "joined": True,
        })
    lines = [f"S2 E2 baseline, {len(logs)} items, config {summary['config_id']}"]
    for name, value in after.model_dump().items():
        lines.append(f"  {name}: {value['count']}/{value['total']} "
                     f"({value['low']:.0%} to {value['high']:.0%})")
    for claim in claims:
        lines.append(f"  {claim.id} {'held' if claim.held else 'FAILED'}: {claim.statement}")
    lines.append(f"  worked examples: {examples}")
    return "\n".join(lines)
