"""Season 5 request shapes: messages, tools, images, the request hash and capability checks."""

import hashlib
import json

import pytest
from pydantic import ValidationError

from lab.providers.base import GenerationRequest, UnsupportedSettingError, request_hash
from lab.providers.capabilities import CapabilityTable, ModelCapabilities
from lab.providers.messages import ImagePart, Message, ToolCall, ToolSpec, tool_result, user
from lab.providers.mock import MockProvider, MockReply

LOOKUP = ToolSpec(
    name="lookup_order",
    description="Find an order by its number.",
    parameters={"type": "object", "properties": {"order_id": {"type": "string"}}},
)
CALL = ToolCall(call_id="c1", name="lookup_order", arguments_json='{"order_id": "H-1"}')


def _request(**overrides) -> GenerationRequest:
    fields = {
        "provider": "mock",
        "model": "m",
        "max_output_tokens": 100,
        "messages": (user("My kettle is broken."),),
    }
    return GenerationRequest(**{**fields, **overrides})


@pytest.fixture
def png(tmp_path):
    path = tmp_path / "receipt.png"
    path.write_bytes(b"\x89PNG fake image bytes")
    return path


def _season_4_hash(request: GenerationRequest) -> str:
    """The hashing rule as it stood before Season 5, for a request with no output format."""
    new_fields = {
        "stream",
        "metadata",
        "output_format",
        "messages",
        "tools",
        "tool_choice",
        "cache_salt",
    }
    payload = request.model_dump(mode="json", exclude=new_fields)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("reasoning", [None, "off", "low"])
def test_prompt_requests_hash_exactly_as_before_season_5(reasoning):
    request = GenerationRequest(
        provider="openai",
        model="gpt-6-luna",
        system="Reply briefly.",
        prompt="Is my kettle in warranty?",
        max_output_tokens=300,
        reasoning=reasoning,
        metadata={"call": "x"},
    )
    assert request_hash(request) == _season_4_hash(request)


def test_hash_covers_messages_tools_and_choice():
    base = _request()
    with_tools = _request(tools=(LOOKUP,))
    forced = _request(tools=(LOOKUP,), tool_choice="required")
    longer = _request(messages=(user("My kettle is broken."), Message(role="assistant", text="ok")))
    hashes = {request_hash(r) for r in (base, with_tools, forced, longer)}
    assert len(hashes) == 4


def test_hash_counts_image_content_not_its_path(png, tmp_path):
    moved = tmp_path / "moved.png"
    moved.write_bytes(png.read_bytes())
    first = _request(messages=(user("see photo", (ImagePart.from_file(png),)),))
    second = _request(messages=(user("see photo", (ImagePart.from_file(moved),)),))
    assert request_hash(first) == request_hash(second)


def test_image_part_refuses_a_changed_file(png):
    image = ImagePart.from_file(png, detail="low")
    assert image.media_type == "image/png" and image.read_bytes().startswith(b"\x89PNG")
    png.write_bytes(b"different")
    with pytest.raises(ValueError, match="sha256"):
        image.read_bytes()


def test_image_part_rejects_unknown_types(tmp_path):
    path = tmp_path / "scan.tiff"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="unsupported"):
        ImagePart.from_file(path)


@pytest.mark.parametrize(
    "fields",
    [
        {"messages": None, "prompt": ""},
        {"prompt": "also a prompt"},
        {"messages": ()},
        {"messages": (Message(role="assistant", text="hi"),)},
        {"tool_choice": "auto"},
        {"tools": (LOOKUP, LOOKUP)},
    ],
)
def test_invalid_requests_are_refused(fields):
    with pytest.raises(ValidationError):
        _request(**fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"role": "assistant", "text": "x", "images": ()},
        {"role": "tool", "text": "x"},
        {"role": "user", "text": "x", "is_error": True},
        {"role": "user", "text": "x", "tool_calls": (CALL,)},
    ],
)
def test_message_fields_must_match_role(fields, png):
    if fields["role"] == "assistant":
        fields = {**fields, "images": (ImagePart.from_file(png),)}
    with pytest.raises(ValidationError):
        Message(**fields)


def test_tool_result_answers_its_call():
    result = tool_result(CALL, '{"error": "not found"}', is_error=True)
    assert (result.tool_call_id, result.tool_name, result.is_error) == ("c1", "lookup_order", True)


@pytest.mark.parametrize("raw", ["{not json", "[1, 2]"])
def test_malformed_arguments_are_reported(raw):
    with pytest.raises(ValueError):
        ToolCall(call_id="c", name="t", arguments_json=raw).arguments()


def test_empty_arguments_parse_as_an_empty_object():
    assert ToolCall(call_id="c", name="t", arguments_json="").arguments() == {}


def _table(**caps) -> CapabilityTable:
    spec = ModelCapabilities(temperature=False, **caps)
    return CapabilityTable({"mock": {"m": spec}})


def test_tools_need_verified_tool_calling():
    with pytest.raises(UnsupportedSettingError, match="tool calling"):
        _table().check(_request(tools=(LOOKUP,)))
    _table(tool_calling="basic").check(_request(tools=(LOOKUP,)))


def test_images_need_verified_image_input_within_the_limit(png):
    image = ImagePart.from_file(png)
    request = _request(messages=(user("photos", (image, image)),))
    with pytest.raises(UnsupportedSettingError, match="image input"):
        _table().check(request)
    with pytest.raises(UnsupportedSettingError, match="at most 1"):
        _table(image_input=True, max_images_per_request=1).check(request)
    _table(image_input=True, max_images_per_request=2).check(request)


def test_luna_and_haiku_are_verified_for_tools_and_images():
    from lab.providers.capabilities import default_capabilities

    table = default_capabilities()
    for provider, model in (("openai", "gpt-6-luna"), ("anthropic", "claude-haiku-5-5")):
        caps = table.lookup(provider, model)
        assert caps.tool_calling == "parallel" and caps.image_input


def test_mock_scripts_tool_calls_then_an_answer():
    # Arrange: call a tool on the first turn, answer once a tool result has come back.
    def respond(request: GenerationRequest) -> MockReply:
        if request.turns()[-1].role == "tool":
            return MockReply(text="Your order H-1 is in warranty.")
        return MockReply(tool_calls=(CALL,))

    provider = MockProvider(respond=respond)
    first = provider.generate(_request(tools=(LOOKUP,)))
    # Act
    history = (user("My kettle is broken."), Message(role="assistant", tool_calls=first.tool_calls))
    second = provider.generate(
        _request(tools=(LOOKUP,), messages=(*history, tool_result(CALL, '{"status": "ok"}')))
    )
    # Assert
    assert first.finish_reason == "tool_calls" and first.tool_calls == (CALL,)
    assert second.finish_reason == "stop" and second.text.startswith("Your order")
    assert second.input_tokens > first.input_tokens


def test_mock_still_answers_plain_prompts():
    result = MockProvider().generate(
        GenerationRequest(provider="mock", model="m", prompt="a b c", max_output_tokens=5)
    )
    assert result.input_tokens == 3 and result.tool_calls == ()


def test_a_cache_salt_separates_repeats_and_is_never_sent():
    plain = _request()
    salted = _request(cache_salt="repeat-1")
    assert request_hash(plain) != request_hash(salted)
    assert request_hash(salted) == request_hash(_request(cache_salt="repeat-1"))
