"""The neutral request, result, and provider interface shared by every adapter."""

import hashlib
import json
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

ProviderName = Literal["openai", "anthropic", "google", "mock"]
# "off" means reasoning fully disabled. Not every model accepts every level; see capabilities.yaml.
ReasoningLevel = Literal["off", "minimal", "low", "medium", "high", "xhigh", "max"]
FinishReason = Literal["stop", "length", "content_filter", "other"]

# Fields that change how a call is delivered or labelled, but not what the model sees.
_FIELDS_EXCLUDED_FROM_HASH = {"stream", "metadata"}


class GenerationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: ProviderName
    model: str = Field(min_length=1)
    system: str | None = None
    prompt: str
    max_output_tokens: int = Field(gt=0)
    temperature: float | None = None
    reasoning: ReasoningLevel | None = None
    # Stream thinking summaries where the provider offers them.
    show_thinking: bool = False
    stream: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


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


def request_hash(request: GenerationRequest) -> str:
    """SHA-256 of the canonical JSON of everything the model sees and every generation setting."""
    payload = request.model_dump(mode="json", exclude=_FIELDS_EXCLUDED_FROM_HASH)
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
