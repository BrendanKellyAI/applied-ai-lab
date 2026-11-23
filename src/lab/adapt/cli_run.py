"""`lab adapt run`, `tune`, `status`, `analyse` and `score`.

`run` and `tune --launch` are the only commands that spend or start anything, and both stop
unless asked: `run` checks the episode's budget in prices.local.yaml, and `tune` launches only
with `--launch` and the name of whoever approved it.
"""

import json
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from lab.adapt.analyse import analyse, write_analysis
from lab.adapt.build_tasks.estimate import format_estimate
from lab.adapt.definitions import Definitions
from lab.adapt.estimate import estimate_experiment
from lab.adapt.experiment import DATA, Experiment
from lab.adapt.items import triage_items
from lab.adapt.requests import load_inputs
from lab.adapt.run import read_jsonl, run_experiment
from lab.adapt.score_a import score_items, summarise
from lab.adapt.tune import JobError, find_job, launch, load_record, prepare, record_result
from lab.adapt.tune_config import TuneConfig
from lab.cache import ResponseCache, shared_cache_root
from lab.prices import load_prices
from lab.providers.registry import available_providers
from lab.rag.embed import Embedder, EmbeddingStore, openai_client
from lab.runner import Runner

PricesOption = Annotated[Path, typer.Option(help="Prices and budgets.")]
PRICES = Path("prices.local.yaml")


def _fail(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def _runner(experiment: Experiment, cache_root: Path) -> Runner:
    names = {experiment.model_for(a).provider for a in experiment.arms if not a.external}
    if experiment.judge is not None:
        names.add(experiment.judge.provider)
    available = available_providers(sorted(names))
    if available.missing_keys:
        _fail("set " + ", ".join(" or ".join(v) for v in available.missing_keys.values()) + ".")
    return Runner(
        providers=dict(available.providers),
        cache=ResponseCache(cache_root),
        limits=experiment.limits,
    )


def run_command(
    config: Annotated[Path, typer.Argument(help="The episode's config.yaml.")],
    estimate: Annotated[
        bool, typer.Option("--estimate", help="Count tokens and cost, and make no call.")
    ] = False,
    cache_dir: Annotated[Path | None, typer.Option(help="Cache folder.")] = None,
    prices_path: PricesOption = PRICES,
    env_file: Annotated[Path, typer.Option(help="File of API keys.")] = Path(".env"),
) -> None:
    """Run the prompted arms (and, for Task B, the judges) against the config's split."""
    experiment = Experiment.load(config)
    inputs = load_inputs(experiment)
    prices = load_prices(prices_path)
    costs = estimate_experiment(experiment, inputs, prices)
    title = f"{experiment.episode} estimate ({experiment.split}, {len(inputs.items)} items)"
    note = "prompt caching not counted"
    typer.echo(format_estimate(costs, prices.currency if prices else "USD", title, note))
    if estimate:
        return
    budget = prices.budget_for(experiment.episode) if prices else None
    expected = [c.expected_cost for c in costs]
    if budget is None or any(c is None for c in expected):
        _fail(f"set a price for every model and a {experiment.episode} budget first.")
    if sum(c for c in expected if c is not None) > budget:
        _fail(f"the expected cost is over the {experiment.episode} budget.")
    load_dotenv(env_file, override=False)
    root = cache_dir if cache_dir is not None else shared_cache_root(Path.cwd())
    embed = None
    if any(a.examples.selection == "similar" and a.examples.n for a in experiment.arms):
        store = EmbeddingStore(root / "embeddings" / "s4.sqlite")
        embed = Embedder(openai_client(), experiment.embed_model, store)
    summaries = run_experiment(_runner(experiment, root), experiment, inputs, embed)
    for stage, summary in summaries.items():
        typer.echo(
            f"{stage}: made {summary['made']}, cached {summary['cached']}, "
            f"failed {summary['failed']}"
        )


def analyse_command(
    config: Annotated[Path, typer.Argument(help="The episode's config.yaml.")],
    prices_path: PricesOption = PRICES,
    charts: Annotated[bool, typer.Option(help="Draw the charts.")] = True,
) -> None:
    """Score every arm, compare each with the reference, and chart. No API calls."""
    experiment = Experiment.load(config)
    result = analyse(experiment, load_inputs(experiment), load_prices(prices_path))
    path = write_analysis(experiment, result, charts=charts)
    metric = result["primary_metric"]
    for name, arm in result["arms"].items():
        p = arm[metric]
        typer.echo(f"{name}: {p['count']} of {p['total']} ({p['low']:.1%} to {p['high']:.1%})")
    typer.echo(f"Wrote {path}")


def tune_command(
    config: Annotated[Path, typer.Argument(help="The tuning job's config.yaml.")],
    launch_job: Annotated[
        bool, typer.Option("--launch", help="Record a launch, after approval.")
    ] = False,
    approved_by: Annotated[str, typer.Option(help="Who approved the launch, and when.")] = "",
    retry_approved: Annotated[
        bool, typer.Option("--retry-approved", help="Allow a launch after a failed attempt.")
    ] = False,
) -> None:
    """Prepare the notebook's files, print the training token count, and record a launch."""
    tune = TuneConfig.load(config)
    try:
        record = prepare(tune) if not launch_job else load_record(tune.arm_folder)
        if launch_job:
            if record is None:
                record = prepare(tune)
            record = launch(tune.arm_folder, approved_by, retry_approved=retry_approved)
    except JobError as exc:
        _fail(str(exc))
    plan = record["plan"]
    tokens = plan["training_tokens_estimate"]
    typer.echo(f"Job {plan['job_id']}: {plan['train']['examples']} training examples")
    typer.echo(
        f"Training tokens: {tokens['per_epoch']:,} a pass x {tokens['epochs']} epochs = "
        f"{tokens['total']:,} ({tokens['tokeniser']})"
    )
    for split, info in plan["eval"].items():
        typer.echo(f"Eval {split}: {info['items']} items")
    typer.echo(f"Attempts: {len(record['attempts'])}; files in {tune.arm_folder}")


def status_command(
    job_id: Annotated[str, typer.Argument(help="The job id, episode/arm.")],
    result: Annotated[
        Path | None, typer.Option(help="The notebook's job_result.json, to record.")
    ] = None,
    root: Annotated[Path, typer.Option(help="Where to look for job records.")] = Path("episodes"),
) -> None:
    """Show a job's attempts, or record the notebook's result for the open attempt."""
    try:
        folder = find_job(root, job_id)
        record = record_result(folder, result) if result else load_record(folder)
    except JobError as exc:
        _fail(str(exc))
    assert record is not None
    for attempt in record["attempts"] or [{"attempt": 0, "status": "prepared"}]:
        typer.echo(f"Attempt {attempt['attempt']}: {attempt['status']}")


def score_command(
    predictions: Annotated[
        Path, typer.Argument(help='JSON lines: {"id", "text"} or {"id", "prediction": {...}}.')
    ],
    split: Annotated[str, typer.Option(help="dev or test.")] = "test",
    data: Annotated[Path, typer.Option(help="The task data folder.")] = DATA,
) -> None:
    """Score your own Task A predictions against the frozen labels. No API calls."""
    if split not in ("dev", "test"):
        _fail("--split must be dev or test.")
    definitions = Definitions.load(data / "routes.yaml")
    items = triage_items(data, split)  # type: ignore[arg-type]
    texts = {}
    for row in read_jsonl(predictions):
        if "prediction" in row:
            texts[row["id"]] = json.dumps(row["prediction"])
        elif row.get("text") is not None:
            texts[row["id"]] = row["text"]
    unknown = set(texts) - {i.id for i in items}
    if unknown:
        _fail(f"{len(unknown)} ids are not in the {split} split, for example {min(unknown)}.")
    result = summarise(items, score_items(items, texts, definitions), definitions)
    typer.echo(json.dumps(result, indent=2))
