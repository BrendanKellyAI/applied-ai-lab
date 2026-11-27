"""Google adapter, using the Gemini API through google-genai with streaming."""

import time
from collections.abc import Callable
from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from lab.providers.base import (
    FinishReason,
    GenerationRequest,
    GenerationResult,
    StreamInterruptedError,
    UnsupportedSettingError,
)
from lab.providers.capabilities import CapabilityTable, default_capabilities
from lab.providers.errors import error_for_status
from lab.providers.google_messages import call_from_part, contents, tool_fields
from lab.providers.messages import ToolCall
from lab.providers.streaming import StreamClock, Usage, build_result

_CONTENT_FILTER_REASONS = {
    "SAFETY",
    "RECITATION",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
    "IMAGE_SAFETY",
    "IMAGE_PROHIBITED_CONTENT",
    "IMAGE_RECITATION",
}


class GoogleProvider:
    def __init__(
        self,
        client: Any | None = None,
        *,
        capabilities: CapabilityTable | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        # Reads GOOGLE_API_KEY, or GEMINI_API_KEY if that is the only one set.
        self._client = client or genai.Client()
        self._capabilities = capabilities or default_capabilities()
        self._clock = clock

    def validate(self, request: GenerationRequest) -> None:
        if request.output_format is not None:
            # Season 4 holds only OpenAI answers to a format; this adapter does not send one.
            raise UnsupportedSettingError("this adapter does not send an output format")
        self._capabilities.check(request)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.validate(request)
        clock = StreamClock(self._clock)
        parts: list[str] = []
        calls: list[ToolCall] = []
        model_returned = None
        usage = None
        finish = None
        try:
            stream = self._client.models.generate_content_stream(
                model=request.model, contents=contents(request), config=build_config(request)
            )
            for chunk in stream:
                model_returned = chunk.model_version or model_returned
                usage = chunk.usage_metadata or usage
                candidate = chunk.candidates[0] if chunk.candidates else None
                if candidate is None:
                    continue
                finish = candidate.finish_reason or finish
                _read_parts(candidate, parts, clock, calls)
        except genai_errors.APIError as exc:
            raise error_for_status(exc.code, str(exc)) from exc
        except httpx.HTTPError as exc:
            raise StreamInterruptedError(f"Gemini stream interrupted: {exc}") from exc
        if usage is None or finish is None:
            raise StreamInterruptedError("Gemini stream ended before the response completed")
        return build_result(
            request,
            text="".join(parts),
            model_returned=model_returned or request.model,
            usage=_usage(usage),
            finish_reason="tool_calls" if calls else _finish_reason(finish),
            times=clock.finish(),
            tool_calls=tuple(calls),
        )


def build_config(request: GenerationRequest) -> types.GenerateContentConfig:
    fields: dict[str, Any] = {"max_output_tokens": request.max_output_tokens}
    fields.update(tool_fields(request))
    if request.system is not None:
        fields["system_instruction"] = request.system
    if request.temperature is not None:
        fields["temperature"] = request.temperature
    if request.reasoning == "off":
        fields["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    elif request.reasoning is not None:
        fields["thinking_config"] = types.ThinkingConfig(
            thinking_level=request.reasoning.upper(), include_thoughts=request.show_thinking
        )
    return types.GenerateContentConfig(**fields)


def _read_parts(
    candidate: Any, parts: list[str], clock: StreamClock, calls: list[ToolCall]
) -> None:
    content = candidate.content
    for part in content.parts if content and content.parts else []:
        if getattr(part, "function_call", None):
            calls.append(call_from_part(part, len(calls)))
        elif part.thought:
            clock.mark_thinking()
        elif part.text:
            clock.mark_answer()
            parts.append(part.text)


def _usage(metadata: Any) -> Usage:
    thoughts = metadata.thoughts_token_count
    return Usage(
        input_tokens=metadata.prompt_token_count or 0,
        # Gemini reports thinking separately from the answer; both are billed as output.
        output_tokens=(metadata.candidates_token_count or 0) + (thoughts or 0),
        reasoning_tokens=thoughts,
        cached_input_tokens=metadata.cached_content_token_count,
    )


def _finish_reason(reason: Any) -> FinishReason:
    name = getattr(reason, "value", reason)
    if name == "STOP":
        return "stop"
    if name == "MAX_TOKENS":
        return "length"
    if name in _CONTENT_FILTER_REASONS:
        return "content_filter"
    return "other"
