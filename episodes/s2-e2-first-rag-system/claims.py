"""S2 E2's six pre-registered claims, applied to the run's log. See PREREGISTRATION.md."""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from lab.rag.analysis import (
    BEFORE_PROMPT,
    INSIDE_PROMPT,
    below,
    declined,
    gives_old_value,
    lost_at_counts,
    of_type,
    recall,
    stale_in_prompt,
    version_values,
)
from lab.rag.corpus import Library
from lab.rag.log import ItemLog


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    statement: str
    held: bool
    detail: dict[str, Any]


def _share(count: int, total: int) -> float:
    return count / total if total else 0.0


def h1(logs: Sequence[ItemLog], marks: Mapping[str, Any]) -> Claim:
    lost = lost_at_counts(logs)
    before = sum(lost[s] for s in BEFORE_PROMPT)
    inside = sum(lost[s] for s in INSIDE_PROMPT)
    return Claim(
        id="H1",
        statement="Search loses more answers than the model does.",
        held=before > inside if marks["h1_before_prompt_exceeds_inside"] else True,
        detail={"before_prompt": before, "inside_prompt": inside, "by_stage": dict(lost)},
    )


def h2(logs: Sequence[ItemLog], marks: Mapping[str, Any], k: int) -> Claim:
    single = recall(of_type(logs, "policy_single"), k)
    shaped = {t: recall(of_type(logs, t), k) for t in marks["h2_types_below_single"]}
    return Claim(
        id="H2",
        statement="Fixed chunks hurt two-sentence and heading-dependent facts.",
        held=all(p.rate < single.rate for p in shaped.values()),
        detail={
            "policy_single": single.model_dump(),
            **{t: p.model_dump() for t, p in shaped.items()},
            "strong_form": all(below(p, single) for p in shaped.values()),
        },
    )


def h3(logs: Sequence[ItemLog], k: int) -> Claim:
    identifier = recall(of_type(logs, "identifier"), k)
    paraphrase = recall(of_type(logs, "paraphrase"), k)
    return Claim(
        id="H3",
        statement="Identifier questions fail under vector search.",
        held=below(identifier, paraphrase),
        detail={"identifier": identifier.model_dump(), "paraphrase": paraphrase.model_dump()},
    )


def h4(logs: Sequence[ItemLog], k: int) -> Claim:
    followup = recall(of_type(logs, "followup"), k)
    single = recall(of_type(logs, "policy_single"), k)
    return Claim(
        id="H4",
        statement="A follow-up searched on its own fails.",
        held=below(followup, single),
        detail={"followup": followup.model_dump(), "policy_single": single.model_dump()},
    )


def h5(logs: Sequence[ItemLog], marks: Mapping[str, Any], library: Library) -> Claim:
    restricted = of_type(logs, "restricted_public")
    leaked = sum(1 for log in restricted if log.leaks)
    other = sum(
        1 for log in logs
        if log.asker == "public" and log.type != "restricted_public" and log.leaks
    )
    versions = of_type(logs, "version")
    stale = sum(1 for log in versions if stale_in_prompt(log))
    old_answers = []
    for log in versions:
        values = version_values(log, library)
        if values and log.answer and gives_old_value(log.answer.text, *values):
            old_answers.append(log.item_id)
    a = (
        _share(leaked, len(restricted)) >= marks["h5a_restricted_leak_share"]
        and other >= marks["h5a_other_type_leaks_at_least"]
    )
    b = (
        _share(stale, len(versions)) >= marks["h5b_stale_in_prompt_share"]
        and len(old_answers) >= marks["h5b_old_value_answers_at_least"]
    )
    return Claim(
        id="H5",
        statement="With no filter, the wrong documents reach the prompt.",
        held=a and b,
        detail={
            "h5a_held": a, "restricted_leaked": leaked, "restricted_items": len(restricted),
            "other_types_leaked": other,
            "h5b_held": b, "stale_in_prompt": stale, "version_items": len(versions),
            "old_value_answers": old_answers,
        },
    )


def h6(logs: Sequence[ItemLog], marks: Mapping[str, Any]) -> Claim:
    absent = declined(of_type(logs, "absent_detail", "absent_topic"))
    wrong_thing = declined(of_type(logs, "restricted_public", "deleted"))
    a = absent.rate >= marks["h6a_absent_not_found_at_least"]
    b = wrong_thing.rate <= marks["h6b_leaked_or_deleted_not_found_at_most"]
    return Claim(
        id="H6",
        statement="The model declines when nothing is there, but not when the wrong thing is.",
        held=a and b,
        detail={
            "h6a_held": a, "absent": absent.model_dump(),
            "h6b_held": b, "restricted_or_deleted": wrong_thing.model_dump(),
        },
    )


def evaluate(
    logs: Sequence[ItemLog], library: Library, marks: Mapping[str, Any], k: int
) -> list[Claim]:
    return [
        h1(logs, marks),
        h2(logs, marks, k),
        h3(logs, k),
        h4(logs, k),
        h5(logs, marks, library),
        h6(logs, marks),
    ]
