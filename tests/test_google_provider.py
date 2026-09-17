import httpx
import pytest
from google.genai import errors as genai_errors
from google.genai import types

from lab.providers.base import (
    AuthenticationError,
    GenerationRequest,
    InvalidRequestError,
    RateLimitError,
    ServerError,
    StreamInterruptedError,
    UnsupportedSettingError,
)
from lab.providers.google_provider import GoogleProvider, build_config
from tests.fakes import RecordingEndpoint, ns, ticking_clock


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "google",
        "model": "gemini-3.5-flash-lite",
        "system": "Reply briefly.",
        "prompt": "Say ready",
        "max_output_tokens": 1024,
        "reasoning": "low",
        "show_thinking": True,
    }
    return GenerationRequest(**{**fields, **overrides})


def _chunk(parts=(), finish=None, usage=None, candidates=True):
    candidate = ns(finish_reason=finish, content=ns(parts=list(parts)))
    return ns(
        model_version="gemini-3.5-flash-lite-001",
        usage_metadata=usage,
        candidates=[candidate] if candidates else None,
    )


USAGE = ns(
    prompt_token_count=10,
    candidates_token_count=3,
    thoughts_token_count=20,
    cached_content_token_count=None,
)


def _chunks(finish=types.FinishReason.STOP):
    return [
        _chunk(candidates=False),
        _chunk([ns(thought=True, text="Thinking")]),
        _chunk([ns(thought=None, text="rea")]),
        _chunk([ns(thought=None, text="dy")], finish=finish, usage=USAGE),
    ]


def _provider(endpoint: RecordingEndpoint) -> GoogleProvider:
    return GoogleProvider(ns(models=ns(generate_content_stream=endpoint)), clock=ticking_clock())


def test_reasoning_level_maps_to_thinking_level_with_thoughts():
    config = build_config(_request(temperature=1.0))

    assert config.max_output_tokens == 1024
    assert config.system_instruction == "Reply briefly."
    assert config.temperature == 1.0
    assert config.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert config.thinking_config.include_thoughts is True


def test_automatic_function_calling_is_disabled():
    config = build_config(_request())

    assert config.automatic_function_calling.disable is True


def test_reasoning_off_sets_thinking_budget_zero():
    request = _request(model="gemini-2.5-flash", reasoning="off", show_thinking=False, system=None)

    config = build_config(request)

    assert config.thinking_config.thinking_budget == 0
    assert config.system_instruction is None
    assert config.temperature is None


def test_streamed_chunks_become_neutral_result():
    endpoint = RecordingEndpoint(_chunks())
    request = _request()

    result = _provider(endpoint).generate(request)

    assert endpoint.kwargs["model"] == "gemini-3.5-flash-lite"
    assert endpoint.kwargs["contents"] == "Say ready"
    assert result.text == "ready"
    assert result.model_returned == "gemini-3.5-flash-lite-001"
    assert (result.input_tokens, result.output_tokens, result.reasoning_tokens) == (10, 23, 20)
    assert result.cached_input_tokens is None
    assert result.time_to_first_thinking_ms == 1000.0
    assert result.time_to_first_answer_token_ms == 2000.0
    assert result.total_latency_ms == 3000.0
    assert result.finish_reason == "stop"


@pytest.mark.parametrize(
    ("finish", "expected"),
    [
        (types.FinishReason.MAX_TOKENS, "length"),
        (types.FinishReason.SAFETY, "content_filter"),
        (types.FinishReason.OTHER, "other"),
    ],
)
def test_finish_reasons_map_to_neutral_values(finish, expected):
    result = _provider(RecordingEndpoint(_chunks(finish=finish))).generate(_request())

    assert result.finish_reason == expected


def test_unsupported_off_fails_before_calling_the_api():
    endpoint = RecordingEndpoint(_chunks())

    with pytest.raises(UnsupportedSettingError):
        _provider(endpoint).generate(
            _request(model="gemini-3.8-flash", reasoning="off", show_thinking=False)
        )

    assert endpoint.kwargs is None


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (genai_errors.ClientError(429, {"error": {"message": "quota"}}), RateLimitError),
        (genai_errors.ClientError(403, {"error": {"message": "key"}}), AuthenticationError),
        (genai_errors.ClientError(400, {"error": {"message": "bad"}}), InvalidRequestError),
        (genai_errors.ServerError(503, {"error": {"message": "busy"}}), ServerError),
        (httpx.ReadError("connection reset"), StreamInterruptedError),
    ],
)
def test_sdk_errors_map_to_neutral_errors(error, expected):
    with pytest.raises(expected):
        _provider(RecordingEndpoint(error=error)).generate(_request())


def test_stream_ending_without_usage_is_interrupted():
    with pytest.raises(StreamInterruptedError):
        _provider(RecordingEndpoint(_chunks()[:3])).generate(_request())


def test_error_part_way_through_stream_is_retryable():
    endpoint = RecordingEndpoint(_chunks()[:2], mid_stream_error=httpx.ReadError("reset"))

    with pytest.raises(StreamInterruptedError):
        _provider(endpoint).generate(_request())


def test_default_client_reads_key_from_environment(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")

    assert GoogleProvider()._client is not None
