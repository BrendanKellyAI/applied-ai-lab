"""Command line entry point for the lab harness.

Commands estimate, run, and analyse are added in later build phases.
"""

import logging
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab import __version__
from lab.cache import ResponseCache
from lab.config import ConfigError, load_config
from lab.plan import PlanError
from lab.providers.base import UnsupportedSettingError
from lab.providers.registry import available_providers
from lab.raw_log import latest_successful, load_records
from lab.runner import Runner, format_summary
from lab.smoke import describe, missing_fields, plan_smoke

app = typer.Typer(help="Run and analyse applied-ai-lab experiments.", no_args_is_help=True)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"applied-ai-lab {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the harness version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
) -> None:
    """Run and analyse applied-ai-lab experiments."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


@app.command()
def smoke(
    config: Annotated[Path, typer.Option(help="Smoke test config.")] = Path("smoke.yaml"),
    cache_dir: Annotated[Path, typer.Option(help="Response cache folder.")] = Path(".cache"),
    env_file: Annotated[Path, typer.Option(help="File to read API keys from.")] = Path(".env"),
) -> None:
    """Make one tiny call per configured model and mode, and show every result field."""
    load_dotenv(env_file, override=False)
    try:
        experiment = load_config(config)
        available = available_providers(experiment.providers)
        for name, variables in available.missing_keys.items():
            typer.echo(f"Skipping {name}: set {' or '.join(variables)} to include it.")
        calls = [c for c in plan_smoke(experiment) if c.request.provider in available.providers]
        if not calls:
            typer.echo("No API keys found. Add at least one key to .env and try again.", err=True)
            raise typer.Exit(code=1)
        runner = Runner(
            providers=available.providers,
            cache=ResponseCache(cache_dir),
            limits={name: experiment.limits_for(name) for name in available.providers},
        )
        raw_path = cache_dir / "smoke" / "raw.jsonl"
        summary = runner.run(calls, raw_path)
    except (ConfigError, PlanError, UnsupportedSettingError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    latest = latest_successful(load_records(raw_path))
    incomplete = False
    for call in calls:
        record = latest.get(call.call_id)
        expects_thinking = call.request.show_thinking
        if record is None:
            typer.echo(f"{call.model_label} [{call.mode}]: FAILED, see warnings above")
            incomplete = True
            continue
        typer.echo("\n".join(describe(record, expects_thinking)))
        incomplete = incomplete or bool(missing_fields(record, expects_thinking))
    typer.echo("")
    typer.echo(format_summary(summary))
    if incomplete:
        typer.echo("Some calls failed or returned empty fields. Check the output above.", err=True)
        raise typer.Exit(code=1)
