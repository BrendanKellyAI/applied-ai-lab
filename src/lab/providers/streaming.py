"""Timing a streamed response and assembling the neutral result."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from lab.providers.base import FinishReason, GenerationRequest, GenerationResult, request_hash


class StreamClock:
    """Records dispatch, first thinking content, first answer token, and completion."""

    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        self._clock = clock
        self._started = clock()
        self._first_thinking: float | None = None
        self._first_answer: float | None = None

    def mark_thinking(self) -> None:
        if self._first_thinking is None:
            self._first_thinking = self._clock()

    def mark_answer(self) -> None:
        if self._first_answer is None:
            self._first_answer = self._clock()

    def elapsed_ms(self, moment: float | None) -> float | None:
        return None if moment is None else (moment - self._started) * 1000

    def finish(self) -> "StreamTimes":
        return StreamTimes(
            first_answer_token_ms=self.elapsed_ms(self._first_answer),
            first_thinking_ms=self.elapsed_ms(self._first_thinking),
            total_ms=(self._clock() - self._started) * 1000,
        )


@dataclass(frozen=True)
class StreamTimes:
    first_answer_token_ms: float | None
    first_thinking_ms: float | None
    total_ms: float


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None
    cached_input_tokens: int | None


def build_result(
    request: GenerationRequest,
    *,
    text: str,
    model_returned: str,
    usage: Usage,
    finish_reason: FinishReason,
    times: StreamTimes,
) -> GenerationResult:
    return GenerationResult(
        request_hash=request_hash(request),
        provider=request.provider,
        model_requested=request.model,
        model_returned=model_returned,
        text=text,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        reasoning_tokens=usage.reasoning_tokens,
        cached_input_tokens=usage.cached_input_tokens,
        time_to_first_answer_token_ms=times.first_answer_token_ms,
        time_to_first_thinking_ms=times.first_thinking_ms,
        total_latency_ms=times.total_ms,
        finish_reason=finish_reason,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )
