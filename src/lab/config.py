"""Pydantic models for experiment configuration files."""

from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from lab.providers.base import ProviderName, ReasoningLevel

CellValue = str | int | float | bool


def _undo_yaml_booleans(value: Any) -> Any:
    """YAML 1.1 reads bare `off` and `on` as booleans. Restore the words."""
    if value is False:
        return "off"
    if value is True:
        return "on"
    return value


class ModeSettings(BaseModel):
    """Settings for one mode of one model. Reasoning and temperature must be stated explicitly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reasoning: ReasoningLevel | None
    temperature: float | None
    max_output_tokens: int = Field(gt=0)
    show_thinking: bool = False

    @field_validator("reasoning", mode="before")
    @classmethod
    def _restore_reasoning(cls, value: Any) -> Any:
        return _undo_yaml_booleans(value)


class ModelConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: ProviderName
    model: str = Field(min_length=1)
    label: str | None = None
    modes: dict[str, ModeSettings] = Field(min_length=1)

    @field_validator("modes", mode="before")
    @classmethod
    def _restore_mode_names(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {_undo_yaml_booleans(name): settings for name, settings in value.items()}
        return value

    @property
    def display_label(self) -> str:
        return self.label or self.model


class ProviderLimits(BaseModel):
    """Conservative defaults for entry-level API tiers. Adjust locally."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrency: int = Field(default=2, ge=1, le=32)
    requests_per_minute: int = Field(default=30, ge=1)


class StratifiedPilot(BaseModel):
    """Sample a fraction of the grid, with at least one call per model and stratum."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: Literal["stratified"]
    fraction: float = Field(default=0.05, gt=0, le=1)
    strata: list[str] = Field(default_factory=list)


class FilterPilot(BaseModel):
    """Select every call whose cell matches all key and value pairs of any include rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: Literal["filter"]
    include: list[dict[str, CellValue]] = Field(min_length=1)

    @field_validator("include")
    @classmethod
    def _rules_not_empty(cls, rules: list[dict[str, CellValue]]) -> list[dict[str, CellValue]]:
        if any(not rule for rule in rules):
            raise ValueError("each include rule needs at least one key")
        return rules


PilotConfig = Annotated[StratifiedPilot | FilterPilot, Field(discriminator="strategy")]


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str = ""
    seed: int
    models: list[ModelConfig] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    limits: dict[ProviderName, ProviderLimits] = Field(default_factory=dict)
    pilot: PilotConfig = StratifiedPilot(strategy="stratified")
    call_order: Literal["planned", "shuffled"] = "planned"

    @model_validator(mode="after")
    def _labels_unique(self) -> "ExperimentConfig":
        labels = [model.display_label for model in self.models]
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            raise ValueError(f"model labels must be unique; repeated: {', '.join(duplicates)}")
        return self

    @property
    def providers(self) -> frozenset[str]:
        return frozenset(model.provider for model in self.models)

    def limits_for(self, provider: str) -> ProviderLimits:
        return self.limits.get(provider, ProviderLimits())


class ConfigError(ValueError):
    """A configuration file is missing, unreadable, or invalid."""


def load_config(path: Path) -> ExperimentConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    try:
        return ExperimentConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"{path} is not a valid experiment config:\n{exc}") from exc
