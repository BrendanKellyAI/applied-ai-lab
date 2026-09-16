import openai
import pytest

from lab.providers.base import (
    AuthenticationError,
    GenerationRequest,
    InvalidRequestError,
    RateLimitError,
    ServerError,
    StreamInterruptedError,
    UnsupportedSettingError,
    request_hash,
)
from lab.providers.openai_provider import OpenAIProvider, build_params
from tests.fakes import REQUEST, RecordingEndpoint, event, http_response, ns, ticking_clock


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "openai",
        "model": "gpt-5.6-luna",
        "system": "Reply briefly.",
        "prompt": "Say ready",
        "max_output_tokens": 500,
        "reasoning": "low",
        "show_thinking": True,
    }
    return GenerationRequest(**{**fields, **overrides})


def _final(status="completed", reason=None, reasoning_tokens=30):
    return ns(
        status=status,
        incomplete_details=ns(reason=reason) if reason else None,
        model="gpt-5.6-luna-2026-08-01",
        usage=ns(
            input_tokens=12,
            output_tokens=40,
            output_tokens_details=ns(reasoning_tokens=reasoning_tokens),
            input_tokens_details=ns(cached_tokens=0),
        ),
    )


def _events(final=None):
    return [
        event("response.created"),
        event("response.output_item.added", item=ns(type="reasoning")),
        event("response.reasoning_summary_text.delta", delta="Thinking"),
        event("response.output_item.added", item=ns(type="message")),
        event("response.output_text.delta", delta="rea"),
        event("response.output_text.delta", delta="dy"),
        event("response.completed", response=final or _final()),
    ]


def _provider(endpoint: RecordingEndpoint) -> OpenAIProvider:
    return OpenAIProvider(ns(responses=ns(create=endpoint)), clock=ticking_clock())


def test_builds_responses_params_without_stored_history():
    params = build_params(_request())

    assert params == {
        "model": "gpt-5.6-luna",
        "input": "Say ready",
        "instructions": "Reply briefly.",
        "max_output_tokens": 500,
        "stream": True,
        "store": False,
        "reasoning": {"effort": "low", "summary": "auto"},
    }


def test_reasoning_off_maps_to_effort_none_without_summary():
    params = build_params(_request(reasoning="off", show_thinking=False, system=None))

    assert params["reasoning"] == {"effort": "none"}
    assert "instructions" not in params
    assert "temperature" not in params


def test_temperature_is_sent_when_set():
    assert build_params(_request(temperature=0.0))["temperature"] == 0.0


def test_streamed_response_becomes_neutral_result():
    endpoint = RecordingEndpoint(_events())
    request = _request()

    result = _provider(endpoint).generate(request)

    assert endpoint.kwargs == build_params(request)
    assert result.text == "ready"
    assert result.request_hash == request_hash(request)
    assert result.model_returned == "gpt-5.6-luna-2026-08-01"
    assert (result.input_tokens, result.output_tokens) == (12, 40)
    assert (result.reasoning_tokens, result.cached_input_tokens) == (30, 0)
    assert result.time_to_first_thinking_ms == 1000.0
    assert result.time_to_first_answer_token_ms == 2000.0
    assert result.total_latency_ms == 3000.0
    assert result.finish_reason == "stop"


@pytest.mark.parametrize(
    ("reason", "expected"),
    [("max_output_tokens", "length"), ("content_filter", "content_filter"), ("other", "other")],
)
def test_incomplete_response_maps_finish_reason(reason, expected):
    final = _final(status="incomplete", reason=reason)
    events = [
        event("response.output_text.delta", delta="x"),
        event("response.incomplete", response=final),
    ]

    result = _provider(RecordingEndpoint(events)).generate(_request())

    assert result.finish_reason == expected


def test_unsupported_setting_fails_before_calling_the_api():
    endpoint = RecordingEndpoint(_events())

    with pytest.raises(UnsupportedSettingError):
        _provider(endpoint).generate(
            _request(model="gpt-6-astra", reasoning="off", show_thinking=False)
        )

    assert endpoint.kwargs is None


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            openai.RateLimitError(
                "slow", response=http_response(429, {"retry-after": "7"}), body=None
            ),
            RateLimitError,
        ),
        (
            openai.AuthenticationError("bad key", response=http_response(401), body=None),
            AuthenticationError,
        ),
        (
            openai.BadRequestError("bad", response=http_response(400), body=None),
            InvalidRequestError,
        ),
        (openai.InternalServerError("down", response=http_response(503), body=None), ServerError),
        (openai.APIConnectionError(request=REQUEST), StreamInterruptedError),
    ],
)
def test_sdk_errors_map_to_neutral_errors(error, expected):
    with pytest.raises(expected):
        _provider(RecordingEndpoint(error=error)).generate(_request())


def test_rate_limit_carries_retry_after():
    error = openai.RateLimitError(
        "slow", response=http_response(429, {"retry-after": "7"}), body=None
    )

    with pytest.raises(RateLimitError) as caught:
        _provider(RecordingEndpoint(error=error)).generate(_request())

    assert caught.value.retry_after_seconds == 7.0


def test_error_part_way_through_stream_is_retryable():
    endpoint = RecordingEndpoint(
        _events()[:3], mid_stream_error=openai.APIConnectionError(request=REQUEST)
    )

    with pytest.raises(StreamInterruptedError):
        _provider(endpoint).generate(_request())


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("rate_limit_exceeded", RateLimitError),
        ("server_error", ServerError),
        ("invalid_prompt", InvalidRequestError),
    ],
)
def test_failed_response_event_maps_error_code(code, expected):
    failed = ns(error=ns(code=code, message="failed"))
    events = [event("response.failed", response=failed)]

    with pytest.raises(expected):
        _provider(RecordingEndpoint(events)).generate(_request())


def test_stream_without_final_response_is_interrupted():
    with pytest.raises(StreamInterruptedError):
        _provider(RecordingEndpoint(_events()[:-1])).generate(_request())


def test_default_client_disables_sdk_retries(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")

    provider = OpenAIProvider()

    assert provider._client.max_retries == 0
