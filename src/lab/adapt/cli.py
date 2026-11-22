"""`lab adapt`: Season 4 commands."""

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab.adapt.build_tasks.config import TaskBuildConfig
from lab.adapt.build_tasks.estimate import estimate_task_a, format_estimate
from lab.adapt.build_tasks.task_a import build_task_a, plan_seeds
from lab.adapt.definitions import Definitions
from lab.cache import ResponseCache, shared_cache_root
from lab.prices import PricesFile, load_prices
from lab.providers.registry import available_providers
from lab.runner import Runner

adapt_app = typer.Typer(
    help="Build and run Season 4 adapting models episodes.", no_args_is_help=True
)

# The budget in prices.local.yaml that the task data build is checked against.
BUDGET_KEY = "s4-task-data"
TASKS = Path("datasets/halvard-tasks")


@adapt_app.command("build-tasks")
def build_tasks(
    folder: Annotated[Path, typer.Option(help="The task data folder.")] = TASKS,
    pilot: Annotated[bool, typer.Option("--pilot", help="Build the Task A pilot only.")] = False,
    estimate: Annotated[
        bool, typer.Option("--estimate", help="Count tokens and cost, and make no call.")
    ] = False,
    cache_dir: Annotated[Path | None, typer.Option(help="Cache folder.")] = None,
    prices_path: Annotated[Path, typer.Option(help="Prices and budgets.")] = Path(
        "prices.local.yaml"
    ),
    env_file: Annotated[Path, typer.Option(help="File of API keys.")] = Path(".env"),
) -> None:
    """Build the Task A triage data (datasets/halvard-tasks/GENERATION_PLAN.md)."""
    config = TaskBuildConfig.load(folder / "config.yaml")
    definitions = Definitions.load(folder / "routes.yaml")
    seeds = plan_seeds(config, definitions, pilot=pilot)
    prices = load_prices(prices_path)
    currency = prices.currency if prices else "USD"
    costs = estimate_task_a(config, definitions, seeds, prices)
    title = f"Task A data build estimate ({'pilot' if pilot else 'full build'})"
    typer.echo(format_estimate(costs, currency, title))
    if estimate:
        return
    _check_budget(prices, [c.expected_cost for c in costs])

    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    available = available_providers([config.generator.provider, config.labeller.provider])
    if available.missing_keys:
        missing = ", ".join(" or ".join(v) for v in available.missing_keys.values())
        typer.echo(f"Error: set {missing}.", err=True)
        raise typer.Exit(code=1)
    runner = Runner(
        providers=dict(available.providers), cache=ResponseCache(root), limits=config.limits
    )
    out = folder / ("pilot" if pilot else "task-a")
    log = build_task_a(runner, config, definitions, out, pilot=pilot)
    typer.echo(f"Kept: {log['kept']}; safety items kept: {log['safety_items_kept']}")
    typer.echo(f"Generation failed: {len(log['generation_failed'])}")
    disagreements = log["label_disagreements"]
    typer.echo(f"Label disagreements: {disagreements['total']} {disagreements['by_field']}")
    typer.echo(f"Near duplicates removed: {len(log['near_duplicates_removed'])}")


def _check_budget(prices: PricesFile | None, expected: list[float | None]) -> None:
    budget = prices.budget_for(BUDGET_KEY) if prices else None
    if budget is None:
        typer.echo(f"Error: set a {BUDGET_KEY} budget in prices.local.yaml first.", err=True)
        raise typer.Exit(code=1)
    if any(c is None for c in expected):
        typer.echo("Error: a price is missing, so the budget cannot be checked.", err=True)
        raise typer.Exit(code=1)
    total = sum(c for c in expected if c is not None)
    if total > budget:
        typer.echo(
            f"Error: the expected cost, {total:,.2f}, is over the {BUDGET_KEY} budget of "
            f"{budget:,.2f}.",
            err=True,
        )
        raise typer.Exit(code=1)
