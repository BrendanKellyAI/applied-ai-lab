"""Translating provider SDK failures into the harness's neutral errors."""

from collections.abc import Mapping

from lab.providers.base import (
    AuthenticationError,
    InvalidRequestError,
    ProviderError,
    RateLimitError,
    RetryableError,
    ServerError,
)

_MAX_MESSAGE_LENGTH = 500


def error_for_status(
    status: int | None, message: str, *, retry_after_seconds: float | None = None
) -> ProviderError:
    """Map an HTTP status to a neutral error. SDK messages are truncated and never include keys."""
    text = f"HTTP {status}: {message[:_MAX_MESSAGE_LENGTH]}"
    if status == 429:
        return RateLimitError(text, status_code=status, retry_after_seconds=retry_after_seconds)
    if status in (401, 403):
        return AuthenticationError(text)
    if status == 408:
        return RetryableError(text, status_code=status, retry_after_seconds=retry_after_seconds)
    if status is not None and status >= 500:
        return ServerError(text, status_code=status, retry_after_seconds=retry_after_seconds)
    return InvalidRequestError(text)


def retry_after_seconds(headers: Mapping[str, str] | None) -> float | None:
    """Read a retry hint from response headers, in seconds."""
    if not headers:
        return None
    for name, scale in (("retry-after-ms", 0.001), ("retry-after", 1.0)):
        value = headers.get(name)
        if value is None:
            continue
        try:
            return float(value) * scale
        except ValueError:
            continue
    return None
