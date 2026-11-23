"""The frozen Task A and Task B items, read from datasets/halvard-tasks."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.config import Split
from lab.adapt.definitions import Label
from lab.adapt.style import Source

FOLDERS = {"a": "task-a", "b": "task-b"}


class TriageItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    message: str
    label: Label
    kind: str


class ReplyItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    question: str
    answer: str
    kind: str
    source: dict
    target_reply: str

    @property
    def source_ref(self) -> Source:
        return Source(**self.source)


def _rows(data: Path, task: str, split: Split) -> list[dict]:
    path = data / FOLDERS[task] / f"{split}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def triage_items(data: Path, split: Split, limit: int | None = None) -> list[TriageItem]:
    return [TriageItem.model_validate(r) for r in _rows(data, "a", split)][:limit]


def reply_items(data: Path, split: Split, limit: int | None = None) -> list[ReplyItem]:
    return [ReplyItem.model_validate(r) for r in _rows(data, "b", split)][:limit]
