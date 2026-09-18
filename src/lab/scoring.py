"""Deterministic scoring and confidence intervals (specification section 5.7).

Scoring is deterministic: normalised exact match, contains match, numeric match with a
tolerance, and the final `ANSWER:` line. Neither Season 1 experiment uses a model as a judge,
so nothing here calls a model.
"""

import math
import re

# Punctuation and formatting that models wrap answers in, stripped from each end only.
_EDGE_CHARACTERS = " \t\r\n\"'`*_()[]{}<>.,;:!?"
_WHITESPACE = re.compile(r"\s+")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
# The answer line every S1 E10 prompt asks for: "ANSWER: <value>". Anchored at the start of the
# line, allowing the markdown a model may wrap it in, so that a model repeating the instruction
# ("...in the form ANSWER: <value>") is not read as having answered.
_ANSWER_LINE = re.compile(r"^[\s>*_`#\-]*answer\s*[:=]\s*(?P<value>.*)", re.IGNORECASE)
# Separators a model may put in a large number, removed before an integer comparison.
_GROUPING = str.maketrans("", "", ", _")
_INTEGER = re.compile(r"^[+-]?\d+$")

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


def parse_answer(text: str) -> str | None:
    """The value on the last `ANSWER:` line, normalised, or None when there is no such line.

    The last line wins, because a model that restates the format before answering would
    otherwise have its example read as the answer. A response with no answer line is not
    guessed at: it is scored incorrect and counted separately (specification section 7.5).
    """
    values = [
        found.group("value") for line in text.splitlines() if (found := _ANSWER_LINE.search(line))
    ]
    if not values:
        return None
    return normalise(values[-1]) or None


def integer_match(value: str, expected: int) -> bool:
    """The value is exactly the expected integer, allowing thousands separators."""
    candidate = value.translate(_GROUPING)
    if not _INTEGER.match(candidate):
        return False
    return int(candidate) == expected


def paired_difference_interval(
    both: int, only_first: int, only_second: int, neither: int, z: float = Z_95
) -> tuple[float, float, float]:
    """Difference between two paired proportions, with Newcombe's score interval (method 10).

    The four counts are the cells of the paired table over the same items: correct in both
    conditions, correct only in the first, correct only in the second, and correct in neither.

    S1 E10 runs the same items in both modes, so the two accuracies are not independent and an
    unpaired interval would be too wide. Newcombe's method combines a Wilson interval for each
    proportion with the observed correlation between them, and keeps the interval inside
    -1 to 1 at the small counts this experiment has.

    Reference: Newcombe, "Improved confidence intervals for the difference between binomial
    proportions based on paired data", Statistics in Medicine 17 (1998), method 10.
    """
    counts = (both, only_first, only_second, neither)
    if any(count < 0 for count in counts):
        raise ValueError("paired counts must not be negative")
    trials = sum(counts)
    if trials == 0:
        return 0.0, -1.0, 1.0

    first, low_first, high_first = wilson_interval(both + only_first, trials, z)
    second, low_second, high_second = wilson_interval(both + only_second, trials, z)
    difference = first - second
    phi = _paired_correlation(both, only_first, only_second, neither)

    down = _distance(first - low_first, high_second - second, phi)
    up = _distance(high_first - first, second - low_second, phi)
    return difference, max(-1.0, difference - down), min(1.0, difference + up)


def _paired_correlation(both: int, only_first: int, only_second: int, neither: int) -> float:
    """Newcombe's phi for the paired table, taken as zero when any margin is empty."""
    margins = (
        both + only_first,
        only_second + neither,
        both + only_second,
        only_first + neither,
    )
    if any(margin == 0 for margin in margins):
        return 0.0
    product = 1.0
    for margin in margins:
        product *= margin
    return (both * neither - only_first * only_second) / math.sqrt(product)


def _distance(first_spread: float, second_spread: float, phi: float) -> float:
    """One arm of the paired interval. Never negative: |phi| <= 1 keeps the root real."""
    squared = first_spread**2 - 2 * phi * first_spread * second_spread + second_spread**2
    return math.sqrt(max(0.0, squared))
