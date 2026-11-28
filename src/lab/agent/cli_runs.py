"""`lab agent run`, `estimate`, `replay` and `score`."""

import json
from pathlib import Path
from typing import Annotated

import typer

from lab.agent.cli import agent_app

PricesOption = Annotated[Path, typer.Option(help="Local prices and budgets file.")]
CacheOption = Annotated[Path, typer.Option(help="Response cache folder.")]


@agent_app.command("estimate")
def estimate_command(config: Path) -> None:
    """Tokens for an agent experiment, from a dry run on the mock provider. No calls."""
    from lab.agent.agent_estimate import estimate_arm
    from lab.agent.config import load_experiment
    from lab.agent.run import load_cases

    experiment = load_experiment(config)
    cases = load_cases(experiment.cases, experiment.case_ids)
    for arm in experiment.arms:
        typer.echo("\n".join(estimate_arm(experiment, arm, cases).lines()))


@agent_app.command("run")
def run_command(
    config: Path,
    prices: PricesOption = Path("prices.local.yaml"),
    cache_dir: CacheOption = Path(".cache"),
    env_file: Annotated[Path, typer.Option(help="File to read API keys from.")] = Path(".env"),
    dry_run: Annotated[
        bool, typer.Option(help="The oracle on the mock provider: no spend.")
    ] = False,
) -> None:
    """Run every arm of an agent experiment. Paid runs need budgets.<experiment> set."""
    from dotenv import load_dotenv

    from lab.agent.caller import BudgetExceeded, ModelCaller
    from lab.agent.config import load_experiment
    from lab.agent.mock_agent import oracle
    from lab.agent.run import load_cases, run_experiment
    from lab.cache import ResponseCache
    from lab.prices import load_prices
    from lab.providers.mock import MockProvider
    from lab.providers.registry import available_providers

    experiment = load_experiment(config)
    # One folder per config, so a dev pilot and a test run never overwrite each other.
    results = config.parent / ("results-dry-run" if dry_run else "results") / config.stem
    if dry_run:
        facts = {
            c.facts.case_id: c.facts for c in load_cases(experiment.cases, experiment.case_ids)
        }
        mock = MockProvider(respond=oracle(facts))
        providers = {arm.model.provider: mock for arm in experiment.arms}
        caller = ModelCaller(
            providers, ResponseCache(results / "cache"), requests_per_minute=100_000
        )
    else:
        load_dotenv(env_file, override=False)
        table = load_prices(prices)
        budget = table.budget_for(experiment.experiment) if table else None
        if budget is None:
            typer.echo(
                f"Refusing: set budgets.{experiment.experiment} in {prices} once approved.",
                err=True,
            )
            raise typer.Exit(code=2)
        available = available_providers(
            {arm.model.provider for arm in experiment.arms} | {"openai"}
        )
        if available.missing_keys:
            typer.echo(f"Missing API keys: {dict(available.missing_keys)}", err=True)
            raise typer.Exit(code=2)
        model_prices = {
            model: (price.input or 0.0, price.output or 0.0)
            for models in table.prices.values()
            for model, price in models.items()
        }
        caller = ModelCaller(
            available.providers,
            ResponseCache(cache_dir),
            requests_per_minute=experiment.requests_per_minute,
            budget=budget,
            prices=model_prices,
        )
    try:
        summaries = run_experiment(experiment, caller, results, cache_dir, keyword_only=dry_run)
    except BudgetExceeded as exc:
        typer.echo(f"Stopped: {exc}", err=True)
        raise typer.Exit(code=3) from exc
    spend = caller.spend
    typer.echo(json.dumps(summaries, indent=1))
    tokens = f"input {spend.input_tokens:,}, output {spend.output_tokens:,}"
    typer.echo(f"New calls {spend.calls} ({tokens}); cached {spend.cached}")


@agent_app.command("replay")
def replay_command(
    runs: Annotated[Path, typer.Argument(help="An arm's runs.jsonl.")],
    case_id: str,
    repeat: int = 0,
    out: Annotated[Path | None, typer.Option(help="Folder for the .md and -slide.svg.")] = None,
) -> None:
    """Print one case's trajectory; with --out, also write Markdown and a slide SVG. No calls."""
    from lab.agent.replay import load_run, markdown, write_replay

    run = load_run(runs, case_id, repeat)
    typer.echo(markdown(run))
    if out is not None:
        for path in write_replay(run, out):
            typer.echo(f"Wrote {path}")


@agent_app.command("score")
def score_command(
    end_states: Annotated[Path, typer.Argument(help="JSON lines: case_id and outcomes.")],
    cases: Annotated[str, typer.Option(help="Case file the end states answer.")] = "dev",
) -> None:
    """Score your own agent's decisions against the cases, with no calls (see the README)."""
    from lab.agent.reader_score import score_file

    typer.echo(json.dumps(score_file(end_states, cases), indent=1))
