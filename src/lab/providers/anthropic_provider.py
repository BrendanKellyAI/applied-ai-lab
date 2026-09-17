"""Anthropic adapter, using the Messages API with streaming."""

import os
import time
from collections.abc import Callable, Mapping
from typing import Any

import anthropic

from lab.providers.base import (
    FinishReason,
    GenerationRequest,
    GenerationResult,
    ProviderError,
    RateLimitError,
    ServerError,
    StreamInterruptedError,
)
from lab.providers.capabilities import CapabilityTable, default_capabilities
from lab.providers.errors import error_for_status, retry_after_seconds
from lab.providers.streaming import StreamClock, Usage, build_result

_STOP_REASONS: dict[str, FinishReason] = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "model_context_window_exceeded": "length",
    "refusal": "content_filter",
}
_RETRYABLE_STREAM_ERRORS = {"overloaded_error": ServerError, "api_error": ServerError}
_WORKSPACE_HEADER = "anthropic-workspace-id"


class AnthropicProvider:
    def __init__(
        self,
        client: Any | None = None,
        *,
        capabilities: CapabilityTable | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        # SDK retries are off: the runner owns retries so attempt counts are honest.
        self._client = client or _default_client()
        self._capabilities = capabilities or default_capabilities()
        self._clock = clock

    def validate(self, request: GenerationRequest) -> None:
        self._capabilities.check(request)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.validate(request)
        clock = StreamClock(self._clock)
        state = _StreamState()
        try:
            for event in self._client.messages.create(**build_params(request)):
                state.apply(event, clock)
        except anthropic.APIStatusError as exc:
            raise _status_error(exc) from exc
        except anthropic.APIError as exc:
            raise StreamInterruptedError(f"Anthropic stream interrupted: {exc}") from exc
        if state.model is None or state.stop_reason is None:
            raise StreamInterruptedError("Anthropic stream ended before the message completed")
        return build_result(
            request,
            text="".join(state.parts),
            model_returned=state.model,
            usage=Usage(
                input_tokens=state.input_tokens,
                output_tokens=state.output_tokens,
                reasoning_tokens=state.thinking_tokens,
                cached_input_tokens=state.cached_input_tokens,
            ),
            finish_reason=_STOP_REASONS.get(state.stop_reason, "other"),
            times=clock.finish(),
        )


def _default_client(environ: Mapping[str, str] | None = None) -> anthropic.Anthropic:
    """Build the SDK client, adding a workspace header when the key is multi-workspace."""
    env = os.environ if environ is None else environ
    workspace_id = env.get("ANTHROPIC_WORKSPACE_ID")
    headers = {_WORKSPACE_HEADER: workspace_id} if workspace_id else None
    return anthropic.Anthropic(max_retries=0, default_headers=headers)


def build_params(request: GenerationRequest) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_output_tokens,
        "messages": [{"role": "user", "content": request.prompt}],
        "stream": True,
    }
    if request.system is not None:
        params["system"] = request.system
    if request.temperature is not None:
        params["temperature"] = request.temperature
    if request.reasoning == "off":
        params["thinking"] = {"type": "disabled"}
    elif request.reasoning is not None:
        display = "summarized" if request.show_thinking else "omitted"
        params["thinking"] = {"type": "adaptive", "display": display}
        params["output_config"] = {"effort": request.reasoning}
    return params


class _StreamState:
    """Accumulates what the event stream reports. Local to one call."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.model: str | None = None
        self.stop_reason: str | None = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.thinking_tokens: int | None = None
        self.cached_input_tokens: int | None = None

    def apply(self, event: Any, clock: StreamClock) -> None:
        if event.type == "message_start":
            self.model = event.message.model
            self._read_usage(event.message.usage)
        elif event.type == "content_block_start":
            if event.content_block.type in ("thinking", "redacted_thinking"):
                clock.mark_thinking()
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                clock.mark_answer()
                self.parts.append(event.delta.text)
            elif event.delta.type == "thinking_delta":
                clock.mark_thinking()
        elif event.type == "message_delta":
            self.stop_reason = event.delta.stop_reason
            self._read_usage(event.usage)

    def _read_usage(self, usage: Any) -> None:
        if getattr(usage, "input_tokens", None) is not None:
            self.input_tokens = usage.input_tokens
        if getattr(usage, "cache_read_input_tokens", None) is not None:
            self.cached_input_tokens = usage.cache_read_input_tokens
        if getattr(usage, "output_tokens", None):
            self.output_tokens = usage.output_tokens
        details = getattr(usage, "output_tokens_details", None)
        if details is not None:
            self.thinking_tokens = details.thinking_tokens


def _status_error(exc: anthropic.APIStatusError) -> ProviderError:
    """Errors sent inside a stream arrive with HTTP 200, so the error type decides."""
    body = exc.body if isinstance(exc.body, dict) else {}
    error_type = (body.get("error") or {}).get("type")
    if error_type == "rate_limit_error":
        return RateLimitError(f"Anthropic rate limit: {exc.message}")
    if error_type in _RETRYABLE_STREAM_ERRORS:
        return _RETRYABLE_STREAM_ERRORS[error_type](f"Anthropic {error_type}: {exc.message}")
    return error_for_status(
        exc.status_code,
        exc.message,
        retry_after_seconds=retry_after_seconds(exc.response.headers),
    )
