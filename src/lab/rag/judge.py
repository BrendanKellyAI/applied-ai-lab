"""Stage 11, score (the judge): is each answer correct, faithful to its passages, or a decline?

The judge sees the question, whether the library can answer it, the reference answer, the
passages the system was given and the system's answer. It never sees the evidence labels, so
it judges the answer against what the model was given. Its instructions are in
prompts/judge.md and are fixed for the season: a change makes a new judge, and the E3
agreement check must be redone.
"""

import json
import re

from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError

from lab.rag.prompt import instruction

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class Verdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    declined: StrictBool
    correct: StrictBool
    faithful: StrictBool
    reason: str


class JudgeParseError(ValueError):
    """The judge's reply is not a valid verdict."""


def judge_instructions() -> str:
    return instruction("judge")


# slide: S2 E3
def judge_prompt(item, passages, answer):
    """What the judge reads: never the evidence labels,
    only what the system was given and what it said."""
    parts = [f"Question: {item.question}"]
    if item.history:
        turns = [f"{t.role.title()}: {t.content}" for t in item.history]
        parts.append("Conversation so far:\n" + "\n".join(turns))
    can = "yes" if item.answerable else "no"
    parts.append(f"Can the question be answered from the documents: {can}")
    parts.append(f"Reference answer: {item.answer}")
    given = [f"[P{n}] {c.title}\n{c.text.strip()}" for n, c in enumerate(passages, start=1)]
    parts.append("Passages given to the system:\n" + ("\n\n".join(given) or "(none)"))
    parts.append(f"System's answer:\n{answer.strip()}")
    return "\n\n".join(parts)


def parse_verdict(text: str) -> Verdict:
    body = _FENCE.sub("", text.strip())
    try:
        return Verdict.model_validate(json.loads(body))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise JudgeParseError(str(exc).splitlines()[0]) from exc


def retry_prompt(original: str, error: str) -> str:
    return (
        f"{original}\n\nYour previous reply could not be read as a verdict ({error}). "
        "Reply again with the JSON object only."
    )
