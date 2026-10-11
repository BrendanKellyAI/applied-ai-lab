"""`lab rag`: estimate and run a Season 2 episode on the reference pipeline."""

import os
from pathlib import Path
from typing import Annotated, Any

import typer
from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ConfigError
from lab.prices import load_prices
from lab.providers.registry import available_providers
from lab.rag.config import Episode, ResolvedCondition, load_episode
from lab.rag.corpus import CorpusError, load_library
from lab.rag.embed import Embedder, EmbeddingsClient, EmbeddingStore
from lab.rag.estimate import ConditionEstimate, estimate_condition, format_estimate
from lab.rag.pipeline import RunContext, run_condition, select_items
from lab.runner import Runner

rag_app = typer.Typer(help="Estimate and run Season 2 RAG episodes.", no_args_is_help=True)

ConfigArg = Annotated[Path, typer.Argument(help="The episode's config.yaml.")]
PilotOption = Annotated[bool, typer.Option("--pilot", help="Run the pilot items only.")]
CacheOption = Annotated[
    Path | None,
    typer.Option(help="Cache folder. Default: the main checkout's .cache, shared by worktrees."),
]
PricesOption = Annotated[Path, typer.Option(help="Prices and budgets file.")]


def _cache_root(cache_dir: Path | None) -> Path:
    return cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())


def _embedder(model: str, client: EmbeddingsClient | None, cache_root: Path) -> Embedder:
    return Embedder(client, model, EmbeddingStore(cache_root / "embeddings" / "s2.sqlite"))


def _embedding_client() -> EmbeddingsClient | None:
    """An OpenAI client for embeddings, or None when there is no key."""
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    import openai

    return openai.OpenAI(max_retries=2)


def _load(config: Path) -> tuple[Episode, Any]:
    try:
        episode = load_episode(config)
        return episode, load_library(episode.library)
    except (ConfigError, CorpusError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _conditions(episode: Episode, name: str | None) -> list[ResolvedCondition]:
    chosen = [c for c in episode.conditions if name is None or c.name == name]
    if not chosen:
        typer.echo(f"Error: no condition named {name}", err=True)
        raise typer.Exit(code=1)
    return chosen


def _estimates(
    episode: Episode,
    library: Any,
    conditions: list[ResolvedCondition],
    *,
    pilot: bool,
    cache_root: Path,
    prices: Any,
) -> list[ConditionEstimate]:
    items = select_items(
        library, episode.config.items, pilot=pilot, per_type=episode.config.pilot_per_type
    )
    return [
        estimate_condition(
            library,
            items,
            condition,
            _embedder(condition.pipeline.embed.model, None, cache_root),
            episode=episode.config.episode,
            cache=ResponseCache(cache_root),
            prices=prices,
        )
        for condition in conditions
    ]


@rag_app.command()
def estimate(
    config: ConfigArg,
    pilot: PilotOption = False,
    condition: Annotated[str | None, typer.Option(help="One condition only.")] = None,
    cache_dir: CacheOption = None,
    prices_path: PricesOption = Path("prices.local.yaml"),
) -> None:
    """Count tokens and cost for an episode. Needs no API key and makes no call."""
    episode, library = _load(config)
    prices = load_prices(prices_path)
    estimates = _estimates(
        episode,
        library,
        _conditions(episode, condition),
        pilot=pilot,
        cache_root=_cache_root(cache_dir),
        prices=prices,
    )
    budget = prices.budget_for(episode.config.episode) if prices else None
    currency = prices.currency if prices else "USD"
    typer.echo(format_estimate(episode.config.episode, estimates, budget, currency))


@rag_app.command()
def run(
    config: ConfigArg,
    pilot: PilotOption = False,
    condition: Annotated[str | None, typer.Option(help="One condition only.")] = None,
    cache_dir: CacheOption = None,
    prices_path: PricesOption = Path("prices.local.yaml"),
    env_file: Annotated[Path, typer.Option(help="File of API keys.")] = Path(".env"),
) -> None:
    """Run an episode's conditions, or one of them. Refuses if over the episode's budget."""
    load_dotenv(env_file, override=False)
    episode, library = _load(config)
    conditions = _conditions(episode, condition)
    cache_root = _cache_root(cache_dir)
    prices = load_prices(prices_path)
    _check_budget(episode, library, conditions, pilot=pilot, cache_root=cache_root, prices=prices)

    runner = _runner(episode, conditions, cache_root)
    items = select_items(
        library, episode.config.items, pilot=pilot, per_type=episode.config.pilot_per_type
    )
    results = episode.folder / "results" / ("pilot" if pilot else "")
    client = _embedding_client()
    for chosen in conditions:
        context = RunContext(
            episode=episode,
            library=library,
            embedder=_embedder(chosen.pipeline.embed.model, client, cache_root),
            runner=runner,
            results=results,
        )
        summary = run_condition(context, chosen, items)
        typer.echo(_one_line(summary))


def _check_budget(
    episode: Episode,
    library: Any,
    conditions: list[ResolvedCondition],
    *,
    pilot: bool,
    cache_root: Path,
    prices: Any,
) -> None:
    budget = prices.budget_for(episode.config.episode) if prices else None
    if budget is None:
        return
    estimates = _estimates(
        episode, library, conditions, pilot=pilot, cache_root=cache_root, prices=prices
    )
    costs = [e.cost for e in estimates]
    if any(c is None for c in costs):
        typer.echo("Error: a price is missing, so the budget cannot be checked.", err=True)
        raise typer.Exit(code=1)
    total = sum(c for c in costs if c is not None)
    if total > budget:
        typer.echo(
            f"Error: the estimate, {total:,.2f}, is over the budget of {budget:,.2f}. "
            "Raise the budget in prices.local.yaml to go ahead.",
            err=True,
        )
        raise typer.Exit(code=1)


def _runner(episode: Episode, conditions: list[ResolvedCondition], cache_root: Path) -> Runner:
    full = [c for c in conditions if c.measure == "full"]
    needed = sorted({s.provider for c in full for s in (c.pipeline.answer, c.pipeline.judge)})
    available = available_providers(needed)
    if available.missing_keys:
        missing = "; ".join(
            f"{name}: set {' or '.join(variables)}"
            for name, variables in sorted(available.missing_keys.items())
        )
        typer.echo(f"Error: no API key for {missing}.", err=True)
        raise typer.Exit(code=1)
    return Runner(
        providers=dict(available.providers),
        cache=ResponseCache(cache_root),
        limits=episode.config.limits,
    )


def _one_line(summary: dict[str, Any]) -> str:
    parts = [f"{summary['condition']} [{summary['config_id']}]"]
    for name, number in summary["numbers"].items():
        parts.append(f"{name} {number['count']}/{number['total']}")
    return "  ".join(parts)
