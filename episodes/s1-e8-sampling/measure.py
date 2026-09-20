"""The S1 E8 measurements, on logits or answers already taken.

Standard library only, so the tests can check every calculation on small synthetic numbers
without torch, a model, or an API key.

Every choice here was fixed before any result was looked at:

- A probability is the softmax of the model's logits divided by the temperature, worked out
  exactly over the whole vocabulary in double precision. Nothing is estimated by sampling.
- The top-p set is the smallest group of the most likely tokens whose probabilities add up to at
  least p, which is how nucleus sampling defines it.
- Two API answers count as the same answer when they match after three steps, in this order:
  strip the whitespace at both ends, fold the case, and remove any punctuation at the end. Only
  the end: a quotation mark at the start is left alone, and words in the middle are left alone.
  The raw text is always kept as well.
- A response counts as an answer only if its status is "completed" and it has visible text. Any
  other response is counted separately, never as a (very different) answer.
"""

import math
import unicodedata
from collections import Counter
from collections.abc import Sequence

PROMPTS = {
    "capital": "The capital of Ireland is",
    "colour": "My favourite colour is",
}
TEMPERATURES = (0.3, 1.0, 1.8)
# One seed per sample, recorded with it, so any sample can be regenerated.
SEEDS = tuple(range(20))
NEW_TOKENS = 10
TOP_K = 10
TOP_P = 0.6
API_RUNS = 20
COMPLETED = "completed"
# Unicode categories that begin with this letter are punctuation.
PUNCTUATION = "P"


def softmax(logits: Sequence[float], temperature: float = 1.0) -> list[float]:
    """Probabilities from logits, reshaped by dividing them by the temperature first.

    Subtracting the largest scaled logit before exponentiating changes no probability but keeps
    the sums from overflowing at a low temperature.
    """
    if temperature <= 0:
        raise ValueError(f"Temperature must be above 0, got {temperature}")
    if not logits:
        raise ValueError("Cannot take the softmax of no logits")
    scaled = [logit / temperature for logit in logits]
    largest = max(scaled)
    exponentials = [math.exp(value - largest) for value in scaled]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def ranked(probabilities: Sequence[float]) -> list[int]:
    """Token indices from most to least likely. Ties go to the lower index, so it is stable."""
    return sorted(range(len(probabilities)), key=lambda index: (-probabilities[index], index))


def top_k(probabilities: Sequence[float], k: int) -> list[tuple[int, float]]:
    """The k most likely tokens as (index, probability), most likely first."""
    return [(index, probabilities[index]) for index in ranked(probabilities)[:k]]


def top_p_set(probabilities: Sequence[float], p: float) -> list[int]:
    """The smallest set of the most likely tokens whose probabilities add up to at least p."""
    if not 0 < p <= 1:
        raise ValueError(f"p must be above 0 and at most 1, got {p}")
    kept: list[int] = []
    cumulative = 0.0
    for index in ranked(probabilities):
        kept.append(index)
        cumulative += probabilities[index]
        # A tiny tolerance, so a set that reaches p only up to rounding is not made one larger.
        if cumulative >= p - 1e-12:
            break
    return kept


def normalise_answer(text: str) -> str:
    """Strip the whitespace at both ends, fold the case, remove punctuation at the end."""
    folded = text.strip().casefold()
    while folded and unicodedata.category(folded[-1]).startswith(PUNCTUATION):
        folded = folded[:-1].rstrip()
    return folded


def distinct_counts(answers: Sequence[str]) -> list[tuple[str, int]]:
    """Each distinct normalised answer with its count, most common first.

    Answers with the same count keep the order in which they first appeared.
    """
    return Counter(normalise_answer(answer) for answer in answers).most_common()


def is_answer(status: str | None, text: str) -> bool:
    """Whether a response is an answer at all, and not an incomplete or empty reply."""
    return status == COMPLETED and bool(text.strip())


def classify_probe(accepted: bool, echoed: float | None, requested: float) -> str:
    """What happened when a temperature was sent: rejected, applied, or accepted but not applied.

    `echoed` is the temperature the response says it used, if it says.
    """
    if not accepted:
        return "rejected"
    if echoed is None:
        return "accepted, no temperature echoed"
    return "accepted and applied" if echoed == requested else "accepted but not applied"
