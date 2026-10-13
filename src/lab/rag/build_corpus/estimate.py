"""The build's cost before any call: input tokens exact where the prompt is known, outputs at
an expected size and at the hard ceiling of the output limit.

Expected output sizes come from v1 S2 E3, where gpt-6-astra at its default reasoning averaged
about 96 reasoning tokens a call: a section at its token ceiling plus 300 for reasoning, a
question at 60 plus 100. Retries are allowed for as a share of calls.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from lab.prices import PricesFile
from lab.rag.build_corpus.build import Blueprint, Scope
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.generate import Task
from lab.rag.build_corpus.questions import question_tasks
from lab.rag.build_corpus.sections import bounds, section_task
from lab.rag.build_corpus.v1 import V1, quote_tasks
from lab.rag.build_corpus.verify import CHUNKER, DEPTH
from lab.rag.config import ModelSpec
from lab.rag.estimate import chat_tokens

RETRY_SHARE = 0.25
REASONING = {"section": 300, "question": 100, "quote": 100, "check": 0}
VISIBLE = {"question": 60, "quote": 60, "check": 80}
# Restricted plans are checked once, as their public item.
CHECKED_PLANS = {"restricted", "absent_detail", "absent_topic", "deleted"}


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


def _cost(prices: PricesFile | None, spec: ModelSpec, inputs: int, outputs: int) -> float | None:
    price = prices.price_for(spec.provider, spec.model) if prices else None
    if price is None or price.input is None or price.output is None:
        return None
    return (inputs * price.input + outputs * price.output) / 1_000_000


def _stage(
    stage: str,
    tasks: Sequence[Task],
    spec: ModelSpec,
    expected_each: int,
    prices: PricesFile | None,
) -> StageCost:
    calls = round(len(tasks) * (1 + RETRY_SHARE))
    inputs = round(
        sum(chat_tokens(t.prompt) + chat_tokens(t.system or "") for t in tasks) * (1 + RETRY_SHARE)
    )
    expected = calls * expected_each
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


def estimate_build(
    config: CorpusConfig,
    bp: Blueprint,
    scope: Scope,
    v1: V1,
    prices: PricesFile | None,
) -> list[StageCost]:
    facts = bp.plan.by_id()
    sections = [section_task(config, d, s) for d, s in scope.sections]
    section_each = max(bounds(config, s)[1] for _, s in scope.sections) + REASONING["section"]
    questions = question_tasks(config, scope.items, facts)
    followups = [Task(id=t.id, prompt=t.prompt) for t in questions if t.id.endswith("/first")]
    quotes = [t for t in quote_tasks(config, v1) if t.id in scope.v1_ids]
    checked = sum(1 for i in scope.items if i.type in CHECKED_PLANS)
    passage_tokens = 2 * DEPTH * CHUNKER.size
    checks = [Task(id=str(n), prompt="x " * passage_tokens) for n in range(checked)]
    gen = config.generation
    return [
        _stage("section", sections, gen, section_each, prices),
        _stage(
            "question",
            questions + followups,
            gen,
            VISIBLE["question"] + REASONING["question"],
            prices,
        ),
        _stage("quote", quotes, gen, VISIBLE["quote"] + REASONING["quote"], prices),
        _stage("check", checks, config.checker, VISIBLE["check"], prices),
    ]


def format_build_estimate(costs: Sequence[StageCost], currency: str, pilot: bool) -> str:
    lines = [
        f"Corpus build estimate ({'pilot' if pilot else 'full build'}), "
        f"allowing {RETRY_SHARE:.0%} for retries:",
        "",
        f"{'stage':<10}{'model':<20}{'calls':>7}{'input':>12}{'expected out':>14}"
        f"{'ceiling out':>13}{'expected':>12}{'ceiling':>12}",
    ]
    for c in costs:
        lines.append(
            f"{c.stage:<10}{c.model:<20}{c.calls:>7,}{c.input_tokens:>12,}"
            f"{c.expected_output:>14,}{c.ceiling_output:>13,}"
            f"{_money(c.expected_cost):>12}{_money(c.ceiling_cost):>12}"
        )
    expected = [c.expected_cost for c in costs]
    ceiling = [c.ceiling_cost for c in costs]
    lines.append("")
    lines.append(f"Total, expected: {_total(expected, currency)}")
    lines.append(f"Total, ceiling (every call at its output limit): {_total(ceiling, currency)}")
    lines.append("Embeddings for the unanswerable check: about 300,000 tokens, under 0.01.")
    return "\n".join(lines)


def _money(value: float | None) -> str:
    return "unknown" if value is None else f"{value:,.2f}"


def _total(values: list[float | None], currency: str) -> str:
    if any(v is None for v in values):
        return "unknown: a price is missing from prices.local.yaml"
    return f"{sum(v for v in values if v is not None):,.2f} {currency}"
