"""The S1 E5 measurements, on timings already taken.

Standard library only, so the tests can check every calculation on synthetic numbers without
torch, transformers, a model download, or a clock.

Every measure here was fixed before any timing was taken:

- Reading is one forward pass over an N-token prompt. Only the last position's next-token scores
  are computed, because that is all a next-token prediction needs and it is what generation does
  when it reads its own prompt. Time per input token is the total time divided by N.
- Writing is greedy generation of exactly N new tokens from an 8-token prompt, with the key and
  value cache on, which is the default. Time per output token is the generation time divided by
  N. The 8-token prompt is read inside that time, which is why the prompt is kept so short.
- Every measured condition runs twice untimed as a warm-up, then five times timed. The figure
  reported is the median, with the minimum and maximum beside it.
- A gap smaller than 10% between two figures is called no gap at all, and the charts highlight
  nothing.
"""

import time
from collections.abc import Callable, Sequence
from statistics import median

# GPT-2 can attend over at most this many tokens, prompt and output together.
CONTEXT_TOKENS = 1024
WARMUPS = 2
REPEATS = 5
# The prompt for every writing condition, so the runs differ only in how much is written.
WRITING_PROMPT_TOKENS = 8
HEADLINE_TOKENS = 512
SWEEP_TOKENS = (64, 128, 256, 512, 896)
# Two figures within this fraction of each other are treated as the same.
SAME_WITHIN = 0.10
MILLISECONDS = 1000


def check_context(prompt_tokens: int, new_tokens: int, limit: int = CONTEXT_TOKENS) -> None:
    """Refuse a condition whose prompt and output together do not fit in the context."""
    if prompt_tokens < 1 or new_tokens < 0:
        raise ValueError(f"Need a prompt of at least 1 token, got {prompt_tokens} and {new_tokens}")
    if prompt_tokens + new_tokens > limit:
        raise ValueError(
            f"{prompt_tokens} prompt tokens plus {new_tokens} new tokens is "
            f"{prompt_tokens + new_tokens}, over the {limit}-token context"
        )


def cut_to_length(ids: Sequence[int], count: int) -> list[int]:
    """The first `count` token ids, so every run sees the same tokens."""
    if count > len(ids):
        raise ValueError(f"Asked for {count} tokens but the text has only {len(ids)}")
    return list(ids[:count])


def per_token_ms(total_seconds: float, tokens: int) -> float:
    if tokens < 1:
        raise ValueError("A per-token time needs at least one token")
    return total_seconds / tokens * MILLISECONDS


def spread(values: Sequence[float]) -> dict[str, float]:
    """Median, minimum and maximum of a set of timings."""
    if not values:
        raise ValueError("Cannot summarise no timings")
    return {"median": float(median(values)), "min": float(min(values)), "max": float(max(values))}


def summarise(seconds: Sequence[float], tokens: int) -> dict[str, dict[str, float]]:
    """A condition's total time, and its time per token, each as median, minimum and maximum."""
    total = spread(seconds)
    return {
        "total_s": total,
        "per_token_ms": {key: per_token_ms(value, tokens) for key, value in total.items()},
    }


def timed(
    run: Callable[[], object],
    warmups: int = WARMUPS,
    repeats: int = REPEATS,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[list[float], object]:
    """Run untimed `warmups` times, then time `repeats` runs. Also returns the last result."""
    for _ in range(warmups):
        run()
    seconds = []
    result = None
    for _ in range(repeats):
        start = clock()
        result = run()
        seconds.append(clock() - start)
    return seconds, result


def ratio(slower: float, faster: float) -> float:
    if faster <= 0:
        raise ValueError("A ratio needs a positive denominator")
    return slower / faster


def same_within(first: float, second: float, tolerance: float = SAME_WITHIN) -> bool:
    """Whether the larger of two figures is no more than `tolerance` above the smaller."""
    larger, smaller = max(first, second), min(first, second)
    return larger <= smaller * (1 + tolerance)


def slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Least-squares slope of ys against xs."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("A slope needs at least two matching points")
    mean_x, mean_y = sum(xs) / len(xs), sum(ys) / len(ys)
    spread_x = sum((x - mean_x) ** 2 for x in xs)
    if spread_x == 0:
        raise ValueError("A slope needs at least two different x values")
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / spread_x
