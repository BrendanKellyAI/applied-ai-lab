"""The retrieval log: one line per item per condition, recording what each stage did.

Chunk text is not stored; it is rebuilt from the corpus and the chunker settings. E14's
diagnosis is computed from this log alone.
"""

import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lab.rag.corpus import Span
from lab.rag.judge import Verdict

# How many ranked chunks each stage records.
LOG_DEPTH = 20


class RankedChunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    score: float


class RemovedChunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    reason: str


class SpanTrace(BaseModel):
    """Where one labelled span went: its rank at each stage, and whether it was cut."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str
    span: Span
    cut: bool
    searched: int | None
    filtered: int | None
    reranked: int | None
    in_prompt: bool


class ModelCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    model_returned: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None
    finish_reason: str


class ItemLog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    type: str
    asker: str
    answerable: bool
    condition: str
    config_id: str
    queries: tuple[str, ...]
    searched: tuple[RankedChunk, ...]
    removed: tuple[RemovedChunk, ...]
    ranked: tuple[RankedChunk, ...]
    prompt_chunks: tuple[str, ...]
    spans: tuple[SpanTrace, ...]
    evidence_rank: int | None
    distractor_above: bool
    leaks: tuple[str, ...]
    answer: ModelCall | None = None
    judge: ModelCall | None = None
    verdict: Verdict | None = None
    judge_error: str | None = None
    code_check: bool | None = None
    lost_at: str | None = None


def write_log(path: Path, logs: Sequence[ItemLog]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [log.model_dump_json() for log in logs]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def read_log(path: Path) -> list[ItemLog]:
    return [
        ItemLog.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
