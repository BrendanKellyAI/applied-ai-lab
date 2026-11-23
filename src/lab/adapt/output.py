"""The Task A output contract: the JSON schema an arm can be held to, and the parser that reads
every arm's reply the same way, whatever format it was asked for.

A reply is valid when it holds one JSON object whose four fields all take allowed values. Free
text arms are parsed by taking the first JSON object in the reply, so a model that wraps its
answer in prose or a code fence is not marked wrong for the wrapping alone.
"""

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from lab.adapt.definitions import Definitions, Label
from lab.providers.base import OutputFormat

OutputKind = Literal["text", "json_mode", "schema"]
SCHEMA_NAME = "triage"


def triage_schema(definitions: Definitions) -> dict[str, Any]:
    """A strict schema: every field required, no others, and only allowed values."""
    return {
        "type": "object",
        "properties": {
            "route": {"type": "string", "enum": list(definitions.routes)},
            "safety": {"type": "boolean"},
            "product": {"type": ["string", "null"], "enum": [*definitions.products, None]},
            "fault": {"type": ["string", "null"], "enum": [*definitions.faults, None]},
        },
        "required": ["route", "safety", "product", "fault"],
        "additionalProperties": False,
    }


def output_format(kind: OutputKind, definitions: Definitions) -> OutputFormat | None:
    if kind == "text":
        return None
    if kind == "json_mode":
        return OutputFormat(kind="json_mode")
    return OutputFormat(kind="schema", name=SCHEMA_NAME, json_schema=triage_schema(definitions))


class Parsed(BaseModel):
    """A reply as scored: the label it gives, or why it gives none."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: Label | None
    problem: str | None = None

    @property
    def valid(self) -> bool:
        return self.label is not None


def first_object(text: str) -> dict[str, Any] | None:
    """The first JSON object in the text, or None."""
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            value, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(value, dict):
            return value
        start = text.find("{", start + 1)
    return None


def parse_triage(text: str | None, definitions: Definitions) -> Parsed:
    if text is None:
        return Parsed(label=None, problem="no reply")
    value = first_object(text)
    if value is None:
        return Parsed(label=None, problem="no JSON object")
    try:
        label = Label.model_validate(value)
        label.check_against(definitions)
    except (ValidationError, ValueError) as exc:
        first = str(exc).splitlines()[0]
        return Parsed(label=None, problem=f"invalid fields: {first}")
    return Parsed(label=label)
