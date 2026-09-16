"""Per-model setting support, checked before any call is made."""

from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from lab.providers.base import GenerationRequest, ReasoningLevel, UnsupportedSettingError

DEFAULT_PATH = Path(__file__).with_name("capabilities.yaml")


class ModelCapabilities(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reasoning: tuple[ReasoningLevel, ...] = Field(default_factory=tuple)
    temperature: bool
    max_output_tokens: int | None = Field(default=None, gt=0)

    @field_validator("reasoning", mode="before")
    @classmethod
    def _restore_off(cls, value: Any) -> Any:
        if isinstance(value, list):
            return ["off" if level is False else level for level in value]
        return value


class CapabilityTable:
    def __init__(self, entries: Mapping[str, Mapping[str, ModelCapabilities]]) -> None:
        self._entries = entries

    @classmethod
    def from_yaml(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(
            {
                provider: {
                    model: ModelCapabilities.model_validate(spec) for model, spec in models.items()
                }
                for provider, models in raw.items()
            }
        )

    def check(self, request: GenerationRequest) -> ModelCapabilities:
        """Raise UnsupportedSettingError unless the request can be sent exactly as specified."""
        caps = self._entries.get(request.provider, {}).get(request.model)
        where = f"{request.provider} model '{request.model}'"
        if caps is None:
            raise UnsupportedSettingError(
                f"{where} is not in capabilities.yaml. Check its settings in the provider "
                "documentation and add it before running."
            )
        if not request.stream:
            raise UnsupportedSettingError("Adapters always stream, to measure time to first token")
        _check_reasoning(request, caps, where)
        if request.temperature is not None and not caps.temperature:
            raise UnsupportedSettingError(
                f"{where} does not accept a temperature; set temperature: null"
            )
        if caps.max_output_tokens and request.max_output_tokens > caps.max_output_tokens:
            raise UnsupportedSettingError(
                f"{where} allows at most {caps.max_output_tokens} output tokens"
            )
        return caps


def _check_reasoning(request: GenerationRequest, caps: ModelCapabilities, where: str) -> None:
    if request.reasoning is None and caps.reasoning:
        raise UnsupportedSettingError(
            f"{where} has a reasoning setting; state it explicitly, because leaving it out "
            f"uses the provider default. Allowed: {', '.join(caps.reasoning)}"
        )
    if request.reasoning is not None and request.reasoning not in caps.reasoning:
        allowed = ", ".join(caps.reasoning) or "none"
        raise UnsupportedSettingError(
            f"{where} does not support reasoning '{request.reasoning}'. Allowed: {allowed}"
        )
    if request.show_thinking and request.reasoning in (None, "off"):
        raise UnsupportedSettingError(f"{where}: show_thinking needs reasoning to be on")


@cache
def default_capabilities() -> CapabilityTable:
    return CapabilityTable.from_yaml(DEFAULT_PATH)
