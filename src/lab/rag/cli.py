"""`lab rag`: estimate and run a Season 2 episode on the reference pipeline."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ConfigError
from lab.experiments import load_sibling
from lab.prices import load_prices
from lab.providers.registry import available_providers
from lab.rag.build_corpus.cli import build_corpus
from lab.rag.config import Episode, ResolvedCondition, load_episode
from lab.rag.corpus import CorpusError, load_library
from lab.rag.embed import Embedder, EmbeddingsClient, EmbeddingStore, openai_client
from lab.rag.estimate import ConditionEstimate, estimate_condition, format_estimate
from lab.rag.judge_check import (
    MARKS,
    REPORT,
    SAMPLE,
    CheckConfig,
    agreement,
    chunk_lookup,
    draw_sample,
    format_report,
    judge_prompt_hash,
    load_check_config,
    read_marks,
    write_sheet,
)
from lab.rag.log import read_log
from lab.rag.pipeline import RunContext, run_condition, select_items
from lab.runner import Runner

rag_app = typer.Typer(help="Estimate and run Season 2 RAG episodes.", no_args_is_help=True)
rag_app.command("build-corpus")(build_corpus)

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
    client = openai_client()
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


@rag_app.command()
def analyse(config: ConfigArg, pilot: PilotOption = False) -> None:
    """Claims, charts and the scoreboard row from an episode's committed results. No key."""
    episode, _ = _load(config)
    module = load_sibling(episode.folder / "analyse.py")
    results = episode.folder / "results" / ("pilot" if pilot else "")
    typer.echo(module.analyse(episode, results, pilot=pilot))


judge_app = typer.Typer(help="Check the judge against hand marks (S2 E3).", no_args_is_help=True)
rag_app.add_typer(judge_app, name="judge-check")
CheckArg = Annotated[Path, typer.Argument(help="The judge check's judge_check.yaml.")]


@judge_app.command("draw")
def judge_draw(config: CheckArg) -> None:
    """Draw the sample and write the blind marking sheet. No key, no call."""
    check = _check_config(config)
    library = load_library(check.library)
    logs = read_log(check.run / "log.jsonl")
    summary = json.loads((check.run / "summary.json").read_text(encoding="utf-8"))
    sample = draw_sample(logs, size=check.size, per_type=check.per_type, seed=check.seed)
    run = {
        "episode": summary["episode"],
        "condition": summary["condition"],
        "config_id": summary["config_id"],
        "seed": check.seed,
    }
    try:
        written = write_sheet(
            check.out, sample, logs, library, chunk_lookup(library, summary["pipeline"]), run=run
        )
    except FileExistsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Drew {len(sample)} items. Mark them in {written[1]}, reading {written[0]}.")


@judge_app.command("report")
def judge_report(config: CheckArg) -> None:
    """Compare the hand marks with the judge and write agreement.json. No key, no call."""
    check = _check_config(config)
    record = json.loads((check.out / SAMPLE).read_text(encoding="utf-8"))
    logs = read_log(check.run / "log.jsonl")
    if record["judge_prompt"] != judge_prompt_hash():
        typer.echo("Error: the judge's instructions changed since the sample was drawn.", err=True)
        raise typer.Exit(code=1)
    if {g.config_id for g in logs} != {record["config_id"]}:
        typer.echo("Error: the run's log is not the run the sample was drawn from.", err=True)
        raise typer.Exit(code=1)
    try:
        marks = read_marks(check.out / MARKS, record["items"])
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    report = agreement(marks, logs)
    (check.out / REPORT).write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    typer.echo(format_report(report))


def _check_config(path: Path) -> CheckConfig:
    try:
        return load_check_config(path)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
