"""The Task A build's cost before any call: input tokens counted from the real prompts, outputs
at an expected size and at the hard ceiling of each output limit.

The generator's message is about 1.4 tokens a word at the middle of its length band, plus 15
for the JSON wrapper. The labeller's reply is about 35 tokens. Retries are allowed for as a
share of generation calls, and every generated message is labelled once.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.config import TaskBuildConfig
from lab.adapt.build_tasks.passages import NOT_FOUND
from lab.adapt.build_tasks.prompts import labeller_prompt, labeller_system
from lab.adapt.build_tasks.prompts_b import (
    CHECK_SYSTEM,
    QA_SYSTEM,
    REWRITE_SYSTEM,
    facts_prompt,
    qa_prompt,
    rewrite_prompt,
    support_prompt,
)
from lab.adapt.build_tasks.seeds import Seed
from lab.adapt.build_tasks.task_a import generation_tasks
from lab.adapt.definitions import Definitions
from lab.prices import PricesFile
from lab.rag.config import ModelSpec
from lab.rag.estimate import chat_tokens

RETRY_SHARE = 0.3
TOKENS_PER_WORD = 1.4
WRAPPER_TOKENS = 15
LABEL_TOKENS = 35


class StageCost(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: str
    model: str
    calls: int
    input_tokens: int
    expected_output: int
    ceiling_output: int
    expected_cost: float | None
    ceiling_cost: float | None


def message_tokens(seed: Seed) -> int:
    low, high = seed.length
    return round((low + high) / 2 * TOKENS_PER_WORD) + WRAPPER_TOKENS


def _cost(prices: PricesFile | None, spec: ModelSpec, inputs: int, outputs: int) -> float | None:
    price = prices.price_for(spec.provider, spec.model) if prices else None
    if price is None or price.input is None or price.output is None:
        return None
    return (inputs * price.input + outputs * price.output) / 1_000_000


def _stage(
    stage: str, spec: ModelSpec, calls: int, inputs: int, expected: int, prices: PricesFile | None
) -> StageCost:
    ceiling = calls * spec.max_output_tokens
    return StageCost(
        stage=stage,
        model=spec.model,
        calls=calls,
        input_tokens=inputs,
        expected_output=expected,
        ceiling_output=ceiling,
        expected_cost=_cost(prices, spec, inputs, expected),
        ceiling_cost=_cost(prices, spec, inputs, ceiling),
    )


def estimate_task_a(
    config: TaskBuildConfig,
    definitions: Definitions,
    seeds: Sequence[Seed],
    prices: PricesFile | None,
) -> list[StageCost]:
    tasks = generation_tasks(seeds, definitions)
    gen_calls = round(len(tasks) * (1 + RETRY_SHARE))
    gen_inputs = round(
        sum(chat_tokens(t.prompt) + chat_tokens(t.system or "") for t in tasks) * (1 + RETRY_SHARE)
    )
    gen_out = round(sum(message_tokens(s) for s in seeds) * (1 + RETRY_SHARE))
    system = chat_tokens(labeller_system(definitions))
    label_inputs = sum(system + chat_tokens(labeller_prompt("")) + message_tokens(s) for s in seeds)
    return [
        _stage("generate", config.generator, gen_calls, gen_inputs, gen_out, prices),
        _stage(
            "label", config.labeller, len(seeds), label_inputs, len(seeds) * LABEL_TOKENS, prices
        ),
    ]


def format_estimate(costs: Sequence[StageCost], currency: str, title: str) -> str:
    lines = [
        f"{title}, allowing {RETRY_SHARE:.0%} for generation retries:",
        "",
        f"{'stage':<10}{'model':<24}{'calls':>7}{'input':>12}{'expected out':>14}"
        f"{'ceiling out':>13}{'expected':>10}{'ceiling':>10}",
    ]
    for c in costs:
        lines.append(
            f"{c.stage:<10}{c.model:<24}{c.calls:>7,}{c.input_tokens:>12,}"
            f"{c.expected_output:>14,}{c.ceiling_output:>13,}"
            f"{_money(c.expected_cost):>10}{_money(c.ceiling_cost):>10}"
        )
    lines += [
        "",
        f"Total, expected: {_total([c.expected_cost for c in costs], currency)}",
        "Total, ceiling (every call at its output limit): "
        f"{_total([c.ceiling_cost for c in costs], currency)}",
    ]
    return "\n".join(lines)


def _money(value: float | None) -> str:
    return "unknown" if value is None else f"{value:,.2f}"


def _total(values: list[float | None], currency: str) -> str:
    if any(v is None for v in values):
        return "unknown: a price is missing from prices.local.yaml"
    return f"{sum(v for v in values if v is not None):,.2f} {currency}"


QA_TOKENS = 130
SUPPORT_TOKENS = 20
REPLY_TOKENS = 170
FACTS_TOKENS = 25


def estimate_task_b(
    config: TaskBuildConfig, seeds: Sequence, style_guide: str, prices: PricesFile | None
) -> list[StageCost]:
    """Four stages; every seed is assumed to reach every stage, an upper bound on calls."""

    retry = 1 + RETRY_SHARE
    answer = "x " * 40
    reply = "x " * 90
    qa_in = sum(chat_tokens(QA_SYSTEM) + chat_tokens(qa_prompt(s)) for s in seeds)
    support_in = sum(
        chat_tokens(CHECK_SYSTEM) + chat_tokens(support_prompt(s, answer, answer)) for s in seeds
    )
    rewrite_in = sum(
        chat_tokens(REWRITE_SYSTEM) + chat_tokens(rewrite_prompt(s, answer, answer, style_guide))
        for s in seeds
    )
    answerable = [s for s in seeds if s.kind != NOT_FOUND]
    facts_in = len(answerable) * (
        chat_tokens(CHECK_SYSTEM) + chat_tokens(facts_prompt(answer, answer, reply))
    )
    n = len(seeds)
    gen, check = config.generator, config.labeller
    return [
        _stage(
            "qa", gen, round(n * retry), round(qa_in * retry), round(n * retry * QA_TOKENS), prices
        ),
        _stage("support", check, n, support_in, n * SUPPORT_TOKENS, prices),
        _stage(
            "rewrite",
            gen,
            round(n * retry),
            round(rewrite_in * retry),
            round(n * retry * REPLY_TOKENS),
            prices,
        ),
        _stage("facts", check, len(answerable), facts_in, len(answerable) * FACTS_TOKENS, prices),
    ]
