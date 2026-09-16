import pytest
from pydantic import ValidationError

from lab.providers.base import GenerationRequest, RetryableError, request_hash


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "mock",
        "model": "mock-a",
        "prompt": "What is the code?",
        "max_output_tokens": 50,
    }
    return GenerationRequest(**{**fields, **overrides})


def test_hash_is_stable_sha256_hex():
    digest = request_hash(_request())

    assert digest == request_hash(_request())
    assert len(digest) == 64


def test_hash_ignores_stream_and_metadata():
    base = _request()
    relabelled = _request(stream=False, metadata={"experiment": "other"})

    assert request_hash(base) == request_hash(relabelled)


@pytest.mark.parametrize(
    "override",
    [
        {"prompt": "Different"},
        {"system": "Be brief."},
        {"model": "mock-b"},
        {"temperature": 0.0},
        {"reasoning": "high"},
        {"max_output_tokens": 51},
    ],
)
def test_hash_changes_with_anything_the_model_sees(override):
    assert request_hash(_request()) != request_hash(_request(**override))


def test_request_is_immutable_and_rejects_unknown_fields():
    request = _request()

    with pytest.raises(ValidationError):
        request.prompt = "changed"
    with pytest.raises(ValidationError):
        _request(api_key="should never be accepted")


def test_retryable_error_carries_retry_after():
    error = RetryableError("slow down", status_code=429, retry_after_seconds=3.0)

    assert error.status_code == 429
    assert error.retry_after_seconds == 3.0
