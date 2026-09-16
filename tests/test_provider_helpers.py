import pytest

from lab.providers.base import (
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
    RetryableError,
    ServerError,
)
from lab.providers.errors import error_for_status, retry_after_seconds
from lab.providers.streaming import StreamClock
from tests.fakes import ticking_clock


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, RateLimitError),
        (401, AuthenticationError),
        (403, AuthenticationError),
        (408, RetryableError),
        (500, ServerError),
        (529, ServerError),
        (400, InvalidRequestError),
        (404, InvalidRequestError),
        (None, InvalidRequestError),
    ],
)
def test_status_maps_to_neutral_error(status, expected):
    error = error_for_status(status, "message")

    assert type(error) is expected
    assert str(status) in str(error)


def test_retryable_status_keeps_retry_hint_and_long_messages_are_truncated():
    error = error_for_status(429, "x" * 5000, retry_after_seconds=4.0)

    assert error.retry_after_seconds == 4.0
    assert len(str(error)) < 600


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"retry-after": "7"}, 7.0),
        ({"retry-after-ms": "1500", "retry-after": "9"}, 1.5),
        ({"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}, None),
        ({}, None),
        (None, None),
    ],
)
def test_retry_after_header_parsing(headers, expected):
    assert retry_after_seconds(headers) == expected


def test_stream_clock_records_first_events_only():
    clock = StreamClock(ticking_clock())

    clock.mark_thinking()
    clock.mark_answer()
    clock.mark_thinking()
    clock.mark_answer()
    times = clock.finish()

    assert (times.first_thinking_ms, times.first_answer_token_ms, times.total_ms) == (
        1000.0,
        2000.0,
        3000.0,
    )


def test_stream_clock_without_events_reports_none():
    times = StreamClock(ticking_clock()).finish()

    assert times.first_answer_token_ms is None
    assert times.first_thinking_ms is None
