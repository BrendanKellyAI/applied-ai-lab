"""Stage 4, rewrite the question: what is searched, which may differ from what was asked.

- `passthrough`: the last turn, as typed.
- `rewrite`: one model call turns the question into a search query.
- `split`: one model call returns one to three stand-alone questions; each is searched and the
  rankings are fused (search.fuse) before the filter.
- `resolve_followup`: for an item with earlier turns, one call rewrites the last turn as a
  stand-alone question; items with no earlier turn are searched as typed, with no call.

The answer prompt always shows the original question and history; only the search changes.
Rewrite calls go through the harness runner, so they are cached, retried and logged, and
their cost is reported.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_serializer

from lab.plan import PlannedCall
from lab.rag.corpus import Item
from lab.rag.prompt import conversation, instruction

MAX_PARTS = 3


class RewriteModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Literal["openai", "anthropic", "google"]
    model: str
    reasoning: str | None = None
    max_output_tokens: int = 200


class RewriteConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["passthrough", "rewrite", "split", "resolve_followup"] = "passthrough"
    # The model for the extra call. None in passthrough.
    model: RewriteModel | None = None

    @model_serializer(mode="wrap")
    def _compact(self, handler):
        # A stage left at passthrough serialises exactly as it did before the stage had options,
        # so config ids from earlier episodes do not change.
        data = handler(self)
        if self.mode == "passthrough":
            return {"mode": "passthrough"}
        return {k: v for k, v in data.items() if v is not None}


def needs_call(item: Item, config: RewriteConfig) -> bool:
    if config.mode == "passthrough":
        return False
    if config.mode == "resolve_followup":
        return bool(item.history)
    return True


# slide: S2 E6
def rewrite_prompt(item):
    """What the rewriting model reads: any earlier turns,
    then the last one. The mode's instruction is the system
    prompt."""
    parts = []
    if item.history:
        parts.append(conversation(item.history))
    parts.append(f"Question: {item.question}")
    return "\n\n".join(parts)


def system_for(mode: str) -> str:
    return instruction(f"rewrite_{mode}")


def parse_queries(text: str, item: Item, mode: str) -> tuple[str, ...]:
    """The queries in a reply: one line each for `split` (at most three), the whole reply
    otherwise. An empty or unusable reply falls back to the question as typed."""
    lines = [line.strip(" -*0123456789.").strip() for line in text.strip().splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return (item.question,)
    if mode == "split":
        return tuple(dict.fromkeys(lines[:MAX_PARTS]))
    return (" ".join(lines),)


def rewrite_calls(
    items: Sequence[Item], config: RewriteConfig, *, episode: str, condition: str
) -> list[PlannedCall]:
    from lab.rag.config import ModelSpec
    from lab.rag.waves import planned, request_for

    if config.model is None:
        raise ValueError("A rewrite mode other than passthrough needs a model")
    spec = ModelSpec(
        provider=config.model.provider,
        model=config.model.model,
        reasoning=config.model.reasoning,
        max_output_tokens=config.model.max_output_tokens,
    )
    return [
        planned(
            request_for(
                spec,
                system=system_for(config.mode),
                prompt=rewrite_prompt(item),
                episode=episode,
                stage="rewrite",
            ),
            stage="rewrite",
            item_id=item.id,
            condition=condition,
        )
        for item in items
        if needs_call(item, config)
    ]


def queries_for_all(
    items: Sequence[Item],
    config: RewriteConfig,
    runner,
    *,
    episode: str,
    condition: str,
    folder: Path,
) -> tuple[dict[str, tuple[str, ...]], list]:
    """Each item's search queries, and the run summaries of any rewrite calls."""
    from lab.rag.waves import run_wave

    queries = {item.id: (item.question,) for item in items}
    if config.mode == "passthrough":
        return queries, []
    if runner is None:
        raise RuntimeError("A rewrite mode needs a runner for its model calls")
    calls = rewrite_calls(items, config, episode=episode, condition=condition)
    results, summary = run_wave(runner, calls, folder / "raw-rewrite.jsonl")
    by_id = {item.id: item for item in items}
    for item_id, result in results.items():
        queries[item_id] = parse_queries(result.text, by_id[item_id], config.mode)
    return queries, [summary]
