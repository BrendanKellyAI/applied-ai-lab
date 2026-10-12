"""`lab rag build-corpus`: estimate, pilot or build the Halvard library."""

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ConfigError
from lab.prices import load_prices
from lab.providers.registry import available_providers
from lab.rag.build_corpus.build import (
    Builder,
    BuildError,
    blueprint,
    full_scope,
    pilot_scope,
    run_build,
)
from lab.rag.build_corpus.catalogue import load_corpus_config
from lab.rag.build_corpus.estimate import estimate_build, format_build_estimate
from lab.rag.build_corpus.v1 import load_v1
from lab.rag.embed import Embedder, EmbeddingStore, openai_client
from lab.runner import Runner

# The budget in prices.local.yaml that a build is checked against.
BUDGET_KEY = "s2-corpus"


def build_corpus(
    folder: Annotated[Path, typer.Option(help="The library folder.")] = Path("datasets/halvard"),
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
    """Build the Halvard library and test set (Season 2 corpus spec)."""
    try:
        config = load_corpus_config(folder / "config.yaml")
    except ConfigError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    v1 = load_v1(folder / "v1")
    bp = blueprint(config, v1)
    scope = pilot_scope(config, bp, v1) if pilot else full_scope(bp, v1)
    prices = load_prices(prices_path)
    currency = prices.currency if prices else "USD"
    costs = estimate_build(config, bp, scope, v1, prices)
    if estimate:
        typer.echo(format_build_estimate(costs, currency, pilot))
        return

    budget = prices.budget_for(BUDGET_KEY) if prices else None
    expected = [c.expected_cost for c in costs]
    if budget is not None:
        if any(c is None for c in expected):
            typer.echo("Error: a price is missing, so the budget cannot be checked.", err=True)
            raise typer.Exit(code=1)
        if sum(expected) > budget:
            typer.echo(
                f"Error: the expected cost, {sum(expected):,.2f}, is over the {BUDGET_KEY} "
                f"budget of {budget:,.2f}.",
                err=True,
            )
            raise typer.Exit(code=1)

    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    available = available_providers([config.generation.provider, config.checker.provider])
    if available.missing_keys:
        missing = ", ".join(" or ".join(v) for v in available.missing_keys.values())
        typer.echo(f"Error: set {missing}.", err=True)
        raise typer.Exit(code=1)
    builder = Builder(
        config=config,
        folder=folder,
        v1=v1,
        runner=Runner(providers=dict(available.providers), cache=ResponseCache(root), limits={}),
        embedder=Embedder(
            openai_client(),
            "text-embedding-3-small",
            EmbeddingStore(root / "embeddings" / "s2.sqlite"),
        ),
    )
    try:
        log = run_build(builder, pilot=pilot)
    except BuildError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Items: {log['items']['test']} test, {log['items']['dev']} dev")
    for stage in ("sections", "questions", "followups", "quotes", "checks"):
        summary = log[stage]
        typer.echo(
            f"{stage}: {summary['passed']} of {summary['tasks']} passed, "
            f"attempts {summary['attempts']}, failed {len(summary['failed'])}"
        )
    typer.echo(f"Disputed by the checker: {len(log['disputed'])}")
