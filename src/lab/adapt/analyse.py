"""`lab adapt analyse`: score every arm, compare each with the reference arm, and chart the
primary metric. Makes no API calls: it reads the predictions and judge files `run` wrote, and
an external arm's own predictions file.

Comparisons are paired on the same items: exact McNemar on the primary metric, Holm-corrected
across the arms compared with the reference, with the per-item flips both ways. Safety recall
gets the same paired test on the safety items. Costs are ratios to the reference arm only, so
no price is published.
"""

import json
from collections.abc import Mapping
from pathlib import Path

from lab.adapt.experiment import Experiment
from lab.adapt.items import ReplyItem, TriageItem
from lab.adapt.requests import Inputs
from lab.adapt.run import arm_folder, predictions_path, read_jsonl, read_texts
from lab.adapt.score_a import score_items
from lab.adapt.score_a import summarise as summarise_a
from lab.adapt.score_b import score_replies, style_summary
from lab.adapt.score_b import summarise as summarise_b
from lab.prices import PricesFile
from lab.rag.compare import flips, holm, paired
from lab.rag.fieldnote import interval_bars

PRIMARY = {"a": "fully_right", "b": "primary"}
LABELS = {"a": "Fully right", "b": "Pass all checks and keep the facts"}


class AnalysisError(ValueError):
    """A file an arm needs is missing, so scoring it would count every item as wrong."""


def _token_totals(rows: list[dict]) -> dict[str, float]:
    n = len(rows) or 1
    total_in = sum(r.get("input_tokens") or 0 for r in rows)
    total_out = sum(r.get("output_tokens") or 0 for r in rows)
    return {
        "calls": len(rows),
        "input_tokens": total_in,
        "cached_input_tokens": sum(r.get("cached_input_tokens") or 0 for r in rows),
        "output_tokens": total_out,
        "mean_input_tokens": round(total_in / n, 1),
        "mean_output_tokens": round(total_out / n, 1),
    }


def _cost(tokens: Mapping[str, float], experiment: Experiment, arm: str, prices) -> float | None:
    spec = experiment.arm(arm)
    if spec.external or prices is None:
        return None
    model = experiment.model_for(spec)
    price = prices.price_for(model.provider, model.model)
    if price is None or price.input is None or price.output is None:
        return None
    cached = tokens.get("cached_input_tokens", 0)
    cached_rate = price.cached_input if price.cached_input is not None else price.input
    return (
        (tokens["input_tokens"] - cached) * price.input
        + cached * cached_rate
        + tokens["output_tokens"] * price.output
    )


def _required(path: Path, what: str) -> Path:
    if not path.exists():
        raise AnalysisError(f"{what} is missing: {path}. Run or record it first.")
    return path


def _hits(experiment: Experiment, inputs: Inputs, arm: str) -> tuple[dict, dict[str, bool], dict]:
    """An arm's summary, its per-item primary hits, and its per-item safety flags."""
    texts = read_texts(_required(predictions_path(experiment, arm), f"arm {arm}'s predictions"))
    if experiment.task == "a":
        items = [i for i in inputs.items if isinstance(i, TriageItem)]
        scores = score_items(items, texts, inputs.definitions)
        summary = summarise_a(items, scores, inputs.definitions)
        flagged = {s.id: s.flagged for s in scores if s.safety_item}
        return summary, {s.id: s.fully_right for s in scores}, flagged
    replies = [i for i in inputs.items if isinstance(i, ReplyItem)]
    folder = arm_folder(experiment, arm)
    facts = read_texts(_required(folder / f"facts-{experiment.split}.jsonl", f"{arm}'s facts"))
    scores_b = score_replies(replies, texts, facts)
    summary = summarise_b(scores_b)
    if arm != experiment.reference:
        style_path = _required(folder / f"style-{experiment.split}.jsonl", f"{arm}'s style")
        style = read_texts(style_path)
        summary["style_against_reference"] = style_summary(replies, style)
    return summary, {s.id: s.primary for s in scores_b}, {}


def analyse(experiment: Experiment, inputs: Inputs, prices: PricesFile | None) -> dict:
    arms: dict[str, dict] = {}
    hits: dict[str, dict[str, bool]] = {}
    flagged: dict[str, dict[str, bool]] = {}
    for arm in experiment.arms:
        summary, hits[arm.name], flagged[arm.name] = _hits(experiment, inputs, arm.name)
        rows = read_jsonl(predictions_path(experiment, arm.name))
        summary["tokens"] = _token_totals(rows)
        # Items with no reply are scored wrong; the count says how many there were.
        summary["items_without_reply"] = len(inputs.items) - len(
            {r["id"] for r in rows if r.get("text") is not None} & {i.id for i in inputs.items}
        )
        arms[arm.name] = summary
    comparisons = _compare(experiment, hits, flagged)
    ratios = _cost_ratios(experiment, arms, prices)
    return {
        "episode": experiment.episode,
        "task": experiment.task,
        "split": experiment.split,
        "items": len(inputs.items),
        "reference": experiment.reference,
        "primary_metric": PRIMARY[experiment.task],
        "arms": arms,
        "comparisons": comparisons,
        "cost_ratios": ratios,
        "cost_note": (
            "Answer calls only, as multiples of the reference arm; judge calls are measurement "
            "and are left out. Cached input is priced at the cached rate where one is known. "
            "External (tuned) arms run on Colab and have no API cost."
        ),
    }


def _compare(
    experiment: Experiment,
    hits: Mapping[str, Mapping[str, bool]],
    flagged: Mapping[str, Mapping[str, bool]],
) -> dict[str, dict]:
    ref = experiment.reference
    others = [a.name for a in experiment.arms if a.name != ref]
    out = {
        name: {**paired(hits[name], hits[ref]), **flips(hits[ref], hits[name])} for name in others
    }
    adjusted = holm({name: out[name]["p_value"] for name in others})
    for name in others:
        out[name]["p_holm"] = adjusted[name]
        if flagged[ref]:
            safety = paired(flagged[name], flagged[ref])
            out[name]["safety_recall"] = {**safety, **flips(flagged[ref], flagged[name])}
    return out


def _cost_ratios(
    experiment: Experiment, arms: Mapping[str, dict], prices: PricesFile | None
) -> dict[str, dict]:
    """Running cost per item and per primary hit, as multiples of the reference arm's."""
    metric = PRIMARY[experiment.task]
    costs = {name: _cost(s["tokens"], experiment, name, prices) for name, s in arms.items()}
    ref_cost = costs.get(experiment.reference)
    ref_hits = arms[experiment.reference][metric]["count"]
    out: dict[str, dict] = {}
    for name, cost in costs.items():
        if cost is None or not ref_cost:
            out[name] = {"per_item": None, "per_primary_hit": None}
            continue
        hits = arms[name][metric]["count"]
        per_hit = (cost / hits) / (ref_cost / ref_hits) if hits and ref_hits else None
        out[name] = {
            "per_item": round(cost / ref_cost, 3),
            "per_primary_hit": round(per_hit, 3) if per_hit is not None else None,
        }
    return out


def write_analysis(experiment: Experiment, result: dict, charts: bool = True) -> Path:
    out = experiment.results / f"analysis-task-{experiment.task}-{experiment.split}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if charts:
        _chart(experiment, result)
    return out


def _chart(experiment: Experiment, result: dict) -> list[Path]:
    metric = result["primary_metric"]
    rows = sorted(
        ((name, arm[metric]) for name, arm in result["arms"].items()),
        key=lambda row: -row[1]["rate"],
    )
    return interval_bars(
        experiment.results / "charts",
        f"{experiment.episode}-{metric}-{experiment.split}",
        rows=rows,
        units=f"{LABELS[experiment.task]}, share of items, 95% Wilson interval",
        sample_size=f"{result['items']} {experiment.split} items per arm",
        highlight_index=0,
    )
