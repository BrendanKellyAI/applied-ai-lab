"""S2 E7 analysis. Run with `uv run lab rag analyse episodes/s2-e7-reranking/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

import json
from pathlib import Path

from lab.rag.analysis import below, load_condition, of_type, recall
from lab.rag.episode import REFERENCE, analyse_episode, claim, load_results, search_join

HERE = Path(__file__).parent
SHORTLISTS = ("llm-10", "llm-20")
LABELS = {"baseline": "Search order (ref)", "llm-10": "LLM rerank, top 10",
          "llm-20": "LLM rerank, top 20"}
K = 5


def choose(dev) -> str | None:
    present = [s for s in SHORTLISTS if s in dev]
    if not present:
        return None
    return max(present, key=lambda s: (recall([g for g in dev[s] if g.answerable], K).count,
                                       -SHORTLISTS.index(s)))


def above(logs) -> int:
    return sum(1 for g in of_type(logs, "distractor") if g.distractor_above)


def claims(test, full, rows, library):
    def r(name):
        return recall([g for g in test[name] if g.answerable], K)

    chosen = choose(load_results(HERE / "results-dev", list(LABELS)))
    for name in test:
        rows[name]["look_alike_above"] = above(test[name])
    found = [
        claim("K3", "A longer shortlist finds more.", r("llm-20").count >= r("llm-10").count,
              llm10=r("llm-10").model_dump(), llm20=r("llm-20").model_dump()),
    ]
    if chosen:
        found = [
            claim("K1", "Reranking puts the found passage in the top 5.",
                  below(r(REFERENCE), r(chosen)), chosen=chosen, recall=r(chosen).model_dump(),
                  reference=r(REFERENCE).model_dump()),
            claim("K2", "Reading the question with the passage beats look-alikes.",
                  above(test[chosen]) < above(test[REFERENCE]), chosen=above(test[chosen]),
                  reference=above(test[REFERENCE])),
            *found,
        ]
    if chosen in full and REFERENCE in full:
        ds = full[chosen].search.count - full[REFERENCE].search.count
        da = full[chosen].answer.count - full[REFERENCE].answer.count
        found.append(claim("K4", "Better search gives better answers.",
                           (ds > 0) == (da > 0) and (ds < 0) == (da < 0),
                           search_change=ds, answer_change=da))
    return found


def cross_encoder(results: Path) -> dict | None:
    folder = results / "cross-encoder-10"
    if not (folder / "log.jsonl").exists():
        return None
    logs, summary = load_condition(results, "cross-encoder-10")
    return {"items": len(logs), "recall_at_5": recall(logs, K).model_dump(),
            "look_alike_above": above(logs), "timing": summary.get("rerank_timing")}


def analyse(episode, results: Path, *, pilot: bool) -> str:
    report, text = analyse_episode(
        episode, results, pilot=pilot, labels=LABELS, claims=claims, join=search_join,
        stage="rerank", chart_types=("distractor", "identifier", "policy_single"),
        extra=lambda test, full, library: {
            "cross_encoder_distractor": cross_encoder(results),
            "llm_distractor": {n: {"recall_at_5": recall(of_type(test[n], "distractor"), K)
                                   .model_dump(), "look_alike_above": above(test[n])}
                               for n in test},
        },
    )
    if report.get("extra", {}).get("cross_encoder_distractor"):
        text += "\n  cross-encoder: " + json.dumps(report["extra"]["cross_encoder_distractor"])
    return text
