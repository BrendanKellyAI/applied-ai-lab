"""S3 E9 analysis. Run with `uv run lab rag analyse field-notes/s3-e9-model-change/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
Every comparison is against the baseline (today's system), item by item. The version arm is
read as the update you did not choose: from gpt-5.6-luna (before) to gpt-6-luna (after).
"""

from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter

from lab.charts import ChartSpec, ChartStyle, export_chart, grouped_bars
from lab.rag.compare import (
    answer_cost,
    answered_right,
    behaviour,
    citation_validity,
    flips,
    format_measures,
    handled,
    hits,
    paired,
    proportion,
    ratios,
)
from lab.rag.corpus import load_library
from lab.rag.fieldnote import (
    answer_prices,
    evidence_checker,
    interval_bars,
    kept_ratios,
    load_arms,
    pipeline_of,
    write_json,
)

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
BASELINE = "baseline"
ARMS = ("version", "provider", "provider-google")
CLAIMED = ("version", "provider")
LABELS = {
    "baseline": "gpt-6-luna (today)",
    "version": "gpt-5.6-luna (before the update)",
    "provider": "claude-haiku-5-5",
    "provider-google": "gemini-3.5-flash-lite",
}
SHORT = {
    "version": "Version update",
    "provider": "Switch to Anthropic",
    "provider-google": "Switch to Google",
}
CHURN_TIMES = 3
CITING_POINTS = 0.05
TOKENS_CHANGE = 0.25


def claim(id_: str, statement: str, held: bool, **detail) -> dict:
    return {"id": id_, "claim": statement, "held": held, **detail}


def analyse(episode, results: Path, *, pilot: bool) -> str:
    names = (BASELINE, *ARMS)
    arms = load_arms(results, names)
    if BASELINE not in arms:
        return "No baseline results"
    library = load_library(ROOT / "datasets" / "halvard")
    per_item = {n: hits(arms[n]) for n in arms}
    measures = {}
    for n, logs in arms.items():
        measures[n] = {
            "answer_model": pipeline_of(results, n)["answer"]["model"],
            "judge": pipeline_of(results, n)["judge"]["model"],
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
            "models_returned": sorted({g.answer.model_returned for g in logs if g.answer}),
        }
    changes = {}
    for n in ARMS:
        if n not in arms:
            continue
        # The version arm reads backwards in time: it is the "before".
        before, after = (
            (per_item[n], per_item[BASELINE])
            if n == "version"
            else (per_item[BASELINE], per_item[n])
        )
        answerable = {g.item_id for g in arms[BASELINE] if g.answerable}
        changes[n] = {
            "direction": f"{LABELS[n]} to {LABELS[BASELINE]}"
            if n == "version"
            else f"{LABELS[BASELINE]} to {LABELS[n]}",
            "handled": {**flips(before, after), **paired(before, after)},
            "answerable_only": flips(
                {i: v for i, v in before.items() if i in answerable},
                {i: v for i, v in after.items() if i in answerable},
            ),
        }
    prices = answer_prices(ROOT)
    totals = {n: sum(per_item[n].values()) for n in arms}
    if prices is not None:
        cost = {n: answer_cost(arms[n], *prices[measures[n]["answer_model"]]) for n in arms}
        cost_ratio = ratios(cost, totals)
    else:
        cost_ratio = kept_ratios(results / "analysis.json", "cost_per_item_handled_ratio") or {}

    base = measures[BASELINE]
    claims = []
    if all(n in changes for n in CLAIMED):
        claims = [
            claim(
                "V1",
                "A total that barely moves hides many changed answers.",
                all(
                    changes[n]["handled"]["flipped"]
                    >= CHURN_TIMES * abs(changes[n]["handled"]["net"])
                    for n in CLAIMED
                ),
                **{n: changes[n]["handled"] for n in CLAIMED},
            ),
            claim(
                "V2",
                "The prompt carries across.",
                all(
                    abs(measures[n]["citing"]["rate"] - base["citing"]["rate"]) <= CITING_POINTS
                    for n in CLAIMED
                ),
                **{n: measures[n]["citing"] for n in (BASELINE, *CLAIMED)},
            ),
            claim(
                "V3",
                "On the total, the swap looks safe.",
                all(changes[n]["handled"]["p_value"] >= 0.05 for n in CLAIMED),
                **{n: changes[n]["handled"]["p_value"] for n in CLAIMED},
            ),
            claim(
                "V4",
                "Behaviour changes even when content does not.",
                any(
                    abs(measures[n]["median_output_tokens"] / base["median_output_tokens"] - 1)
                    >= TOKENS_CHANGE
                    for n in CLAIMED
                ),
                **{n: measures[n]["median_output_tokens"] for n in (BASELINE, *CLAIMED)},
            ),
        ]
    report = {
        "episode": "s3-e9-model-change",
        "items": len(arms[BASELINE]),
        "labels": LABELS,
        "measures": measures,
        "changes": changes,
        "cost_per_item_handled_ratio": cost_ratio,
        "cost_note": "Answer calls only, from provider-reported tokens and published prices on "
        "18 October 2026; 1 is the cheapest per item handled right.",
        "claims": claims,
    }
    write_json(results / "analysis.json", report)
    if not pilot and changes:
        charts(results / "charts", measures, changes)
    lines = [f"{n}: handled {totals[n]}/{len(arms[n])}" for n in arms]
    lines += [f"{n}: {c['handled']}" for n, c in changes.items()]
    lines += [f"{c['id']} {'Held' if c['held'] else 'Failed'}: {c['claim']}" for c in claims]
    return "\n".join(lines)


def charts(out: Path, measures: dict, changes: dict) -> None:
    arms = [n for n in ARMS if n in changes]

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        grouped_bars(
            ax,
            categories=[SHORT[n] for n in arms],
            series=[
                ("Change in the total", [abs(changes[n]["handled"]["net"]) for n in arms]),
                ("Items that flipped", [changes[n]["handled"]["flipped"] for n in arms]),
            ],
            style=style,
            highlight_bar=(1, 0),
            value_formatter=StrMethodFormatter("{x:.0f}"),
        )

    export_chart(
        draw,
        out,
        ChartSpec(
            name="churn",
            units="Items (net change shown as a size)",
            sample_size="520 test items per arm",
            footnote="Flipped: right to wrong plus wrong to right",
        ),
    )
    interval_bars(
        out,
        "citing",
        rows=[(LABELS[n].split(" (")[0], measures[n]["citing"]) for n in ("baseline", *arms)],
        units="Share of non-decline answers with a parseable citation",
        sample_size="Answers that were not declines, per arm",
    )
