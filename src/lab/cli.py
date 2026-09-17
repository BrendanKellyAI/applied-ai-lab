"""Command line entry point for the lab harness.

Commands estimate, run, and analyse are added in later build phases.
"""

import logging
from datetime import UTC, datetime
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
from lab.smoke import describe, plan_smoke, problems

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
    fresh: Annotated[
        bool, typer.Option(help="Ignore cached responses and make new calls, to re-measure.")
    ] = False,
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
        raw_path = _smoke_log_path(cache_dir, fresh)
        summary = runner.run(calls, raw_path, use_cache=not fresh)
    except (ConfigError, PlanError, UnsupportedSettingError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    latest = latest_successful(load_records(raw_path))
    incomplete = False
    for call in calls:
        record = latest.get(call.call_id)
        if record is None:
            typer.echo(f"{call.model_label} [{call.mode}]: FAILED, see warnings above")
            incomplete = True
            continue
        typer.echo("\n".join(describe(record, call.request)))
        incomplete = incomplete or bool(problems(record, call.request))
    typer.echo("")
    typer.echo(format_summary(summary))
    if incomplete:
        typer.echo(
            "Some calls failed, returned empty fields, or raised warnings. Check the output above.",
            err=True,
        )
        raise typer.Exit(code=1)


def _smoke_log_path(cache_dir: Path, fresh: bool) -> Path:
    if not fresh:
        return cache_dir / "smoke" / "raw.jsonl"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return cache_dir / "smoke-fresh" / stamp / "raw.jsonl"
