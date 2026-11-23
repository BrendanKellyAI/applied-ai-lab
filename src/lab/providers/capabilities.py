"""Per-model setting support, checked before any call is made."""

from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lab.providers.base import GenerationRequest, ReasoningLevel, UnsupportedSettingError

DEFAULT_PATH = Path(__file__).with_name("capabilities.yaml")

# How a model can be held to an output format: not at all, valid JSON only, or a JSON schema.
StructuredOutput = Literal["none", "json_mode", "schema"]
TuningMethod = Literal["supervised", "preference"]


class ModelCapabilities(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reasoning: tuple[ReasoningLevel, ...] = Field(default_factory=tuple)
    temperature: bool
    max_output_tokens: int | None = Field(default=None, gt=0)
    # Season 4. fine_tunable means tuning through the provider's own API. structured_output is
    # None until it has been verified for the model.
    fine_tunable: bool = False
    tuning_method: tuple[TuningMethod, ...] = Field(default_factory=tuple)
    structured_output: StructuredOutput | None = None

    @field_validator("reasoning", mode="before")
    @classmethod
    def _restore_off(cls, value: Any) -> Any:
        if isinstance(value, list):
            return ["off" if level is False else level for level in value]
        return value

    @model_validator(mode="after")
    def _tuning_needs_a_tunable_model(self) -> Self:
        if self.tuning_method and not self.fine_tunable:
            raise ValueError("tuning_method is set but fine_tunable is false")
        return self


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

    def lookup(self, provider: str, model: str) -> ModelCapabilities:
        """Return a model's entry, or raise UnsupportedSettingError if it is not listed."""
        caps = self._entries.get(provider, {}).get(model)
        if caps is None:
            raise UnsupportedSettingError(
                f"{provider} model '{model}' is not in capabilities.yaml. Check its settings in "
                "the provider documentation and add it before running."
            )
        return caps

    def check(self, request: GenerationRequest) -> ModelCapabilities:
        """Raise UnsupportedSettingError unless the request can be sent exactly as specified."""
        caps = self.lookup(request.provider, request.model)
        where = f"{request.provider} model '{request.model}'"
        if not request.stream:
            raise UnsupportedSettingError("Adapters always stream, to measure time to first token")
        _check_reasoning(request, caps, where)
        if request.temperature is not None and not caps.temperature:
            raise UnsupportedSettingError(
                f"{where} does not accept a temperature; set temperature: null"
            )
        _check_output_format(request, caps, where)
        if caps.max_output_tokens and request.max_output_tokens > caps.max_output_tokens:
            raise UnsupportedSettingError(
                f"{where} allows at most {caps.max_output_tokens} output tokens"
            )
        return caps


def _check_output_format(request: GenerationRequest, caps: ModelCapabilities, where: str) -> None:
    """JSON mode needs JSON mode or schema support; a schema needs schema support."""
    wanted = request.output_format
    if wanted is None:
        return
    offered = caps.structured_output or "none"
    allowed = {"json_mode": ("json_mode", "schema"), "schema": ("schema",)}[wanted.kind]
    if offered not in allowed:
        raise UnsupportedSettingError(
            f"{where} does not offer {wanted.kind} output (capabilities.yaml says {offered})"
        )


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
