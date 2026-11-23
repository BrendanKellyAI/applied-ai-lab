"""A tuning job's config: the open base model, the train subset, and the adapter settings.

Tuning runs in a Colab notebook (season4/colab/), not through a provider API: no provider offers
tuning this season can use (season4/PLAN.md, section 1a). `lab adapt tune` prepares the files
the notebook reads and keeps the job record; the notebook trains, predicts and writes a result
file that `lab adapt status` records. A train size of 0 prepares an eval-only job: the untuned
model, prompted the same way, which is the baseline every tuning comparison needs.
"""

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.adapt.build_tasks.config import Split
from lab.adapt.experiment import DATA, TASK_A_LEVELS, TASK_B_LEVELS, Task


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
    task: Task
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
    folder: Path = Path(".")

    @model_validator(mode="after")
    def _instructions_fit_the_task(self) -> Self:
        levels = TASK_A_LEVELS if self.task == "a" else TASK_B_LEVELS
        if self.instructions not in levels:
            raise ValueError(f"instructions must be one of {levels}")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    @property
    def data_folder(self) -> Path:
        return self.data if self.data.is_absolute() else self.folder / self.data

    @property
    def arm_folder(self) -> Path:
        return self.folder / "results" / self.arm

    @property
    def job_id(self) -> str:
        return f"{self.episode}/{self.arm}"
