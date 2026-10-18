"""S3 E3 analysis. Run with `uv run lab rag analyse field-notes/s3-e3-leaderboard/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
Cost ratios need the local prices file; without it, the committed ratios are kept.
"""

import json
from itertools import combinations
from pathlib import Path

import yaml

from lab.rag.compare import (
    all_pairs,
    answer_cost,
    answered_right,
    behaviour,
    bootstrap_tau,
    citation_validity,
    distinguishable,
    format_measures,
    handled,
    hits,
    proportion,
    ratios,
    tiers,
)
from lab.rag.corpus import load_library
from lab.rag.fieldnote import (
    answer_prices,
    evidence_checker,
    incomplete,
    interval_bars,
    kept_ratios,
    load_arms,
    pipeline_of,
    ratio_bars,
    slope_chart,
    write_json,
)
from lab.rag.score import Proportion

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
FAMILIES = {
    "OpenAI": ("gpt-6-1-sol", "gpt-6-luna"),
    "Anthropic": ("claude-opus-5-5", "claude-haiku-5-5"),
    "Google": ("gemini-3-8-flash", "gemini-3-5-flash-lite"),
}
REVERSAL_GAP = 5
B3_RATIO = 5


def board() -> dict:
    return yaml.safe_load((HERE / "leaderboard.yaml").read_text(encoding="utf-8"))


def label(entry: dict) -> str:
    return entry["row"].split(" (")[0]


def claim(id_: str, statement: str, held: bool, **detail) -> dict:
    return {"id": id_, "claim": statement, "held": held, **detail}


def analyse(episode, results: Path, *, pilot: bool) -> str:
    entries = board()["models"]
    names = [e["condition"] for e in entries]
    scores = {e["condition"]: e["score"] for e in entries}
    labels = {e["condition"]: label(e) for e in entries}
    arms = load_arms(results, names)
    if set(arms) != set(names):
        return f"Missing arms: {sorted(set(names) - set(arms))}"
    gaps = incomplete(arms)
    if gaps:
        return f"Incomplete arms (items without an answer or verdict): {gaps}. No claims stated."
    library = load_library(ROOT / "datasets" / "halvard")
    per_item = {n: hits(arms[n]) for n in names}
    totals = {n: sum(per_item[n].values()) for n in names}
    pairs = all_pairs(per_item)
    grouped = tiers(totals, pairs)
    tau = bootstrap_tau(scores, per_item)

    models = {}
    for n in names:
        logs = arms[n]
        models[n] = {
            "board": scores[n],
            "setting": next(e["setting"] for e in entries if e["condition"] == n),
            "handled": proportion(logs).model_dump(),
            "answered_right": proportion(
                [g for g in logs if g.answerable], answered_right
            ).model_dump(),
            "declined": proportion([g for g in logs if not g.answerable], handled).model_dump(),
            "citation_validity": citation_validity(
                logs, evidence_checker(library, pipeline_of(results, n))
            ),
            **format_measures(logs),
            **behaviour(logs, results / n / "raw-answer.jsonl"),
            "judge": pipeline_of(results, n)["judge"]["model"],
            "code_check": Proportion.of(
                sum(1 for g in logs if g.answerable and g.code_check),
                sum(1 for g in logs if g.answerable and g.code_check is not None),
            ).model_dump(),
            "models_returned": sorted({g.answer.model_returned for g in logs if g.answer}),
        }

    prices = answer_prices(ROOT)
    analysis_path = results / "analysis.json"
    if prices is not None:
        cost = {}
        for n in names:
            model = pipeline_of(results, n)["answer"]["model"]
            cost[n] = answer_cost(arms[n], *prices[model])
        cost_ratio = ratios(cost, totals)
    else:
        cost_ratio = kept_ratios(analysis_path, "cost_per_item_handled_ratio") or {}

    reversed_pairs = []
    for a, b in combinations(names, 2):
        if scores[a] == scores[b]:
            continue
        high, low = (a, b) if scores[a] > scores[b] else (b, a)
        if totals[low] > totals[high] and distinguishable(pairs, a, b):
            reversed_pairs.append(
                {
                    "board_higher": high,
                    "halvard_higher": low,
                    "board_gap": scores[high] - scores[low],
                    "halvard_gap": totals[low] - totals[high],
                }
            )
    # B3: the board's top pick and the best-value pick in Halvard's top tier.
    top_score = max(scores.values())
    top_pick = max((n for n in names if scores[n] == top_score), key=lambda n: (totals[n], n))
    best_value = (
        min(grouped[0], key=lambda n: (cost_ratio.get(n, float("inf")), n)) if cost_ratio else None
    )
    b3_ratio = (
        round(cost_ratio[top_pick] / cost_ratio[best_value], 2)
        if best_value and top_pick in cost_ratio
        else None
    )

    family = {
        f: {
            "top": a,
            "cheapest": b,
            "handled": [totals[a], totals[b]],
            "p_holm": (pairs.get((a, b)) or pairs[(b, a)])["p_holm"],
            "distinguishable": distinguishable(pairs, a, b),
        }
        for f, (a, b) in FAMILIES.items()
    }
    claims = [
        claim(
            "B1",
            "The board's order does not predict the Halvard order.",
            tau["low"] <= 0 <= tau["high"],
            **tau,
        ),
        claim(
            "B2",
            "Within a provider, the board's top model is not distinguishable on "
            "Halvard from the cheapest.",
            sum(1 for v in family.values() if not v["distinguishable"]) >= 2,
            families=family,
        ),
        claim(
            "B3",
            "Picking by the board costs several times more per item handled right.",
            b3_ratio is not None and best_value != top_pick and b3_ratio >= B3_RATIO,
            top_pick=top_pick,
            best_value=best_value,
            ratio=b3_ratio,
        ),
        claim(
            "B4",
            "At least one pair is reversed.",
            any(r["board_gap"] >= REVERSAL_GAP for r in reversed_pairs),
            reversed=reversed_pairs,
        ),
    ]
    report = {
        "episode": "s3-e3-leaderboard",
        "items": len(next(iter(arms.values()))),
        "board": {k: v for k, v in board().items() if k != "models"},
        "models": models,
        "handled_totals": totals,
        "tiers": grouped,
        "pairs": {f"{a} vs {b}": v for (a, b), v in pairs.items()},
        "kendall_tau_b": tau,
        "cost_per_item_handled_ratio": cost_ratio,
        "cost_note": "Answer calls only, from provider-reported tokens and published prices on "
        "18 October 2026; 1 is the cheapest per item handled right. Reranking is identical "
        "across arms; judging is measurement, not cost of the system.",
        "claims": claims,
    }
    write_json(analysis_path, report)
    if not pilot:
        charts(results / "charts", names, labels, scores, totals, models, cost_ratio, best_value)
    lines = [f"{n}: board {scores[n]}, handled {totals[n]}/520" for n in names]
    lines.append(f"Tiers: {grouped}")
    lines.append(f"tau-b {tau}")
    lines += [f"{c['id']} {'Held' if c['held'] else 'Failed'}: {c['claim']}" for c in claims]
    return "\n".join(lines)


def charts(out, names, labels, scores, totals, models, cost_ratio, best_value):
    slope_chart(
        out,
        "order",
        left=scores,
        right=totals,
        labels=labels,
        left_title="Leaderboard",
        right_title="Halvard",
        units="Rank by board score and by items handled right",
        sample_size="8 models; 520 test items",
        highlight_key=best_value,
    )
    ordered = sorted(names, key=lambda n: -totals[n])
    interval_bars(
        out,
        "handled",
        rows=[(labels[n], models[n]["handled"]) for n in ordered],
        units="Share of items handled right, with 95% intervals",
        sample_size="520 test items per model",
        highlight_index=ordered.index(best_value) if best_value in ordered else None,
    )
    if cost_ratio:
        by_cost = sorted(cost_ratio, key=lambda n: cost_ratio[n])
        ratio_bars(
            out,
            "cost",
            rows=[(labels[n], cost_ratio[n]) for n in by_cost],
            units="Answer cost per item handled right, times the cheapest",
            sample_size="520 test items per model",
            highlight_index=by_cost.index(best_value) if best_value in by_cost else None,
        )


if __name__ == "__main__":  # pragma: no cover
    from lab.rag.config import load_episode

    ep = load_episode(HERE / "config.yaml")
    print(analyse(ep, HERE / "results" / "2026-10", pilot=False))
    print(json.dumps(board()["accessed"]))
