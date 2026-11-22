"""Code checks on each generated Task A message, and parsing of model JSON replies.

A check returns None when the message passes, or the reason it failed, which is sent back to
the generator with the draft.
"""

import json
import re
from collections.abc import Sequence

from lab.adapt.build_tasks.seeds import Seed
from lab.adapt.definitions import Definitions

# Words outside the length band are allowed within this margin: generators count loosely.
LENGTH_MARGIN = 0.25
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class ReplyError(ValueError):
    """A model reply that is not the JSON object asked for."""


def parse_object(text: str) -> dict:
    body = _FENCE.sub("", text.strip())
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ReplyError(f"not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ReplyError("not a JSON object")
    return value


def message_of(text: str) -> str:
    value = parse_object(text)
    message = value.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ReplyError('no "message" string')
    return message.strip()


def word_count(text: str) -> int:
    return len(text.split())


def product_mentions(message: str, products: Sequence[str]) -> set[str]:
    """Products named in a message, matched on their distinctive first word (Brio, Tessa)."""
    lowered = message.lower()
    return {
        product
        for product in products
        if re.search(rf"\b{re.escape(product.split()[0].lower())}\b", lowered)
    }


def check_message(seed: Seed, text: str, definitions: Definitions) -> str | None:
    try:
        message = message_of(text)
    except ReplyError as exc:
        return f"The reply was {exc}. Reply with one JSON object with a message field."
    for problem in (
        _length_problem(seed, message),
        _label_leak(message, definitions),
        _product_problem(seed, message, definitions),
    ):
        if problem is not None:
            return problem
    return None


def _length_problem(seed: Seed, message: str) -> str | None:
    low, high = seed.length
    words = word_count(message)
    if words < low * (1 - LENGTH_MARGIN) or words > high * (1 + LENGTH_MARGIN):
        return f"The message has {words} words; write {low} to {high}."
    return None


def _label_leak(message: str, definitions: Definitions) -> str | None:
    keys = [*definitions.routes, *definitions.faults]
    leaked = [key for key in keys if "_" in key and key in message]
    if leaked:
        return f"The message uses internal labels ({', '.join(leaked)}); write as a customer."
    return None


def _product_problem(seed: Seed, message: str, definitions: Definitions) -> str | None:
    named = product_mentions(message, definitions.products)
    expected = {p for p in (seed.label.product,) if p is not None}
    if seed.kind == "two_products" and seed.also_named:
        expected.add(seed.also_named)
    missing = expected - named
    extra = named - expected
    if missing:
        return f"The message must name: {', '.join(sorted(missing))}."
    if extra:
        return f"The message must not name: {', '.join(sorted(extra))}."
    return None
