"""The neutral request, result, and provider interface shared by every adapter."""

import hashlib
import json
from typing import Any, Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.providers.messages import Message, ToolCall, ToolChoice, ToolSpec, hash_payload

ProviderName = Literal["openai", "anthropic", "google", "mock"]
# "off" means reasoning fully disabled. Not every model accepts every level; see capabilities.yaml.
ReasoningLevel = Literal["off", "minimal", "low", "medium", "high", "xhigh", "max"]
# "tool_calls": the model stopped to ask for one or more tool calls (Season 5).
FinishReason = Literal["stop", "length", "content_filter", "tool_calls", "other"]

# Fields that change how a call is delivered or labelled, but not what the model sees.
_FIELDS_EXCLUDED_FROM_HASH = {"stream", "metadata"}
# Fields added after Season 1. Each is left out of the hash when unset, so a request that does
# not use it hashes exactly as it did before the field existed, and earlier caches still match.
_FIELDS_HASHED_ONLY_WHEN_SET = ("output_format", "messages", "tools", "tool_choice")


class OutputFormat(BaseModel):
    """Hold the reply to a format: any valid JSON object, or one that fits a JSON schema."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["json_mode", "schema"]
    name: str | None = None
    json_schema: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _schema_matches_kind(self) -> Self:
        if (self.kind == "schema") != (self.json_schema is not None and self.name is not None):
            raise ValueError("a schema format needs a name and a json_schema; JSON mode has none")
        return self


class GenerationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: ProviderName
    model: str = Field(min_length=1)
    system: str | None = None
    # Seasons 1 to 4: one user prompt. Season 5 sends `messages` instead, and leaves this empty.
    prompt: str = ""
    max_output_tokens: int = Field(gt=0)
    temperature: float | None = None
    reasoning: ReasoningLevel | None = None
    # Stream thinking summaries where the provider offers them.
    show_thinking: bool = False
    stream: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)
    # Season 4. Left out of the request hash when unset, so earlier seasons' caches still match.
    output_format: OutputFormat | None = None
    # Season 5. A conversation of turns in place of `prompt`, the tools the model may call, and
    # whether it must, may or must not call one. All left out of the hash when unset.
    messages: tuple[Message, ...] | None = None
    tools: tuple[ToolSpec, ...] | None = None
    tool_choice: ToolChoice | None = None

    @model_validator(mode="after")
    def _prompt_or_messages(self) -> Self:
        if self.messages is None:
            if not self.prompt:
                raise ValueError("a request needs a prompt or messages")
        elif self.prompt:
            raise ValueError("send a prompt or messages, not both")
        elif not self.messages or self.messages[0].role != "user":
            raise ValueError("messages must start with a user turn")
        if self.tool_choice is not None and not self.tools:
            raise ValueError("tool_choice needs tools")
        if self.tools and len({tool.name for tool in self.tools}) != len(self.tools):
            raise ValueError("tool names must be unique")
        return self

    def turns(self) -> tuple[Message, ...]:
        """The conversation as turns, whichever form the request was written in."""
        if self.messages is not None:
            return self.messages
        return (Message(role="user", text=self.prompt),)


class GenerationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_hash: str
    provider: str
    model_requested: str
    model_returned: str
    text: str
    input_tokens: int
    # Total billed output tokens, including any reasoning tokens.
    output_tokens: int
    # Only where the provider reports reasoning tokens separately.
    reasoning_tokens: int | None
    cached_input_tokens: int | None
    # Dispatch to the first token of visible answer text.
    time_to_first_answer_token_ms: float | None
    # Dispatch to the first streamed reasoning or thinking content, where the provider streams it.
    time_to_first_thinking_ms: float | None = None
    total_latency_ms: float
    finish_reason: FinishReason
    timestamp_utc: str
    error: str | None = None
    # Season 5. Tool calls the model asked for, in the order it asked. Empty for older results.
    tool_calls: tuple[ToolCall, ...] = ()


def request_hash(request: GenerationRequest) -> str:
    """SHA-256 of the canonical JSON of everything the model sees and every generation setting."""
    payload = request.model_dump(mode="json", exclude=_FIELDS_EXCLUDED_FROM_HASH)
    for name in _FIELDS_HASHED_ONLY_WHEN_SET:
        if payload.get(name) is None:
            payload.pop(name, None)
    if payload.get("messages") is not None:
        payload["messages"] = hash_payload(payload["messages"])
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ProviderError(Exception):
    """Base class for errors an adapter raises. Messages must never contain API keys."""


class RetryableError(ProviderError):
    """Transient failure worth retrying with backoff."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


class RateLimitError(RetryableError):
    """HTTP 429."""


class ServerError(RetryableError):
    """HTTP 5xx, including overloaded responses such as Anthropic's 529."""


class StreamInterruptedError(RetryableError):
    """The stream broke before it completed."""


class NonRetryableError(ProviderError):
    """Failure that retrying cannot fix."""


class AuthenticationError(NonRetryableError):
    """Missing, invalid, or unauthorised API key."""


class InvalidRequestError(NonRetryableError):
    """The provider rejected the request as invalid."""


class UnsupportedSettingError(NonRetryableError):
    """The model does not support a requested setting. Raised before any call is made."""


class Provider(Protocol):
    def validate(self, request: GenerationRequest) -> None:
        """Raise UnsupportedSettingError if the request cannot be sent as specified."""
        ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...
