"""Shared analysis for the episodes from S2 E5 on: one call reads an episode's committed results
and writes analysis.json, the charts and the scoreboard row. Each episode supplies only its own
claims and its joining rule.

The reference condition is always named `baseline`. A condition is "full" when its items were
answered and judged; otherwise it is search-only and contributes search numbers alone.
"""

import json
import statistics
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.rag.analysis import (
    below,
    is_wrong,
    load_condition,
    lost_at_counts,
    numbers,
    of_type,
    recall,
)
from lab.rag.chunk import chunk_library, count_tokens
from lab.rag.config import Episode
from lab.rag.corpus import Library, load_library
from lab.rag.log import ItemLog
from lab.rag.score import Proportion, SeasonNumbers
from lab.rag.scoreboard import Row, export_scoreboard, record, record_history

REFERENCE = "baseline"
NUMBERS = ("search", "answer", "not_found", "leaks")


def load_results(folder: Path, names: Sequence[str]) -> dict[str, list[ItemLog]]:
    return {n: load_condition(folder, n)[0] for n in names if (folder / n / "log.jsonl").exists()}


def is_full(logs: Sequence[ItemLog]) -> bool:
    judged = all(g.verdict is not None or g.judge_error for g in logs)
    return judged and any(g.verdict for g in logs)


def condition_row(logs: Sequence[ItemLog], chunks: Mapping[str, Any], status, k: int) -> dict:
    answerable = [g for g in logs if g.answerable]
    sizes = [sum(count_tokens(chunks[c].text) for c in g.prompt_chunks) for g in logs]
    slots = [chunks[c] for g in logs for c in g.prompt_chunks]
    types = sorted({g.type for g in answerable})
    return {
        "recall": recall(answerable, k).model_dump(),
        "recall_by_type": {t: recall(of_type(logs, t), k).model_dump() for t in types},
        "leak_items": sum(1 for g in logs if g.leaks),
        "cut_items": sum(
            1 for g in answerable if any(s.kind == "evidence" and s.cut for s in g.spans)
        ),
        "superseded_slots": sum(1 for c in slots if status[(c.doc_id, c.version)] == "superseded"),
        "prompt_slots": len(slots),
        "median_prompt_tokens": statistics.median(sizes) if sizes else 0,
    }


def recall_chart(labels: Sequence[str], props: Sequence[Proportion], highlight: int | None):
    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=list(labels),
            series=[("Share", [p.rate for p in props])],
            style=style,
            horizontal=True,
            highlight_bar=None if highlight is None else (0, highlight),
        )
        positions = [len(props) - 1 - i for i in range(len(props))]
        ax.errorbar(
            [p.rate for p in props],
            positions,
            xerr=[[p.rate - p.low for p in props], [p.high - p.rate for p in props]],
            fmt="none",
            ecolor=WHITE,
            elinewidth=style.line_width_pt,
            capsize=style.label_pt / 4,
        )
        for p, y in zip(props, positions, strict=True):
            ax.text(p.high + 0.02, y, f"{p.count}/{p.total}", va="center", color=MIST)
        ax.set_xlim(0, 1.3)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])

    return draw


def best_above_reference(props: dict[str, Proportion]) -> int | None:
    """The index of the best condition if its interval sits above the reference's."""
    names = list(props)
    top = max(props[n].count for n in names)
    leaders = [i for i, n in enumerate(names) if props[n].count == top]
    if len(leaders) > 1:
        return None  # a tie at the top highlights nothing
    best = leaders[0]
    return best if below(props[REFERENCE], props[names[best]]) else None


def search_join(full: Mapping[str, SeasonNumbers]) -> dict[str, Any]:
    """The rule for stages before the prompt: search above the reference's interval, and the
    answer number not lower. Of those that pass, the higher search number joins."""
    ref = full[REFERENCE]
    passed = {
        n: v
        for n, v in full.items()
        if n != REFERENCE and below(ref.search, v.search) and v.answer.count >= ref.answer.count
    }
    joined = max(
        passed, key=lambda n: (passed[n].search.count, passed[n].answer.count), default=None
    )
    return {
        "rule": "search above the reference's interval, answer not lower",
        "passed": sorted(passed),
        "joined": joined,
    }


def mcnemar(reference: Sequence[ItemLog], other: Sequence[ItemLog], hit: Callable) -> dict:
    """Items only each condition gets right, and an exact two-sided McNemar p-value."""
    from math import comb

    ref = {g.item_id: hit(g) for g in reference}
    oth = {g.item_id: hit(g) for g in other}
    only_other = sum(1 for i in ref if i in oth and oth[i] and not ref[i])
    only_ref = sum(1 for i in ref if i in oth and ref[i] and not oth[i])
    n, low = only_other + only_ref, min(only_other, only_ref)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(low + 1)) / 2**n) if n else 1.0
    return {"only_other": only_other, "only_reference": only_ref, "p_value": p}


def analyse_episode(
    episode: Episode,
    results: Path,
    *,
    pilot: bool,
    labels: Mapping[str, str],
    claims: Callable[[dict, dict, dict, Library], list[dict]],
    join: Callable[[Mapping[str, SeasonNumbers]], dict[str, Any]],
    stage: str,
    chart_types: Sequence[str] | None = None,
    extra: Callable[[dict, dict, Library], dict] | None = None,
) -> tuple[dict[str, Any], str]:
    """Analyse an episode's committed results. `claims(test, full, rows, library)` returns the
    claim dicts; `join(full_numbers)` decides whether a full condition joins the reference."""
    library = load_library(episode.library)
    status = {(d.doc_id, d.version): d.status for d in library.documents}
    pipelines = {c.name: c.pipeline for c in episode.conditions}
    k_of = {n: p.prompt.k for n, p in pipelines.items()}
    test = load_results(results, list(pipelines))
    chunk_cache: dict[str, dict] = {}
    rows = {}
    for name, logs in test.items():
        key = json.dumps(pipelines[name].chunk.model_dump(), sort_keys=True)
        if key not in chunk_cache:
            chunk_cache[key] = {
                c.chunk_id: c for c in chunk_library(library.documents, pipelines[name].chunk)
            }
        rows[name] = {
            "label": labels.get(name, name),
            **condition_row(logs, chunk_cache[key], status, k_of[name]),
        }
    full = {n: numbers(logs, k_of[n]) for n, logs in test.items() if is_full(logs)}
    report: dict[str, Any] = {
        "items": len(test.get(REFERENCE, [])),
        "conditions": rows,
        "full": {n: v.model_dump() for n, v in full.items()},
        "lost_at": {n: dict(lost_at_counts(test[n])) for n in full},
        "wrong_answerable": {n: sum(1 for g in test[n] if is_wrong(g)) for n in full},
        "claims": claims(test, full, rows, library) if REFERENCE in test else [],
        "join": join(full) if REFERENCE in full else None,
        "paired_search": {
            n: mcnemar(
                test[REFERENCE],
                test[n],
                lambda g, k=k_of[n]: g.evidence_rank is not None and g.evidence_rank <= k,
            )
            for n in test
            if n != REFERENCE and REFERENCE in test
        },
        "paired_answer": {
            n: mcnemar(
                test[REFERENCE],
                test[n],
                lambda g: bool(g.verdict and g.verdict.correct and g.verdict.faithful),
            )
            for n in full
            if n != REFERENCE and REFERENCE in full
        },
    }
    if extra:
        report["extra"] = extra(test, full, library)
    (results / "analysis.json").write_text(
        json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8", newline="\n"
    )
    _charts(episode, results, test, rows, full, report, library, stage, pilot, chart_types, k_of)
    return report, summary_text(report)


def _charts(episode, results, test, rows, full, report, library, stage, pilot, chart_types, k_of):
    charts = results / "charts"
    names = list(rows)
    if chart_types:
        props = {n: recall(of_type(test[n], *chart_types), k_of[n]) for n in names}
        units = "Recall at 5, " + ", ".join(chart_types)
    else:
        props = {n: Proportion(**rows[n]["recall"]) for n in names}
        units = "Recall at 5"
    if REFERENCE in props:
        highlight = best_above_reference(props)
        export_chart(
            recall_chart([rows[n]["label"] for n in names], list(props.values()), highlight),
            charts,
            ChartSpec(
                name="recall",
                units=units,
                sample_size=f"n = {next(iter(props.values())).total} items",
                no_highlight_note=None
                if highlight is not None
                else "No highlight: none clears the reference alone",
            ),
        )
    if len(full) > 1:
        _numbers_chart(full, rows, charts)
        _scoreboard(episode, report, full, library, charts, stage, pilot, results)


def _numbers_chart(full, rows, charts):
    names = list(full)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        series = [
            (rows[n]["label"], [getattr(full[n], f).rate for f in NUMBERS]) for n in names[:2]
        ]
        grouped_bars(
            ax, categories=["Search", "Answer", "Not found", "Leaks"], series=series, style=style
        )
        ax.set_ylim(0, 1)

    if len(names) == 2:
        export_chart(
            draw,
            charts,
            ChartSpec(
                name="numbers",
                units="Share of items",
                sample_size="n = 520 test items",
                no_highlight_note="No highlight: see the joining rule",
            ),
        )


def _scoreboard(episode, report, full, library, charts, stage, pilot, results):
    candidates = [n for n in full if n != REFERENCE]
    joined = report["join"]["joined"]
    # An episode's join rule may name the candidate to show; otherwise the best by search.
    shown = (
        joined
        or report["join"].get("candidate")
        or max(candidates, key=lambda n: (full[n].search.count, full[n].answer.count))
    )
    summary = {
        n: json.loads((results / n / "summary.json").read_text(encoding="utf-8"))
        for n in (REFERENCE, shown)
    }
    row = Row(
        episode=episode.config.episode,
        stage_changed=stage,
        config_before=summary[REFERENCE]["config_id"],
        config_after=summary[shown]["config_id"],
        before=full[REFERENCE],
        after=full[shown],
        joined=joined is not None,
        models_returned=summary[shown]["models_returned"],
        corpus_version=library.corpus_version,
    )
    export_scoreboard(row, charts, f"n = {report['items']} test items")
    if not pilot:
        season = episode.folder.parents[1] / "season2"
        record(season / "scoreboard.json", row)
        record_history(
            season / "reference_history.yaml",
            {
                "episode": episode.config.episode,
                "stage_changed": stage,
                "reference_before": summary[REFERENCE]["config_id"],
                "reference_after": summary[joined]["config_id"]
                if joined
                else summary[REFERENCE]["config_id"],
                "pass_mark": report["join"]["rule"],
                "joined": joined is not None,
                "candidate": shown,
            },
        )


def summary_text(report: dict[str, Any]) -> str:
    lines = [f"{len(report['conditions'])} conditions, {report['items']} items"]
    for row in report["conditions"].values():
        r = row["recall"]
        lines.append(
            f"  {row['label']:<28} search {r['count']}/{r['total']}  "
            f"leak items {row['leak_items']}  prompt {row['median_prompt_tokens']:.0f}"
        )
    for name, n in report["full"].items():
        lines.append(
            f"  full {name}: " + "  ".join(f"{f} {n[f]['count']}/{n[f]['total']}" for f in NUMBERS)
        )
    for claim in report["claims"]:
        verdict = "held" if claim["held"] else "FAILED"
        lines.append(f"  {claim['id']} {verdict}: {claim['statement']}")
    if report["join"]:
        lines.append(f"  joins the reference: {report['join']['joined']}")
    return "\n".join(lines)


def claim(id_: str, statement: str, held: bool, **detail: Any) -> dict[str, Any]:
    return {"id": id_, "statement": statement, "held": bool(held), "detail": detail}
