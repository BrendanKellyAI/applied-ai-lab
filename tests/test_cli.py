from typer.testing import CliRunner

import lab
from lab.cli import app

runner = CliRunner()


def test_package_exposes_version():
    assert lab.__version__ == "0.1.0"


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "applied-ai-lab 0.1.0" in result.output


def test_no_arguments_shows_help():
    result = runner.invoke(app, [])

    assert "Usage" in result.output
