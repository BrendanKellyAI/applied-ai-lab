from pathlib import Path

import pytest
from typer.testing import CliRunner

from lab import cli
from lab.cli import app
from lab.config import ConfigError
from lab.experiments import (
    load_analyse_function,
    load_plan_function,
    load_sibling,
    results_dir,
)

CONFIG = """
experiment: demo
seed: 1
models:
  - provider: mock
    model: mock-a
    modes:
      standard: { reasoning: off, temperature: null, max_output_tokens: 50 }
pilot:
  strategy: filter
  include:
    - { item: 0 }
"""

BUILD_DATASET = """
from lab.plan import PlannedCall, build_request, make_call_id


def plan_calls(config, folder):
    model = config.models[0]
    label = model.display_label
    return [
        PlannedCall(
            call_id=make_call_id(model_label=label, mode="standard", cell={"item": i}),
            model_label=model.display_label,
            mode="standard",
            cell={"item": i},
            request=build_request(model, "standard", prompt="one two three four five"),
        )
        for i in range(3)
    ]
"""

ANALYSE = """
def analyse(config, folder, records):
    return f"{config.experiment}: {len(records)} records"
"""

PRICES = """
currency: USD
prices_checked: 2026-09-17
prices:
  mock:
    mock-a: { input: 2.00, cached_input: 0.20, output: 10.00 }
budgets:
  demo: 5.00
"""


def _field_note(
    tmp_path: Path,
    build_dataset: str | None = BUILD_DATASET,
    analyse: str | None = ANALYSE,
) -> Path:
    folder = tmp_path / "field-notes" / "demo"
    folder.mkdir(parents=True)
    (folder / "config.yaml").write_text(CONFIG, encoding="utf-8")
    if build_dataset is not None:
        (folder / "build_dataset.py").write_text(build_dataset, encoding="utf-8")
    if analyse is not None:
        (folder / "analyse.py").write_text(analyse, encoding="utf-8")
    return folder / "config.yaml"


def test_loads_plan_function_from_field_note_folder(tmp_path):
    config_path = _field_note(tmp_path)

    plan = load_plan_function(config_path)

    assert callable(plan)
    assert results_dir(config_path) == config_path.parent / "results"


def test_missing_build_dataset_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="build_dataset.py"):
        load_plan_function(_field_note(tmp_path, build_dataset=None))


def test_build_dataset_without_plan_calls_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="plan_calls"):
        load_plan_function(_field_note(tmp_path, build_dataset="VALUE = 1\n"))


def test_estimate_command_prints_report(tmp_path, monkeypatch):
    config_path = _field_note(tmp_path)
    prices = tmp_path / "prices.local.yaml"
    prices.write_text(PRICES, encoding="utf-8")
    monkeypatch.setattr(cli, "default_token_counter", lambda: lambda text: len(text.split()))

    result = CliRunner().invoke(
        app,
        [
            "estimate",
            str(config_path),
            "--prices",
            str(prices),
            "--cache-dir",
            str(tmp_path / ".cache"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Estimate for demo" in result.output
    assert "Pilot: 1 call," in result.output
    assert "Full run: 3 calls" in result.output
    assert "Budget: $5.00" in result.output


def test_estimate_command_without_prices_shows_tokens_only(tmp_path, monkeypatch):
    config_path = _field_note(tmp_path)
    monkeypatch.setattr(cli, "default_token_counter", lambda: lambda text: len(text.split()))

    result = CliRunner().invoke(
        app,
        [
            "estimate",
            str(config_path),
            "--prices",
            str(tmp_path / "none.yaml"),
            "--cache-dir",
            str(tmp_path / ".cache"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "no prices file" in result.output


def test_estimate_command_reports_config_errors(tmp_path):
    result = CliRunner().invoke(app, ["estimate", str(tmp_path / "missing.yaml")])

    assert result.exit_code == 2
    assert "Config file not found" in result.output


def test_loads_analyse_function_from_field_note_folder(tmp_path):
    config_path = _field_note(tmp_path)

    analyse = load_analyse_function(config_path)

    assert callable(analyse)


def test_missing_analyse_module_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="analyse.py"):
        load_analyse_function(_field_note(tmp_path, analyse=None))


def test_analyse_module_without_analyse_function_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="analyse"):
        load_analyse_function(_field_note(tmp_path, analyse="VALUE = 1"))


def test_a_sibling_module_is_loaded_by_path(tmp_path):
    folder = tmp_path / "field-notes" / "demo"
    folder.mkdir(parents=True)
    (folder / "helpers.py").write_text("SHARED = 7\n", encoding="utf-8")

    assert load_sibling(folder / "helpers.py").SHARED == 7


def test_a_missing_sibling_module_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="helpers.py"):
        load_sibling(tmp_path / "helpers.py")
