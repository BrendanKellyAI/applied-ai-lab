"""Task B scoring: the style guide's code checks, the facts judge, and the pairwise style judge.

Primary: replies that pass every code check and keep the facts, out of the items scored. A not
found item keeps its facts when it uses the fixed sentence, which the code checks; the judge
decides the rest. Style is judged in both orders against the reference arm: a win needs the
arm preferred both times, a loss the reference preferred both times, and anything else is a
tie, which absorbs position bias.
"""

from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.checks import ReplyError, parse_object
from lab.adapt.build_tasks.task_b import facts_verdict
from lab.adapt.items import ReplyItem
from lab.adapt.style import CHECKS, check_reply
from lab.rag.score import Proportion

Outcome = Literal["win", "tie", "loss"]


class ReplyScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: str
    answered: bool
    checks: dict[str, bool]
    all_checks: bool
    facts_kept: bool
    primary: bool
    words: int
    mean_sentence_words: float


def score_reply(item: ReplyItem, text: str | None, facts_text: str | None) -> ReplyScore:
    if text is None:
        return ReplyScore(
            id=item.id,
            kind=item.kind,
            answered=False,
            checks=dict.fromkeys(CHECKS, False),
            all_checks=False,
            facts_kept=False,
            primary=False,
            words=0,
            mean_sentence_words=0.0,
        )
    report = check_reply(text, item.source_ref)
    checks = {name: getattr(report, name) for name in CHECKS}
    kept = report.not_found if item.kind == "not_found" else facts_verdict(facts_text)
    return ReplyScore(
        id=item.id,
        kind=item.kind,
        answered=True,
        checks=checks,
        all_checks=report.all_pass,
        facts_kept=kept,
        primary=report.all_pass and kept,
        words=report.words,
        mean_sentence_words=round(report.mean_sentence_words, 2),
    )


def score_replies(
    items: Sequence[ReplyItem], texts: Mapping[str, str], facts: Mapping[str, str]
) -> list[ReplyScore]:
    return [score_reply(i, texts.get(i.id), facts.get(i.id)) for i in items]


def summarise(scores: Sequence[ReplyScore]) -> dict:
    n = len(scores)
    answered = [s for s in scores if s.answered]
    return {
        "items": n,
        "primary": Proportion.of(sum(s.primary for s in scores), n).model_dump(),
        "all_checks": Proportion.of(sum(s.all_checks for s in scores), n).model_dump(),
        "facts_kept": Proportion.of(sum(s.facts_kept for s in scores), n).model_dump(),
        "checks": {
            name: Proportion.of(sum(s.checks[name] for s in scores), n).model_dump()
            for name in CHECKS
        },
        "mean_words": round(sum(s.words for s in answered) / len(answered), 1) if answered else 0,
        "mean_sentence_words": round(
            sum(s.mean_sentence_words for s in answered) / len(answered), 2
        )
        if answered
        else 0,
    }


def _choice(text: str | None) -> str | None:
    if text is None:
        return None
    try:
        value = parse_object(text).get("better")
    except ReplyError:
        return None
    return str(value) if value in ("1", "2", "tie", 1, 2) else None


def style_outcome(arm_first: str | None, reference_first: str | None) -> Outcome:
    """Arm first ("ar") and reference first ("ra") verdicts, combined."""
    a, r = _choice(arm_first), _choice(reference_first)
    if a == "1" and r == "2":
        return "win"
    if a == "2" and r == "1":
        return "loss"
    return "tie"


def style_summary(items: Sequence[ReplyItem], style: Mapping[str, str]) -> dict:
    """Outcomes over the pairs judged in both orders. A pair with a missing or unreadable
    verdict is counted as unjudged, not as a tie."""
    outcomes = []
    unjudged = 0
    for item in items:
        first, second = style.get(f"{item.id}:ar"), style.get(f"{item.id}:ra")
        if _choice(first) is None or _choice(second) is None:
            unjudged += first is not None or second is not None
            continue
        outcomes.append(style_outcome(first, second))
    n = len(outcomes)
    return {
        "pairs": n,
        "unjudged": unjudged,
        **{
            name: Proportion.of(outcomes.count(name), n).model_dump()
            for name in ("win", "tie", "loss")
        },
    }
