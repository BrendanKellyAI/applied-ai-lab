import pytest

from lab.providers.anthropic_provider import AnthropicProvider
from lab.providers.google_provider import GoogleProvider
from lab.providers.mock import MockProvider
from lab.providers.openai_provider import OpenAIProvider
from lab.providers.registry import available_providers, create_provider, has_api_key


@pytest.mark.parametrize(
    ("name", "environ", "expected"),
    [
        ("openai", {"OPENAI_API_KEY": "k"}, True),
        ("openai", {"OPENAI_API_KEY": ""}, False),
        ("google", {"GEMINI_API_KEY": "k"}, True),
        ("google", {}, False),
        ("mock", {}, True),
    ],
)
def test_has_api_key(name, environ, expected):
    assert has_api_key(name, environ) is expected


def test_available_providers_skips_missing_keys():
    available = available_providers(["openai", "mock", "google"], environ={})

    assert set(available.providers) == {"mock"}
    assert available.missing_keys == {
        "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        "openai": ("OPENAI_API_KEY",),
    }


@pytest.mark.parametrize(
    ("name", "variable", "expected_type"),
    [
        ("openai", "OPENAI_API_KEY", OpenAIProvider),
        ("anthropic", "ANTHROPIC_API_KEY", AnthropicProvider),
        ("google", "GOOGLE_API_KEY", GoogleProvider),
        ("mock", None, MockProvider),
    ],
)
def test_create_provider_builds_each_adapter(monkeypatch, name, variable, expected_type):
    if variable:
        monkeypatch.setenv(variable, "test-key-not-real")

    assert isinstance(create_provider(name), expected_type)


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_provider("acme")
