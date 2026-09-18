"""Scores S1 E10 results and works out its statistics (specification section 7.5).

Kept apart from `analyse.py` so the numbers and the report that prints them can be read
separately. Nothing here draws anything or writes a file.

Scoring is deterministic: the final `ANSWER:` line is parsed, then compared by exact integer
match or, for the puzzles, by normalised exact match on the ordered list. A response with no
answer line is scored incorrect and counted separately, because a model that cannot follow the
output format is a real result, not a gap in the data.
"""

import math
import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from lab.raw_log import RunRecord, latest_successful
from lab.scoring import integer_match, paired_difference_interval, parse_answer, wilson_interval

INTEGER = "integer"
PERCENTAGE_POINTS = 100.0
TOKEN_BLOCK = 1000.0
# Nearest-rank percentile, which needs no interpolation and never invents a value.
P90 = 0.9


@dataclass(frozen=True)
class Outcome:
    """One scored call."""

    model: str
    task: str
    mode: str
    item_index: int
    correct: bool
    parsed: bool
    answer: str | None
    output_tokens: int
    reasoning_tokens: int | None
    total_latency_ms: float
    first_answer_ms: float | None
    first_thinking_ms: float | None
    finish_reason: str


@dataclass(frozen=True)
class Accuracy:
    """Accuracy over a group of calls, with its Wilson 95% interval."""

    correct: int
    trials: int
    point: float
    low: float
    high: float


@dataclass(frozen=True)
class Gain:
    """The paired change in accuracy from the lowest setting to high reasoning."""

    pairs: int
    change: float
    low: float
    high: float

    @property
    def significant(self) -> bool:
        """Whether the 95% interval excludes zero, which is what the chart rule needs."""
        return self.low > 0 or self.high < 0

    @property
    def change_points(self) -> float:
        return self.change * PERCENTAGE_POINTS


def canonical_list(value: str) -> str:
    """An ordered answer in one shape, so spacing never decides whether an answer is right.

    Commas are the format the prompt asks for. A model that answers with spaces alone is still
    read, because the order it gave is unambiguous and the question is whether it solved the
    puzzle, not whether it typed commas.
    """
    parts = [part.strip() for part in value.split(",")]
    if len(parts) == 1:
        parts = value.split()
    return ", ".join(part for part in parts if part)


def score(text: str, expected: str, answer_kind: str) -> tuple[bool, str | None]:
    """Whether the response is correct, and the answer it gave, or None when it gave none."""
    parsed = parse_answer(text)
    if parsed is None:
        return False, None
    if answer_kind == INTEGER:
        return integer_match(parsed, int(expected)), parsed
    return canonical_list(parsed) == canonical_list(expected), parsed


def successful(records: Sequence[RunRecord]) -> list[RunRecord]:
    return list(latest_successful(list(records)).values())


def current_records(
    records: Sequence[RunRecord], current_hashes: Mapping[str, str]
) -> tuple[list[RunRecord], int]:
    """The records that answered the questions asked now, and how many answered older ones.

    When the questions change, earlier answers stay in the log. Scoring them against the new
    questions would mark right answers wrong, so any record whose request no longer matches the
    current plan is set aside and counted.
    """
    kept = [r for r in records if current_hashes.get(r.call_id) == r.request_hash]
    stale = {r.call_id for r in records if r.result is not None} - {
        r.call_id for r in kept if r.result is not None
    }
    return kept, len(stale)


def outcomes(records: Sequence[RunRecord], items: Iterable) -> list[Outcome]:
    """Score every successful record against the committed item it was built from."""
    expected = {(item.task, item.index): item for item in items}
    scored: list[Outcome] = []
    for record in successful(records):
        result = record.result
        if result is None:  # pragma: no cover - successful() has already filtered these
            continue
        key = (str(record.cell["task"]), int(record.cell["item_index"]))
        item = expected.get(key)
        if item is None:
            continue
        correct, answer = score(result.text, item.answer, item.answer_kind)
        scored.append(
            Outcome(
                model=record.model_label,
                task=key[0],
                mode=record.mode,
                item_index=key[1],
                correct=correct,
                parsed=answer is not None,
                answer=answer,
                output_tokens=result.output_tokens,
                reasoning_tokens=result.reasoning_tokens,
                total_latency_ms=result.total_latency_ms,
                first_answer_ms=result.time_to_first_answer_token_ms,
                first_thinking_ms=result.time_to_first_thinking_ms,
                finish_reason=result.finish_reason,
            )
        )
    return scored


def select(
    scored: Sequence[Outcome],
    *,
    model: str | None = None,
    task: str | None = None,
    mode: str | None = None,
) -> list[Outcome]:
    return [
        outcome
        for outcome in scored
        if (model is None or outcome.model == model)
        and (task is None or outcome.task == task)
        and (mode is None or outcome.mode == mode)
    ]


def accuracy(scored: Sequence[Outcome]) -> Accuracy | None:
    """Accuracy with a Wilson 95% interval, or None when there is nothing to score."""
    if not scored:
        return None
    correct = sum(1 for outcome in scored if outcome.correct)
    point, low, high = wilson_interval(correct, len(scored))
    return Accuracy(correct=correct, trials=len(scored), point=point, low=low, high=high)


def paired(
    scored: Sequence[Outcome], *, lowest_mode: str, high_mode: str
) -> tuple[list[Outcome], list[Outcome]]:
    """The outcomes for items answered in both modes, as (lowest, high) over the same items.

    Every comparison between the two modes goes through this, so a call that failed in one mode
    can never tilt a ratio by leaving its partner behind. Losing the longest reasoning traces to
    the output limit, for example, would otherwise understate what high reasoning cost.
    """
    high_keys = {(o.model, o.task, o.item_index) for o in scored if o.mode == high_mode}
    low_keys = {(o.model, o.task, o.item_index) for o in scored if o.mode == lowest_mode}
    shared = high_keys & low_keys
    return (
        [o for o in scored if o.mode == lowest_mode and (o.model, o.task, o.item_index) in shared],
        [o for o in scored if o.mode == high_mode and (o.model, o.task, o.item_index) in shared],
    )


def gain(scored: Sequence[Outcome], *, lowest_mode: str, high_mode: str) -> Gain | None:
    """The paired change in accuracy, over items answered in both modes.

    The same items run in both modes, so an unpaired interval would be wider than the data
    warrants. Only items with a successful call in both modes are counted, so a failure in one
    mode never counts as a wrong answer in the other.
    """
    high = {(o.model, o.task, o.item_index): o.correct for o in scored if o.mode == high_mode}
    low = {(o.model, o.task, o.item_index): o.correct for o in scored if o.mode == lowest_mode}
    shared = sorted(set(high) & set(low))
    if not shared:
        return None
    both = sum(1 for key in shared if high[key] and low[key])
    only_high = sum(1 for key in shared if high[key] and not low[key])
    only_low = sum(1 for key in shared if low[key] and not high[key])
    neither = len(shared) - both - only_high - only_low
    change, low_bound, high_bound = paired_difference_interval(both, only_high, only_low, neither)
    return Gain(pairs=len(shared), change=change, low=low_bound, high=high_bound)


def median(values: Sequence[float]) -> float | None:
    numbers = [value for value in values if value is not None]
    return statistics.median(numbers) if numbers else None


def percentile_90(values: Sequence[float]) -> float | None:
    """The nearest-rank 90th percentile: always a value that was actually measured."""
    numbers = sorted(value for value in values if value is not None)
    if not numbers:
        return None
    rank = min(len(numbers), max(1, math.ceil(P90 * len(numbers))))
    return numbers[rank - 1]


def mean(values: Sequence[float]) -> float | None:
    numbers = [value for value in values if value is not None]
    return statistics.fmean(numbers) if numbers else None


def _ratio(high: float | None, low: float | None) -> float | None:
    if high is None or low is None or low == 0:
        return None
    return high / low


@dataclass(frozen=True)
class Comparison:
    """High reasoning against the lowest setting, for one model and task."""

    model: str
    task: str
    accuracy_change_points: float | None
    extra_output_tokens: float | None
    output_token_multiple: float | None
    latency_multiple: float | None
    first_answer_token_multiple: float | None

    @property
    def points_per_thousand_tokens(self) -> float | None:
        """Accuracy points gained for every 1,000 extra output tokens spent."""
        if self.accuracy_change_points is None or not self.extra_output_tokens:
            return None
        if self.extra_output_tokens < 0:
            # High reasoning spent fewer tokens, so there is no cost to divide by. The change
            # itself is still reported; a cost per point would be a negative number that reads
            # as the worst result when it is the best.
            return None
        return self.accuracy_change_points / (self.extra_output_tokens / TOKEN_BLOCK)


def compare(
    scored: Sequence[Outcome], *, model: str, task: str, lowest_mode: str, high_mode: str
) -> Comparison:
    """Every derived ratio in specification section 7.5, for one model and task."""
    cell = select(scored, model=model, task=task)
    low, high = paired(cell, lowest_mode=lowest_mode, high_mode=high_mode)
    change = gain(cell, lowest_mode=lowest_mode, high_mode=high_mode)
    high_tokens = mean([outcome.output_tokens for outcome in high])
    low_tokens = mean([outcome.output_tokens for outcome in low])
    extra = None if high_tokens is None or low_tokens is None else high_tokens - low_tokens
    return Comparison(
        model=model,
        task=task,
        accuracy_change_points=None if change is None else change.change_points,
        extra_output_tokens=extra,
        output_token_multiple=_ratio(high_tokens, low_tokens),
        latency_multiple=_ratio(
            median([outcome.total_latency_ms for outcome in high]),
            median([outcome.total_latency_ms for outcome in low]),
        ),
        first_answer_token_multiple=_ratio(
            median([outcome.first_answer_ms for outcome in high]),
            median([outcome.first_answer_ms for outcome in low]),
        ),
    )


def token_multiple(scored: Sequence[Outcome], *, task: str, lowest_mode: str, high_mode: str):
    """Billed output tokens for a task, high against lowest, over every model.

    Both sides are summed over the same items, so a call that failed in one mode cannot shrink
    one denominator and inflate the multiple.
    """
    low, high = paired(select(scored, task=task), lowest_mode=lowest_mode, high_mode=high_mode)
    return _ratio(
        float(sum(outcome.output_tokens for outcome in high)),
        float(sum(outcome.output_tokens for outcome in low)),
    )
