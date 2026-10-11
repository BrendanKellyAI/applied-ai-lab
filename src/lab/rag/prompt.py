"""Stage 8, build the prompt: which passages, in what order, under which instruction.

Instruction texts live in prompts/ beside this file. A change to one changes every request
hash, so a cached answer can never be reused under a different prompt.
"""

from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from lab.rag.chunk import Chunk
from lab.rag.corpus import Turn

PROMPTS = Path(__file__).with_name("prompts")


class PromptConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    k: int = Field(default=5, gt=0)
    order: Literal["rank", "reverse", "ends"] = "rank"
    instruction: Literal["plain"] = "plain"


class BuiltPrompt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    system: str
    prompt: str
    chunk_ids: tuple[str, ...]


@cache
def instruction(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8").strip()


def order_passages[T](ranked: Sequence[T], order: str) -> list[T]:
    """`rank` keeps the ranking; `reverse` puts the best last; `ends` puts the best first and
    the second best last, working inwards, so the weakest sit in the middle (S1 E7)."""
    if order == "rank":
        return list(ranked)
    if order == "reverse":
        return list(reversed(ranked))
    front = list(ranked[0::2])
    back = list(ranked[1::2])
    return front + back[::-1]


# slide: S2 E2
def build_prompt(question, history, passages):
    """Numbered passages, then any earlier turns,
    then the question."""
    parts = ["Passages:"]
    for n, chunk in enumerate(passages, start=1):
        parts.append(f"[P{n}] {chunk.title}\n{chunk.text.strip()}")
    if history:
        turns = [f"{t.role.title()}: {t.content}" for t in history]
        parts.append("Conversation so far:\n" + "\n".join(turns))
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


def render(
    question: str, history: Sequence[Turn], ranked: Sequence[Chunk], config: PromptConfig
) -> BuiltPrompt:
    passages = order_passages(list(ranked[: config.k]), config.order)
    return BuiltPrompt(
        system=instruction(config.instruction),
        prompt=build_prompt(question, history, passages),
        chunk_ids=tuple(chunk.chunk_id for chunk in passages),
    )
