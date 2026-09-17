"""Command line entry point for the lab harness.

Commands run and analyse are added with the field notes in later build phases.
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
from lab.estimate import build_report, default_token_counter, format_report
from lab.experiments import load_plan_function, results_dir
from lab.plan import PlanError
from lab.prices import load_prices
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
def estimate(
    config: Annotated[Path, typer.Argument(help="Experiment config.yaml.")],
    prices: Annotated[Path, typer.Option(help="Local prices file.")] = Path("prices.local.yaml"),
    cache_dir: Annotated[Path, typer.Option(help="Response cache folder.")] = Path(".cache"),
) -> None:
    """Estimate tokens and cost for the pilot and the full run. Makes no API calls."""
    try:
        experiment = load_config(config)
        calls = load_plan_function(config)(experiment, config.parent)
        report = build_report(
            experiment,
            calls,
            cache=ResponseCache(cache_dir),
            prior_records=load_records(results_dir(config) / "raw.jsonl"),
            prices=load_prices(prices),
            count_tokens=default_token_counter(),
        )
    except (ConfigError, PlanError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(format_report(report))


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
