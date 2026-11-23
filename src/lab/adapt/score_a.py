"""Task A scoring, all by code against the label: no judge.

Primary: items fully right (route, safety, product and fault all correct), out of the items
scored. A missing or invalid reply is wrong on every field. Safety recall is reported beside it:
a missed safety incident is the costly error.
"""

from collections import Counter
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict

from lab.adapt.definitions import Definitions
from lab.adapt.items import TriageItem
from lab.adapt.output import parse_triage
from lab.rag.score import Proportion

FIELDS = ("route", "safety", "product", "fault")


class TriageScore(BaseModel):
    """One item, as scored."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: str
    valid: bool
    problem: str | None
    fields: dict[str, bool]
    fully_right: bool
    safety_item: bool
    flagged: bool
    route: str | None


def score_item(item: TriageItem, text: str | None, definitions: Definitions) -> TriageScore:
    parsed = parse_triage(text, definitions)
    label = parsed.label
    fields = {
        name: label is not None and getattr(label, name) == getattr(item.label, name)
        for name in FIELDS
    }
    return TriageScore(
        id=item.id,
        kind=item.kind,
        valid=parsed.valid,
        problem=parsed.problem,
        fields=fields,
        fully_right=all(fields.values()),
        safety_item=item.label.safety,
        flagged=bool(label and label.safety),
        route=label.route if label else None,
    )


def score_items(
    items: Sequence[TriageItem], texts: Mapping[str, str], definitions: Definitions
) -> list[TriageScore]:
    return [score_item(item, texts.get(item.id), definitions) for item in items]


def macro_f1(items: Sequence[TriageItem], scores: Sequence[TriageScore], routes) -> float:
    """Mean F1 over routes; a route with no true and no predicted items is left out."""
    truth = {i.id: i.label.route for i in items}
    f1s = []
    for route in routes:
        tp = sum(1 for s in scores if s.route == route and truth[s.id] == route)
        fp = sum(1 for s in scores if s.route == route and truth[s.id] != route)
        fn = sum(1 for s in scores if s.route != route and truth[s.id] == route)
        if tp + fp + fn == 0:
            continue
        f1s.append(2 * tp / (2 * tp + fp + fn))
    return sum(f1s) / len(f1s) if f1s else 0.0


def summarise(
    items: Sequence[TriageItem], scores: Sequence[TriageScore], definitions: Definitions
) -> dict:
    n = len(scores)
    safety = [s for s in scores if s.safety_item]
    not_safety = [s for s in scores if not s.safety_item]
    by_kind: dict[str, list[TriageScore]] = {}
    for s in scores:
        by_kind.setdefault(s.kind, []).append(s)
    return {
        "items": n,
        "fully_right": Proportion.of(sum(s.fully_right for s in scores), n).model_dump(),
        "safety_recall": Proportion.of(sum(s.flagged for s in safety), len(safety)).model_dump(),
        "safety_false_alarms": Proportion.of(
            sum(s.flagged for s in not_safety), len(not_safety)
        ).model_dump(),
        "json_valid": Proportion.of(sum(s.valid for s in scores), n).model_dump(),
        "field_accuracy": {
            name: Proportion.of(sum(s.fields[name] for s in scores), n).model_dump()
            for name in FIELDS
        },
        "route_macro_f1": round(macro_f1(items, scores, definitions.routes), 4),
        "fully_right_by_kind": {
            kind: Proportion.of(sum(s.fully_right for s in group), len(group)).model_dump()
            for kind, group in sorted(by_kind.items())
        },
        "invalid_reasons": dict(
            Counter((s.problem or "").split(":")[0] for s in scores if not s.valid)
        ),
    }
