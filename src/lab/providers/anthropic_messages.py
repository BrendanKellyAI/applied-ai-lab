"""Season 5: mapping messages, tools and images to the Anthropic Messages API, and tool calls back.

Shapes from https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview and
https://platform.claude.com/docs/en/build-with-claude/vision, checked 27 November 2026.
"""

from typing import Any

from lab.providers.base import GenerationRequest
from lab.providers.messages import Message, ToolCall, ToolSpec

_TOOL_CHOICE = {"auto": {"type": "auto"}, "required": {"type": "any"}, "none": {"type": "none"}}


def api_messages(request: GenerationRequest) -> list[dict[str, Any]]:
    """Turns as Anthropic messages. Tool results that follow one another share one user turn."""
    messages: list[dict[str, Any]] = []
    for turn in request.turns():
        role = "assistant" if turn.role == "assistant" else "user"
        blocks = _blocks_for(turn)
        if turn.role == "tool" and messages and _is_tool_results(messages[-1]):
            messages[-1] = {"role": "user", "content": [*messages[-1]["content"], *blocks]}
        else:
            messages.append({"role": role, "content": blocks})
    return messages


def _is_tool_results(message: dict[str, Any]) -> bool:
    content = message["content"]
    return (
        message["role"] == "user"
        and isinstance(content, list)
        and all(block["type"] == "tool_result" for block in content)
    )


def _blocks_for(turn: Message) -> list[dict[str, Any]]:
    if turn.role == "tool":
        return [
            {
                "type": "tool_result",
                "tool_use_id": turn.tool_call_id,
                "content": turn.text,
                "is_error": turn.is_error,
            }
        ]
    blocks: list[dict[str, Any]] = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": image.media_type, "data": image.base64()},
        }
        for image in turn.images
    ]
    if turn.text:
        blocks.append({"type": "text", "text": turn.text})
    blocks.extend(
        {"type": "tool_use", "id": call.call_id, "name": call.name, "input": _input(call)}
        for call in turn.tool_calls
    )
    return blocks


def _input(call: ToolCall) -> dict[str, Any]:
    """A replayed call's arguments. Malformed ones go back empty: the tool result already told
    the model they were malformed, and the API accepts only an object here."""
    try:
        return call.arguments()
    except ValueError:
        return {}


def tool_params(request: GenerationRequest) -> dict[str, Any]:
    if not request.tools:
        return {}
    params: dict[str, Any] = {"tools": [_tool(tool) for tool in request.tools]}
    if request.tool_choice is not None:
        params["tool_choice"] = _TOOL_CHOICE[request.tool_choice]
    return params


def _tool(tool: ToolSpec) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters,
    }
    if tool.strict:
        spec["strict"] = True
    return spec


class ToolUseCollector:
    """Rebuilds tool calls from streamed blocks: a start with id and name, then JSON pieces."""

    def __init__(self) -> None:
        self._open: dict[int, dict[str, Any]] = {}
        self.calls: list[ToolCall] = []

    def start(self, index: int, block: Any) -> None:
        self._open[index] = {"id": block.id, "name": block.name, "parts": []}

    def add(self, index: int, partial_json: str) -> None:
        if index in self._open:
            self._open[index]["parts"].append(partial_json)

    def stop(self, index: int) -> None:
        block = self._open.pop(index, None)
        if block is not None:
            self.calls.append(
                ToolCall(
                    call_id=block["id"],
                    name=block["name"],
                    arguments_json="".join(block["parts"]) or "{}",
                )
            )
