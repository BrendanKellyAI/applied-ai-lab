"""Token and cost estimates for an episode, with no API key.

Embeddings: the texts not yet in the cache. Prompts: exact when every vector is cached, so the
real retrieval can run offline; otherwise an upper bound built from the k longest chunks.
Outputs are counted at their configured limits, so the estimate errs high. Answer calls whose
exact request is already in the response cache cost nothing and are left out; judge calls
are always counted, because their prompts depend on answers not yet made.
"""

from collections.abc import Sequence

import tiktoken
from pydantic import BaseModel, ConfigDict

from lab.cache import ResponseCache
from lab.prices import PricesFile
from lab.rag.chunk import Chunk, chunk_library, count_tokens
from lab.rag.config import ModelSpec, ResolvedCondition
from lab.rag.corpus import Item, Library
from lab.rag.embed import Embedder
from lab.rag.index import embed_text
from lab.rag.judge import judge_instructions, judge_prompt
from lab.rag.prompt import build_prompt, instruction
from lab.rag.retrieve import build, queries_for, retrieve
from lab.rag.waves import request_for

# Counts chat tokens. Exact for OpenAI's current models; an approximation for Claude.
CHAT_ENCODING = tiktoken.get_encoding("o200k_base")


class StageEstimate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    calls: int
    cached: int
    input_tokens: int
    output_tokens: int
    cost: float | None


class ConditionEstimate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    measure: str
    exact_prompts: bool
    embedding_texts: int
    embedding_tokens: int
    embedding_cost: float | None
    answer: StageEstimate | None
    judge: StageEstimate | None

    @property
    def cost(self) -> float | None:
        parts = [self.embedding_cost]
        parts += [s.cost for s in (self.answer, self.judge) if s is not None]
        return None if any(p is None for p in parts) else sum(p for p in parts if p is not None)


def chat_tokens(text: str) -> int:
    return len(CHAT_ENCODING.encode(text, disallowed_special=()))


def estimate_condition(
    library: Library,
    items: Sequence[Item],
    condition: ResolvedCondition,
    embedder: Embedder,
    *,
    episode: str,
    cache: ResponseCache | None = None,
    prices: PricesFile | None = None,
) -> ConditionEstimate:
    pipeline = condition.pipeline
    chunks = chunk_library(library.documents, pipeline.chunk)
    headings = getattr(pipeline.chunk, "embed_headings", False)
    texts = [embed_text(c, headings) for c in chunks]
    texts += [q for item in items for q in queries_for(item)]
    missing = embedder.missing(texts)
    embedding_tokens = sum(count_tokens(t) for t in missing)
    exact = not missing
    answer = judge = None
    if condition.measure == "full":
        prompts = _exact_prompts(library, items, condition, embedder) if exact else None
        prompts = prompts or _bounded_prompts(items, chunks, pipeline.prompt.k)
        system = instruction(pipeline.prompt.instruction)
        answer = _stage(
            [(system, p) for p in prompts.values()], pipeline.answer, episode, cache, prices
        )
        judge = _judge_bound(items, prompts, pipeline.answer, pipeline.judge, prices)
    return ConditionEstimate(
        name=condition.name,
        measure=condition.measure,
        exact_prompts=exact,
        embedding_texts=len(missing),
        embedding_tokens=embedding_tokens,
        embedding_cost=_price(prices, "openai", pipeline.embed.model, embedding_tokens, 0),
        answer=answer,
        judge=judge,
    )


def _exact_prompts(
    library: Library, items: Sequence[Item], condition: ResolvedCondition, embedder: Embedder
) -> dict[str, str]:
    index = build(library, condition.pipeline, embedder)
    retrievals = retrieve(items, index, condition.pipeline, embedder)
    return {item_id: r.prompt.prompt for item_id, r in retrievals.items()}


def _bounded_prompts(items: Sequence[Item], chunks: Sequence[Chunk], k: int) -> dict[str, str]:
    """Each item's prompt filled with the k longest chunks: no real prompt can be longer."""
    longest = sorted(chunks, key=lambda c: -len(c.text))[:k]
    return {item.id: build_prompt(item.question, item.history, longest) for item in items}


def _judge_bound(
    items: Sequence[Item],
    prompts: dict[str, str],
    answer: ModelSpec,
    judge: ModelSpec,
    prices: PricesFile | None,
) -> StageEstimate:
    """The judge reads the answer prompt's passages and question again, its own instructions,
    the reference answer, and an answer at most as long as the answer model's limit."""
    fixed = chat_tokens(judge_instructions()) + answer.max_output_tokens
    input_tokens = sum(
        fixed + chat_tokens(prompts[item.id]) + chat_tokens(judge_prompt(item, (), ""))
        for item in items
    )
    output_tokens = judge.max_output_tokens * len(items)
    return StageEstimate(
        calls=len(items),
        cached=0,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=_price(prices, judge.provider, judge.model, input_tokens, output_tokens),
    )


def _stage(
    prompts: Sequence[tuple[str, str]],
    spec: ModelSpec,
    episode: str,
    cache: ResponseCache | None,
    prices: PricesFile | None,
) -> StageEstimate:
    uncached = [
        (system, prompt)
        for system, prompt in prompts
        if cache is None
        or cache.get(
            request_for(spec, system=system, prompt=prompt, episode=episode, stage="answer")
        )
        is None
    ]
    input_tokens = sum(chat_tokens(s) + chat_tokens(p) for s, p in uncached)
    output_tokens = spec.max_output_tokens * len(uncached)
    return StageEstimate(
        calls=len(prompts),
        cached=len(prompts) - len(uncached),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=_price(prices, spec.provider, spec.model, input_tokens, output_tokens),
    )


def _price(
    prices: PricesFile | None, provider: str, model: str, input_tokens: int, output_tokens: int
) -> float | None:
    price = prices.price_for(provider, model) if prices else None
    if price is None or price.input is None or (output_tokens and price.output is None):
        return None
    return (input_tokens * price.input + output_tokens * (price.output or 0)) / 1_000_000


def format_estimate(
    episode: str, estimates: Sequence[ConditionEstimate], budget: float | None, currency: str
) -> str:
    lines = [f"Estimate for {episode} (outputs counted at their limits, so this errs high)", ""]
    for e in estimates:
        lines.append(
            f"{e.name} [{e.measure}]: prompts {'exact' if e.exact_prompts else 'upper bound'}"
        )
        lines.append(
            f"  embeddings: {e.embedding_texts:,} texts, {e.embedding_tokens:,} tokens, "
            f"{_money(e.embedding_cost, currency)}"
        )
        for label, stage in (("answer", e.answer), ("judge", e.judge)):
            if stage is not None:
                lines.append(
                    f"  {label}: {stage.calls - stage.cached:,} calls to make "
                    f"({stage.cached:,} cached), input {stage.input_tokens:,}, "
                    f"output up to {stage.output_tokens:,}, {_money(stage.cost, currency)}"
                )
    costs = [e.cost for e in estimates]
    total = None if any(c is None for c in costs) else sum(c for c in costs if c is not None)
    lines += ["", f"Total: {_money(total, currency)}"]
    if budget is not None:
        lines.append(f"Budget: {budget:,.2f} {currency}")
    return "\n".join(lines)


def _money(value: float | None, currency: str) -> str:
    return "price unknown" if value is None else f"{value:,.2f} {currency}"
