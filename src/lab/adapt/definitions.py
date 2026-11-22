"""Task A definitions (datasets/halvard-tasks/routes.yaml) and the label every item carries."""

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Route(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    team: str
    policy: str | None
    definition: str


class Safety(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: str
    share: float = Field(gt=0, lt=1)


class HardCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    share: float = Field(gt=0, lt=1)
    note: str


class Definitions(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    routes: dict[str, Route]
    precedence: tuple[str, ...]
    products: tuple[str, ...]
    product_rule: str
    faults: dict[str, str]
    fault_rule: str
    safety: Safety
    hard_cases: dict[str, HardCase]

    @model_validator(mode="after")
    def _hard_cases_leave_room(self) -> Self:
        if sum(case.share for case in self.hard_cases.values()) >= 1:
            raise ValueError("hard case shares must add up to less than 1")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


class Label(BaseModel):
    """What a triage answer must contain. Every field is checked by code."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    route: str
    safety: bool
    product: str | None
    fault: str | None

    def check_against(self, definitions: Definitions) -> None:
        if self.route not in definitions.routes:
            raise ValueError(f"unknown route {self.route!r}")
        if self.product is not None and self.product not in definitions.products:
            raise ValueError(f"unknown product {self.product!r}")
        if self.fault is not None and self.fault not in definitions.faults:
            raise ValueError(f"unknown fault {self.fault!r}")

    def disagreements(self, other: "Label") -> tuple[str, ...]:
        """The fields on which two labels differ, in field order."""
        return tuple(
            name for name in Label.model_fields if getattr(self, name) != getattr(other, name)
        )
