"""`lab estimate`: tokens and cost for the pilot and full run, to protect the owner's budget.

Published results never include prices. This module exists only for budgeting.
"""

import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Any

from lab.cache import ResponseCache
from lab.config import ExperimentConfig
from lab.pilot import select_calls
from lab.plan import PlannedCall
from lab.prices import PricesFile
from lab.providers.base import request_hash
from lab.raw_log import RunRecord, latest_successful

TokenCounter = Callable[[str], int]

# Input tokens are counted with o200k_base. Other providers' tokenisers can count up to about
# 30% more for the same text (Anthropic documents this for its current models).
TOKENISER_VARIATION = 1.3
# Output estimates switch from the output limit to real usage once this many results exist.
MIN_PILOT_SAMPLES = 3
# Verified 17 September 2026: OpenAI, Anthropic, and Google batch APIs all cost 50% less, with
# results within 24 hours. Batch mode is not built yet.
BATCH_DISCOUNT = 0.5


class BudgetError(ValueError):
    """The estimated cost exceeds the budget, or cannot be checked against it."""


@cache
def default_token_counter() -> TokenCounter:
    """o200k_base token counter. tiktoken downloads the encoding once on first use."""
    import tiktoken

    encoding = tiktoken.get_encoding("o200k_base")
    return lambda text: len(encoding.encode(text, disallowed_special=()))


@dataclass(frozen=True)
class TokenRange:
    low: int
    high: int


@dataclass(frozen=True)
class CostRange:
    low: float
    high: float

    def __add__(self, other: "CostRange") -> "CostRange":
        return CostRange(self.low + other.low, self.high + other.high)


@dataclass(frozen=True)
class GroupEstimate:
    provider: str
    model: str
    model_label: str
    mode: str
    calls: int
    done_calls: int
    input_tokens: TokenRange
    output_tokens: TokenRange
    output_basis: str
    cost: CostRange | None

    @property
    def uncached_calls(self) -> int:
        return self.calls - self.done_calls


@dataclass(frozen=True)
class RunEstimate:
    name: str
    groups: tuple[GroupEstimate, ...]

    @property
    def calls(self) -> int:
        return sum(group.calls for group in self.groups)

    @property
    def done_calls(self) -> int:
        return sum(group.done_calls for group in self.groups)

    @property
    def uncached_calls(self) -> int:
        return self.calls - self.done_calls

    @property
    def missing_prices(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    f"{group.provider} {group.model}"
                    for group in self.groups
                    if group.uncached_calls and group.cost is None
                }
            )
        )

    @property
    def cost(self) -> CostRange | None:
        if self.missing_prices:
            return None
        return sum((g.cost for g in self.groups if g.cost is not None), CostRange(0.0, 0.0))


@dataclass(frozen=True)
class EstimateReport:
    experiment: str
    prices: PricesFile | None
    pilot: RunEstimate
    full: RunEstimate
    budget: float | None
    batch_note: str


def _output_samples(records: Sequence[RunRecord]) -> dict[tuple[str, str], list[int]]:
    samples: dict[tuple[str, str], list[int]] = defaultdict(list)
    for record in latest_successful(list(records)).values():
        if record.result is not None:
            samples[(record.model_label, record.mode)].append(record.result.output_tokens)
    return samples


def _percentile_90(values: Sequence[int]) -> int:
    ordered = sorted(values)
    return ordered[math.ceil(0.9 * len(ordered)) - 1]


def _estimate_group(
    group: Sequence[PlannedCall],
    *,
    done_ids: set[str],
    samples: Sequence[int],
    prices: PricesFile | None,
    count_tokens: TokenCounter,
) -> GroupEstimate:
    first = group[0]
    to_make = [call for call in group if call.call_id not in done_ids]
    input_low = sum(
        count_tokens(call.request.system or "") + count_tokens(call.request.prompt)
        for call in to_make
    )
    if len(samples) >= MIN_PILOT_SAMPLES:
        output = TokenRange(
            round(statistics.fmean(samples) * len(to_make)), _percentile_90(samples) * len(to_make)
        )
        basis = f"pilot usage (n={len(samples)})"
    else:
        limit = sum(call.request.max_output_tokens for call in to_make)
        output = TokenRange(limit, limit)
        basis = "output limit (upper bound)"
    input_tokens = TokenRange(input_low, math.ceil(input_low * TOKENISER_VARIATION))
    price = prices.price_for(first.request.provider, first.request.model) if prices else None
    cost = None
    if price is not None and price.is_complete:
        cost = CostRange(
            (input_tokens.low * price.input + output.low * price.output) / 1_000_000,
            (input_tokens.high * price.input + output.high * price.output) / 1_000_000,
        )
    elif not to_make:
        cost = CostRange(0.0, 0.0)
    return GroupEstimate(
        provider=first.request.provider,
        model=first.request.model,
        model_label=first.model_label,
        mode=first.mode,
        calls=len(group),
        done_calls=len(group) - len(to_make),
        input_tokens=input_tokens,
        output_tokens=output,
        output_basis=basis,
        cost=cost,
    )


def estimate_run(
    name: str,
    calls: Sequence[PlannedCall],
    *,
    cache: ResponseCache,
    prior_records: Sequence[RunRecord],
    prices: PricesFile | None,
    count_tokens: TokenCounter,
) -> RunEstimate:
    """Estimate the calls still to make. Cached input discounts are not applied."""
    completed = latest_successful(list(prior_records))
    done_ids = {
        call.call_id
        for call in calls
        if (
            call.call_id in completed
            and completed[call.call_id].request_hash == request_hash(call.request)
        )
        or cache.get(call.request) is not None
    }
    samples = _output_samples(prior_records)
    groups: dict[tuple[str, str, str], list[PlannedCall]] = defaultdict(list)
    for call in calls:
        groups[(call.request.provider, call.model_label, call.mode)].append(call)
    return RunEstimate(
        name=name,
        groups=tuple(
            _estimate_group(
                groups[key],
                done_ids=done_ids,
                samples=samples.get((key[1], key[2]), []),
                prices=prices,
                count_tokens=count_tokens,
            )
            for key in sorted(groups)
        ),
    )


def _batch_note(config: ExperimentConfig, full: RunEstimate) -> str:
    if config.measures_latency:
        return (
            "Batch: this experiment measures latency, so batch APIs (50% cheaper, results "
            "within 24 hours) are not suitable."
        )
    saving = ""
    if full.cost is not None:
        saving = (
            f" For the full run that is about {_money(full.cost.low * BATCH_DISCOUNT)} to "
            f"{_money(full.cost.high * BATCH_DISCOUNT)} instead of "
            f"{_money(full.cost.low)} to {_money(full.cost.high)}."
        )
    return (
        "Batch: this experiment does not measure latency, so batch APIs from all three "
        "providers could cut the cost by 50%, with results within 24 hours." + saving + " "
        "Batch mode is not built yet."
    )


def build_report(
    config: ExperimentConfig,
    calls: Sequence[PlannedCall],
    **options: Any,
) -> EstimateReport:
    """Estimate the pilot and the full run separately. Options are passed to estimate_run."""
    pilot = estimate_run("Pilot", select_calls(calls, config, pilot=True), **options)
    full = estimate_run("Full run", select_calls(calls, config), **options)
    prices: PricesFile | None = options.get("prices")
    return EstimateReport(
        experiment=config.experiment,
        prices=prices,
        pilot=pilot,
        full=full,
        budget=prices.budget_for(config.experiment) if prices else None,
        batch_note=_batch_note(config, full),
    )


def check_budget(run: RunEstimate, budget: float | None) -> None:
    """Refuse a run whose estimated cost, at the high end, exceeds the budget."""
    if budget is None or run.uncached_calls == 0:
        return
    if run.cost is None:
        raise BudgetError(
            f"Cannot check the budget of {_money(budget)}: no price for "
            f"{', '.join(run.missing_prices)}. Add them to prices.local.yaml."
        )
    if run.cost.high > budget:
        raise BudgetError(
            f"{run.name} estimate of up to {_money(run.cost.high)} exceeds the budget of "
            f"{_money(budget)}. Run the pilot first, or raise the budget in prices.local.yaml."
        )


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _tokens(tokens: TokenRange) -> str:
    if tokens.low == tokens.high:
        return f"{tokens.low:,}"
    return f"{tokens.low:,} to {tokens.high:,}"


def _cost(cost: CostRange | None) -> str:
    if cost is None:
        return "no price"
    low, high = _money(cost.low), _money(cost.high)
    return low if low == high else f"{low} to {high}"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _format_run(run: RunEstimate) -> list[str]:
    header = (
        "Provider",
        "Model",
        "Mode",
        "To make",
        "Input tokens",
        "Output tokens",
        "Basis",
        "Cost",
    )
    rows = [
        (
            group.provider,
            group.model_label,
            group.mode,
            f"{group.uncached_calls:,}",
            _tokens(group.input_tokens),
            _tokens(group.output_tokens),
            group.output_basis,
            _cost(group.cost),
        )
        for group in run.groups
    ]
    rows.append(("Total", "", "", f"{run.uncached_calls:,}", "", "", "", _cost(run.cost)))
    widths = [max(len(row[i]) for row in (header, *rows)) for i in range(len(header))]
    lines = [
        f"{run.name}: {_plural(run.calls, 'call')}, {run.done_calls:,} already cached or "
        f"complete, {run.uncached_calls:,} to make"
    ]
    lines.extend(
        "  "
        + "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in (header, *rows)
    )
    return lines


def _budget_line(report: EstimateReport) -> str:
    if report.prices is None:
        return "Budget: not checked, because there is no prices file."
    if report.budget is None:
        return f"Budget: none set for {report.experiment} in prices.local.yaml."
    try:
        check_budget(report.full, report.budget)
    except BudgetError as exc:
        return f"Budget: {_money(report.budget)}. {exc}"
    return f"Budget: {_money(report.budget)}. The full run estimate is within budget."


def format_report(report: EstimateReport) -> str:
    if report.prices is None:
        price_line = "Costs not shown: no prices file found. Tokens only."
    else:
        checked = report.prices.prices_checked or "an unknown date"
        price_line = f"Prices checked {checked}, in {report.prices.currency} per 1 million tokens."
    lines = [
        f"Estimate for {report.experiment}",
        price_line,
        "Input tokens are counted with o200k_base; the high end allows 30% more for other "
        "tokenisers. Cached input discounts are not applied.",
        "",
        *_format_run(report.pilot),
        "",
        *_format_run(report.full),
        "",
        _budget_line(report),
        report.batch_note,
    ]
    return "\n".join(lines)
