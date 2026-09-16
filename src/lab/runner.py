"""Runs planned calls with caching, per-provider pacing, retries, and resume."""

import logging
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from lab.cache import ResponseCache
from lab.config import ProviderLimits
from lab.plan import PlanError, PlannedCall, ensure_unique_call_ids
from lab.providers.base import (
    GenerationResult,
    Provider,
    ProviderError,
    RetryableError,
    request_hash,
)
from lab.raw_log import RawLogWriter, RunRecord, latest_successful, load_records

logger = logging.getLogger(__name__)

Sleep = Callable[[float], None]
Clock = Callable[[], float]


@dataclass(frozen=True)
class RunnerSettings:
    max_attempts: int = 5
    backoff_multiplier_seconds: float = 1.0
    max_backoff_seconds: float = 60.0


@dataclass(frozen=True)
class TokenTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_input_tokens: int = 0

    def add(self, result: GenerationResult) -> "TokenTotals":
        return TokenTotals(
            input_tokens=self.input_tokens + result.input_tokens,
            output_tokens=self.output_tokens + result.output_tokens,
            reasoning_tokens=self.reasoning_tokens + (result.reasoning_tokens or 0),
            cached_input_tokens=self.cached_input_tokens + (result.cached_input_tokens or 0),
        )


@dataclass(frozen=True)
class RunSummary:
    planned: int
    already_complete: int
    cached: int
    made: int
    failed: int
    # Tokens billed by calls made in this run. Cached and already complete calls are excluded.
    tokens_by_provider: Mapping[str, TokenTotals] = field(default_factory=dict)


@dataclass(frozen=True)
class _Outcome:
    kind: Literal["api", "cache", "failed"]
    provider: str
    result: GenerationResult | None


class RateLimiter:
    """Spaces requests evenly to stay within a requests-per-minute limit. Thread-safe."""

    def __init__(self, requests_per_minute: int, *, clock: Clock, sleep: Sleep) -> None:
        self._interval = 60.0 / requests_per_minute
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next_slot: float | None = None

    def acquire(self) -> None:
        with self._lock:
            now = self._clock()
            slot = now if self._next_slot is None else max(now, self._next_slot)
            self._next_slot = slot + self._interval
        if slot > now:
            self._sleep(slot - now)


class Runner:
    def __init__(
        self,
        *,
        providers: Mapping[str, Provider],
        cache: ResponseCache,
        limits: Mapping[str, ProviderLimits],
        settings: RunnerSettings | None = None,
        sleep: Sleep = time.sleep,
        clock: Clock = time.monotonic,
    ) -> None:
        self._providers = providers
        self._cache = cache
        self._limits = limits
        self._settings = settings or RunnerSettings()
        self._sleep = sleep
        self._clock = clock
        self._backoff = wait_random_exponential(
            multiplier=self._settings.backoff_multiplier_seconds,
            max=self._settings.max_backoff_seconds,
        )

    def run(
        self, calls: Sequence[PlannedCall], raw_path: Path, *, use_cache: bool = True
    ) -> RunSummary:
        """Run every call not already completed in `raw_path`.

        Every call is validated before any is sent. Results are appended to `raw_path` as they
        complete. With `use_cache=False`, cached responses are ignored and new calls are made.
        """
        self._validate(calls)
        completed = {
            call_id: record.request_hash
            for call_id, record in latest_successful(load_records(raw_path)).items()
        }
        pending = [c for c in calls if completed.get(c.call_id) != request_hash(c.request)]

        outcomes: list[_Outcome] = []
        with RawLogWriter(raw_path) as writer:
            to_send = []
            for call in pending:
                cached = self._cache.get(call.request) if use_cache else None
                if cached is None:
                    to_send.append(call)
                    continue
                writer.append(RunRecord.for_call(call, source="cache", attempts=0, result=cached))
                outcomes.append(_Outcome("cache", call.request.provider, cached))
            outcomes.extend(self._send_all(to_send, writer))

        return _summarise(len(calls), len(calls) - len(pending), outcomes)

    def _validate(self, calls: Sequence[PlannedCall]) -> None:
        ensure_unique_call_ids(calls)
        for call in calls:
            provider = self._providers.get(call.request.provider)
            if provider is None:
                raise PlanError(
                    f"No provider configured for '{call.request.provider}'. "
                    "Check its API key or run with --provider."
                )
            provider.validate(call.request)

    def _send_all(self, calls: Sequence[PlannedCall], writer: RawLogWriter) -> list[_Outcome]:
        if not calls:
            return []
        names = sorted({call.request.provider for call in calls})
        limits = {name: self._limits.get(name, ProviderLimits()) for name in names}
        limiters = {
            name: RateLimiter(
                limits[name].requests_per_minute, clock=self._clock, sleep=self._sleep
            )
            for name in names
        }
        executors = {
            name: ThreadPoolExecutor(
                max_workers=limits[name].max_concurrency, thread_name_prefix=f"lab-{name}"
            )
            for name in names
        }
        try:
            futures: list[Future[_Outcome]] = [
                executors[call.request.provider].submit(
                    self._send_one, call, limiters[call.request.provider], writer
                )
                for call in calls
            ]
            return [future.result() for future in as_completed(futures)]
        except BaseException:
            # Stop queued calls; calls already in flight finish and are logged.
            for executor in executors.values():
                executor.shutdown(wait=True, cancel_futures=True)
            raise
        finally:
            for executor in executors.values():
                executor.shutdown(wait=True)

    def _send_one(self, call: PlannedCall, limiter: RateLimiter, writer: RawLogWriter) -> _Outcome:
        provider_name = call.request.provider
        provider = self._providers[provider_name]
        attempts = 0
        try:
            for attempt in self._retrying():
                with attempt:
                    attempts = attempt.retry_state.attempt_number
                    limiter.acquire()
                    result = provider.generate(call.request)
        except ProviderError as exc:
            return self._record_failure(call, attempts, f"{type(exc).__name__}: {exc}", writer)

        if result.error is not None:
            return self._record_failure(call, attempts, result.error, writer)
        self._cache.put(call.request, result)
        writer.append(RunRecord.for_call(call, source="api", attempts=attempts, result=result))
        return _Outcome("api", provider_name, result)

    def _record_failure(
        self, call: PlannedCall, attempts: int, error: str, writer: RawLogWriter
    ) -> _Outcome:
        logger.warning("Call %s failed after %d attempt(s): %s", call.call_id, attempts, error)
        writer.append(RunRecord.for_call(call, source="api", attempts=attempts, error=error))
        return _Outcome("failed", call.request.provider, None)

    def _retrying(self) -> Retrying:
        return Retrying(
            retry=retry_if_exception_type(RetryableError),
            stop=stop_after_attempt(self._settings.max_attempts),
            wait=self._wait,
            sleep=self._sleep,
            reraise=True,
        )

    def _wait(self, retry_state: RetryCallState) -> float:
        backoff = self._backoff(retry_state)
        error = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = getattr(error, "retry_after_seconds", None) or 0.0
        return max(backoff, retry_after)


def _summarise(planned: int, already_complete: int, outcomes: list[_Outcome]) -> RunSummary:
    tokens: dict[str, TokenTotals] = {}
    for outcome in outcomes:
        if outcome.kind == "api" and outcome.result is not None:
            tokens[outcome.provider] = tokens.get(outcome.provider, TokenTotals()).add(
                outcome.result
            )
    return RunSummary(
        planned=planned,
        already_complete=already_complete,
        cached=sum(1 for o in outcomes if o.kind == "cache"),
        made=sum(1 for o in outcomes if o.kind == "api"),
        failed=sum(1 for o in outcomes if o.kind == "failed"),
        tokens_by_provider=tokens,
    )


def format_summary(summary: RunSummary) -> str:
    lines = [
        f"Calls planned:          {summary.planned}",
        f"Already complete:       {summary.already_complete}",
        f"Served from cache:      {summary.cached}",
        f"Calls made:             {summary.made}",
        f"Calls failed:           {summary.failed}",
    ]
    if summary.tokens_by_provider:
        lines.append("Tokens billed by calls made in this run:")
        for name, totals in sorted(summary.tokens_by_provider.items()):
            lines.append(
                f"  {name}: input {totals.input_tokens:,} "
                f"(cached {totals.cached_input_tokens:,}), "
                f"output {totals.output_tokens:,} "
                f"(reasoning {totals.reasoning_tokens:,})"
            )
    return "\n".join(lines)
