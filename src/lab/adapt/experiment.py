"""An episode's config: which task, which split, and the arms it compares.

An arm is either prompted (run through the API by `lab adapt run`) or external: its
predictions come from a file another tool wrote, such as the Colab notebook for a tuned model.
Both kinds are scored and compared the same way. Paths in the file are relative to the file.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.adapt.build_tasks.config import Split
from lab.adapt.output import OutputKind
from lab.config import ProviderLimits
from lab.rag.config import ModelSpec

Task = Literal["a", "b"]
# Instruction levels, from the least the model is told to the most (E2 and E7).
TASK_A_LEVELS = ("short", "one_line", "definitions", "policy", "unsure")
TASK_B_LEVELS = ("short", "one_line", "style_guide")
DATA = Path("datasets/halvard-tasks")


class Examples(BaseModel):
    """Worked examples from train, shown before the message (E3)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    n: int = Field(default=0, ge=0)
    # random: the same examples for every item; similar: the nearest train messages to each item.
    selection: Literal["random", "similar"] = "random"
    seed: int = 0
    # Set to show the same examples in a different order.
    shuffle_seed: int | None = None


class Arm(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    instructions: str | None = None
    examples: Examples = Examples()
    output: OutputKind = "text"
    # Overrides the experiment's answer model for this arm.
    model: ModelSpec | None = None
    # An external arm: a predictions file, one {"id", "text"} object per line.
    predictions: Path | None = None
    note: str = ""

    @model_validator(mode="after")
    def _prompted_or_external(self) -> Self:
        if (self.predictions is None) == (self.instructions is None):
            raise ValueError(f"arm {self.name}: give instructions or predictions, not both")
        return self

    @property
    def external(self) -> bool:
        return self.predictions is not None


class Experiment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(min_length=1)
    task: Task
    split: Split = "test"
    # Score only the first n items of the split: for pilots.
    limit: int | None = Field(default=None, gt=0)
    data: Path = DATA
    answer: ModelSpec
    # Task B: the judge of facts kept and of style.
    judge: ModelSpec | None = None
    embed_model: str = "text-embedding-3-small"
    arms: tuple[Arm, ...] = Field(min_length=1)
    # The arm every other arm is compared with.
    reference: str
    limits: dict[str, ProviderLimits] = Field(default_factory=dict)
    folder: Path = Path(".")

    @model_validator(mode="after")
    def _arms_fit_the_task(self) -> Self:
        names = [arm.name for arm in self.arms]
        if len(set(names)) != len(names):
            raise ValueError("arm names must be unique")
        if self.reference not in names:
            raise ValueError(f"reference arm {self.reference!r} is not an arm")
        levels = TASK_A_LEVELS if self.task == "a" else TASK_B_LEVELS
        for arm in self.arms:
            if arm.instructions is not None and arm.instructions not in levels:
                raise ValueError(f"arm {arm.name}: instructions must be one of {levels}")
            if self.task == "b" and arm.output != "text":
                raise ValueError(f"arm {arm.name}: Task B replies are plain text")
        if self.task == "b" and self.judge is None:
            raise ValueError("Task B needs a judge")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    def path(self, relative: Path) -> Path:
        return relative if relative.is_absolute() else self.folder / relative

    @property
    def data_folder(self) -> Path:
        return self.path(self.data)

    @property
    def results(self) -> Path:
        return self.folder / "results"

    def arm(self, name: str) -> Arm:
        return next(arm for arm in self.arms if arm.name == name)

    def model_for(self, arm: Arm) -> ModelSpec:
        return arm.model or self.answer
