"""OpenAI adapter, using the Responses API with streaming."""

import time
from collections.abc import Callable
from typing import Any

import openai

from lab.providers.base import (
    FinishReason,
    GenerationRequest,
    GenerationResult,
    InvalidRequestError,
    ProviderError,
    RateLimitError,
    ServerError,
    StreamInterruptedError,
)
from lab.providers.capabilities import CapabilityTable, default_capabilities
from lab.providers.errors import error_for_status, retry_after_seconds
from lab.providers.streaming import StreamClock, Usage, build_result

_THINKING_EVENTS = {"response.reasoning_summary_text.delta", "response.reasoning_text.delta"}
_FINAL_EVENTS = {"response.completed", "response.incomplete"}


class OpenAIProvider:
    def __init__(
        self,
        client: Any | None = None,
        *,
        capabilities: CapabilityTable | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        # SDK retries are off: the runner owns retries so attempt counts are honest.
        self._client = client or openai.OpenAI(max_retries=0)
        self._capabilities = capabilities or default_capabilities()
        self._clock = clock

    def validate(self, request: GenerationRequest) -> None:
        self._capabilities.check(request)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.validate(request)
        clock = StreamClock(self._clock)
        parts: list[str] = []
        final = None
        try:
            for event in self._client.responses.create(**build_params(request)):
                if event.type == "response.output_text.delta":
                    clock.mark_answer()
                    parts.append(event.delta)
                elif event.type in _THINKING_EVENTS or _is_reasoning_item(event):
                    clock.mark_thinking()
                elif event.type in _FINAL_EVENTS:
                    final = event.response
                elif event.type == "response.failed":
                    raise _failed_response_error(event.response)
        except openai.APIStatusError as exc:
            raise error_for_status(
                exc.status_code,
                exc.message,
                retry_after_seconds=retry_after_seconds(exc.response.headers),
            ) from exc
        except openai.APIError as exc:
            raise StreamInterruptedError(f"OpenAI stream interrupted: {exc}") from exc
        if final is None or final.usage is None:
            raise StreamInterruptedError("OpenAI stream ended without a final response")
        return _result(request, final, "".join(parts), clock)


def build_params(request: GenerationRequest) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": request.model,
        "input": request.prompt,
        "max_output_tokens": request.max_output_tokens,
        "stream": True,
        # Nothing is stored server side, so no call can see another call's history.
        "store": False,
    }
    if request.system is not None:
        params["instructions"] = request.system
    if request.temperature is not None:
        params["temperature"] = request.temperature
    if request.reasoning is not None:
        reasoning: dict[str, str] = {
            "effort": "none" if request.reasoning == "off" else request.reasoning
        }
        if request.show_thinking:
            reasoning["summary"] = "auto"
        params["reasoning"] = reasoning
    return params


def _is_reasoning_item(event: Any) -> bool:
    return event.type == "response.output_item.added" and event.item.type == "reasoning"


def _failed_response_error(response: Any) -> ProviderError:
    error = getattr(response, "error", None)
    code = getattr(error, "code", None) or "unknown"
    message = f"OpenAI response failed ({code}): {getattr(error, 'message', '')}"
    if code == "rate_limit_exceeded":
        return RateLimitError(message)
    if code in ("server_error", "vector_store_timeout"):
        return ServerError(message)
    return InvalidRequestError(message)


def _finish_reason(response: Any) -> FinishReason:
    if response.status == "completed":
        return "stop"
    reason = getattr(response.incomplete_details, "reason", None)
    if reason == "max_output_tokens":
        return "length"
    if reason == "content_filter":
        return "content_filter"
    return "other"


def _result(
    request: GenerationRequest, response: Any, text: str, clock: StreamClock
) -> GenerationResult:
    usage = response.usage
    output_details = getattr(usage, "output_tokens_details", None)
    input_details = getattr(usage, "input_tokens_details", None)
    return build_result(
        request,
        text=text,
        model_returned=response.model,
        usage=Usage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=getattr(output_details, "reasoning_tokens", None),
            cached_input_tokens=getattr(input_details, "cached_tokens", None),
        ),
        finish_reason=_finish_reason(response),
        times=clock.finish(),
    )
