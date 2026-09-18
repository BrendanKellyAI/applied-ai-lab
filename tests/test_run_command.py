"""`lab run` and `lab analyse` (specification sections 5.4, 5.10)."""

import json
from pathlib import Path

from typer.testing import CliRunner

from lab import cli
from lab.cli import app

runner = CliRunner()

CONFIG = """
experiment: demo
description: A tiny experiment
seed: 7
models:
  - provider: mock
    model: mock-a
    label: Mock A
    modes:
      standard: { reasoning: off, temperature: null, max_output_tokens: 50 }
limits:
  mock: { max_concurrency: 4, requests_per_minute: 6000 }
pilot:
  strategy: filter
  include:
    - { item: 0 }
"""

BUILD_DATASET = """
from lab.metadata import DatasetSource
from lab.plan import PlannedCall, build_request, make_call_id


def dataset_sources(config, folder):
    return [DatasetSource(name="Demo filler", licence="Public domain", url="https://example.test")]


def plan_calls(config, folder):
    (folder / "dataset").mkdir(exist_ok=True)
    model = config.models[0]
    calls = []
    for item in range(3):
        cell = {"item": item}
        calls.append(
            PlannedCall(
                call_id=make_call_id(model_label=model.display_label, mode="standard", cell=cell),
                model_label=model.display_label,
                mode="standard",
                cell=cell,
                request=build_request(model, "standard", prompt=f"item {item} please answer"),
            )
        )
    return calls
"""

ANALYSE = """
def analyse(config, folder, records, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.csv").write_text("item,correct\\n", encoding="utf-8")
    return f"Analysed {config.experiment}: {len(records)} records"
"""

PRICES_GENEROUS = """
currency: USD
prices_checked: 2026-09-17
prices:
  mock:
    mock-a: { input: 1.00, cached_input: 0.10, output: 2.00 }
budgets:
  demo: 100.00
"""

PRICES_TIGHT = """
currency: USD
prices_checked: 2026-09-17
prices:
  mock:
    mock-a: { input: 1000000.00, cached_input: 0.10, output: 2000000.00 }
budgets:
  demo: 0.01
"""


def _field_note(tmp_path: Path, analyse: str | None = ANALYSE) -> Path:
    folder = tmp_path / "field-notes" / "demo"
    folder.mkdir(parents=True)
    (folder / "config.yaml").write_text(CONFIG, encoding="utf-8")
    (folder / "build_dataset.py").write_text(BUILD_DATASET, encoding="utf-8")
    if analyse is not None:
        (folder / "analyse.py").write_text(analyse, encoding="utf-8")
    return folder / "config.yaml"


def _invoke(config_path: Path, tmp_path: Path, *args: str, prices: str | None = None):
    prices_path = tmp_path / "prices.local.yaml"
    if prices is not None:
        prices_path.write_text(prices, encoding="utf-8")
    return runner.invoke(
        app,
        [
            "run",
            str(config_path),
            "--cache-dir",
            str(tmp_path / ".cache"),
            "--env-file",
            str(tmp_path / "absent.env"),
            "--prices",
            str(prices_path),
            *args,
        ],
    )


def _counts_tokens(monkeypatch):
    monkeypatch.setattr(cli, "default_token_counter", lambda: lambda text: len(text.split()))


def _no_providers(names):
    from lab.providers.registry import AvailableProviders

    return AvailableProviders(providers={}, missing_keys={name: ("MOCK_KEY",) for name in names})


class TestRun:
    def test_runs_every_call_and_writes_results(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        result = _invoke(config_path, tmp_path)

        assert result.exit_code == 0, result.output
        lines = (
            (config_path.parent / "results" / "raw.jsonl")
            .read_text(encoding="utf-8")
            .strip()
            .splitlines()
        )
        assert len(lines) == 3
        assert "Calls made:             3" in result.output

    def test_writes_run_metadata_with_dataset_sources(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        _invoke(config_path, tmp_path)

        metadata = json.loads(
            (config_path.parent / "results" / "run_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["experiment"] == "demo"
        assert metadata["counts"]["made"] == 3
        assert metadata["datasets"][0]["name"] == "Demo filler"
        assert metadata["models"][0]["label"] == "Mock A"
        assert "price" not in json.dumps(metadata).lower()

    def test_pilot_runs_only_the_pilot_calls(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        result = _invoke(config_path, tmp_path, "--pilot")

        assert result.exit_code == 0, result.output
        assert "Calls planned:          1" in result.output

    def test_second_run_makes_no_calls(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        _invoke(config_path, tmp_path)

        result = _invoke(config_path, tmp_path)

        assert result.exit_code == 0, result.output
        assert "Already complete:       3" in result.output
        assert "Calls made:             0" in result.output

    def test_fresh_writes_elsewhere_and_leaves_committed_results_alone(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        _invoke(config_path, tmp_path)
        committed = (config_path.parent / "results" / "raw.jsonl").read_text(encoding="utf-8")

        result = _invoke(config_path, tmp_path, "--fresh")

        assert result.exit_code == 0, result.output
        assert "Calls made:             3" in result.output
        unchanged = (config_path.parent / "results" / "raw.jsonl").read_text(encoding="utf-8")
        assert unchanged == committed
        fresh = list((config_path.parent / "results-fresh").glob("*/raw.jsonl"))
        assert len(fresh) == 1
        assert "results-fresh" in result.output

    def test_provider_filter_refuses_a_provider_not_in_the_config(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        result = _invoke(config_path, tmp_path, "--provider", "openai")

        assert result.exit_code == 2
        assert "not in this config" in result.output

    def test_refuses_to_start_when_the_estimate_exceeds_the_budget(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        result = _invoke(config_path, tmp_path, prices=PRICES_TIGHT)

        assert result.exit_code == 2
        assert "exceeds the budget" in result.output
        assert not (config_path.parent / "results" / "raw.jsonl").exists()

    def test_runs_when_within_budget(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)

        result = _invoke(config_path, tmp_path, prices=PRICES_GENEROUS)

        assert result.exit_code == 0, result.output
        assert "Calls made:             3" in result.output

    def test_reports_config_errors_without_a_traceback(self, tmp_path):
        result = runner.invoke(app, ["run", str(tmp_path / "missing.yaml")])

        assert result.exit_code == 2
        assert "Config file not found" in result.output
        assert "Traceback" not in result.output

    def test_reports_a_missing_api_key(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        monkeypatch.setattr(cli, "available_providers", _no_providers)

        result = _invoke(config_path, tmp_path)

        assert result.exit_code == 2
        assert "mock" in result.output


class TestAnalyse:
    def test_prints_the_field_note_report_from_committed_results(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        _invoke(config_path, tmp_path)

        result = runner.invoke(app, ["analyse", str(config_path)])

        assert result.exit_code == 0, result.output
        assert "Analysed demo: 3 records" in result.output
        assert (config_path.parent / "results" / "summary.csv").exists()

    def test_refuses_when_there_are_no_results(self, tmp_path):
        config_path = _field_note(tmp_path)

        result = runner.invoke(app, ["analyse", str(config_path)])

        assert result.exit_code == 2
        assert "No results" in result.output

    def test_reads_an_alternative_results_folder(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        _invoke(config_path, tmp_path, "--fresh")
        fresh = next((config_path.parent / "results-fresh").glob("*"))

        result = runner.invoke(app, ["analyse", str(config_path), "--results", str(fresh)])

        assert result.exit_code == 0, result.output
        assert "3 records" in result.output

    def test_analysing_a_fresh_run_leaves_published_results_untouched(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path)
        _invoke(config_path, tmp_path, "--fresh")
        fresh = next((config_path.parent / "results-fresh").glob("*"))

        runner.invoke(app, ["analyse", str(config_path), "--results", str(fresh)])

        assert (fresh / "summary.csv").exists()
        assert not (config_path.parent / "results" / "summary.csv").exists()

    def test_missing_analyse_module_is_reported(self, tmp_path, monkeypatch):
        _counts_tokens(monkeypatch)
        config_path = _field_note(tmp_path, analyse=None)
        _invoke(config_path, tmp_path)

        result = runner.invoke(app, ["analyse", str(config_path)])

        assert result.exit_code == 2
        assert "analyse.py" in result.output
