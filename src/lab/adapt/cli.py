"""`lab adapt`: Season 4 commands."""

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab.adapt.build_tasks.config import TaskBuildConfig
from lab.adapt.build_tasks.estimate import estimate_task_a, estimate_task_b, format_estimate
from lab.adapt.build_tasks.task_a import build_task_a, plan_seeds
from lab.adapt.build_tasks.task_b import build_task_b, plan_b_seeds
from lab.adapt.definitions import Definitions
from lab.cache import ResponseCache, shared_cache_root
from lab.prices import PricesFile, load_prices
from lab.providers.registry import available_providers
from lab.rag.corpus import load_library
from lab.runner import Runner

adapt_app = typer.Typer(
    help="Build and run Season 4 adapting models episodes.", no_args_is_help=True
)

# The budgets in prices.local.yaml that each task data build is checked against.
BUDGET_KEYS = {"a": "s4-task-data", "b": "s4-task-b-data"}
TASKS = Path("datasets/halvard-tasks")


@adapt_app.command("build-tasks")
def build_tasks(
    folder: Annotated[Path, typer.Option(help="The task data folder.")] = TASKS,
    task: Annotated[str, typer.Option(help="Which task to build: a or b.")] = "a",
    pilot: Annotated[bool, typer.Option("--pilot", help="Build the pilot only.")] = False,
    estimate: Annotated[
        bool, typer.Option("--estimate", help="Count tokens and cost, and make no call.")
    ] = False,
    cache_dir: Annotated[Path | None, typer.Option(help="Cache folder.")] = None,
    prices_path: Annotated[Path, typer.Option(help="Prices and budgets.")] = Path(
        "prices.local.yaml"
    ),
    env_file: Annotated[Path, typer.Option(help="File of API keys.")] = Path(".env"),
) -> None:
    """Build the Task A or Task B data (datasets/halvard-tasks/GENERATION_PLAN.md)."""
    if task not in ("a", "b"):
        typer.echo("Error: --task must be a or b.", err=True)
        raise typer.Exit(code=1)
    config = TaskBuildConfig.load(folder / "config.yaml")
    prices = load_prices(prices_path)
    currency = prices.currency if prices else "USD"
    kind = "pilot" if pilot else "full build"
    if task == "a":
        definitions = Definitions.load(folder / "routes.yaml")
        seeds = plan_seeds(config, definitions, pilot=pilot)
        costs = estimate_task_a(config, definitions, seeds, prices)
    else:
        library = load_library(folder / config.task_b.library)
        style_guide = (folder / "style-guide.md").read_text(encoding="utf-8")
        b_seeds = plan_b_seeds(config, library, pilot=pilot)
        costs = estimate_task_b(config, b_seeds, style_guide, prices)
    typer.echo(
        format_estimate(costs, currency, f"Task {task.upper()} data build estimate ({kind})")
    )
    if estimate:
        return
    _check_budget(prices, [c.expected_cost for c in costs], BUDGET_KEYS[task])
    runner = _runner(config, cache_dir, env_file)
    if task == "a":
        log = build_task_a(
            runner, config, definitions, folder / ("pilot" if pilot else "task-a"), pilot=pilot
        )
        _report_a(log)
    else:
        out = folder / ("pilot-b" if pilot else "task-b")
        log = build_task_b(runner, config, library, style_guide, out, pilot=pilot)
        _report_b(log)


def _runner(config: TaskBuildConfig, cache_dir: Path | None, env_file: Path) -> Runner:
    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    available = available_providers([config.generator.provider, config.labeller.provider])
    if available.missing_keys:
        missing = ", ".join(" or ".join(v) for v in available.missing_keys.values())
        typer.echo(f"Error: set {missing}.", err=True)
        raise typer.Exit(code=1)
    return Runner(
        providers=dict(available.providers), cache=ResponseCache(root), limits=config.limits
    )


def _report_a(log: dict) -> None:
    typer.echo(f"Kept: {log['kept']}; safety items kept: {log['safety_items_kept']}")
    typer.echo(f"Generation failed: {len(log['generation_failed'])}")
    disagreements = log["label_disagreements"]
    typer.echo(f"Label disagreements: {disagreements['total']} {disagreements['by_field']}")
    typer.echo(f"Near duplicates removed: {len(log['near_duplicates_removed'])}")


def _report_b(log: dict) -> None:
    typer.echo(f"Kept: {log['kept']}; not found items kept: {log['not_found_kept']}")
    for name in ("qa_failed", "unsupported", "rewrite_failed", "facts_not_kept"):
        typer.echo(f"{name.replace('_', ' ')}: {len(log[name])}")


def _check_budget(prices: PricesFile | None, expected: list[float | None], key: str) -> None:
    budget = prices.budget_for(key) if prices else None
    if budget is None:
        typer.echo(f"Error: set a {key} budget in prices.local.yaml first.", err=True)
        raise typer.Exit(code=1)
    if any(c is None for c in expected):
        typer.echo("Error: a price is missing, so the budget cannot be checked.", err=True)
        raise typer.Exit(code=1)
    total = sum(c for c in expected if c is not None)
    if total > budget:
        typer.echo(
            f"Error: the expected cost, {total:,.2f}, is over the {key} budget of {budget:,.2f}.",
            err=True,
        )
        raise typer.Exit(code=1)


# Imported here, after the app exists, to keep the build commands' module short.
from lab.adapt import cli_run  # noqa: E402

adapt_app.command("run")(cli_run.run_command)
adapt_app.command("analyse")(cli_run.analyse_command)
adapt_app.command("tune")(cli_run.tune_command)
adapt_app.command("status")(cli_run.status_command)
adapt_app.command("score")(cli_run.score_command)

from lab.adapt import cli_facts  # noqa: E402

adapt_app.command("pairs")(cli_facts.pairs_command)
adapt_app.command("facts-run")(cli_facts.facts_run_command)
adapt_app.command("facts-analyse")(cli_facts.facts_analyse_command)
