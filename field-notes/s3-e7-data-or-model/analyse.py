"""S3 E7 analysis. Run with `uv run lab rag analyse field-notes/s3-e7-data-or-model/config.yaml`.

Reads committed results only; no key, no call. The claims and the title rule are those in
PREREGISTRATION.md. Cost ratios need the local prices file; without it the committed ratios
are kept.
"""

import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from lab.charts import ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.rag.compare import answer_cost, hits, paired, proportion, ratios
from lab.rag.fieldnote import answer_prices, kept_ratios, load_arms, pipeline_of, write_json

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PIPELINES = {"p0": "P0 Start", "p1": "P1 Data fixes", "p2": "P2 Final"}
MODELS = {"small": "gpt-6-luna (small)", "large": "gpt-6.1-sol (large)"}
CELLS = [f"{p}-{m}" for p in PIPELINES for m in MODELS]


def claim(id_: str, statement: str, held: bool, **detail) -> dict:
    return {"id": id_, "claim": statement, "held": held, **detail}


def numbers(results: Path, cell: str) -> dict:
    summary = json.loads((results / cell / "summary.json").read_text(encoding="utf-8"))
    return {k: summary["numbers"][k] for k in ("answer", "not_found", "leaks")}


def analyse(episode, results: Path, *, pilot: bool) -> str:
    arms = load_arms(results, CELLS)
    if set(arms) != set(CELLS):
        return f"Missing cells: {sorted(set(CELLS) - set(arms))}"
    per_item = {c: hits(arms[c]) for c in CELLS}
    totals = {c: sum(per_item[c].values()) for c in CELLS}
    cells = {
        c: {
            **numbers(results, c),
            "handled": proportion(arms[c]).model_dump(),
            "config_id": json.loads((results / c / "summary.json").read_text("utf-8"))["config_id"],
            "models_returned": sorted({g.answer.model_returned for g in arms[c] if g.answer}),
        }
        for c in CELLS
    }
    prices = answer_prices(ROOT)
    if prices is not None:
        cost = {
            c: answer_cost(arms[c], *prices[pipeline_of(results, c)["answer"]["model"]])
            for c in CELLS
        }
        cost_ratio = ratios(cost, totals)
    else:
        cost_ratio = kept_ratios(results / "analysis.json", "cost_per_item_handled_ratio") or {}

    d1 = paired(per_item["p2-small"], per_item["p0-large"])
    d2 = paired(per_item["p1-small"], per_item["p0-small"])
    gain_p0 = totals["p0-large"] - totals["p0-small"]
    gain_p2 = totals["p2-large"] - totals["p2-small"]
    data_gain = totals["p1-small"] - totals["p0-small"]
    whole_gain = totals["p2-small"] - totals["p0-small"]
    share = data_gain / whole_gain if whole_gain else None
    claims = [
        claim(
            "D1",
            "The small model on the final system beats the large model on the naive one.",
            totals["p2-small"] > totals["p0-large"] and d1["p_value"] < 0.05,
            p2_small=totals["p2-small"],
            p0_large=totals["p0-large"],
            **d1,
        ),
        claim(
            "D2",
            "Data work alone buys a real gain.",
            totals["p1-small"] > totals["p0-small"] and d2["p_value"] < 0.05,
            p1_small=totals["p1-small"],
            p0_small=totals["p0-small"],
            **d2,
        ),
        claim(
            "D3",
            "The bigger model adds less on a better system.",
            gain_p2 < gain_p0,
            large_gain_on_p0=gain_p0,
            large_gain_on_p2=gain_p2,
            large_gain_on_p1=totals["p1-large"] - totals["p1-small"],
        ),
    ]
    title = {
        "rule": "Better data if P0 to P1 (small) gives at least half of P0 to P2 (small)",
        "data_gain": data_gain,
        "whole_gain": whole_gain,
        "share": round(share, 3) if share is not None else None,
        "title": "Better data or a bigger model?"
        if share is not None and share >= 0.5
        else "Better retrieval or a bigger model?",
    }
    report = {
        "episode": "s3-e7-data-or-model",
        "items": len(arms["p0-small"]),
        "cells": cells,
        "handled_totals": totals,
        "cost_per_item_handled_ratio": cost_ratio,
        "cost_note": "Answer calls only, from provider-reported tokens and published prices on "
        "18 October 2026; 1 is the cheapest per item handled right. P2 adds a reranker call "
        "to gpt-6-luna per item for both models, not counted here.",
        "claims": claims,
        "title_rule": title,
        "leaks_note": "Leaks are set by the pipeline before the model sees the prompt, so they "
        "are identical across the two models by construction.",
    }
    write_json(results / "analysis.json", report)
    if not pilot:
        charts(results / "charts", cells)
    lines = [
        f"{c}: handled {totals[c]}/520, answer {cells[c]['answer']['count']}/400, "
        f"declined {cells[c]['not_found']['count']}/120, leaks {cells[c]['leaks']['count']}/480"
        for c in CELLS
    ]
    lines += [f"{c['id']} {'Held' if c['held'] else 'Failed'}: {c['claim']}" for c in claims]
    lines.append(f"Title: {title['title']} (share {title['share']})")
    return "\n".join(lines)


def charts(out: Path, cells: dict) -> None:
    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=list(PIPELINES.values()),
            series=[
                (MODELS[m], [cells[f"{p}-{m}"]["answer"]["rate"] for p in PIPELINES])
                for m in MODELS
            ],
            style=style,
            highlight_bar=(0, 2),
        )
        ax.set_ylim(0, 1)

    export_chart(
        draw,
        out,
        ChartSpec(
            name="grid",
            units="Share of answerable questions answered right",
            sample_size="400 answerable test items per cell",
            footnote="The large model costs 20 times the small per token",
        ),
    )

    def leaks(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=list(PIPELINES.values()),
            series=[
                (MODELS[m], [cells[f"{p}-{m}"]["leaks"]["rate"] for p in PIPELINES]) for m in MODELS
            ],
            style=style,
        )

    export_chart(
        leaks,
        out,
        ChartSpec(
            name="leaks",
            units="Share of public questions with a staff-only passage in the prompt",
            sample_size="480 public test items per cell",
            footnote="Set by the pipeline, before any model reads the prompt",
        ),
    )
