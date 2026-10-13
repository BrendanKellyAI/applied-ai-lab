"""S2 E14 analysis: every wrong answer walked back to the first stage that lost its passage.

Run with `uv run python episodes/s2-e14-tracing/analyse.py`. No key, no call: it reads the
committed logs of three reference runs.
"""

import json
from collections import Counter
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from lab.charts import ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.rag.analysis import is_wrong
from lab.rag.log import ItemLog, read_log

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
RUNS = {
    "E2": ROOT / "episodes" / "s2-e2-first-rag-system" / "results" / "baseline",
    "E4": ROOT / "episodes" / "s2-e4-chunking" / "results" / "baseline",
    "Final": ROOT / "field-notes" / "s2-e12-embedding-swap" / "results" / "baseline",
}
SHORTLIST = 20
STAGES = {"chunk": "Cut", "search": "Missed", "filter": "Filtered",
          "shortlist": "Outside the shortlist", "rerank": "Ranked too low",
          "prompt": "Ignored", "answer": "Misread"}


def evidence_filtered_rank(log: ItemLog) -> int | None:
    ranks = [s.filtered for s in log.spans if s.kind == "evidence" and s.filtered is not None]
    return min(ranks) if ranks else None


def stage(log: ItemLog, reranked: bool) -> str:
    """The first lost stage, with ranking split at the reranker's shortlist."""
    lost = log.lost_at or "answer"
    if lost == "rerank" and reranked:
        rank = evidence_filtered_rank(log)
        if rank is None or rank > SHORTLIST:
            return "shortlist"
    return lost


def example(log: ItemLog, label: str) -> dict:
    spans = [s.model_dump(include={"kind", "cut", "searched", "filtered", "reranked",
                                   "in_prompt"}) for s in log.spans if s.kind == "evidence"]
    return {"stage": label, "item_id": log.item_id, "type": log.type,
            "question": log.queries[-1] if log.queries else None,
            "evidence": spans, "prompt_chunks": list(log.prompt_chunks),
            "answer": log.answer.text if log.answer else None,
            "judge_reason": log.verdict.reason if log.verdict else None}


def run_report(logs: list[ItemLog], reranked: bool) -> dict:
    wrong = [g for g in logs if is_wrong(g)]
    stages = Counter(stage(g, reranked) for g in wrong)
    return {
        "config_id": logs[0].config_id,
        "wrong": len(wrong),
        "by_stage": {s: stages.get(s, 0) for s in STAGES},
        "by_type": dict(Counter(g.type for g in wrong).most_common()),
        "leak_items": sum(1 for g in logs if g.leaks),
        "undeclined_unanswerable": dict(Counter(
            g.type for g in logs
            if not g.answerable and g.verdict and not g.verdict.declined).most_common()),
    }


def claims(final: dict, logs: list[ItemLog]) -> list[dict]:
    ranking = final["by_stage"]["shortlist"] + final["by_stage"]["rerank"]
    two = final["by_type"].get("followup", 0) + final["by_type"].get("identifier", 0)
    undeclined = final["undeclined_unanswerable"]
    absent = undeclined.get("absent_detail", 0)
    return [
        {"id": "T1", "statement": "Most of the final system's ranking losses happen before the "
         "reranker.", "held": ranking > 0 and final["by_stage"]["shortlist"] * 2 >= ranking,
         "detail": {"outside_shortlist": final["by_stage"]["shortlist"], "ranking": ranking}},
        {"id": "T2", "statement": "The final system's failures sit in two item types, "
         "follow-ups and identifiers.", "held": two >= 0.6 * final["wrong"],
         "detail": {"followup_and_identifier": two, "wrong": final["wrong"]}},
        {"id": "T3", "statement": "When it answers a question it should decline, the library "
         "usually covers the topic but not the detail.",
         "held": absent * 2 >= sum(undeclined.values()) > 0,
         "detail": {"absent_detail": absent, "undeclined": sum(undeclined.values())}},
    ]


def chart(reports: dict) -> None:
    names = ["E2", "Final"]
    labels = list(STAGES.values())

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        series = [(n, [reports[n]["by_stage"][s] for s in STAGES]) for n in names]
        grouped_bars(ax, categories=labels, series=series, style=style, horizontal=True,
                     value_formatter=FuncFormatter(lambda v, _: f"{v:.0f}"))
        ax.legend()

    export_chart(draw, HERE / "results" / "charts", ChartSpec(
        name="lost-at", units="Wrong answers, by first lost stage",
        sample_size="n = 400 answerable per run",
        footnote="E2 had an earlier judge and no reranker"))


def main() -> dict:
    logs = {n: read_log(p / "log.jsonl") for n, p in RUNS.items()}
    reports = {n: run_report(g, reranked=(n == "Final")) for n, g in logs.items()}
    final_logs = logs["Final"]
    examples = []
    for key, label in STAGES.items():
        hit = next((g for g in final_logs if is_wrong(g) and stage(g, True) == key), None)
        if hit:
            examples.append(example(hit, label))
    report = {"runs": reports, "claims": claims(reports["Final"], final_logs),
              "examples_final": examples}
    out = HERE / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8",
                                       newline="\n")
    chart(reports)
    return report


if __name__ == "__main__":
    r = main()
    print(json.dumps({"runs": r["runs"], "claims": r["claims"]}, indent=1))
