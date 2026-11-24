"""`lab adapt pairs`, `facts-run` and `facts-analyse`: S4 E8's commands.

`pairs` and `facts-run` spend, so both print their estimate first and stop unless the
episode's budget in prices.local.yaml covers the ceiling cost. `facts-analyse` makes no call.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab.adapt.build_tasks.estimate import StageCost, format_estimate
from lab.adapt.facts import blocked_questions, build_pairs, training_passages, write_pairs
from lab.adapt.facts_eval import (
    FactsExperiment,
    PairsConfig,
    analyse,
    estimate_judge,
    estimate_pairs,
    run_judge,
    run_pairs,
    write_analysis,
)
from lab.cache import ResponseCache, shared_cache_root
from lab.config import ProviderLimits
from lab.prices import PricesFile, load_prices
from lab.providers.registry import available_providers
from lab.rag.corpus import load_library
from lab.runner import Runner

PRICES = Path("prices.local.yaml")
PricesOption = Annotated[Path, typer.Option(help="Prices and budgets.")]
EstimateOption = Annotated[
    bool, typer.Option("--estimate", help="Count tokens and cost, and make no call.")
]
EnvOption = Annotated[Path, typer.Option(help="File of API keys.")]
CacheOption = Annotated[Path | None, typer.Option(help="Cache folder.")]


def _fail(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def _gate(episode: str, costs: Sequence[StageCost], prices: PricesFile | None) -> None:
    """Stop unless every model has a price and the episode's budget covers the ceiling."""
    budget = prices.budget_for(episode) if prices else None
    ceiling = [c.ceiling_cost for c in costs]
    if budget is None or any(c is None for c in ceiling):
        _fail(f"set a price for every model and a {episode} budget first.")
    total = sum(c for c in ceiling if c is not None)
    if total > budget:
        _fail(f"the ceiling cost, {total:,.2f}, is over the {episode} budget of {budget:,.2f}.")
    typer.echo(f"Budget check on the ceiling cost: {total:,.2f} of {budget:,.2f}.")


def _runner(provider: str, limits: dict[str, ProviderLimits], cache_root: Path) -> Runner:
    available = available_providers([provider])
    if available.missing_keys:
        _fail("set " + ", ".join(" or ".join(v) for v in available.missing_keys.values()) + ".")
    return Runner(
        providers=dict(available.providers), cache=ResponseCache(cache_root), limits=limits
    )


def pairs_command(
    config: Annotated[Path, typer.Argument(help="The episode's pairs.yaml.")],
    estimate: EstimateOption = False,
    cache_dir: CacheOption = None,
    prices_path: PricesOption = PRICES,
    env_file: EnvOption = Path(".env"),
) -> None:
    """Generate E8's training pairs from the library's current public passages."""
    spec = PairsConfig.load(config)
    library = load_library(spec.data_folder)
    prices = load_prices(prices_path)
    cost = estimate_pairs(spec, library, prices)
    title = f"{spec.episode} pairs estimate"
    typer.echo(format_estimate([cost], prices.currency if prices else "USD", title, ""))
    if estimate:
        return
    _gate(spec.episode, [cost], prices)
    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    runner = _runner(spec.generator.provider, spec.limits, root)
    replies, summary = run_pairs(runner, spec, library)
    passages = training_passages(library)
    pairs, log = build_pairs(passages, replies, spec.per_passage, blocked_questions(library))
    write_pairs(spec.out_path, pairs)
    log_path = spec.out_path.with_name("pairs-log.json")
    log_path.write_bytes((json.dumps(log, indent=2) + "\n").encode("utf-8"))
    typer.echo(f"pairs: made {summary.made}, cached {summary.cached}, failed {summary.failed}")
    near = len(log["near_duplicates_of_dev_or_test"])
    typer.echo(
        f"Kept {log['pairs_kept']} pairs from {log['passages']} passages; "
        f"{len(log['passages_failed'])} passages failed, {near} near duplicates of dev or test "
        f"questions removed, {log['repeated_questions']} repeated questions removed."
    )


def facts_run_command(
    config: Annotated[Path, typer.Argument(help="The episode's config.yaml.")],
    estimate: EstimateOption = False,
    cache_dir: CacheOption = None,
    prices_path: PricesOption = PRICES,
    env_file: EnvOption = Path(".env"),
) -> None:
    """Judge every closed-book arm's answers. The Season 2 reference makes no call."""
    experiment = FactsExperiment.load(config)
    prices = load_prices(prices_path)
    costs = estimate_judge(experiment, prices)
    title = f"{experiment.episode} judge estimate ({experiment.split})"
    typer.echo(format_estimate(costs, prices.currency if prices else "USD", title, ""))
    if estimate:
        return
    _gate(experiment.episode, costs, prices)
    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    runner = _runner(experiment.judge.provider, experiment.limits, root)
    for arm, summary in run_judge(runner, experiment).items():
        typer.echo(
            f"judge-{arm}: made {summary['made']}, cached {summary['cached']}, "
            f"failed {summary['failed']}"
        )


def facts_analyse_command(
    config: Annotated[Path, typer.Argument(help="The episode's config.yaml.")],
) -> None:
    """Score every arm from its judge verdicts. No API calls."""
    experiment = FactsExperiment.load(config)
    result = analyse(experiment)
    path = write_analysis(experiment, result)
    for name, arm in result["arms"].items():
        r, d, w = arm["right"], arm["declined_unanswerable"], arm["confident_wrong"]
        typer.echo(
            f"{name}: right {r['count']} of {r['total']}, declined {d['count']} of "
            f"{d['total']}, confident wrong {w['count']} of {w['total']}"
        )
    typer.echo(f"Wrote {path}")
