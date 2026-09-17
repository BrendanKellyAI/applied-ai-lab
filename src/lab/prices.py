"""The owner's local prices and budget ceilings, read from the gitignored prices.local.yaml."""

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from lab.config import ConfigError


class ModelPrice(BaseModel):
    """US dollars (or the file's currency) per 1 million tokens. Blank means unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input: float | None = Field(default=None, ge=0)
    cached_input: float | None = Field(default=None, ge=0)
    output: float | None = Field(default=None, ge=0)

    @property
    def is_complete(self) -> bool:
        return self.input is not None and self.output is not None


class PricesFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    currency: str = "USD"
    prices_checked: date | None = None
    prices: dict[str, dict[str, ModelPrice]] = Field(default_factory=dict)
    budgets: dict[str, float | None] = Field(default_factory=dict)

    @field_validator("budgets")
    @classmethod
    def _budgets_not_negative(cls, budgets: dict[str, float | None]) -> dict[str, float | None]:
        negative = [name for name, value in budgets.items() if value is not None and value < 0]
        if negative:
            raise ValueError(f"budgets must not be negative: {', '.join(negative)}")
        return budgets

    def price_for(self, provider: str, model: str) -> ModelPrice | None:
        return self.prices.get(provider, {}).get(model)

    def budget_for(self, experiment: str) -> float | None:
        return self.budgets.get(experiment)


def load_prices(path: Path) -> PricesFile | None:
    """Load prices, or return None when the file does not exist."""
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return PricesFile.model_validate(raw)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    except ValidationError as exc:
        raise ConfigError(f"{path} is not a valid prices file:\n{exc}") from exc
