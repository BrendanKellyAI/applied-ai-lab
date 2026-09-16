"""A deterministic, offline provider for tests and dry runs. Never makes a network call."""

import threading
import time
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import UTC, datetime

from lab.providers.base import (
    GenerationRequest,
    GenerationResult,
    ReasoningLevel,
    UnsupportedSettingError,
    request_hash,
)

_REASONING_TOKENS = {"low": 10, "medium": 20, "high": 40}
ALL_REASONING: tuple[ReasoningLevel | None, ...] = ("off", "low", "medium", "high", None)


def _echo(request: GenerationRequest) -> str:
    return f"mock answer for {request.model}"


class MockProvider:
    """Offline provider.

    `failures` maps a prompt to exceptions raised, in order, on successive calls with that prompt.
    """

    def __init__(
        self,
        *,
        respond: Callable[[GenerationRequest], str] = _echo,
        failures: Mapping[str, Sequence[BaseException]] | None = None,
        supported_reasoning: Collection[ReasoningLevel | None] = ALL_REASONING,
        supports_temperature: bool = True,
        delay_seconds: float = 0.0,
        error_text: str | None = None,
    ) -> None:
        self._respond = respond
        self._pending_failures = {
            prompt: list(errors) for prompt, errors in (failures or {}).items()
        }
        self._supported_reasoning = tuple(supported_reasoning)
        self._supports_temperature = supports_temperature
        self._delay_seconds = delay_seconds
        self._error_text = error_text
        self._lock = threading.Lock()
        self._in_flight = 0
        self.calls: list[GenerationRequest] = []
        self.max_in_flight = 0

    def validate(self, request: GenerationRequest) -> None:
        if request.reasoning not in self._supported_reasoning:
            raise UnsupportedSettingError(
                f"{request.model} does not support reasoning={request.reasoning!r}"
            )
        if request.temperature is not None and not self._supports_temperature:
            raise UnsupportedSettingError(f"{request.model} does not accept a temperature")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        started = time.perf_counter()
        with self._lock:
            self.calls.append(request)
            self._in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self._in_flight)
            pending = self._pending_failures.get(request.prompt)
            failure = pending.pop(0) if pending else None
        try:
            if failure is not None:
                raise failure
            if self._delay_seconds:
                time.sleep(self._delay_seconds)
            return self._result(request, started)
        finally:
            with self._lock:
                self._in_flight -= 1

    def _result(self, request: GenerationRequest, started: float) -> GenerationResult:
        text = self._respond(request)
        latency_ms = (time.perf_counter() - started) * 1000
        reasoning_tokens = _REASONING_TOKENS.get(request.reasoning or "off")
        prompt_tokens = len(request.prompt.split()) + len((request.system or "").split())
        return GenerationResult(
            request_hash=request_hash(request),
            provider=request.provider,
            model_requested=request.model,
            model_returned=f"{request.model}-mock-0001",
            text=text,
            input_tokens=prompt_tokens,
            output_tokens=len(text.split()) + (reasoning_tokens or 0),
            reasoning_tokens=reasoning_tokens,
            cached_input_tokens=0,
            time_to_first_token_ms=latency_ms,
            time_to_first_thinking_ms=latency_ms if reasoning_tokens else None,
            total_latency_ms=latency_ms,
            finish_reason="stop",
            timestamp_utc=datetime.now(UTC).isoformat(),
            error=self._error_text,
        )
