"""The second marker (S2 E3): a model from a third provider marks the judge-check sample.

It reads exactly what the judge read, under the same instructions, so the two models can be
compared item by item. A person then marks only the items where they disagree most, which is
where a hand mark tells us the most about which model to believe. Items where both models
agree are not hand-marked: the report says so and treats their shared verdict as an
assumption, never as a measurement.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lab.rag.chunk import Chunk
from lab.rag.config import ModelSpec
from lab.rag.corpus import Library
from lab.rag.judge import Verdict, judge_prompt
from lab.rag.judge_check import FIELDS, Mark
from lab.rag.log import ItemLog
from lab.rag.score import Proportion
from lab.rag.waves import judge
from lab.runner import Runner, RunSummary

EPISODE = "s2-e3-measuring"
CONDITION = "second-judge"
FOLDER = "second"
VERDICTS = "verdicts.jsonl"


def second_prompts(
    sample: Sequence[str], logs: Sequence[ItemLog], library: Library, chunks: Mapping[str, Chunk]
) -> dict[str, str]:
    """The prompt the judge was given for each sampled item, rebuilt from the run's log."""
    by_id = {g.item_id: g for g in logs}
    items = {i.id: i for i in library.test + library.dev}
    prompts = {}
    for item_id in sample:
        log = by_id[item_id]
        passages = [chunks[c] for c in log.prompt_chunks]
        prompts[item_id] = judge_prompt(
            items[item_id], passages, log.answer.text if log.answer else ""
        )
    return prompts


def run_second(
    runner: Runner, prompts: Mapping[str, str], spec: ModelSpec, folder: Path
) -> tuple[dict[str, Verdict | None], list[RunSummary]]:
    """Send the prompts to the second model, with the judge's retry rule, and save the verdicts."""
    judged, summaries = judge(
        runner, prompts, spec, episode=EPISODE, condition=CONDITION, folder=folder
    )
    verdicts = {
        item_id: (judged[item_id].verdict if item_id in judged else None) for item_id in prompts
    }
    lines = [
        json.dumps(
            {
                "item_id": item_id,
                "verdict": v.model_dump() if v else None,
                "error": None
                if v
                else (judged[item_id].error if item_id in judged else "no reply"),
            }
        )
        for item_id, v in verdicts.items()
    ]
    (folder / VERDICTS).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return verdicts, summaries


def read_second(folder: Path) -> dict[str, Verdict | None]:
    rows = [
        json.loads(line) for line in (folder / VERDICTS).read_text(encoding="utf-8").splitlines()
    ]
    return {
        r["item_id"]: Verdict.model_validate(r["verdict"]) if r["verdict"] else None for r in rows
    }


def right(verdict: Verdict) -> bool:
    """The verdict E2's answer number counts: correct and faithful."""
    return verdict.correct and verdict.faithful


def disagreement(first: Verdict, second: Verdict | None) -> int:
    """How strongly two verdicts differ. A different call on "right" outranks any number of
    other fields; a second model that gave no verdict ranks above full agreement."""
    if second is None:
        return 5
    fields = sum(1 for f in FIELDS if getattr(first, f) != getattr(second, f))
    return 10 * (right(first) != right(second)) + fields


def pick_for_hand(
    sample: Sequence[str],
    first: Mapping[str, Verdict],
    second: Mapping[str, Verdict | None],
    n: int,
) -> list[str]:
    """The `n` items where the models disagree most, ties in sample order. When fewer than `n`
    disagree, agreeing items fill the rest, so the person also checks some shared verdicts."""
    ranked = sorted(sample, key=lambda i: -disagreement(first[i], second.get(i)))
    return ranked[:n]


def _agree(pairs: Sequence[tuple[Verdict, Verdict | Mark]], read) -> Proportion:
    return Proportion.of(sum(1 for a, b in pairs if read(a) == read(b)), len(pairs))


def _by_field(pairs) -> dict[str, Any]:
    out = {f: _agree(pairs, lambda v, f=f: getattr(v, f)).model_dump() for f in FIELDS}
    out["right"] = _agree(pairs, right).model_dump()
    return out


def two_marker_report(
    sample: Sequence[str],
    logs: Sequence[ItemLog],
    second: Mapping[str, Verdict | None],
    marks: Sequence[Mark],
) -> dict[str, Any]:
    """The judge against the second model on the whole sample, both against the hand marks,
    the code check against the hand marks, and an estimate of the judge's accuracy on "right"."""
    by_id = {g.item_id: g for g in logs}
    judge_of = {i: by_id[i].verdict for i in sample}
    both = [i for i in sample if second.get(i) is not None]
    hand = {m.item_id: m for m in marks}
    split = [i for i in both if right(judge_of[i]) != right(second[i])]
    marked_split = [i for i in split if i in hand]
    with_judge = sum(1 for i in marked_split if right(hand[i]) == right(judge_of[i]))
    agreed = len(both) - len(split)
    coded = [i for i in hand if by_id[i].code_check is not None]
    return {
        "sample": len(sample),
        "second_errors": sorted(i for i in sample if second.get(i) is None),
        "models": _by_field([(judge_of[i], second[i]) for i in both]),
        "hand_items": len(hand),
        "judge_with_hand": _by_field([(judge_of[i], hand[i]) for i in hand]),
        "second_with_hand": _by_field([(second[i], hand[i]) for i in hand if second.get(i)]),
        "code_check_on_hand": {
            "items": len(coded),
            "judge_matches_hand": sum(1 for i in coded if judge_of[i].correct == hand[i].correct),
            "code_matches_hand": sum(1 for i in coded if by_id[i].code_check == hand[i].correct),
        },
        "right_split": {
            "items": len(split),
            "hand_marked": len(marked_split),
            "hand_sides_with_judge": with_judge,
            "hand_sides_with_second": sum(
                1 for i in marked_split if right(hand[i]) == right(second[i])
            ),
            "not_marked": sorted(set(split) - set(marked_split)),
        },
        # Assumes that where both models agree on "right", they are right. Not measured.
        "judge_right_estimate": Proportion.of(
            agreed + with_judge, agreed + len(marked_split)
        ).model_dump(),
        "hand_disagreements": [
            _row(i, judge_of[i], second.get(i), hand[i])
            for i in hand
            if any(getattr(hand[i], f) != getattr(judge_of[i], f) for f in FIELDS)
            or (second.get(i) and any(getattr(hand[i], f) != getattr(second[i], f) for f in FIELDS))
        ],
    }


def _row(item_id: str, first: Verdict, second: Verdict | None, mark: Mark) -> dict[str, Any]:
    pick = lambda v: {f: getattr(v, f) for f in FIELDS}  # noqa: E731
    return {
        "item_id": item_id,
        "judge": pick(first),
        "second": pick(second) if second else None,
        "hand": pick(mark),
        "judge_reason": first.reason,
        "second_reason": second.reason if second else None,
        "note": mark.note,
    }


def format_two_marker(report: dict[str, Any]) -> str:
    def line(name: str, p: dict[str, Any]) -> str:
        return f"{name} {p['count']}/{p['total']} ({p['low']:.0%} to {p['high']:.0%})"

    lines = [
        f"Judge check, {report['sample']} items, second model on all, "
        f"{report['hand_items']} by hand"
    ]
    for label, key in (
        ("judge vs second", "models"),
        ("judge vs hand", "judge_with_hand"),
        ("second vs hand", "second_with_hand"),
    ):
        lines.append(f"  {label}: " + "; ".join(line(f, p) for f, p in report[key].items()))
    split = report["right_split"]
    lines.append(
        f"  split on right: {split['items']}, hand-marked {split['hand_marked']}, "
        f"sided with judge {split['hand_sides_with_judge']}, "
        f"with second {split['hand_sides_with_second']}"
    )
    code = report["code_check_on_hand"]
    lines.append(
        f"  correct on {code['items']} hand items with key values: "
        f"judge {code['judge_matches_hand']}, "
        f"code {code['code_matches_hand']}"
    )
    lines.append("  " + line("judge right, estimated", report["judge_right_estimate"]))
    if report["second_errors"]:
        lines.append(f"  second model gave no verdict on: {', '.join(report['second_errors'])}")
    return "\n".join(lines)
