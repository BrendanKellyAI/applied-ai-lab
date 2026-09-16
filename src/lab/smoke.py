"""`lab smoke`: one tiny call per configured model and mode, to check keys and adapters."""

from lab.config import ExperimentConfig
from lab.plan import PlannedCall, build_request, make_call_id
from lab.raw_log import RunRecord

DEFAULT_PROMPT = "Reply with the single word: ready"

# Expected only when thinking is requested and shown. A model may still skip thinking on a
# trivial prompt, so these are flagged for review rather than assumed to be bugs.
_THINKING_FIELDS = {"reasoning_tokens", "time_to_first_thinking_ms"}
# Providers may leave this empty when no prompt cache was involved.
_OPTIONAL_FIELDS = {"cached_input_tokens"}


def plan_smoke(config: ExperimentConfig) -> list[PlannedCall]:
    prompt = str(config.parameters.get("prompt", DEFAULT_PROMPT))
    return [
        PlannedCall(
            call_id=make_call_id(model_label=model.display_label, mode=mode, cell={}),
            model_label=model.display_label,
            mode=mode,
            cell={},
            request=build_request(
                model, mode, prompt=prompt, metadata={"experiment": config.experiment}
            ),
        )
        for model in config.models
        for mode in model.modes
    ]


def _expected(name: str, expects_thinking: bool) -> bool:
    if name in _OPTIONAL_FIELDS:
        return False
    return expects_thinking or name not in _THINKING_FIELDS


def reasoning_warnings(record: RunRecord, reasoning: str | None) -> list[str]:
    """Flag a model that reports reasoning tokens although reasoning was set to off."""
    if record.result is None or reasoning != "off":
        return []
    tokens = record.result.reasoning_tokens
    if tokens:
        return [f"reasoning is off but {tokens} reasoning tokens were reported"]
    return []


def describe(record: RunRecord, expects_thinking: bool, reasoning: str | None = None) -> list[str]:
    """Human-readable lines for one smoke result, flagging any field that came back empty."""
    heading = f"{record.model_label} [{record.mode}]"
    if record.result is None:
        return [f"{heading}: FAILED after {record.attempts} attempt(s): {record.error}"]
    result = record.result
    fields = result.model_dump(exclude={"request_hash", "error"})
    lines = [f"{heading}: {record.source}"]
    for name, value in fields.items():
        if value is None or value == "":
            note = "NOT REPORTED" if _expected(name, expects_thinking) else "not reported"
            lines.append(f"  {name}: {note}")
        else:
            shown = value if not isinstance(value, float) else f"{value:,.0f}"
            lines.append(f"  {name}: {str(shown)[:80]}")
    lines.extend(f"  WARNING: {warning}" for warning in reasoning_warnings(record, reasoning))
    return lines


def missing_fields(record: RunRecord, expects_thinking: bool) -> list[str]:
    """Fields that should have been populated but were not."""
    if record.result is None:
        return ["result"]
    return [
        name
        for name, value in record.result.model_dump(exclude={"error"}).items()
        if (value is None or value == "") and _expected(name, expects_thinking)
    ]
