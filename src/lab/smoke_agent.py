"""Season 5 smoke checks: a tool call, parallel tool calls, a tool result round trip and an image.

Added to `lab smoke` when a config sets `parameters.agent_checks: true`. Each check runs for
every model whose capabilities.yaml entry claims the feature, in the model's first mode, so a
claim in that file is confirmed by a real call before anything is built on it.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from lab.config import ExperimentConfig, ModelConfig
from lab.plan import PlannedCall, build_request, make_call_id
from lab.providers.base import GenerationRequest, GenerationResult
from lab.providers.capabilities import default_capabilities
from lab.providers.messages import ImagePart, Message, ToolCall, ToolSpec, tool_result, user

LOOKUP_ORDER = ToolSpec(
    name="lookup_order",
    description=(
        "Look up one Halvard Home order by its order number, such as H-100001. Returns the "
        "product, delivery date and price. Call it once for each order number."
    ),
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order number"}},
        "required": ["order_id"],
        "additionalProperties": False,
    },
    strict=True,
)
TOOL_PROMPT = "Look up order H-100001 for me."
PARALLEL_PROMPT = "Look up orders H-100001 and H-100002 for me, both at once."
ROUND_TRIP_RESULT = '{"order_id": "H-100001", "product": "Brio kettle", "delivered": "2026-03-14"}'
ROUND_TRIP_EXPECT = "Brio kettle"
IMAGE_PROMPT = "Read the serial number on this rating plate. Reply with the serial number only."
# Invented; the plate is drawn below in a style that resembles no real maker's label.
IMAGE_SERIAL = "KW61-48213"
SMOKE_IMAGE = Path("season5") / "smoke" / "rating-plate.png"

# Keys in a planned call's metadata, which is not part of the request hash.
CHECK = "agent_check"
EXPECT = "expect"


def render_rating_plate(path: Path = SMOKE_IMAGE) -> Path:
    """Draw the smoke test's invented rating plate, if it is not already on disk."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (640, 320), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 631, 311), outline="black", width=4)
    font = ImageFont.load_default(size=30)
    lines = ["HALVARD HOME (invented)", "Model HV-KW-610", f"Serial {IMAGE_SERIAL}", "230 V  50 Hz"]
    for row, text in enumerate(lines):
        draw.text((32, 32 + row * 66), text, fill="black", font=font)
    image.save(path, format="PNG")
    return path


def plan_agent_checks(
    config: ExperimentConfig, image_path: Path = SMOKE_IMAGE
) -> list[PlannedCall]:
    if not config.parameters.get("agent_checks"):
        return []
    table = default_capabilities()
    calls: list[PlannedCall] = []
    for model in config.models:
        caps = table.lookup(model.provider, model.model)
        mode = next(iter(model.modes))
        if caps.tool_calling in ("basic", "parallel"):
            calls.extend(
                _tool_checks(config, model, mode, parallel=caps.tool_calling == "parallel")
            )
        if caps.image_input:
            calls.append(_image_check(config, model, mode, render_rating_plate(image_path)))
    return calls


def _planned(model: ModelConfig, mode: str, check: str, request: GenerationRequest) -> PlannedCall:
    return PlannedCall(
        call_id=make_call_id(model_label=model.display_label, mode=f"{mode}-{check}", cell={}),
        model_label=model.display_label,
        mode=f"{mode} {check}",
        cell={},
        request=request,
    )


def _request(
    config: ExperimentConfig,
    model: ModelConfig,
    mode: str,
    check: str,
    expect: str,
    **fields: object,
) -> GenerationRequest:
    base = build_request(
        model,
        mode,
        prompt="unused",
        metadata={"experiment": config.experiment, CHECK: check, EXPECT: expect},
    )
    return GenerationRequest.model_validate({**base.model_dump(), "prompt": "", **fields})


def _tool_checks(
    config: ExperimentConfig, model: ModelConfig, mode: str, *, parallel: bool
) -> list[PlannedCall]:
    tools = (LOOKUP_ORDER,)
    call = ToolCall(
        call_id="call_smoke_1", name="lookup_order", arguments_json='{"order_id": "H-100001"}'
    )
    history = (
        user(TOOL_PROMPT),
        Message(role="assistant", tool_calls=(call,)),
        tool_result(call, ROUND_TRIP_RESULT),
    )
    checks = [
        (
            "tool_call",
            "lookup_order",
            {"messages": (user(TOOL_PROMPT),), "tool_choice": "required"},
        ),
        ("round_trip", ROUND_TRIP_EXPECT, {"messages": history, "tool_choice": "none"}),
    ]
    if parallel:
        checks.append(
            ("parallel", "2", {"messages": (user(PARALLEL_PROMPT),), "tool_choice": "required"})
        )
    return [
        _planned(
            model, mode, name, _request(config, model, mode, name, expect, tools=tools, **fields)
        )
        for name, expect, fields in checks
    ]


def _image_check(
    config: ExperimentConfig, model: ModelConfig, mode: str, path: Path
) -> PlannedCall:
    image = ImagePart.from_file(path, detail="high")
    request = _request(
        config, model, mode, "image", IMAGE_SERIAL, messages=(user(IMAGE_PROMPT, (image,)),)
    )
    return _planned(model, mode, "image", request)


def agent_problems(request: GenerationRequest, result: GenerationResult) -> list[str]:
    """Failures for a Season 5 check; empty for a plain smoke call."""
    check = request.metadata.get(CHECK)
    expect = request.metadata.get(EXPECT, "")
    if check in ("tool_call", "parallel"):
        return _tool_call_problems(
            request, result, minimum=int(expect) if check == "parallel" else 1
        )
    if check in ("round_trip", "image") and expect not in result.text:
        return [f"{check}: expected {expect!r} in the answer, got {result.text[:60]!r}"]
    return []


def _tool_call_problems(
    request: GenerationRequest, result: GenerationResult, *, minimum: int
) -> list[str]:
    names = {tool.name for tool in request.tools or ()}
    found = []
    for call in result.tool_calls:
        if call.name not in names:
            found.append(f"called an unknown tool {call.name!r}")
            continue
        try:
            call.arguments()
        except ValueError as exc:
            found.append(f"malformed arguments for {call.name}: {exc}")
    if len(result.tool_calls) < minimum:
        found.append(f"expected at least {minimum} tool calls, got {len(result.tool_calls)}")
    return found


def tool_only_fields(result: GenerationResult) -> set[str]:
    """Fields that are rightly empty when the model answered only with tool calls."""
    return {"text", "time_to_first_answer_token_ms"} if result.tool_calls else set()
