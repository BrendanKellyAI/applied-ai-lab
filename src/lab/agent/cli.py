"""`lab agent`: the Season 5 case environment and agent runs."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lab.agent.build import SEED, build_dataset

agent_app = typer.Typer(help="Season 5: the Halvard case environment and agent runs.")


@agent_app.command("build-world")
def build_world_command(
    root: Annotated[Path, typer.Option(help="Repository root to write under.")] = Path("."),
    seed: Annotated[int, typer.Option(help="Random seed for the world and cases.")] = SEED,
) -> None:
    """Build the case world, case facts, images and telemetry logs. No model calls."""
    summary = build_dataset(root, seed)
    typer.echo(json.dumps(asdict(summary), indent=2))


CASES_DIR = Path("datasets") / "halvard-cases" / "cases"


@agent_app.command("estimate-data")
def estimate_data_command(
    prices: Annotated[Path, typer.Option(help="Local prices file.")] = Path("prices.local.yaml"),
) -> None:
    """Tokens (and cost, from local prices) for writing messages and checking labels."""
    from lab.agent.data_estimate import all_cases, estimate, format_estimate
    from lab.prices import load_prices

    typer.echo(format_estimate(estimate(all_cases(CASES_DIR)), load_prices(prices)))


@agent_app.command("write-messages")
def write_messages_command(
    prices: Annotated[Path, typer.Option(help="Local prices file.")] = Path("prices.local.yaml"),
    cache_dir: Annotated[Path, typer.Option(help="Response cache folder.")] = Path(".cache"),
    env_file: Annotated[Path, typer.Option(help="File to read API keys from.")] = Path(".env"),
) -> None:
    """Paid: write every case message and check its label. Needs an approved budget."""
    from dotenv import load_dotenv

    from lab.agent.data_run import BudgetRefused, run_case_data
    from lab.prices import load_prices
    from lab.providers.registry import available_providers

    load_dotenv(env_file, override=False)
    available = available_providers(["google", "anthropic"])
    if available.missing_keys:
        typer.echo(f"Missing API keys: {dict(available.missing_keys)}", err=True)
        raise typer.Exit(code=2)
    try:
        log = run_case_data(
            cases_dir=CASES_DIR,
            review_path=Path("season5") / "case-review.md",
            prices=load_prices(prices),
            providers=available.providers,
            cache_dir=cache_dir,
        )
    except BudgetRefused as exc:
        typer.echo(f"Refusing: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    summary = {k: log[k] for k in ("cases_written", "discarded", "accepted_on_attempt")}
    typer.echo(json.dumps(summary, indent=2))
