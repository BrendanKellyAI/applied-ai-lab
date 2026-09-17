"""`lab smoke`: one tiny call per configured model and mode, to check keys and adapters."""

from lab.config import ExperimentConfig
from lab.plan import PlannedCall, build_request, make_call_id
from lab.providers.base import GenerationRequest, GenerationResult
from lab.raw_log import RunRecord

DEFAULT_PROMPT = "Reply with the single word: ready"
# Modes that show thinking need a prompt worth thinking about; on a trivial prompt, models with
# adaptive reasoning skip thinking and the thinking fields cannot be checked.
DEFAULT_THINKING_PROMPT = (
    "How many times does the letter r appear in the words strawberry, raspberry, and "
    "cranberry combined? Reply with the number only."
)

# Providers may leave this empty when no prompt cache was involved.
_OPTIONAL_FIELDS = {"cached_input_tokens"}
_NOT_CHECKED = {"request_hash", "error"}


def plan_smoke(config: ExperimentConfig) -> list[PlannedCall]:
    prompt = str(config.parameters.get("prompt", DEFAULT_PROMPT))
    thinking_prompt = str(config.parameters.get("thinking_prompt", DEFAULT_THINKING_PROMPT))
    return [
        PlannedCall(
            call_id=make_call_id(model_label=model.display_label, mode=mode, cell={}),
            model_label=model.display_label,
            mode=mode,
            cell={},
            request=build_request(
                model,
                mode,
                prompt=thinking_prompt if settings.show_thinking else prompt,
                metadata={"experiment": config.experiment},
            ),
        )
        for model in config.models
        for mode, settings in model.modes.items()
    ]


def _did_not_think(result: GenerationResult) -> bool:
    return result.reasoning_tokens == 0


def _absent_field_note(name: str, request: GenerationRequest, result: GenerationResult) -> str:
    """Why an empty field is acceptable, or NOT REPORTED when it should have been populated."""
    if name in _OPTIONAL_FIELDS:
        return "not reported"
    if name == "reasoning_tokens" and not request.show_thinking:
        return "not reported"
    if name == "time_to_first_thinking_ms":
        if not request.show_thinking:
            return "not reported"
        if _did_not_think(result):
            return "not applicable, the model did not think"
    return "NOT REPORTED"


def _warnings(request: GenerationRequest, result: GenerationResult) -> list[str]:
    warnings = []
    if request.reasoning == "off" and result.reasoning_tokens:
        warnings.append(
            f"reasoning is off but {result.reasoning_tokens} reasoning tokens were reported"
        )
    if request.show_thinking and _did_not_think(result):
        warnings.append(
            "thinking was requested but the model did not think, so the thinking fields are "
            "unverified; use a prompt that needs reasoning"
        )
    return warnings


def _absent_fields(result: GenerationResult) -> list[str]:
    return [
        name
        for name, value in result.model_dump(exclude=_NOT_CHECKED).items()
        if value is None or value == ""
    ]


def problems(record: RunRecord, request: GenerationRequest) -> list[str]:
    """Everything that should stop a smoke test passing for this call."""
    if record.result is None:
        return [f"call failed: {record.error}"]
    result = record.result
    missing = [
        f"{name} not reported"
        for name in _absent_fields(result)
        if _absent_field_note(name, request, result) == "NOT REPORTED"
    ]
    return missing + _warnings(request, result)


def describe(record: RunRecord, request: GenerationRequest) -> list[str]:
    """Human-readable lines for one smoke result, noting every empty field and warning."""
    heading = f"{record.model_label} [{record.mode}]"
    if record.result is None:
        return [f"{heading}: FAILED after {record.attempts} attempt(s): {record.error}"]
    result = record.result
    lines = [f"{heading}: {record.source}"]
    for name, value in result.model_dump(exclude=_NOT_CHECKED).items():
        if value is None or value == "":
            lines.append(f"  {name}: {_absent_field_note(name, request, result)}")
        else:
            shown = f"{value:,.0f}" if isinstance(value, float) else value
            lines.append(f"  {name}: {str(shown)[:80]}")
    lines.extend(f"  WARNING: {warning}" for warning in _warnings(request, result))
    return lines
