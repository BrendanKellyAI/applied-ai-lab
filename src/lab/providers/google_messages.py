"""Season 5: mapping messages, tools and images to the Gemini API (google-genai), and calls back.

Gemini 3 models return a thought signature with each function call; it must be sent back
unchanged on the next turn (https://aistudio.google.com/docs/function-calling, checked
27 November 2026), so it is carried on the neutral ToolCall as base64.
"""

import base64
import json
from typing import Any

from google.genai import types

from lab.providers.base import GenerationRequest
from lab.providers.messages import Message, ToolCall

_MODES = {"auto": "AUTO", "required": "ANY", "none": "NONE"}


def contents(request: GenerationRequest) -> list[types.Content] | str:
    if request.messages is None:
        return request.prompt
    turns: list[types.Content] = []
    for turn in request.messages:
        role = "model" if turn.role == "assistant" else "user"
        parts = _parts_for(turn)
        if turn.role == "tool" and turns and _is_responses(turns[-1]):
            turns[-1] = types.Content(role="user", parts=[*(turns[-1].parts or []), *parts])
        else:
            turns.append(types.Content(role=role, parts=parts))
    return turns


def _is_responses(content: types.Content) -> bool:
    parts = content.parts or []
    return content.role == "user" and bool(parts) and all(p.function_response for p in parts)


def _parts_for(turn: Message) -> list[types.Part]:
    if turn.role == "tool":
        key = "error" if turn.is_error else "result"
        return [
            types.Part(
                function_response=types.FunctionResponse(
                    id=turn.tool_call_id, name=turn.tool_name, response={key: turn.text}
                )
            )
        ]
    parts = [
        types.Part.from_bytes(data=image.read_bytes(), mime_type=image.media_type)
        for image in turn.images
    ]
    if turn.text:
        parts.append(types.Part(text=turn.text))
    parts.extend(_call_part(call) for call in turn.tool_calls)
    return parts


def _call_part(call: ToolCall) -> types.Part:
    try:
        args = call.arguments()
    except ValueError:
        args = {}
    signature = base64.b64decode(call.signature) if call.signature else None
    return types.Part(
        function_call=types.FunctionCall(id=call.call_id, name=call.name, args=args),
        thought_signature=signature,
    )


def tool_fields(request: GenerationRequest) -> dict[str, Any]:
    if not request.tools:
        # No tools: rule out tool calls and silence the SDK's automatic calling warning.
        return {"automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True)}
    declarations = [
        types.FunctionDeclaration(
            name=tool.name, description=tool.description, parameters_json_schema=tool.parameters
        )
        for tool in request.tools
    ]
    fields: dict[str, Any] = {
        "tools": [types.Tool(function_declarations=declarations)],
        # The harness runs every tool itself; the SDK must never call one on its own.
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
    }
    if request.tool_choice is not None:
        fields["tool_config"] = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode=_MODES[request.tool_choice])
        )
    return fields


def call_from_part(part: Any, position: int) -> ToolCall:
    """A streamed function call part as a neutral call. Gemini may omit the id; one is made."""
    call = part.function_call
    signature = getattr(part, "thought_signature", None)
    return ToolCall(
        call_id=call.id or f"call_{position}",
        name=call.name,
        arguments_json=json.dumps(call.args or {}, sort_keys=True),
        signature=base64.b64encode(signature).decode("ascii") if signature else None,
    )
