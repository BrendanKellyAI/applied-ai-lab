"""Planted values: drawn from the seed, written by kind, and unique across the whole library.

A value is refused if it was drawn before or if it already appears, as a whole token, in any
text the library holds (the v1 articles), so a planted value can only ever be found where it
was planted.
"""

import random
from collections.abc import Iterable

from lab.scoring import contains_match


class ValuesExhausted(ValueError):
    """No unused value is left for a draw."""


class ValuePool:
    def __init__(self, kinds: dict[str, str], rng: random.Random, existing: Iterable[str] = ()):
        self._kinds = kinds
        self._rng = rng
        self._existing = list(existing)
        self.used: set[str] = set()

    def render(self, kind: str, n: int) -> str:
        text = self._kinds[kind].format(n=n)
        # "1 day", not "1 days": every unit written after the number takes a plural "s".
        if n == 1 and text.endswith("s") and text.startswith("1 "):
            return text[:-1]
        return text

    def draw(self, kind: str, low: int, high: int) -> str:
        """An unused value of this kind between low and high, chosen at random."""
        candidates = [self.render(kind, n) for n in range(low, high + 1)]
        self._rng.shuffle(candidates)
        for value in candidates:
            if self.available(value):
                self.used.add(value)
                return value
        raise ValuesExhausted(f"No unused {kind} value left between {low} and {high}")

    def available(self, value: str) -> bool:
        if value in self.used:
            return False
        # Whole tokens only: "£12.00" inside "£112.00" does not count as a match.
        return not any(contains_match(text, value) for text in self._existing)
