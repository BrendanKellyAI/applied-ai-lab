"""Season 5 smoke checks: what is planned, and when a tool or image check passes."""

from pathlib import Path

import pytest

from lab.config import load_config
from lab.providers.base import GenerationResult, request_hash
from lab.providers.messages import ToolCall
from lab.raw_log import RunRecord
from lab.smoke import describe, plan_smoke, problems
from lab.smoke_agent import IMAGE_SERIAL, render_rating_plate

CONFIG = Path(__file__).resolve().parents[1] / "season5" / "smoke.yaml"


@pytest.fixture
def calls(tmp_path, monkeypatch):
    monkeypatch.setattr("lab.smoke_agent.SMOKE_IMAGE", tmp_path / "plate.png")
    import lab.smoke_agent as smoke_agent

    original = smoke_agent.plan_agent_checks
    monkeypatch.setattr(
        "lab.smoke.plan_agent_checks", lambda config: original(config, tmp_path / "plate.png")
    )
    return {c.mode + " " + c.model_label: c for c in plan_smoke(load_config(CONFIG))}


def _result(request, *, text="", tool_calls=()) -> GenerationResult:
    return GenerationResult(
        request_hash=request_hash(request),
        provider=request.provider,
        model_requested=request.model,
        model_returned=request.model,
        text=text,
        input_tokens=10,
        output_tokens=5,
        reasoning_tokens=0,
        cached_input_tokens=0,
        time_to_first_answer_token_ms=1.0 if text else None,
        total_latency_ms=2.0,
        finish_reason="tool_calls" if tool_calls else "stop",
        timestamp_utc="2026-11-27T00:00:00+00:00",
        tool_calls=tool_calls,
    )


def _record(call, result) -> RunRecord:
    return RunRecord.model_validate(
        {
            "call_id": call.call_id,
            "model_label": call.model_label,
            "mode": call.mode,
            "cell": {},
            "request_hash": request_hash(call.request),
            "attempts": 1,
            "source": "api",
            "result": result.model_dump(),
            "error": None,
        }
    )


def _call(name, order="H-100001"):
    return ToolCall(call_id=f"c-{order}", name=name, arguments_json=f'{{"order_id": "{order}"}}')


def test_plans_four_checks_per_tool_and_image_model_and_none_for_the_generator(calls):
    assert len(calls) == 11
    gemini = [key for key in calls if "gemini" in key]
    assert gemini == ["lowest gemini-3.1-flash-lite"]


def test_tool_call_answer_with_no_text_passes(calls):
    call = calls["lowest tool_call gpt-6-luna"]
    result = _result(call.request, tool_calls=(_call("lookup_order"),))
    assert problems(_record(call, result), call.request) == []
    assert any("not applicable" in line for line in describe(_record(call, result), call.request))


@pytest.mark.parametrize(
    ("tool_calls", "message"),
    [
        ((), "at least 1"),
        ((_call("refund"),), "unknown tool"),
        ((ToolCall(call_id="x", name="lookup_order", arguments_json="{bad"),), "malformed"),
    ],
)
def test_tool_call_failures_are_reported(calls, tool_calls, message):
    call = calls["lowest tool_call claude-haiku-5-5"]
    result = _result(call.request, text="" if tool_calls else "sorry", tool_calls=tool_calls)
    assert any(message in p for p in problems(_record(call, result), call.request))


def test_parallel_needs_two_calls(calls):
    call = calls["lowest parallel gpt-6-luna"]
    one = _result(call.request, tool_calls=(_call("lookup_order"),))
    two = _result(call.request, tool_calls=(_call("lookup_order"), _call("lookup_order", "H-2")))
    assert problems(_record(call, one), call.request)
    assert problems(_record(call, two), call.request) == []


@pytest.mark.parametrize(
    ("check", "good"), [("round_trip", "It is a Brio kettle."), ("image", IMAGE_SERIAL)]
)
def test_answers_must_contain_the_expected_value(calls, check, good):
    call = calls[f"lowest {check} gpt-6-luna"]
    assert problems(_record(call, _result(call.request, text=good)), call.request) == []
    bad = _record(call, _result(call.request, text="I cannot tell."))
    assert problems(bad, call.request)
    assert any("FAILED CHECK" in line for line in describe(bad, call.request))


def test_round_trip_sends_the_call_and_its_result(calls):
    turns = calls["lowest round_trip claude-haiku-5-5"].request.turns()
    assert [t.role for t in turns] == ["user", "assistant", "tool"]


def test_rating_plate_is_drawn_once(tmp_path):
    path = render_rating_plate(tmp_path / "p.png")
    first = path.read_bytes()
    assert render_rating_plate(path).read_bytes() == first and first.startswith(b"\x89PNG")
