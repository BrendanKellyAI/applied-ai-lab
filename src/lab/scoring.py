"""Deterministic scoring and confidence intervals (specification section 5.7).

Scoring is deterministic: normalised exact match, contains match, and numeric match with a
tolerance. Neither Season 1 experiment uses a model as a judge, so nothing here calls a model.
"""

import math
import re

# Punctuation and formatting that models wrap answers in, stripped from each end only.
_EDGE_CHARACTERS = " \t\r\n\"'`*_()[]{}<>.,;:!?"
_WHITESPACE = re.compile(r"\s+")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")

# 95% confidence, two-sided.
Z_95 = 1.959963984540054


def normalise(text: str) -> str:
    """Lowercase, collapse whitespace, and drop punctuation at each end."""
    return _WHITESPACE.sub(" ", text).strip().strip(_EDGE_CHARACTERS).strip().lower()


def exact_match(response: str, expected: str) -> bool:
    """The whole normalised response is the expected value."""
    return normalise(response) == normalise(expected)


def contains_match(response: str, expected: str) -> bool:
    """The normalised response contains the expected value as a whole token.

    Whole token, so "83521" does not count as containing "8352". This is E7's scoring rule
    (section 6.5): correct if the normalised response contains the exact inserted value.
    """
    value = normalise(expected)
    if not value:
        return False
    pattern = re.compile(rf"(?<![0-9a-z]){re.escape(value)}(?![0-9a-z])")
    return pattern.search(normalise(response)) is not None


def numeric_match(response: str, expected: float, *, tolerance: float) -> bool:
    """The first number in the response is within `tolerance` of the expected value."""
    found = _NUMBER.search(normalise(response))
    if found is None:
        return False
    return abs(float(found.group()) - expected) <= tolerance


def wilson_interval(correct: int, trials: int, z: float = Z_95) -> tuple[float, float, float]:
    """Point estimate and Wilson score interval for a proportion.

    The Wilson interval is used rather than the normal approximation because cells hold only six
    calls, where the normal approximation is unreliable and can run past 0 or 1.
    """
    if trials < 0 or correct < 0:
        raise ValueError("correct and trials must not be negative")
    if correct > trials:
        raise ValueError(f"correct ({correct}) cannot exceed trials ({trials})")
    if trials == 0:
        return 0.0, 0.0, 1.0

    proportion = correct / trials
    denominator = 1 + z**2 / trials
    centre = (proportion + z**2 / (2 * trials)) / denominator
    spread = (
        z * math.sqrt(proportion * (1 - proportion) / trials + z**2 / (4 * trials**2)) / denominator
    )
    return proportion, max(0.0, centre - spread), min(1.0, centre + spread)
