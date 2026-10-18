"""The scoring rule: gates, criteria with anchors, weights, the autonomy table and sourcing.

The rule lives in a YAML file (`season3/case/rule.yaml` for Halvard Home). Readers scoring their
own use cases can copy it and change the weights; everything else in the package reads the rule
rather than hard-coding it.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from lab.config import ConfigError

AUTONOMY_ORDER = ("assist", "automate", "act")
ErrorCost = Literal["low", "high", "regulatory"]
Caught = Literal["reviewer", "downstream", "nobody"]
Autonomy = Literal["assist", "automate", "act"]


class Gate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    label: str
    episode: int
    question: str
    fail_means: str


class Criterion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    label: str
    episode: int
    question: str | None = None
    anchors: dict[int, str]

    @model_validator(mode="after")
    def _anchors_1_3_5(self) -> "Criterion":
        if sorted(self.anchors) != [1, 3, 5]:
            raise ValueError(f"criterion {self.id} needs anchors for 1, 3 and 5")
        return self


class AutonomyTable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: int
    levels: dict[Autonomy, str]
    error_costs: dict[ErrorCost, str]
    caught_by: dict[Caught, str]
    table: dict[ErrorCost, dict[Caught, Literal["assist", "automate"]]]
    act_requires_reversible: bool = True

    def allowed(self, error_cost: ErrorCost, caught: Caught, reversible: bool) -> Autonomy:
        """The highest autonomy the table allows. Act needs automate and a reversible error."""
        level = self.table[error_cost][caught]
        if level == "automate" and (reversible or not self.act_requires_reversible):
            return "act"
        return level


class Sourcing(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: int
    application: dict[str, str]
    model_access: dict[str, str]


class SensitivitySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    equal: dict[str, float]
    ceo: dict[str, float]
    regulator: dict[str, float]
    halve_each: bool = True
    double_each: bool = True


class Rule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: int
    gates: tuple[Gate, ...] = Field(min_length=1)
    criteria: tuple[Criterion, ...] = Field(min_length=1)
    weights: dict[str, float]
    autonomy: AutonomyTable
    sourcing: Sourcing
    sensitivity: SensitivitySpec
    stop_criteria: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _weights_match(self) -> "Rule":
        ids = {c.id for c in self.criteria}
        for name, weights in [("weights", self.weights)] + [
            (f"sensitivity.{k}", getattr(self.sensitivity, k)) for k in ("equal", "ceo", "regulator")
        ]:
            if set(weights) != ids:
                raise ValueError(f"{name} must give a weight for each criterion: {sorted(ids)}")
            if any(w < 0 for w in weights.values()) or sum(weights.values()) <= 0:
                raise ValueError(f"{name} must be non-negative and not all zero")
        if abs(sum(self.weights.values()) - 1) > 1e-9:
            raise ValueError("weights must sum to 1")
        return self

    @property
    def criterion_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    @property
    def gate_ids(self) -> tuple[str, ...]:
        return tuple(g.id for g in self.gates)


def load_rule(path: Path) -> Rule:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Rule file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    try:
        return Rule.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"{path} is not a valid rule:\n{exc}") from exc
