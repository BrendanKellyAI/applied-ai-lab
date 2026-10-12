"""`lab rag judge-check`: check the judge against hand marks, and optionally a second model."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from dotenv import load_dotenv

from lab.cache import ResponseCache, shared_cache_root
from lab.config import ConfigError
from lab.prices import load_prices
from lab.providers.registry import available_providers
from lab.rag.chunk import count_tokens
from lab.rag.corpus import load_library
from lab.rag.judge import judge_instructions
from lab.rag.judge_check import (
    MARKS,
    REPORT,
    CheckConfig,
    agreement,
    chunk_lookup,
    draw_sample,
    format_report,
    judge_prompt_hash,
    load_check_config,
    read_marks,
    read_record,
    write_record,
    write_sheet,
)
from lab.rag.judge_second import (
    FOLDER,
    format_two_marker,
    pick_for_hand,
    read_second,
    run_second,
    second_prompts,
    two_marker_report,
)
from lab.rag.log import read_log
from lab.runner import Runner

judge_app = typer.Typer(help="Check the judge against hand marks (S2 E3).", no_args_is_help=True)
CheckArg = Annotated[Path, typer.Argument(help="The judge check's judge_check.yaml.")]


@judge_app.command("draw")
def judge_draw(config: CheckArg) -> None:
    """Draw the sample and write the blind marking sheet. No key, no call."""
    check = _check_config(config)
    library = load_library(check.library)
    logs = read_log(check.run / "log.jsonl")
    summary = _summary(check)
    sample = draw_sample(logs, size=check.size, per_type=check.per_type, seed=check.seed)
    written = _sheet(check, sample, logs, library, summary)
    write_record(
        check.out,
        {
            "episode": summary["episode"],
            "condition": summary["condition"],
            "config_id": summary["config_id"],
            "seed": check.seed,
            "judge_prompt": judge_prompt_hash(),
            "items": sample,
        },
    )
    typer.echo(f"Drew {len(sample)} items. Mark them in {written[1]}, reading {written[0]}.")


@judge_app.command("second")
def judge_second(
    config: CheckArg,
    estimate: Annotated[bool, typer.Option("--estimate", help="Count tokens; no call.")] = False,
    env_file: Annotated[Path, typer.Option(help="File of API keys.")] = Path(".env"),
    prices_path: Annotated[Path, typer.Option(help="Prices file.")] = Path("prices.local.yaml"),
) -> None:
    """Have the second model mark the drawn sample, then write the hand sheet for the items
    where it disagrees most with the judge. Paid: run with --estimate first."""
    check = _check_config(config)
    if check.second_judge is None or check.hand is None:
        _fail("judge_check.yaml sets no second_judge and hand count")
    spec = check.second_judge
    record = _record(check)
    library = load_library(check.library)
    logs = read_log(check.run / "log.jsonl")
    summary = _summary(check)
    chunks = chunk_lookup(library, summary["pipeline"])
    prompts = second_prompts(record["items"], logs, library, chunks)
    if estimate:
        typer.echo(_estimate(prompts, spec, prices_path))
        return
    load_dotenv(env_file, override=False)
    available = available_providers([spec.provider])
    if available.missing_keys:
        _fail(f"no API key for {spec.provider}")
    runner = Runner(
        providers=dict(available.providers),
        cache=ResponseCache(shared_cache_root(Path.cwd())),
        limits=check.limits,
    )
    folder = check.out / FOLDER
    second, _ = run_second(runner, prompts, spec, folder)
    first = {g.item_id: g.verdict for g in logs if g.item_id in second}
    hand = pick_for_hand(record["items"], first, second, check.hand)
    written = _sheet(check, hand, logs, library, summary)
    write_record(check.out, {**record, "second_judge": spec.model_dump(), "hand": hand})
    errors = sum(1 for v in second.values() if v is None)
    typer.echo(
        f"Second model marked {len(second) - errors} of {len(second)}. "
        f"Mark the {len(hand)} items in {written[1]}, reading {written[0]}."
    )


@judge_app.command("report")
def judge_report(config: CheckArg) -> None:
    """Compare the hand marks with the judge (and the second model) and write agreement.json."""
    check = _check_config(config)
    record = _record(check)
    logs = read_log(check.run / "log.jsonl")
    if record["judge_prompt"] != judge_prompt_hash():
        _fail("the judge's instructions changed since the sample was drawn")
    if {g.config_id for g in logs} != {record["config_id"]}:
        _fail("the run's log is not the run the sample was drawn from")
    marked = record.get("hand", record["items"])
    try:
        marks = read_marks(check.out / MARKS, marked)
    except ValueError as exc:
        _fail(str(exc))
    if "hand" in record:
        report = two_marker_report(record["items"], logs, read_second(check.out / FOLDER), marks)
        text = format_two_marker(report)
    else:
        report = agreement(marks, logs)
        text = format_report(report)
    (check.out / REPORT).write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    typer.echo(text)


def _estimate(prompts: dict[str, str], spec: Any, prices_path: Path) -> str:
    system = count_tokens(judge_instructions())
    tokens_in = sum(system + count_tokens(p) for p in prompts.values())
    tokens_out = len(prompts) * spec.max_output_tokens
    lines = [
        f"{len(prompts)} calls to {spec.model} at reasoning {spec.reasoning}",
        f"  input about {tokens_in:,} tokens (cl100k count; the model's own count differs)",
        f"  output at most {tokens_out:,} tokens "
        f"({spec.max_output_tokens:,} each, thinking included)",
    ]
    prices = load_prices(prices_path)
    price = prices.price_for(spec.provider, spec.model) if prices else None
    if price is not None and price.is_complete:
        worst = (tokens_in * price.input + tokens_out * price.output) / 1_000_000
        lines.append(f"  cost at most {worst:,.2f} {prices.currency}, before any cache hits")
    return "\n".join(lines)


def _sheet(check: CheckConfig, ids, logs, library, summary) -> list[Path]:
    try:
        return write_sheet(
            check.out, ids, logs, library, chunk_lookup(library, summary["pipeline"])
        )
    except FileExistsError as exc:
        _fail(str(exc))


def _summary(check: CheckConfig) -> dict[str, Any]:
    return json.loads((check.run / "summary.json").read_text(encoding="utf-8"))


def _record(check: CheckConfig) -> dict[str, Any]:
    try:
        return read_record(check.out)
    except FileNotFoundError:
        _fail("no sample drawn yet: run `lab rag judge-check draw` first")


def _check_config(path: Path) -> CheckConfig:
    try:
        return load_check_config(path)
    except ConfigError as exc:
        _fail(str(exc))


def _fail(message: str):
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)
