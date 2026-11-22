"""The task data build settings (datasets/halvard-tasks/config.yaml)."""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.rag.config import ModelSpec

Split = Literal["train", "dev", "test"]
SPLITS: tuple[Split, ...] = ("train", "dev", "test")


class Personas(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tone: tuple[str, ...] = Field(min_length=1)
    habit: tuple[str, ...] = Field(min_length=1)
    channel: tuple[str, ...] = Field(min_length=1)
    name: tuple[str, ...] = Field(min_length=1)


class TaskAConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    splits: dict[Split, int]
    overgenerate: float = Field(ge=0, lt=1)
    pilot_seeds: int = Field(gt=0)
    near_duplicate_threshold: float = Field(gt=0, le=1)
    route_weights: dict[str, float]
    length_bands: tuple[tuple[int, int], ...] = Field(min_length=1)
    unsold_products: tuple[str, ...] = Field(min_length=1)
    personas: Personas

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> Self:
        if abs(sum(self.route_weights.values()) - 1) > 1e-9:
            raise ValueError("route_weights must add up to 1")
        return self


class TaskBuildConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_version: str
    seed: int
    generator: ModelSpec
    labeller: ModelSpec
    max_attempts: int = Field(gt=0)
    task_a: TaskAConfig

    @model_validator(mode="after")
    def _labeller_is_another_provider(self) -> Self:
        if self.labeller.provider == self.generator.provider:
            raise ValueError("the labeller must come from a different provider to the generator")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
