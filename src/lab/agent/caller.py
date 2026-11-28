"""Model calls for the agent loop: cached, paced per provider, retried on transient errors.

The batch runner plans calls up front; an agent's next call depends on the last one, so the
loop calls one at a time through this. Every response is cached by request hash, so a replayed
run with the same tool results costs nothing.
"""

import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from lab.cache import ResponseCache
from lab.providers.base import GenerationRequest, GenerationResult, Provider, RetryableError
from lab.runner import RateLimiter


@dataclass
class Spend:
    """Tokens billed by calls made now, not served from the cache."""

    calls: int = 0
    cached: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, result: GenerationResult) -> None:
        with self.lock:
            self.calls += 1
            self.input_tokens += result.input_tokens
            self.output_tokens += result.output_tokens


class BudgetExceeded(RuntimeError):
    """Spend on new calls passed the approved budget; no further call is made."""


class ModelCaller:
    def __init__(
        self,
        providers: Mapping[str, Provider],
        cache: ResponseCache,
        *,
        requests_per_minute: int = 120,
        max_attempts: int = 5,
        sleep=time.sleep,
        budget: float | None = None,
        prices: Mapping[str, tuple[float, float]] | None = None,
    ) -> None:
        """`budget` caps spend on new calls, priced per model by `prices` (input, output per
        million tokens). With no budget, nothing is capped (mock and cache-only runs)."""
        self._providers = providers
        self._cache = cache
        self._limiters = {
            name: RateLimiter(requests_per_minute, clock=time.monotonic, sleep=sleep)
            for name in providers
        }
        self._max_attempts = max_attempts
        self._sleep = sleep
        self.spend = Spend()
        self._budget = budget
        self._prices = dict(prices or {})
        self._spent = 0.0

    @property
    def providers(self) -> Mapping[str, Provider]:
        return self._providers

    @property
    def cache(self) -> ResponseCache:
        return self._cache

    def __call__(self, request: GenerationRequest) -> tuple[GenerationResult, str]:
        cached = self._cache.get(request)
        if cached is not None:
            with self.spend.lock:
                self.spend.cached += 1
            return cached, "cache"
        if self._budget is not None and self._spent >= self._budget:
            raise BudgetExceeded(f"spent {self._spent:.4f} of the {self._budget:.2f} budget")
        provider = self._providers[request.provider]
        provider.validate(request)
        for attempt in Retrying(
            retry=retry_if_exception_type(RetryableError),
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_random_exponential(multiplier=1, max=60),
            sleep=self._sleep,
            reraise=True,
        ):
            with attempt:
                self._limiters[request.provider].acquire()
                result = provider.generate(request)
        self._cache.put(request, result)
        self.spend.add(result)
        price_in, price_out = self._prices.get(request.model, (0.0, 0.0))
        with self.spend.lock:
            self._spent += (result.input_tokens * price_in + result.output_tokens * price_out) / 1e6
        return result, "api"
