"""Planned calls: one fully specified request per cell of an experiment grid."""

import hashlib
import json
from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, field_validator

from lab.config import CellValue, ModelConfig
from lab.providers.base import GenerationRequest

RESERVED_KEYS = frozenset({"model", "provider", "mode"})


class PlanError(ValueError):
    """A plan cannot be run as specified."""


class PlannedCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str
    model_label: str
    mode: str
    cell: dict[str, CellValue]
    request: GenerationRequest

    @field_validator("cell")
    @classmethod
    def _no_reserved_keys(cls, cell: dict[str, CellValue]) -> dict[str, CellValue]:
        clashes = RESERVED_KEYS & cell.keys()
        if clashes:
            raise ValueError(f"cell keys {sorted(clashes)} are reserved")
        return cell

    def descriptor(self) -> dict[str, CellValue]:
        """The cell plus model, provider, and mode, for pilot selection and analysis."""
        return {
            "model": self.model_label,
            "provider": self.request.provider,
            "mode": self.mode,
            **self.cell,
        }


def make_call_id(*, model_label: str, mode: str, cell: dict[str, CellValue]) -> str:
    """Deterministic identifier for a call, stable across runs and machines."""
    payload = {"model": model_label, "mode": mode, "cell": cell}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def ensure_unique_call_ids(calls: Sequence[PlannedCall]) -> None:
    duplicates = [
        call_id for call_id, count in Counter(c.call_id for c in calls).items() if count > 1
    ]
    if duplicates:
        raise PlanError(f"Duplicate call identifiers in plan: {', '.join(sorted(duplicates))}")


def build_request(
    model: ModelConfig,
    mode: str,
    *,
    prompt: str,
    system: str | None = None,
    metadata: dict[str, str] | None = None,
) -> GenerationRequest:
    """A request for one model in one of its configured modes."""
    if mode not in model.modes:
        raise PlanError(f"Model '{model.display_label}' has no mode '{mode}'")
    settings = model.modes[mode]
    return GenerationRequest(
        provider=model.provider,
        model=model.model,
        system=system,
        prompt=prompt,
        max_output_tokens=settings.max_output_tokens,
        temperature=settings.temperature,
        reasoning=settings.reasoning,
        show_thinking=settings.show_thinking,
        metadata={**(metadata or {}), "mode": mode},
    )
