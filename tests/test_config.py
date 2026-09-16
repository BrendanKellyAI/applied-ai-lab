from pathlib import Path

import pytest

from lab.config import ConfigError, ExperimentConfig, ProviderLimits, load_config

VALID_YAML = """
experiment: s1-e10-reasoning-vs-standard
description: Reasoning on and off
seed: 20260916
models:
  - provider: openai
    model: model-one
    modes:
      off: { reasoning: off, temperature: 0, max_output_tokens: 4000 }
      high: { reasoning: high, temperature: null, max_output_tokens: 32000 }
  - provider: anthropic
    model: model-two
    label: Model Two
    modes:
      standard: { reasoning: null, temperature: 0, max_output_tokens: 50 }
limits:
  openai: { max_concurrency: 4, requests_per_minute: 60 }
pilot:
  strategy: stratified
  fraction: 0.05
  strata: [task, mode]
call_order: shuffled
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_valid_config(tmp_path):
    config = load_config(_write(tmp_path, VALID_YAML))

    assert config.seed == 20260916
    assert config.call_order == "shuffled"
    assert config.pilot.strategy == "stratified"
    assert config.models[1].display_label == "Model Two"
    assert config.models[0].display_label == "model-one"


def test_yaml_off_is_read_as_reasoning_off_not_false(tmp_path):
    config = load_config(_write(tmp_path, VALID_YAML))
    modes = config.models[0].modes

    assert set(modes) == {"off", "high"}
    assert modes["off"].reasoning == "off"
    assert modes["high"].temperature is None


def test_limits_fall_back_to_conservative_defaults(tmp_path):
    config = load_config(_write(tmp_path, VALID_YAML))

    assert config.limits_for("openai") == ProviderLimits(max_concurrency=4, requests_per_minute=60)
    assert config.limits_for("anthropic") == ProviderLimits(
        max_concurrency=2, requests_per_minute=30
    )


def test_pilot_defaults_to_five_percent_stratified():
    config = ExperimentConfig.model_validate(
        {
            "experiment": "demo",
            "seed": 1,
            "models": [
                {
                    "provider": "mock",
                    "model": "m",
                    "modes": {
                        "standard": {
                            "reasoning": "off",
                            "temperature": 0,
                            "max_output_tokens": 10,
                        }
                    },
                }
            ],
        }
    )

    assert config.pilot.strategy == "stratified"
    assert config.pilot.fraction == 0.05


@pytest.mark.parametrize(
    ("find", "replace", "message"),
    [
        ("reasoning: high, ", "", "reasoning"),
        ("temperature: null, ", "", "temperature"),
        ("provider: openai", "provider: acme", "provider"),
        ("label: Model Two", "label: model-one", "unique"),
        ("fraction: 0.05", "fraction: 1.5", "fraction"),
        ("max_concurrency: 4", "max_concurrency: 0", "max_concurrency"),
    ],
)
def test_rejects_invalid_config_with_clear_message(tmp_path, find, replace, message):
    assert find in VALID_YAML
    path = _write(tmp_path, VALID_YAML.replace(find, replace, 1))

    with pytest.raises(ConfigError, match=message):
        load_config(path)


def test_rejects_filter_pilot_without_rules(tmp_path):
    text = VALID_YAML.replace(
        "strategy: stratified\n  fraction: 0.05\n  strata: [task, mode]",
        "strategy: filter\n  include: []",
    )

    with pytest.raises(ConfigError, match="include"):
        load_config(_write(tmp_path, text))


def test_rejects_non_mapping_and_broken_yaml(tmp_path):
    with pytest.raises(ConfigError, match="mapping"):
        load_config(_write(tmp_path, "- just a list"))
    with pytest.raises(ConfigError, match="YAML"):
        load_config(_write(tmp_path, "experiment: [unclosed"))


def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.yaml")
