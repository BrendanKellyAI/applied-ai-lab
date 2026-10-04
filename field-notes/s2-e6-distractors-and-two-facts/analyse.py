"""Scores the S2 E6 results, evaluates the pre-registered claims, and builds the charts.

Run through the harness, which needs no API key:

    uv run lab analyse field-notes/s2-e6-distractors-and-two-facts/config.yaml

The fact sets come from the committed results/dataset_manifest.json, so the analysis needs only
committed files, not the Gutenberg text. It writes, beside the records it reads:

- summary.csv: one row per scored call
- wrong_answers.csv: every incorrect reply, with its type, for a manual read
- summary.json: every figure the README quotes
- charts/: the four charts, at slide and article size
"""

import csv
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean

from lab.config import ExperimentConfig
from lab.experiments import load_sibling
from lab.raw_log import RunRecord, latest_successful

HERE = Path(__file__).parent
BUILD = load_sibling(HERE / "build_dataset.py")
SCORING = load_sibling(HERE / "scoring.py")
CLAIMS = load_sibling(HERE / "claims.py")
FIGURES = load_sibling(HERE / "figures.py")

SUMMARY_COLUMNS = (
    "model",
    "shape",
    "context_length_tokens",
    "item",
    "bridge_first",
    "correct",
    "type",
    "truncated",
    "also_names_distractor",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "finish_reason",
    "model_returned",
)
WRONG_COLUMNS = (
    "model",
    "shape",
    "context_length_tokens",
    "item",
    "identifier",
    "expected",
    "reply",
    "type",
    "matched",
    "matched_role",
    "truncated",
    "finish_reason",
)
# Phrases providers use when a prompt is longer than the model accepts.
TOO_LONG = ("too long", "maximum context", "context length", "context_length", "too many tokens")


class AnalysisError(RuntimeError):
    """The results cannot be analysed."""


@dataclass(frozen=True)
class Scored:
    record: RunRecord
    shape: str
    length: int
    item: int
    verdict: object  # scoring.Verdict

    @property
    def model(self) -> str:
        return self.record.model_label


def _fact_sets(folder: Path) -> tuple:
    manifest = BUILD.load_manifest(folder)
    if manifest is None:
        raise AnalysisError(
            f"No {BUILD.MANIFEST_PATH} in {folder}. Build the dataset first: "
            "uv run python field-notes/s2-e6-distractors-and-two-facts/build_dataset.py"
        )
    return BUILD.fact_sets_from(manifest), manifest


def score_records(
    records: Sequence[RunRecord], facts: Sequence, config: ExperimentConfig
) -> list[Scored]:
    """Score every successful call in the run. Pilot calls outside the run's subset (the
    16,000-token pilot calls) are left out, so every cell holds the same items."""
    scored = []
    for record in latest_successful(list(records)).values():
        length, item = int(record.cell["context_length_tokens"]), int(record.cell["item"])
        if not BUILD.in_run(config, length, item):
            continue
        shape = str(record.cell["shape"])
        fact = facts[int(record.cell["item"])]
        verdict = SCORING.classify(
            record.result.text, record.result.finish_reason, fact, shape, BUILD
        )
        scored.append(
            Scored(
                record=record,
                shape=shape,
                length=int(record.cell["context_length_tokens"]),
                item=int(record.cell["item"]),
                verdict=verdict,
            )
        )
    return sorted(
        scored,
        key=lambda s: (s.model, BUILD.SHAPES.index(s.shape), s.length, s.item),
    )


def cell_counts(scored: Sequence[Scored], models: Sequence[str], items: int):
    tallies: dict[tuple[str, str, int], list[int]] = defaultdict(lambda: [0, 0])
    for s in scored:
        tally = tallies[(s.model, s.shape, s.length)]
        tally[0] += int(s.verdict.correct)
        tally[1] += 1
    counts = {key: CLAIMS.Count(correct, trials) for key, (correct, trials) in tallies.items()}
    return CLAIMS.Cells(counts, models, items)


def wrong_by_shape(scored: Sequence[Scored]) -> dict[str, dict[str, int]]:
    """Wrong replies by shape and type, all lengths and models pooled."""
    table = {shape: dict.fromkeys(SCORING.WRONG_TYPES, 0) for shape in BUILD.SHAPES}
    for s in scored:
        if not s.verdict.correct:
            table[s.shape][s.verdict.type] += 1
    return table


def order_counts(scored: Sequence[Scored], facts: Sequence) -> dict:
    """Bridge first against answer first, in the two-fact shapes: descriptive only."""
    table: dict[str, dict] = {}
    for shape in sorted(BUILD.TWO_FACT_SHAPES, key=BUILD.SHAPES.index):
        for order, first in (("bridge first", True), ("answer first", False)):
            chosen = [s for s in scored if s.shape == shape and facts[s.item].bridge_first == first]
            for length in sorted({s.length for s in chosen}):
                at = [s for s in chosen if s.length == length]
                count = CLAIMS.Count(sum(s.verdict.correct for s in at), len(at))
                table.setdefault(shape, {}).setdefault(order, {})[str(length)] = count.to_json()
            count = CLAIMS.Count(sum(s.verdict.correct for s in chosen), len(chosen))
            table.setdefault(shape, {}).setdefault(order, {})["all"] = count.to_json()
    return table


def _per_model_tokens(scored: Sequence[Scored], manifest: dict) -> dict:
    """Provider-reported input tokens against the o200k_base document length, by length."""
    o200k = {
        (d["item"], d["shape"], d["context_length_tokens"]): d["actual_tokens"]
        for d in manifest["documents"]
    }
    table: dict[str, dict] = {}
    for model in sorted({s.model for s in scored}):
        mine = [s for s in scored if s.model == model]
        results = [s.record.result for s in mine]
        by_length = {}
        for length in sorted({s.length for s in mine}):
            at = [s for s in mine if s.length == length]
            reported = sum(s.record.result.input_tokens for s in at)
            documents = sum(o200k[(s.item, s.shape, s.length)] for s in at)
            by_length[str(length)] = {
                "calls": len(at),
                "provider_input_tokens": reported,
                "o200k_document_tokens": documents,
                "ratio": round(reported / documents, 3) if documents else None,
                "max_provider_input_tokens": max(s.record.result.input_tokens for s in at),
            }
        reasoning = [r.reasoning_tokens for r in results if r.reasoning_tokens is not None]
        table[model] = {
            "calls": len(results),
            "input_tokens": sum(r.input_tokens for r in results),
            "cached_input_tokens": sum(r.cached_input_tokens or 0 for r in results),
            "output_tokens": sum(r.output_tokens for r in results),
            "max_output_tokens_per_call": max(r.output_tokens for r in results),
            "mean_output_tokens_per_call": round(fmean(r.output_tokens for r in results), 2),
            "reasoning_tokens_reported_on": len(reasoning),
            "reasoning_tokens": sum(reasoning),
            "models_returned": sorted({r.model_returned for r in results}),
            "by_length": by_length,
        }
    return table


def _failures(records: Sequence[RunRecord]) -> list[dict]:
    """Calls with no successful result. A prompt the provider rejects as too long is flagged."""
    succeeded = set(latest_successful(list(records)))
    failed: dict[str, RunRecord] = {}
    for record in records:
        if record.result is None and record.call_id not in succeeded:
            failed[record.call_id] = record
    return [
        {
            "model": r.model_label,
            **r.cell,
            "error": r.error,
            "too_long": any(phrase in (r.error or "").lower() for phrase in TOO_LONG),
        }
        for r in failed.values()
    ]


def _wrong_row(s: Scored, facts: Sequence) -> dict:
    fact = facts[s.item]
    return {
        "model": s.model,
        "shape": s.shape,
        "context_length_tokens": s.length,
        "item": s.item,
        "identifier": fact.identifier,
        "expected": BUILD.expected(fact, s.shape),
        "reply": s.record.result.text,
        "type": s.verdict.type,
        "matched": s.verdict.matched,
        "matched_role": s.verdict.matched_role,
        "truncated": s.verdict.truncated,
        "finish_reason": s.record.result.finish_reason,
    }


def _summary_row(s: Scored, facts: Sequence) -> dict:
    result = s.record.result
    return {
        "model": s.model,
        "shape": s.shape,
        "context_length_tokens": s.length,
        "item": s.item,
        "bridge_first": facts[s.item].bridge_first,
        "correct": s.verdict.correct,
        "type": s.verdict.type,
        "truncated": s.verdict.truncated,
        "also_names_distractor": s.verdict.also_names_distractor,
        "input_tokens": result.input_tokens,
        "cached_input_tokens": result.cached_input_tokens,
        "output_tokens": result.output_tokens,
        "reasoning_tokens": result.reasoning_tokens,
        "finish_reason": result.finish_reason,
        "model_returned": result.model_returned,
    }


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def _cells_json(cells, lengths: Sequence[int]) -> dict:
    by_model = {
        model: {
            shape: {
                str(length): count.to_json()
                for length in lengths
                if (count := cells.model(model, shape, length)) is not None
            }
            for shape in BUILD.SHAPES
        }
        for model in cells.models
    }
    pooled = {
        shape: {
            str(length): count.to_json()
            for length in lengths
            if (count := cells.pooled(shape, length)) is not None
        }
        for shape in BUILD.SHAPES
    }
    return {"by_model": by_model, "pooled": pooled}


def _grid_complete(cells, lengths: Sequence[int]) -> bool:
    return all(cells.complete(shape, length) for shape in BUILD.SHAPES for length in lengths)


def _charts(cells, wrong, lengths, out_dir: Path) -> tuple[list[Path], dict]:
    if not _grid_complete(cells, lengths):
        return [], {}
    calls = cells.items * len(lengths) * len(BUILD.SHAPES) * len(cells.models)
    highlights = {
        "shapes-128k": FIGURES.lowest_shape_clearing_single(cells),
        "wrong-types": FIGURES.distractor_leads(wrong),
        "models-hardest": FIGURES.lowest_model_clearing_highest(cells),
    }
    written = [
        *FIGURES.shapes_chart(cells, out_dir),
        *FIGURES.wrong_types_chart(wrong, SCORING.WRONG_TYPES, out_dir, calls),
        *FIGURES.models_chart(cells, out_dir),
    ]
    # The length chart needs more than one length; the reduced run has only 128,000.
    if FIGURES.SHORTEST in lengths and FIGURES.LONGEST in lengths:
        highlights["length-hardest"] = FIGURES.largest_drop_model(cells, lengths)
        written += FIGURES.length_chart(cells, lengths, out_dir)
    return written, highlights


def _outside_run(records: Sequence[RunRecord], facts: Sequence, config: ExperimentConfig) -> list:
    """Pilot calls outside the run's subset, scored by the same rule but kept out of every claim."""
    rows = []
    for record in latest_successful(list(records)).values():
        length, item = int(record.cell["context_length_tokens"]), int(record.cell["item"])
        if BUILD.in_run(config, length, item):
            continue
        shape = str(record.cell["shape"])
        verdict = SCORING.classify(
            record.result.text, record.result.finish_reason, facts[item], shape, BUILD
        )
        rows.append(
            {
                "model": record.model_label,
                "shape": shape,
                "length": length,
                "item": item,
                "correct": verdict.correct,
                "type": verdict.type,
                "matched_role": verdict.matched_role,
                "reply": record.result.text,
            }
        )
    return sorted(rows, key=lambda row: (row["model"], BUILD.SHAPES.index(row["shape"])))


def _run_window(scored: Sequence[Scored]) -> dict:
    stamps = sorted(s.record.result.timestamp_utc for s in scored)
    return {"first_result_utc": stamps[0], "last_result_utc": stamps[-1]} if stamps else {}


def build_summary(config: ExperimentConfig, folder: Path, records: Sequence[RunRecord]) -> tuple:
    facts, manifest = _fact_sets(folder)
    scored = score_records(records, facts, config)
    if not scored:
        raise AnalysisError(
            "These results contain no successful calls, so there is nothing to score."
        )
    models = [model.display_label for model in config.models]
    lengths = BUILD.run_lengths(config)
    items = BUILD.run_items(config)
    cells = cell_counts(scored, models, len(items))
    wrong = wrong_by_shape(scored)
    distractor_replies = sum(counts[SCORING.DISTRACTOR] for counts in wrong.values())
    claims = CLAIMS.evaluate(cells, lengths, distractor_replies, config.parameters["pass_marks"])
    roles = Counter(
        s.verdict.matched_role.split("(")[-1].rstrip(")")
        for s in scored
        if s.verdict.type == SCORING.DISTRACTOR and "(" in s.verdict.matched_role
    )
    return (
        {
            "experiment": config.experiment,
            "scored_calls": len(scored),
            "planned_calls": len(items) * len(lengths) * len(BUILD.SHAPES) * len(models),
            "run_lengths_tokens": lengths,
            "run_items": items,
            "pilot_calls_outside_run": _outside_run(records, facts, config),
            "grid_complete": _grid_complete(cells, lengths),
            "run_window": _run_window(scored),
            "dataset": {
                "documents": len(manifest["documents"]),
                "max_length_deviation_percent": manifest["max_length_deviation_percent"],
                "max_position_deviation_points": manifest["max_position_deviation_points"],
                "length_tolerance_percent": config.parameters["length_tolerance_percent"],
                "position_tolerance_points": config.parameters["position_tolerance_points"],
            },
            "accuracy": _cells_json(cells, lengths),
            "claims": [asdict(claim) for claim in claims],
            "wrong_by_shape": wrong,
            "wrong_by_model": {
                model: dict(
                    Counter(
                        s.verdict.type for s in scored if s.model == model and not s.verdict.correct
                    )
                )
                for model in models
            },
            "distractor_replies_by_edit_kind": dict(roles),
            "correct_but_also_named_distractor": sum(
                s.verdict.also_names_distractor for s in scored
            ),
            "truncated": [
                {"model": s.model, "shape": s.shape, "length": s.length, "item": s.item}
                for s in scored
                if s.verdict.truncated
            ],
            "order": order_counts(scored, facts),
            "tokens": _per_model_tokens(scored, manifest),
            "failures": _failures(records),
        },
        scored,
        cells,
        wrong,
        facts,
    )


def _report(summary: dict, models: Sequence[str]) -> list[str]:
    lines = [
        f"{summary['experiment']}: {summary['scored_calls']} of {summary['planned_calls']} "
        "planned calls scored.",
        "",
        "Pooled accuracy by shape and length (three models):",
    ]
    for shape, by_length in summary["accuracy"]["pooled"].items():
        cells = ", ".join(
            f"{length}: {c['correct']}/{c['trials']} ({c['wilson_low']:.0%}-{c['wilson_high']:.0%})"
            for length, c in by_length.items()
        )
        lines.append(f"  {shape:<22} {cells or '-'}")
    lines += ["", "By model:"]
    for model in models:
        for shape, by_length in summary["accuracy"]["by_model"][model].items():
            cells = ", ".join(
                f"{length}: {c['correct']}/{c['trials']}" for length, c in by_length.items()
            )
            lines.append(f"  {model:<18} {shape:<22} {cells or '-'}")
    lines += ["", "Claims:"]
    lines += [f"  {c['id']}: {c['verdict']}. {c['evidence']}" for c in summary["claims"]]
    lines += ["", "Wrong replies by shape and type:"]
    for shape, counts in summary["wrong_by_shape"].items():
        lines.append(f"  {shape:<22} " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    truncated = summary["truncated"]
    lines += ["", f"Truncated replies: {len(truncated)}" + (f" {truncated}" if truncated else "")]
    lines += ["", "Tokens per model:"]
    for model, t in summary["tokens"].items():
        ratios = ", ".join(f"{k}: x{v['ratio']}" for k, v in t["by_length"].items())
        lines.append(
            f"  {model}: reasoning {t['reasoning_tokens']} (reported on "
            f"{t['reasoning_tokens_reported_on']} of {t['calls']}), output max "
            f"{t['max_output_tokens_per_call']} per call; input vs o200k {ratios}"
        )
    failures = summary["failures"]
    if failures:
        too_long = [f for f in failures if f["too_long"]]
        lines += ["", f"{len(failures)} call(s) failed and are not scored."]
        if too_long:
            lines.append(
                f"STOP: {len(too_long)} prompt(s) rejected as too long. These are errors, not "
                "wrong answers. Do not continue the run before reporting them."
            )
    if not summary["grid_complete"]:
        lines += [
            "",
            "The grid is not complete (as in a pilot), so charts are not drawn and "
            "claims needing missing cells are not evaluated.",
        ]
    return lines


def analyse(
    config: ExperimentConfig,
    folder: Path,
    records: Sequence[RunRecord],
    out_dir: Path | None = None,
) -> str:
    """Score the results, write the tables, summary and charts, and return the report text."""
    results_folder = out_dir if out_dir is not None else folder / "results"
    summary, scored, cells, wrong, facts = build_summary(config, folder, records)
    lengths = BUILD.run_lengths(config)
    charts, highlights = _charts(cells, wrong, lengths, results_folder / "charts")
    summary["chart_highlights"] = highlights

    _write_csv(
        results_folder / "summary.csv", SUMMARY_COLUMNS, [_summary_row(s, facts) for s in scored]
    )
    _write_csv(
        results_folder / "wrong_answers.csv",
        WRONG_COLUMNS,
        [_wrong_row(s, facts) for s in scored if not s.verdict.correct],
    )
    (results_folder / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    models = [model.display_label for model in config.models]
    lines = [
        *_report(summary, models),
        "",
        f"Chart highlights: {highlights or 'charts not drawn'}",
        f"Written: summary.csv, wrong_answers.csv, summary.json in {results_folder}",
        f"Charts:  {len(charts)} file(s) in {results_folder / 'charts'}",
    ]
    return "\n".join(lines)
