import pytest

from lab.providers.base import GenerationRequest, UnsupportedSettingError
from lab.providers.capabilities import (
    CapabilityTable,
    ModelCapabilities,
    default_capabilities,
)

TABLE = CapabilityTable(
    {
        "openai": {
            "reasoner": ModelCapabilities(
                reasoning=["off", "low", "high"], temperature=False, max_output_tokens=1000
            ),
            "plain": ModelCapabilities(temperature=True),
        }
    }
)


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "openai",
        "model": "reasoner",
        "prompt": "hi",
        "max_output_tokens": 100,
        "reasoning": "off",
    }
    return GenerationRequest(**{**fields, **overrides})


def test_supported_request_passes():
    assert TABLE.check(_request(reasoning="high", show_thinking=True)).temperature is False


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"model": "unknown"}, "not in capabilities.yaml"),
        ({"reasoning": None}, "state it explicitly"),
        ({"reasoning": "medium"}, "does not support reasoning 'medium'"),
        ({"temperature": 0.0}, "does not accept a temperature"),
        ({"max_output_tokens": 1001}, "at most 1000"),
        ({"show_thinking": True}, "show_thinking needs reasoning"),
        ({"stream": False}, "always stream"),
        ({"model": "plain", "reasoning": "low"}, "Allowed: none"),
    ],
)
def test_unsupported_settings_are_refused(overrides, message):
    with pytest.raises(UnsupportedSettingError, match=message):
        TABLE.check(_request(**overrides))


def test_model_without_reasoning_control_accepts_no_reasoning_and_temperature():
    TABLE.check(_request(model="plain", reasoning=None, temperature=0.0))


def test_packaged_table_loads_and_reads_yaml_off_as_a_level():
    table = default_capabilities()

    luna = table.check(_request(model="gpt-5.6-luna", reasoning="off"))
    assert "off" in luna.reasoning
    with pytest.raises(UnsupportedSettingError):
        table.check(_request(model="gpt-6-astra", reasoning="off"))


@pytest.mark.parametrize(
    ("provider", "model"),
    [
        ("openai", "gpt-6-astra"),
        ("openai", "gpt-5.6-luna"),
        ("anthropic", "claude-opus-5"),
        ("anthropic", "claude-sonnet-5"),
        ("google", "gemini-3.5-flash-lite"),
        ("google", "gemini-2.5-flash"),
    ],
)
def test_packaged_table_covers_models_named_in_configs(provider, model):
    request = _request(provider=provider, model=model, reasoning="low")
    default_capabilities().check(request)
