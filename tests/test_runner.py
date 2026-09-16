import pytest

from lab.cache import ResponseCache
from lab.config import ProviderLimits
from lab.plan import PlanError
from lab.providers.base import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    UnsupportedSettingError,
)
from lab.providers.mock import MockProvider
from lab.raw_log import load_records
from lab.runner import RateLimiter, Runner, RunnerSettings, format_summary

FAST = {"mock": ProviderLimits(max_concurrency=1, requests_per_minute=600_000)}


def _runner(tmp_path, provider, *, limits=None, sleeps=None, settings=None) -> Runner:
    return Runner(
        providers={"mock": provider},
        cache=ResponseCache(tmp_path / ".cache"),
        limits=limits or FAST,
        settings=settings or RunnerSettings(),
        sleep=sleeps.append if sleeps is not None else (lambda _seconds: None),
    )


def _calls(make_call, count: int):
    return [make_call(item=i) for i in range(count)]


def test_fresh_run_makes_every_call_and_logs_results(tmp_path, make_call):
    provider = MockProvider()
    calls = _calls(make_call, 3)
    raw = tmp_path / "results" / "raw.jsonl"

    summary = _runner(tmp_path, provider).run(calls, raw)

    assert len(provider.calls) == 3
    assert (summary.planned, summary.made, summary.cached, summary.failed) == (3, 3, 0, 0)
    assert {r.call_id for r in load_records(raw)} == {c.call_id for c in calls}


def test_cache_hit_makes_no_call(tmp_path, make_call):
    calls = _calls(make_call, 2)
    _runner(tmp_path, MockProvider()).run(calls, tmp_path / "first" / "raw.jsonl")

    second_provider = MockProvider()
    raw = tmp_path / "second" / "raw.jsonl"
    summary = _runner(tmp_path, second_provider).run(calls, raw)

    assert second_provider.calls == []
    assert (summary.cached, summary.made) == (2, 0)
    assert {r.source for r in load_records(raw)} == {"cache"}


def test_cache_reads_can_be_disabled_for_fresh_runs(tmp_path, make_call):
    calls = _calls(make_call, 2)
    _runner(tmp_path, MockProvider()).run(calls, tmp_path / "first" / "raw.jsonl")

    provider = MockProvider()
    summary = _runner(tmp_path, provider).run(
        calls, tmp_path / "fresh" / "raw.jsonl", use_cache=False
    )

    assert len(provider.calls) == 2
    assert summary.made == 2


def test_interrupted_run_resumes_where_it_stopped(tmp_path, make_call):
    calls = _calls(make_call, 5)
    raw = tmp_path / "raw.jsonl"
    interrupted = MockProvider(failures={calls[2].request.prompt: [KeyboardInterrupt()]})

    with pytest.raises(KeyboardInterrupt):
        _runner(tmp_path, interrupted).run(calls, raw)
    completed_before = {r.call_id for r in load_records(raw) if r.result is not None}
    assert 0 < len(completed_before) < 5

    resumed = MockProvider()
    summary = _runner(tmp_path, resumed).run(calls, raw, use_cache=False)

    assert len(resumed.calls) == 5 - len(completed_before)
    assert summary.already_complete == len(completed_before)
    completed_after = {r.call_id for r in load_records(raw) if r.result is not None}
    assert completed_after == {c.call_id for c in calls}


def test_rate_limit_is_retried_then_succeeds(tmp_path, make_call):
    call = make_call()
    errors = [RateLimitError("slow down", status_code=429)] * 2
    provider = MockProvider(failures={call.request.prompt: errors})
    raw = tmp_path / "raw.jsonl"

    summary = _runner(tmp_path, provider).run([call], raw)

    assert len(provider.calls) == 3
    assert (summary.made, summary.failed) == (1, 0)
    assert load_records(raw)[0].attempts == 3


def test_retry_after_from_provider_is_honoured(tmp_path, make_call):
    call = make_call()
    error = RateLimitError("slow down", status_code=429, retry_after_seconds=42.0)
    provider = MockProvider(failures={call.request.prompt: [error]})
    sleeps: list[float] = []

    _runner(tmp_path, provider, sleeps=sleeps).run([call], tmp_path / "raw.jsonl")

    assert max(sleeps) >= 42.0


def test_authentication_error_is_not_retried(tmp_path, make_call):
    call = make_call()
    provider = MockProvider(failures={call.request.prompt: [AuthenticationError("bad key")]})
    raw = tmp_path / "raw.jsonl"

    summary = _runner(tmp_path, provider).run([call], raw)

    assert len(provider.calls) == 1
    assert summary.failed == 1
    record = load_records(raw)[0]
    assert record.result is None
    assert "AuthenticationError" in record.error


def test_gives_up_after_five_attempts_and_retries_on_resume(tmp_path, make_call):
    call = make_call()
    provider = MockProvider(failures={call.request.prompt: [ServerError("down")] * 10})
    raw = tmp_path / "raw.jsonl"

    first = _runner(tmp_path, provider).run([call], raw)

    assert len(provider.calls) == 5
    assert first.failed == 1
    assert ResponseCache(tmp_path / ".cache").get(call.request) is None

    second = _runner(tmp_path, MockProvider()).run([call], raw)

    assert (second.made, second.failed, second.already_complete) == (1, 0, 0)


def test_result_with_error_field_is_recorded_as_failure(tmp_path, make_call):
    call = make_call()
    provider = MockProvider(error_text="content filtered")

    summary = _runner(tmp_path, provider).run([call], tmp_path / "raw.jsonl")

    assert summary.failed == 1
    assert ResponseCache(tmp_path / ".cache").get(call.request) is None


def test_unsupported_setting_fails_before_any_call(tmp_path, make_call):
    calls = [make_call(item=0), make_call(item=1, reasoning="high")]
    provider = MockProvider(supported_reasoning=("off",))
    raw = tmp_path / "raw.jsonl"

    with pytest.raises(UnsupportedSettingError, match="high"):
        _runner(tmp_path, provider).run(calls, raw)

    assert provider.calls == []
    assert not raw.exists()


def test_missing_provider_fails_before_any_call(tmp_path, make_call):
    runner = Runner(providers={}, cache=ResponseCache(tmp_path), limits={})

    with pytest.raises(PlanError, match="mock"):
        runner.run([make_call()], tmp_path / "raw.jsonl")


def test_changed_request_for_same_call_is_run_again(tmp_path, make_call):
    raw = tmp_path / "raw.jsonl"
    original = make_call(item=0)
    _runner(tmp_path, MockProvider()).run([original], raw)

    changed = original.model_copy(
        update={"request": original.request.model_copy(update={"prompt": "new wording"})}
    )
    provider = MockProvider()
    summary = _runner(tmp_path, provider).run([changed], raw)

    assert len(provider.calls) == 1
    assert summary.already_complete == 0


def test_concurrency_limit_is_respected(tmp_path, make_call):
    provider = MockProvider(delay_seconds=0.05)
    limits = {"mock": ProviderLimits(max_concurrency=2, requests_per_minute=600_000)}

    _runner(tmp_path, provider, limits=limits).run(_calls(make_call, 6), tmp_path / "raw.jsonl")

    assert provider.max_in_flight == 2


def test_summary_counts_tokens_for_calls_made(tmp_path, make_call):
    calls = _calls(make_call, 2)
    summary = _runner(tmp_path, MockProvider()).run(calls, tmp_path / "raw.jsonl")

    expected_input = sum(len(c.request.prompt.split()) for c in calls)
    assert summary.tokens_by_provider["mock"].input_tokens == expected_input
    assert summary.tokens_by_provider["mock"].output_tokens > 0

    text = format_summary(summary)
    for label in ("planned", "cached", "made", "failed", "mock"):
        assert label in text


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_rate_limiter_spaces_requests_evenly():
    clock = FakeClock()
    limiter = RateLimiter(30, clock=clock, sleep=clock.sleep)

    for _ in range(3):
        limiter.acquire()

    assert clock.sleeps == [2.0, 2.0]


def test_rate_limiter_does_not_wait_after_idle_period():
    clock = FakeClock()
    limiter = RateLimiter(30, clock=clock, sleep=clock.sleep)

    limiter.acquire()
    clock.now = 10.0
    limiter.acquire()

    assert clock.sleeps == []
