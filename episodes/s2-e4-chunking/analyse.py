"""S2 E4 analysis: every chunker's search results, the claims, the full runs and the scoreboard.

Run with `uv run lab rag analyse episodes/s2-e4-chunking/config.yaml`. Reads committed results
only, so it needs no key and makes no call. Dev results, in `results-dev/`, are read only for
the choice of which conditions ran in full.
"""

import json
import statistics
from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import MIST, WHITE, ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.experiments import load_sibling
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
from lab.rag.corpus import load_library
from lab.rag.log import ItemLog
from lab.rag.score import Proportion
from lab.rag.scoreboard import Row, export_scoreboard, record, record_history

HERE = Path(__file__).parent
REFERENCE = "baseline"


def label(name: str, chunker: Any) -> str:
    if chunker.kind == "fixed":
        text = f"Fixed {chunker.size}" + (" +25%" if chunker.overlap else "")
        return text + (" (ref)" if name == REFERENCE else "")
    return f"Structure {chunker.max_tokens}" + (" +heads" if chunker.embed_headings else "")


def _load(folder: Path, names: list[str]) -> dict[str, list[ItemLog]]:
    return {n: load_condition(folder, n)[0] for n in names if (folder / n / "log.jsonl").exists()}


def _full(logs: list[ItemLog]) -> bool:
    judged = all(g.verdict is not None or g.judge_error for g in logs)
    return judged and any(g.verdict for g in logs)


def condition_rows(test, chunkers, library, marks, k) -> dict[str, dict[str, Any]]:
    """Per condition: recall overall, on policy items and by type; cut items; how many prompt
    slots went to superseded chunks; and the prompt's median size in tokens."""
    status = {(d.doc_id, d.version): d.status for d in library.documents}
    rows = {}
    for name, logs in test.items():
        chunks = {c.chunk_id: c for c in chunk_library(library.documents, chunkers[name])}
        sizes = [sum(count_tokens(chunks[c].text) for c in g.prompt_chunks) for g in logs]
        slots = [chunks[c] for g in logs for c in g.prompt_chunks]
        answerable = [g for g in logs if g.answerable]
        types = sorted({g.type for g in answerable})
        rows[name] = {
            "label": label(name, chunkers[name]),
            "chunks": len(chunks),
            "recall": recall(answerable, k).model_dump(),
            "policy_recall": recall(of_type(logs, *marks["policy_types"]), k).model_dump(),
            "recall_by_type": {t: recall(of_type(logs, t), k).model_dump() for t in types},
            "cut_items": sum(
                1 for g in answerable if any(s.kind == "evidence" and s.cut for s in g.spans)
            ),
            "superseded_slots": sum(
                1 for c in slots if status[(c.doc_id, c.version)] == "superseded"
            ),
            "prompt_slots": len(slots),
            "median_prompt_tokens": statistics.median(sizes),
        }
    return rows


def _bars(ax: Axes, style: ChartStyle, labels, props: list[Proportion], highlight: int | None):
    grouped_bars(ax, categories=labels, series=[("Recall at 5", [p.rate for p in props])],
                 style=style, horizontal=True,
                 highlight_bar=None if highlight is None else (0, highlight))
    positions = [len(props) - 1 - i for i in range(len(props))]
    ax.errorbar([p.rate for p in props], positions,
                xerr=[[p.rate - p.low for p in props], [p.high - p.rate for p in props]],
                fmt="none", ecolor=WHITE, elinewidth=style.line_width_pt,
                capsize=style.label_pt / 4)
    for p, y in zip(props, positions, strict=True):
        ax.text(p.high + 0.02, y, f"{p.count}/{p.total}", va="center", color=MIST)
    ax.set_xlim(0, 1.3)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])


def policy_chart(rows: dict[str, dict[str, Any]]):
    """Policy recall for every chunker. Acid green: the best, if its interval sits above the
    reference's; otherwise nothing, and the chart says so."""
    names = list(rows)
    props = [Proportion(**rows[n]["policy_recall"]) for n in names]
    best = max(range(len(names)), key=lambda i: props[i].count)
    ref = Proportion(**rows[REFERENCE]["policy_recall"])
    highlight = best if below(ref, props[best]) else None

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(ax, style, [rows[n]["label"] for n in names], props, highlight)

    note = None if highlight is not None else "No highlight: no chunker clears the reference"
    return draw, note


def heading_chart(test, chunkers, marks, k):
    """Heading-dependent facts: the reference and each structure size with and without
    headings. Nothing highlighted: the claim is a set of pairwise comparisons."""
    names = [REFERENCE] + [n for pair in marks["c3_pairs"] for n in reversed(pair)]
    props = [recall(of_type(test[n], marks["c3_heading_type"]), k) for n in names]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        _bars(ax, style, [label(n, chunkers[n]) for n in names], props, None)

    return draw


def cut_chart(claim_detail: dict[str, Any]):
    pairs = claim_detail["cut_items_by_size"]
    sizes = list(pairs)

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax, categories=[str(s) for s in sizes],
            series=[("No overlap", [pairs[s]["no_overlap"] for s in sizes]),
                    ("25% overlap", [pairs[s]["overlap"] for s in sizes])],
            style=style, value_formatter=None,
        )
        ax.yaxis.set_major_formatter("{x:.0f}")
        top = max(max(p.values()) for p in pairs.values()) or 1
        for i, s in enumerate(sizes):
            for j, key in enumerate(("no_overlap", "overlap")):
                ax.text(i - 0.2 + 0.4 * j, pairs[s][key] + top * 0.02, str(pairs[s][key]),
                        ha="center", color=MIST)
        ax.set_ylim(0, top * 1.15)

    return draw


def analyse(episode: Episode, results: Path, *, pilot: bool) -> str:
    claims = load_sibling(HERE / "claims.py")
    marks = episode.config.pass_marks
    library = load_library(episode.library)
    chunkers = {c.name: c.pipeline.chunk for c in episode.conditions}
    k = episode.conditions[0].pipeline.prompt.k
    test = _load(results, list(chunkers))
    dev = {} if pilot else _load(episode.folder / "results-dev", list(chunkers))
    rows = condition_rows(test, chunkers, library, marks, k)
    full = {n: numbers(logs, k) for n, logs in test.items() if _full(logs)}
    complete = len(test) == len(chunkers) and REFERENCE in full
    found = claims.evaluate(test, chunkers, full, marks, k) if complete else []
    report = {
        "items": len(test.get(REFERENCE, [])),
        "conditions": rows,
        "choice": (
            claims.choose_full(dev, chunkers, marks, k) if len(dev) == len(chunkers) else None
        ),
        "full": {n: v.model_dump() for n, v in full.items()},
        "lost_at": {n: dict(lost_at_counts(test[n])) for n in full},
        "wrong_answerable": {n: sum(1 for g in test[n] if is_wrong(g)) for n in full},
        "claims": [c.model_dump() for c in found],
        "join": claims.join(full) if REFERENCE in full else None,
        "paired": {n: claims.mcnemar(test[REFERENCE], test[n], k)
                   for n in full if n != REFERENCE},
    }
    (results / "analysis.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    charts = results / "charts"
    policy_items = len(of_type(test.get(REFERENCE, []), *marks["policy_types"]))
    draw, note = policy_chart(rows)
    export_chart(draw, charts, ChartSpec(
        name="policy-recall", units="Recall at 5", sample_size=f"n = {policy_items} policy items",
        no_highlight_note=note,
    ))
    if complete:
        export_chart(heading_chart(test, chunkers, marks, k), charts, ChartSpec(
            name="headings", units="Recall at 5", sample_size="n = 20 heading items",
            no_highlight_note="No highlight: the claim compares pairs",
        ))
        export_chart(cut_chart(found[1].detail), charts, ChartSpec(
            name="cut-evidence", units="Items with evidence cut", sample_size="n = 400 answerable",
            no_highlight_note="No highlight: the claim compares pairs",
        ))
        _scoreboard(episode, report, full, library, charts, pilot)
    return _summary(report, rows)


def _scoreboard(episode, report, full, library, charts, pilot) -> None:
    candidates = [n for n in full if n != REFERENCE]
    if not candidates:
        return
    joined = report["join"]["joined"]
    shown = joined or max(candidates, key=lambda n: (full[n].search.count, full[n].answer.count))
    summary_of = {n: json.loads((episode.folder / "results" / n / "summary.json").read_text(
        encoding="utf-8")) for n in (REFERENCE, shown)}
    row = Row(
        episode=episode.config.episode, stage_changed="chunk",
        config_before=summary_of[REFERENCE]["config_id"],
        config_after=summary_of[shown]["config_id"],
        before=full[REFERENCE], after=full[shown], joined=joined is not None,
        models_returned=summary_of[shown]["models_returned"],
        corpus_version=library.corpus_version,
    )
    export_scoreboard(row, charts, f"n = {report['items']} test items")
    if not pilot:
        season = episode.folder.parents[1] / "season2"
        record(season / "scoreboard.json", row)
        record_history(season / "reference_history.yaml", {
            "episode": episode.config.episode,
            "stage_changed": "chunk",
            "reference_before": summary_of[REFERENCE]["config_id"],
            "reference_after": summary_of[joined]["config_id"] if joined else
            summary_of[REFERENCE]["config_id"],
            "pass_mark": "search interval above the reference's, answer not lower",
            "joined": joined is not None,
            "candidate": shown,
        })


def _summary(report: dict[str, Any], rows: dict[str, dict[str, Any]]) -> str:
    lines = [f"S2 E4, {len(rows)} conditions"]
    for row in rows.values():
        r, p = row["recall"], row["policy_recall"]
        lines.append(f"  {row['label']:<24} all {r['count']}/{r['total']}  "
                     f"policy {p['count']}/{p['total']}  cut {row['cut_items']}  "
                     f"prompt {row['median_prompt_tokens']:.0f} tokens")
    if report["choice"]:
        lines.append(f"  chosen on dev: {report['choice']}")
    for claim in report["claims"]:
        verdict = "held" if claim["held"] else "FAILED"
        lines.append(f"  {claim['id']} {verdict}: {claim['statement']}")
    if report["join"]:
        lines.append(f"  joins the reference: {report['join']['joined']}")
    return "\n".join(lines)
