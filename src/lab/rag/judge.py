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

from lab.rag.prompt import conversation, instruction, numbered

ANSWERABLE = "Can the question be answered from the documents"
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
        parts.append(conversation(item.history))
    can = "yes" if item.answerable else "no"
    parts.append(f"{ANSWERABLE}: {can}")
    parts.append(f"Reference answer: {item.answer}")
    given = "\n\n".join(numbered(passages)) or "(none)"
    parts.append(f"Passages given to the system:\n{given}")
    parts.append(f"System's answer:\n{answer.strip()}")
    return "\n\n".join(parts)


def parse_verdict(text: str) -> Verdict:
    """The verdict in the reply. The judge sometimes reasons in prose first, so the last JSON
    object in the reply is taken; a reply with no complete, valid object is refused."""
    body = _FENCE.sub("", text.strip())
    try:
        return Verdict.model_validate(json.loads(body))
    except (json.JSONDecodeError, ValidationError) as exc:
        error = exc
    decoder = json.JSONDecoder()
    for start in reversed([i for i, char in enumerate(body) if char == "{"]):
        try:
            found, _ = decoder.raw_decode(body, start)
            return Verdict.model_validate(found)
        except (json.JSONDecodeError, ValidationError):
            continue
    raise JudgeParseError(str(error).splitlines()[0]) from error


def retry_prompt(original: str, error: str) -> str:
    return (
        f"{original}\n\nYour previous reply could not be read as a verdict ({error}). "
        "Reply again with the JSON object only."
    )
