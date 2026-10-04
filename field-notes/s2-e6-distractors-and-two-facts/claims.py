"""S2 E6 pre-registered claims H0 to H5, evaluated from cell counts.

The pass marks come from config.yaml (`parameters.pass_marks`), which PREREGISTRATION.md states
in words; a test checks the two agree. Differences are compared in whole calls, so a mark of
"10 points" on 36 calls needs a gap of 4 calls (11.1 points), never a rounding accident.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations

from lab.scoring import wilson_interval

HELD = "Held"
FAILED = "Failed"
NOT_EVALUATED = "Not evaluated"
NOT_TESTED = "Not tested"
LONGEST = 128000
SHORTEST = 16000
ITEMS = 12  # per model, shape, and length, in the full grid


@dataclass(frozen=True)
class Count:
    correct: int
    trials: int

    @property
    def interval(self) -> tuple[float, float, float]:
        return wilson_interval(self.correct, self.trials)

    def to_json(self) -> dict:
        point, low, high = self.interval
        return {
            "correct": self.correct,
            "trials": self.trials,
            "accuracy": round(point, 4),
            "wilson_low": round(low, 4),
            "wilson_high": round(high, 4),
        }


@dataclass(frozen=True)
class Claim:
    id: str
    verdict: str
    evidence: str
    figures: dict = field(default_factory=dict)


def _points(higher: Count, lower: Count) -> float:
    """Percentage points by which `lower` is below `higher`."""
    return 100 * (higher.correct / higher.trials - lower.correct / lower.trials)


def _verdict(passed: bool) -> str:
    return HELD if passed else FAILED


def _at_least(drop: float, mark: float) -> bool:
    return drop >= mark - 1e-9


class Cells:
    """Counts per (model, shape, length) and pooled per (shape, length)."""

    def __init__(
        self,
        counts: Mapping[tuple[str, str, int], Count],
        models: Sequence[str],
        items: int = ITEMS,
    ):
        self.counts = dict(counts)
        self.models = list(models)
        self.items = items

    def model(self, model: str, shape: str, length: int) -> Count | None:
        return self.counts.get((model, shape, length))

    def complete(self, shape: str, length: int) -> bool:
        cells = [self.model(model, shape, length) for model in self.models]
        return all(cell is not None and cell.trials == self.items for cell in cells)

    def pooled(self, shape: str, length: int) -> Count | None:
        if not self.complete(shape, length):
            return None
        cells = [self.counts[(model, shape, length)] for model in self.models]
        return Count(sum(c.correct for c in cells), sum(c.trials for c in cells))


def _missing(claim_id: str, needed: str) -> Claim:
    return Claim(claim_id, NOT_EVALUATED, f"Needs every call for {needed}.")


def h0(cells: Cells, lengths: Sequence[int], marks: Mapping) -> Claim:
    if not all(cells.complete("single", length) for length in lengths):
        return _missing("H0", "the Single shape")
    per_model = {
        model: sum(cells.model(model, "single", length).correct for length in lengths)
        for model in cells.models
    }
    pooled = cells.pooled("single", LONGEST)
    trials = cells.items * len(lengths)
    passed = (
        all(correct >= marks["h0_single_correct_per_model"] for correct in per_model.values())
        and pooled.correct >= marks["h0_single_correct_pooled_128k"]
    )
    detail = ", ".join(f"{model} {n} of {trials}" for model, n in per_model.items())
    return Claim(
        "H0",
        _verdict(passed),
        f"{detail}; pooled at 128,000 {pooled.correct} of {pooled.trials}.",
        {"per_model": per_model, "trials_per_model": trials, "pooled_128k": pooled.to_json()},
    )


def _drop_claim(
    claim_id: str, cells: Cells, high: tuple[str, int], low: tuple[str, int], mark: float
) -> Claim:
    above, below = cells.pooled(*high), cells.pooled(*low)
    if above is None or below is None:
        return _missing(claim_id, f"{high[0]} at {high[1]:,} and {low[0]} at {low[1]:,}")
    drop = _points(above, below)
    return Claim(
        claim_id,
        _verdict(_at_least(drop, mark)),
        f"{below.correct} of {below.trials} against {above.correct} of {above.trials}: "
        f"{drop:.1f} points lower (mark {mark}).",
        {"higher": above.to_json(), "lower": below.to_json(), "drop_points": round(drop, 2)},
    )


def h1(cells: Cells, distractor_replies: int, marks: Mapping) -> Claim:
    base = _drop_claim(
        "H1", cells, ("single", LONGEST), ("distractors", LONGEST), marks["h1_drop_points"]
    )
    if base.verdict == NOT_EVALUATED:
        return base
    named = distractor_replies >= marks["h1_distractor_replies"]
    passed = base.verdict == HELD and named
    return Claim(
        "H1",
        _verdict(passed),
        f"{base.evidence} {distractor_replies} wrong replies named a distractor value "
        f"(mark {marks['h1_distractor_replies']}).",
        {**base.figures, "distractor_value_replies": distractor_replies},
    )


def h3(cells: Cells, marks: Mapping) -> Claim:
    hardest = cells.pooled("two-fact-distractors", LONGEST)
    others = {shape: cells.pooled(shape, LONGEST) for shape in ("distractors", "two-fact")}
    if hardest is None or any(count is None for count in others.values()):
        return _missing("H3", "shapes 2, 3 and 4 at 128,000")
    drops = {shape: _points(count, hardest) for shape, count in others.items()}
    passed = all(_at_least(drop, marks["h3_drop_points"]) for drop in drops.values())
    return Claim(
        "H3",
        _verdict(passed),
        f"Shape 4 {hardest.correct} of {hardest.trials}; "
        + "; ".join(
            f"{drops[shape]:.1f} points below {shape} ({count.correct} of {count.trials})"
            for shape, count in others.items()
        )
        + f" (mark {marks['h3_drop_points']}).",
        {
            "shape_4": hardest.to_json(),
            **{shape: count.to_json() for shape, count in others.items()},
            "drop_points": {shape: round(drop, 2) for shape, drop in drops.items()},
        },
    )


def h4(cells: Cells, lengths: Sequence[int], marks: Mapping) -> Claim:
    if SHORTEST not in lengths or "h4_drop_points" not in marks:
        return Claim(
            "H4",
            NOT_TESTED,
            "Withdrawn before the run: the reduced run has no 16,000-token calls.",
        )
    return _drop_claim(
        "H4",
        cells,
        ("two-fact-distractors", SHORTEST),
        ("two-fact-distractors", LONGEST),
        marks["h4_drop_points"],
    )


def separated_pairs(cells: Cells, shape: str, length: int) -> list[tuple[str, str]]:
    """Model pairs whose Wilson 95% intervals do not overlap, lower model first."""
    pairs = []
    for first, second in combinations(cells.models, 2):
        a, b = cells.model(first, shape, length), cells.model(second, shape, length)
        (_, a_low, a_high), (_, b_low, b_high) = a.interval, b.interval
        if a_high < b_low:
            pairs.append((first, second))
        elif b_high < a_low:
            pairs.append((second, first))
    return pairs


def h5(cells: Cells) -> Claim:
    if not cells.complete("two-fact-distractors", LONGEST):
        return _missing("H5", "shape 4 at 128,000")
    pairs = separated_pairs(cells, "two-fact-distractors", LONGEST)
    detail = "; ".join(
        f"{model} {cell.correct} of {cell.trials} "
        f"({cell.interval[1]:.0%} to {cell.interval[2]:.0%})"
        for model in cells.models
        if (cell := cells.model(model, "two-fact-distractors", LONGEST))
    )
    found = ", ".join(f"{low} below {high}" for low, high in pairs) or "no pair separates"
    return Claim(
        "H5",
        _verdict(bool(pairs)),
        f"{detail}. {found}.",
        {"separated_pairs": [list(pair) for pair in pairs]},
    )


def evaluate(
    cells: Cells, lengths: Sequence[int], distractor_replies: int, marks: Mapping
) -> list[Claim]:
    return [
        h0(cells, lengths, marks),
        h1(cells, distractor_replies, marks),
        _drop_claim(
            "H2", cells, ("single", LONGEST), ("two-fact", LONGEST), marks["h2_drop_points"]
        ),
        h3(cells, marks),
        h4(cells, lengths, marks),
        h5(cells),
    ]
