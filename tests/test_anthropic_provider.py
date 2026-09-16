import anthropic
import pytest

from lab.providers.anthropic_provider import AnthropicProvider, build_params
from lab.providers.base import (
    AuthenticationError,
    GenerationRequest,
    InvalidRequestError,
    RateLimitError,
    ServerError,
    StreamInterruptedError,
    UnsupportedSettingError,
)
from tests.fakes import REQUEST, RecordingEndpoint, event, http_response, ns, ticking_clock


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "anthropic",
        "model": "claude-sonnet-5",
        "system": "Reply briefly.",
        "prompt": "Say ready",
        "max_output_tokens": 1024,
        "reasoning": "high",
        "show_thinking": True,
    }
    return GenerationRequest(**{**fields, **overrides})


def _events(stop_reason="end_turn", details=True):
    return [
        event(
            "message_start",
            message=ns(
                model="claude-sonnet-5",
                usage=ns(
                    input_tokens=20,
                    cache_read_input_tokens=0,
                    output_tokens=1,
                    output_tokens_details=None,
                ),
            ),
        ),
        event("content_block_start", content_block=ns(type="thinking")),
        event("content_block_delta", delta=ns(type="thinking_delta", thinking="Hmm")),
        event("content_block_delta", delta=ns(type="signature_delta", signature="sig")),
        event("content_block_stop"),
        event("content_block_start", content_block=ns(type="text")),
        event("content_block_delta", delta=ns(type="text_delta", text="rea")),
        event("content_block_delta", delta=ns(type="text_delta", text="dy")),
        event(
            "message_delta",
            delta=ns(stop_reason=stop_reason),
            usage=ns(
                input_tokens=None,
                cache_read_input_tokens=None,
                output_tokens=55,
                output_tokens_details=ns(thinking_tokens=50) if details else None,
            ),
        ),
        event("message_stop"),
    ]


def _provider(endpoint: RecordingEndpoint) -> AnthropicProvider:
    return AnthropicProvider(ns(messages=ns(create=endpoint)), clock=ticking_clock())


def test_reasoning_level_maps_to_effort_with_adaptive_thinking():
    assert build_params(_request()) == {
        "model": "claude-sonnet-5",
        "max_tokens": 1024,
        "system": "Reply briefly.",
        "messages": [{"role": "user", "content": "Say ready"}],
        "stream": True,
        "thinking": {"type": "adaptive", "display": "summarized"},
        "output_config": {"effort": "high"},
    }


def test_hidden_thinking_uses_omitted_display():
    params = build_params(_request(show_thinking=False))

    assert params["thinking"] == {"type": "adaptive", "display": "omitted"}


def test_reasoning_off_disables_thinking_without_effort():
    params = build_params(_request(reasoning="off", show_thinking=False, system=None))

    assert params["thinking"] == {"type": "disabled"}
    assert "output_config" not in params
    assert "system" not in params


def test_temperature_is_sent_when_set():
    request = _request(
        model="claude-haiku-4-5-20251001", reasoning="off", show_thinking=False, temperature=0.0
    )

    assert build_params(request)["temperature"] == 0.0


def test_streamed_message_becomes_neutral_result():
    result = _provider(RecordingEndpoint(_events())).generate(_request())

    assert result.text == "ready"
    assert result.model_returned == "claude-sonnet-5"
    assert (result.input_tokens, result.output_tokens) == (20, 55)
    assert (result.reasoning_tokens, result.cached_input_tokens) == (50, 0)
    assert result.time_to_first_thinking_ms == 1000.0
    assert result.time_to_first_answer_token_ms == 2000.0
    assert result.total_latency_ms == 3000.0
    assert result.finish_reason == "stop"


def test_missing_thinking_breakdown_is_reported_as_none():
    result = _provider(RecordingEndpoint(_events(details=False))).generate(_request())

    assert result.reasoning_tokens is None


@pytest.mark.parametrize(
    ("stop_reason", "expected"),
    [
        ("max_tokens", "length"),
        ("model_context_window_exceeded", "length"),
        ("refusal", "content_filter"),
        ("pause_turn", "other"),
    ],
)
def test_stop_reasons_map_to_finish_reasons(stop_reason, expected):
    result = _provider(RecordingEndpoint(_events(stop_reason=stop_reason))).generate(_request())

    assert result.finish_reason == expected


def test_temperature_on_current_model_fails_before_calling_the_api():
    endpoint = RecordingEndpoint(_events())

    with pytest.raises(UnsupportedSettingError, match="temperature"):
        _provider(endpoint).generate(_request(temperature=0.0))

    assert endpoint.kwargs is None


def _overloaded_in_stream() -> anthropic.APIStatusError:
    body = {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
    return anthropic.APIStatusError("Overloaded", response=http_response(200), body=body)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            anthropic.RateLimitError(
                "slow", response=http_response(429, {"retry-after": "3"}), body=None
            ),
            RateLimitError,
        ),
        (
            anthropic.AuthenticationError("bad key", response=http_response(401), body=None),
            AuthenticationError,
        ),
        (
            anthropic.BadRequestError("bad", response=http_response(400), body=None),
            InvalidRequestError,
        ),
        (
            anthropic.APIStatusError("Overloaded", response=http_response(529), body=None),
            ServerError,
        ),
        (_overloaded_in_stream(), ServerError),
        (
            anthropic.APIStatusError(
                "limit", response=http_response(200), body={"error": {"type": "rate_limit_error"}}
            ),
            RateLimitError,
        ),
        (anthropic.APIConnectionError(request=REQUEST), StreamInterruptedError),
    ],
)
def test_sdk_errors_map_to_neutral_errors(error, expected):
    with pytest.raises(expected):
        _provider(RecordingEndpoint(error=error)).generate(_request())


def test_overload_part_way_through_stream_is_retryable():
    endpoint = RecordingEndpoint(_events()[:4], mid_stream_error=_overloaded_in_stream())

    with pytest.raises(ServerError):
        _provider(endpoint).generate(_request())


def test_stream_ending_before_message_delta_is_interrupted():
    with pytest.raises(StreamInterruptedError):
        _provider(RecordingEndpoint(_events()[:6])).generate(_request())


def test_default_client_disables_sdk_retries(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    assert AnthropicProvider()._client.max_retries == 0
