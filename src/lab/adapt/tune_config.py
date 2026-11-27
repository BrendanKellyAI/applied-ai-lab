"""A tuning job's config: the open base model, the train subset, and the adapter settings.

Tuning runs in a Colab notebook (season4/colab/), not through a provider API: no provider offers
tuning this season can use (season4/PLAN.md, section 1a). `lab adapt tune` prepares the files
the notebook reads and keeps the job record; the notebook trains, predicts and writes a result
file that `lab adapt status` records. A train size of 0 prepares an eval-only job: the untuned
model, prompted the same way, which is the baseline every tuning comparison needs.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.adapt.build_tasks.config import Split
from lab.adapt.experiment import DATA, TASK_A_LEVELS, TASK_B_LEVELS

# Task A triage, Task B replies, E8's closed-book questions on the Halvard library, and E10's
# eval-only jobs: given prompt sets, run by a base model or a saved adapter, no training.
TuneTask = Literal["a", "b", "facts", "eval"]
FACTS_LEVELS = ("short",)
EVAL_LEVELS = ("none",)
LEVELS = {"a": TASK_A_LEVELS, "b": TASK_B_LEVELS, "facts": FACTS_LEVELS, "eval": EVAL_LEVELS}


class Lora(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    r: int = Field(default=16, gt=0)
    alpha: int = Field(default=32, gt=0)
    dropout: float = Field(default=0.05, ge=0, lt=1)
    target_modules: tuple[str, ...] = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )


class Training(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    epochs: int = Field(default=3, gt=0)
    learning_rate: float = Field(default=2e-4, gt=0)
    batch_size: int = Field(default=8, gt=0)
    gradient_accumulation: int = Field(default=2, gt=0)
    warmup_ratio: float = Field(default=0.03, ge=0, lt=1)
    max_length: int = Field(default=1024, gt=0)
    seed: int = 1


class TuneConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(min_length=1)
    task: TuneTask
    arm: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    base_model: str = Field(min_length=1)
    # A Hugging Face commit, so a rerun loads the same weights. "main" only for a pilot.
    base_revision: str = "main"
    train_size: int = Field(ge=0)
    # Subsets are nested: the same seed and a smaller size give a subset of a larger one (E6).
    subset_seed: int = 20261122
    instructions: str = "short"
    eval_splits: tuple[Split, ...] = ("dev", "test")
    lora: Lora = Lora()
    training: Training = Training()
    max_new_tokens: int = Field(default=160, gt=0)
    data: Path = DATA
    # E8: the generated question and answer pairs to train on (the facts task only).
    pairs: Path | None = None
    # E9: a teacher's predictions on train, used as the targets instead of the true labels
    # (Task A only). A teacher reply that is not a valid label is left out and counted.
    teacher: Path | None = None
    # E10: prompt sets to run, by name, each a JSONL of {"id", "messages"} (the eval task only).
    eval_sets: dict[str, Path] | None = None
    # E10: an earlier job's arm folder whose recorded adapter is loaded instead of training.
    adapter_from: Path | None = None
    folder: Path = Path(".")

    @model_validator(mode="after")
    def _instructions_fit_the_task(self) -> Self:
        levels = LEVELS[self.task]
        if self.instructions not in levels:
            raise ValueError(f"instructions must be one of {levels}")
        if (self.task == "facts") != (self.pairs is not None):
            raise ValueError("pairs are set for the facts task, and only for it")
        if self.teacher is not None and self.task != "a":
            raise ValueError("teacher labels are for Task A only")
        if (self.task == "eval") != (self.eval_sets is not None):
            raise ValueError("eval_sets are set for the eval task, and only for it")
        if self.task == "eval" and (self.train_size or self.eval_splits):
            raise ValueError("an eval job has no training rows and no dev or test splits")
        if self.adapter_from is not None and self.task != "eval":
            raise ValueError("adapter_from is for the eval task only")
        return self

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.folder / path

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    @property
    def data_folder(self) -> Path:
        return self.data if self.data.is_absolute() else self.folder / self.data

    @property
    def pairs_path(self) -> Path | None:
        if self.pairs is None:
            return None
        return self.pairs if self.pairs.is_absolute() else self.folder / self.pairs

    @property
    def teacher_path(self) -> Path | None:
        if self.teacher is None:
            return None
        return self.teacher if self.teacher.is_absolute() else self.folder / self.teacher

    @property
    def arm_folder(self) -> Path:
        return self.folder / "results" / self.arm

    @property
    def job_id(self) -> str:
        return f"{self.episode}/{self.arm}"
