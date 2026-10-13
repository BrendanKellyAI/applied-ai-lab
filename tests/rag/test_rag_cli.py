import json

import pytest
import yaml
from typer.testing import CliRunner

from lab.cli import app
from lab.providers.mock import MockProvider
from lab.providers.registry import AvailableProviders
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mock_models import respond

cli = CliRunner()


@pytest.fixture
def config(episode):
    return episode.folder / "config.yaml"


@pytest.fixture
def offline_models(monkeypatch):
    provider = MockProvider(respond=respond())
    monkeypatch.setattr(
        "lab.rag.cli.available_providers",
        lambda names: AvailableProviders(
            providers={name: provider for name in names}, missing_keys={}
        ),
    )
    monkeypatch.setattr("lab.rag.cli.openai_client", FakeEmbeddingsClient)
    return provider


def _prices(tmp_path, budget):
    path = tmp_path / "prices.yaml"
    data = {
        "prices": {
            "openai": {
                "gpt-6.1-sol": {"input": 2.0, "output": 10.0},
                "text-embedding-3-small": {"input": 0.02},
            },
            "anthropic": {"claude-sonnet-5-5": {"input": 2.0, "output": 10.0}},
        },
        "budgets": {"s2-e2-first-rag-system": budget},
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_estimate_needs_no_key(config, tmp_path):
    result = cli.invoke(
        app,
        [
            "rag",
            "estimate",
            str(config),
            "--cache-dir",
            str(tmp_path / "c"),
            "--prices-path",
            str(_prices(tmp_path, 5.0)),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "baseline [full]: prompts upper bound" in result.output
    assert "k-3 [search]" in result.output
    assert "Budget: 5.00 USD" in result.output


def test_run_writes_results_for_every_condition(config, tmp_path, offline_models):
    result = cli.invoke(
        app,
        [
            "rag",
            "run",
            str(config),
            "--cache-dir",
            str(tmp_path / "c"),
            "--prices-path",
            str(tmp_path / "none.yaml"),
            "--env-file",
            str(tmp_path / "none"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "baseline [" in result.output and "k-3 [" in result.output
    summary = json.loads((config.parent / "results" / "baseline" / "summary.json").read_text())
    assert summary["measure"] == "full"


def test_pilot_runs_one_condition_into_its_own_folder(config, tmp_path, offline_models):
    result = cli.invoke(
        app,
        [
            "rag",
            "run",
            str(config),
            "--pilot",
            "--condition",
            "k-3",
            "--cache-dir",
            str(tmp_path / "c"),
            "--prices-path",
            str(tmp_path / "none.yaml"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (config.parent / "results" / "pilot" / "k-3" / "log.jsonl").exists()
    assert not (config.parent / "results" / "pilot" / "baseline").exists()


def test_run_over_budget_is_refused_before_any_call(config, tmp_path, offline_models):
    result = cli.invoke(
        app,
        [
            "rag",
            "run",
            str(config),
            "--cache-dir",
            str(tmp_path / "c"),
            "--prices-path",
            str(_prices(tmp_path, 0.0001)),
        ],
    )

    assert result.exit_code == 1
    assert "over the budget" in result.output
    assert offline_models.calls == []


def test_missing_key_is_refused(config, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lab.rag.cli.available_providers",
        lambda names: AvailableProviders(
            providers={}, missing_keys={"openai": ("OPENAI_API_KEY",)}
        ),
    )

    result = cli.invoke(
        app,
        [
            "rag",
            "run",
            str(config),
            "--cache-dir",
            str(tmp_path / "c"),
            "--prices-path",
            str(tmp_path / "none.yaml"),
        ],
    )

    assert result.exit_code == 1
    assert "OPENAI_API_KEY" in result.output


def test_unknown_condition_is_refused(config, tmp_path):
    result = cli.invoke(
        app, ["rag", "estimate", str(config), "--condition", "nope", "--cache-dir", str(tmp_path)]
    )

    assert result.exit_code == 1
    assert "no condition named nope" in result.output


def test_bad_config_is_reported(tmp_path):
    result = cli.invoke(app, ["rag", "estimate", str(tmp_path / "missing.yaml")])

    assert result.exit_code == 1
    assert "not found" in result.output
