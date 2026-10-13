import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from lab.cli import app
from lab.providers.registry import AvailableProviders

SOURCE = Path(__file__).parents[3] / "datasets" / "halvard"
cli = CliRunner()


def _folder(tmp_path):
    folder = tmp_path / "halvard"
    folder.mkdir()
    shutil.copy(SOURCE / "config.yaml", folder / "config.yaml")
    shutil.copytree(SOURCE / "v1", folder / "v1")
    return folder


def _prices(tmp_path, budget=None):
    data = {
        "prices": {
            "openai": {"gpt-6-astra": {"input": 10.0, "output": 50.0}},
            "anthropic": {"claude-sonnet-5-5": {"input": 2.0, "output": 10.0}},
        },
        "budgets": {"s2-corpus": budget},
    }
    path = tmp_path / "prices.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_estimate_prices_every_stage_with_no_key(tmp_path):
    result = cli.invoke(
        app,
        [
            "rag",
            "build-corpus",
            "--folder",
            str(_folder(tmp_path)),
            "--estimate",
            "--pilot",
            "--prices-path",
            str(_prices(tmp_path)),
        ],
    )

    assert result.exit_code == 0, result.output
    for stage in ("section", "question", "quote", "check"):
        assert f"\n{stage} " in result.output
    assert "Total, expected:" in result.output and "USD" in result.output


def test_estimate_without_prices_says_so(tmp_path):
    result = cli.invoke(
        app,
        [
            "rag",
            "build-corpus",
            "--folder",
            str(_folder(tmp_path)),
            "--estimate",
            "--prices-path",
            str(tmp_path / "none.yaml"),
        ],
    )

    assert result.exit_code == 0
    assert "a price is missing" in result.output


def test_build_over_budget_is_refused_before_any_call(tmp_path):
    result = cli.invoke(
        app,
        [
            "rag",
            "build-corpus",
            "--folder",
            str(_folder(tmp_path)),
            "--pilot",
            "--prices-path",
            str(_prices(tmp_path, budget=0.01)),
        ],
    )

    assert result.exit_code == 1
    assert "over the s2-corpus budget" in result.output


def test_build_without_keys_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lab.rag.build_corpus.cli.available_providers",
        lambda names: AvailableProviders(
            providers={}, missing_keys={"openai": ("OPENAI_API_KEY",)}
        ),
    )

    result = cli.invoke(
        app,
        [
            "rag",
            "build-corpus",
            "--folder",
            str(_folder(tmp_path)),
            "--pilot",
            "--prices-path",
            str(tmp_path / "none.yaml"),
            "--env-file",
            str(tmp_path / "none"),
        ],
    )

    assert result.exit_code == 1
    assert "OPENAI_API_KEY" in result.output


def test_missing_config_is_reported(tmp_path):
    result = cli.invoke(app, ["rag", "build-corpus", "--folder", str(tmp_path), "--estimate"])

    assert result.exit_code == 1
    assert "not found" in result.output
