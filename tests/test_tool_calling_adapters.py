"""Season 5: each adapter sends messages, tools and images, and reads tool calls back."""

import base64
import json

import pytest
from google.genai import types

from lab.providers.anthropic_provider import AnthropicProvider
from lab.providers.anthropic_provider import build_params as anthropic_params
from lab.providers.base import GenerationRequest, UnsupportedSettingError
from lab.providers.capabilities import CapabilityTable, ModelCapabilities
from lab.providers.google_messages import contents
from lab.providers.google_provider import GoogleProvider, build_config
from lab.providers.messages import ImagePart, Message, ToolCall, ToolSpec, tool_result, user
from lab.providers.openai_provider import OpenAIProvider
from lab.providers.openai_provider import build_params as openai_params
from tests.fakes import RecordingEndpoint, event, ns, ticking_clock

LOOKUP = ToolSpec(
    name="lookup_order",
    description="Find an order by its number.",
    parameters={"type": "object", "properties": {"order_id": {"type": "string"}}},
    strict=True,
)
REFUND = ToolSpec(name="issue_refund", description="Refund.", parameters={"type": "object"})
CALL_A = ToolCall(call_id="c1", name="lookup_order", arguments_json='{"order_id": "H-1"}')
CALL_B = ToolCall(call_id="c2", name="lookup_order", arguments_json='{"order_id": "H-2"}')


@pytest.fixture
def image(tmp_path) -> ImagePart:
    path = tmp_path / "plate.png"
    path.write_bytes(b"\x89PNG plate")
    return ImagePart.from_file(path, detail="high")


def _history(image: ImagePart) -> tuple[Message, ...]:
    return (
        user("Here is the rating plate.", (image,)),
        Message(role="assistant", text="Checking both.", tool_calls=(CALL_A, CALL_B)),
        tool_result(CALL_A, '{"status": "in warranty"}'),
        tool_result(CALL_B, '{"error": "not found"}', is_error=True),
    )


def _request(provider: str, model: str, image: ImagePart, **overrides) -> GenerationRequest:
    fields = {
        "provider": provider,
        "model": model,
        "system": "You resolve warranty cases.",
        "max_output_tokens": 500,
        "reasoning": "off",
        "messages": _history(image),
        "tools": (LOOKUP, REFUND),
        "tool_choice": "required",
    }
    return GenerationRequest(**{**fields, **overrides})


# OpenAI


def test_openai_sends_turns_as_input_items(image):
    params = openai_params(_request("openai", "gpt-6-luna", image))
    items = params["input"]
    assert params["instructions"] == "You resolve warranty cases."
    assert items[0]["content"][1] == {
        "type": "input_image",
        "image_url": f"data:image/png;base64,{base64.b64encode(b'\x89PNG plate').decode()}",
        "detail": "high",
    }
    assert items[1] == {"role": "assistant", "content": "Checking both."}
    assert [i["type"] for i in items[2:]] == ["function_call"] * 2 + ["function_call_output"] * 2
    assert items[4] == {
        "type": "function_call_output",
        "call_id": "c1",
        "output": items[4]["output"],
    }
    assert params["tool_choice"] == "required"
    assert params["tools"][0] == {
        "type": "function",
        "name": "lookup_order",
        "description": "Find an order by its number.",
        "parameters": LOOKUP.parameters,
        "strict": True,
    }


def test_openai_json_mode_keeps_the_conversation_after_the_developer_turn(image):
    from lab.providers.base import OutputFormat

    request = _request("openai", "gpt-6-luna", image, output_format=OutputFormat(kind="json_mode"))
    items = openai_params(request)["input"]
    assert items[0] == {"role": "developer", "content": "You resolve warranty cases."}
    assert items[1]["role"] == "user"


def test_openai_reads_function_calls_from_the_final_response(image):
    final = ns(
        status="completed",
        incomplete_details=None,
        model="gpt-6-luna",
        output=[
            ns(type="message"),
            ns(type="function_call", call_id="c9", name="issue_refund", arguments='{"x": 1}'),
        ],
        usage=ns(
            input_tokens=50,
            output_tokens=9,
            output_tokens_details=ns(reasoning_tokens=0),
            input_tokens_details=ns(cached_tokens=0),
        ),
    )
    endpoint = RecordingEndpoint([event("response.completed", response=final)])
    provider = OpenAIProvider(ns(responses=ns(create=endpoint)), clock=ticking_clock())
    result = provider.generate(_request("openai", "gpt-6-luna", image))
    assert result.finish_reason == "tool_calls"
    assert result.tool_calls == (
        ToolCall(call_id="c9", name="issue_refund", arguments_json='{"x": 1}'),
    )


def test_openai_refuses_tools_with_reasoning_on(image):
    provider = OpenAIProvider(ns(responses=ns(create=RecordingEndpoint())))
    with pytest.raises(UnsupportedSettingError, match="reasoning"):
        provider.validate(_request("openai", "gpt-6-luna", image, reasoning="low"))


# Anthropic


def test_anthropic_merges_tool_results_into_one_user_turn(image):
    params = anthropic_params(_request("anthropic", "claude-haiku-5-5", image))
    first, second, third = params["messages"]
    assert first["content"][0]["source"]["media_type"] == "image/png"
    assert first["content"][1] == {"type": "text", "text": "Here is the rating plate."}
    assert [b["type"] for b in second["content"]] == ["text", "tool_use", "tool_use"]
    assert second["content"][1]["input"] == {"order_id": "H-1"}
    assert third["role"] == "user"
    assert [b["tool_use_id"] for b in third["content"]] == ["c1", "c2"]
    assert third["content"][1]["is_error"] is True
    assert params["tool_choice"] == {"type": "any"}
    assert params["tools"][0]["input_schema"] == LOOKUP.parameters
    assert params["tools"][0]["strict"] is True
    assert "strict" not in params["tools"][1]


def test_anthropic_replays_malformed_arguments_as_an_empty_object(image):
    broken = ToolCall(call_id="c3", name="lookup_order", arguments_json="{oops")
    messages = (user("hi"), Message(role="assistant", tool_calls=(broken,)))
    params = anthropic_params(_request("anthropic", "claude-haiku-5-5", image, messages=messages))
    assert params["messages"][1]["content"][0]["input"] == {}


def test_anthropic_rebuilds_streamed_tool_calls(image):
    events = [
        event("message_start", message=ns(model="claude-haiku-5-5", usage=ns(input_tokens=80))),
        event("content_block_start", index=0, content_block=ns(type="text")),
        event("content_block_delta", index=0, delta=ns(type="text_delta", text="Looking.")),
        event("content_block_stop", index=0),
        event("content_block_start", index=1, content_block=ns(type="tool_use", id="t1", name="x")),
        event(
            "content_block_delta", index=1, delta=ns(type="input_json_delta", partial_json='{"a"')
        ),
        event(
            "content_block_delta", index=1, delta=ns(type="input_json_delta", partial_json=": 1}")
        ),
        event("content_block_stop", index=1),
        event("content_block_start", index=2, content_block=ns(type="tool_use", id="t2", name="y")),
        event("content_block_stop", index=2),
        event("message_delta", delta=ns(stop_reason="tool_use"), usage=ns(output_tokens=20)),
    ]
    provider = AnthropicProvider(ns(messages=ns(create=RecordingEndpoint(events))))
    result = provider.generate(_request("anthropic", "claude-haiku-5-5", image))
    assert result.text == "Looking." and result.finish_reason == "tool_calls"
    assert [(c.call_id, c.arguments_json) for c in result.tool_calls] == [
        ("t1", '{"a": 1}'),
        ("t2", "{}"),
    ]


# Google

GEMINI = CapabilityTable(
    {
        "google": {
            "g": ModelCapabilities(
                reasoning=("off",), temperature=True, tool_calling="parallel", image_input=True
            )
        }
    }
)


def test_google_maps_turns_tools_and_choice(image):
    signed = CALL_A.model_copy(update={"signature": base64.b64encode(b"sig").decode()})
    messages = (
        user("Here is the rating plate.", (image,)),
        Message(role="assistant", tool_calls=(signed, CALL_B)),
        tool_result(CALL_A, "ok"),
        tool_result(CALL_B, "missing", is_error=True),
    )
    request = _request("google", "g", image, messages=messages)
    turns = contents(request)
    assert [t.role for t in turns] == ["user", "model", "user"]
    assert turns[0].parts[0].inline_data.mime_type == "image/png"
    assert turns[1].parts[0].thought_signature == b"sig"
    assert turns[1].parts[1].thought_signature is None
    assert turns[2].parts[0].function_response.response == {"result": "ok"}
    assert turns[2].parts[1].function_response.response == {"error": "missing"}
    config = build_config(request)
    assert config.tools[0].function_declarations[0].parameters_json_schema == LOOKUP.parameters
    assert config.tool_config.function_calling_config.mode == types.FunctionCallingConfigMode.ANY
    assert config.automatic_function_calling.disable is True


def test_google_reads_function_calls_and_keeps_their_signature(image):
    call_part = ns(
        function_call=ns(id=None, name="lookup_order", args={"order_id": "H-1"}),
        thought_signature=b"sig",
        thought=None,
        text=None,
    )
    usage = ns(
        prompt_token_count=40,
        candidates_token_count=6,
        thoughts_token_count=None,
        cached_content_token_count=None,
    )
    chunk = ns(
        model_version="g-001",
        usage_metadata=usage,
        candidates=[ns(finish_reason="STOP", content=ns(parts=[call_part]))],
    )
    client = ns(models=ns(generate_content_stream=lambda **_: iter([chunk])))
    result = GoogleProvider(client, capabilities=GEMINI).generate(_request("google", "g", image))
    (call,) = result.tool_calls
    assert result.finish_reason == "tool_calls"
    assert (call.call_id, json.loads(call.arguments_json)) == ("call_0", {"order_id": "H-1"})
    assert base64.b64decode(call.signature) == b"sig"


def test_google_prompt_requests_still_send_the_prompt_string(image):
    request = GenerationRequest(
        provider="google", model="g", prompt="hi", max_output_tokens=10, reasoning="off"
    )
    assert contents(request) == "hi"
    assert build_config(request).tools is None
