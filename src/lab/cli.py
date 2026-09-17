"""Command line entry point for the lab harness."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab import __version__
from lab.cache import ResponseCache
from lab.config import ConfigError, ExperimentConfig, load_config
from lab.estimate import (
    BudgetError,
    build_report,
    check_budget,
    default_token_counter,
    estimate_run,
    format_report,
)
from lab.experiments import (
    dataset_sources,
    load_analyse_function,
    load_plan_function,
    results_dir,
)
from lab.metadata import build_metadata, write_metadata
from lab.pilot import select_calls
from lab.plan import PlanError, PlannedCall
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
def run(
    config: Annotated[Path, typer.Argument(help="Experiment config.yaml.")],
    pilot: Annotated[bool, typer.Option(help="Run only the pilot defined by the config.")] = False,
    fresh: Annotated[
        bool,
        typer.Option(
            help="Make new calls into a separate folder, leaving committed results untouched."
        ),
    ] = False,
    provider: Annotated[
        str | None, typer.Option(help="Run one provider only, for readers with a single key.")
    ] = None,
    prices: Annotated[Path, typer.Option(help="Local prices file.")] = Path("prices.local.yaml"),
    cache_dir: Annotated[Path, typer.Option(help="Response cache folder.")] = Path(".cache"),
    env_file: Annotated[Path, typer.Option(help="File to read API keys from.")] = Path(".env"),
) -> None:
    """Run an experiment. Resumable: calls already complete are never repeated."""
    load_dotenv(env_file, override=False)
    started = datetime.now(UTC).isoformat()
    try:
        experiment = load_config(config)
        calls = load_plan_function(config)(experiment, config.parent)
        selected = select_calls(calls, experiment, pilot=pilot, provider=provider)
        if not selected:
            typer.echo("Nothing to run: the selection matched no calls.", err=True)
            raise typer.Exit(code=2)
        cache = ResponseCache(cache_dir)
        raw_path = _run_log_path(config, fresh)
        _check_budget(
            experiment,
            selected,
            cache=cache,
            raw_path=raw_path,
            prices_path=prices,
            pilot=pilot,
        )
        providers = _providers_for(experiment, selected)
        runner = Runner(
            providers=providers,
            cache=cache,
            limits={name: experiment.limits_for(name) for name in providers},
        )
        summary = runner.run(selected, raw_path, use_cache=not fresh)
    except (ConfigError, PlanError, UnsupportedSettingError, BudgetError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    records = load_records(raw_path)
    write_metadata(
        raw_path.parent / "run_metadata.json",
        build_metadata(
            config=experiment,
            summary=summary,
            records=records,
            started_utc=started,
            ended_utc=datetime.now(UTC).isoformat(),
            datasets=dataset_sources(config)(experiment, config.parent),
            repo_dir=config.parent,
        ),
    )
    typer.echo(format_summary(summary))
    typer.echo(f"\nResults written to {raw_path.parent}")
    if summary.failed:
        typer.echo(
            f"{summary.failed} call(s) failed. Run the same command again to retry them.", err=True
        )
        raise typer.Exit(code=1)


@app.command()
def analyse(
    config: Annotated[Path, typer.Argument(help="Experiment config.yaml.")],
    results: Annotated[
        Path | None, typer.Option(help="Results folder to analyse. Defaults to results/.")
    ] = None,
) -> None:
    """Score results and build tables and charts. Reads committed results; needs no API key."""
    try:
        experiment = load_config(config)
        folder = results if results is not None else results_dir(config)
        records = load_records(folder / "raw.jsonl")
        if not records:
            typer.echo(
                f"No results found in {folder}. Run `lab run {config}` first, or pass --results.",
                err=True,
            )
            raise typer.Exit(code=2)
        report = load_analyse_function(config)(experiment, config.parent, records)
    except (ConfigError, PlanError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(report)


def _run_log_path(config: Path, fresh: bool) -> Path:
    """Committed results drive resume. `--fresh` writes to a separate, gitignored folder."""
    if not fresh:
        return results_dir(config) / "raw.jsonl"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return config.parent / "results-fresh" / stamp / "raw.jsonl"


def _check_budget(
    experiment: ExperimentConfig,
    selected: list[PlannedCall],
    *,
    cache: ResponseCache,
    raw_path: Path,
    prices_path: Path,
    pilot: bool,
) -> None:
    """Refuse to start when the calls still to make would cost more than the budget."""
    prices = load_prices(prices_path)
    budget = prices.budget_for(experiment.experiment) if prices else None
    if budget is None:
        return
    check_budget(
        estimate_run(
            "Pilot" if pilot else "Full run",
            selected,
            cache=cache,
            prior_records=load_records(raw_path),
            prices=prices,
            count_tokens=default_token_counter(),
        ),
        budget,
    )


def _providers_for(experiment: ExperimentConfig, selected: list[PlannedCall]) -> dict:
    """Providers needed by the selected calls, refusing early when a key is missing."""
    needed = sorted({call.request.provider for call in selected})
    available = available_providers(needed)
    if available.missing_keys:
        missing = "; ".join(
            f"{name}: set {' or '.join(variables)}"
            for name, variables in sorted(available.missing_keys.items())
        )
        raise PlanError(
            f"No API key for {missing}. Add the key to .env, or run one provider with --provider."
        )
    return dict(available.providers)


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
