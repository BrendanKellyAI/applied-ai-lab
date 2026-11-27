"""Season 5: mapping messages, tools and images to the OpenAI Responses API, and tool calls back.

Shapes from https://developers.openai.com/api/docs/guides/function-calling and
https://developers.openai.com/api/docs/guides/images-vision, checked 27 November 2026.
"""

from typing import Any

from lab.providers.base import GenerationRequest, UnsupportedSettingError
from lab.providers.messages import Message, ToolCall, ToolSpec

_TOOL_CHOICE = {"auto": "auto", "required": "required", "none": "none"}


def check_supported(request: GenerationRequest) -> None:
    """Refuse what this adapter cannot yet send faithfully.

    With reasoning on, OpenAI returns reasoning items alongside tool calls that must be passed
    back on the next turn. Nothing is stored server side (`store: false`), so they would have to
    be carried as encrypted content. That is not built: Season 5 runs the agent with reasoning
    off, and E4's optional low reasoning arm would need it added first.
    """
    if request.tools and request.reasoning not in (None, "off"):
        raise UnsupportedSettingError(
            "tool calls with reasoning on are not supported by this adapter yet; set reasoning: off"
        )


def input_items(request: GenerationRequest) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for turn in request.messages or ():
        items.extend(_items_for(turn))
    return items


def _items_for(turn: Message) -> list[dict[str, Any]]:
    if turn.role == "user":
        content: list[dict[str, Any]] = [{"type": "input_text", "text": turn.text}]
        content.extend(
            {
                "type": "input_image",
                "image_url": f"data:{image.media_type};base64,{image.base64()}",
                "detail": image.detail,
            }
            for image in turn.images
        )
        return [{"role": "user", "content": content}]
    if turn.role == "tool":
        return [{"type": "function_call_output", "call_id": turn.tool_call_id, "output": turn.text}]
    items: list[dict[str, Any]] = []
    if turn.text:
        items.append({"role": "assistant", "content": turn.text})
    items.extend(
        {
            "type": "function_call",
            "call_id": call.call_id,
            "name": call.name,
            "arguments": call.arguments_json,
        }
        for call in turn.tool_calls
    )
    return items


def tool_params(request: GenerationRequest) -> dict[str, Any]:
    if not request.tools:
        return {}
    params: dict[str, Any] = {"tools": [_tool(tool) for tool in request.tools]}
    if request.tool_choice is not None:
        params["tool_choice"] = _TOOL_CHOICE[request.tool_choice]
    return params


def _tool(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
        "strict": tool.strict,
    }


def tool_calls(response: Any) -> tuple[ToolCall, ...]:
    """Function calls in the final response, in the order the model made them."""
    return tuple(
        ToolCall(call_id=item.call_id, name=item.name, arguments_json=item.arguments or "")
        for item in getattr(response, "output", None) or ()
        if getattr(item, "type", None) == "function_call"
    )
