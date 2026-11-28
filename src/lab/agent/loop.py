"""The agent loop: the model asks for tools, code runs them, results go back, until done.

Stops when every appliance in the case is closed, when the model answers without asking for a
tool, or when a cap is hit (turns, tool calls, input tokens), which leaves the case unresolved
with the cap named. In E3's crash arm, a tool error also ends the run.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.agent.caller import ModelCaller
from lab.agent.case_model import CaseFacts
from lab.agent.config import Arm, caps_for
from lab.agent.env import CaseEnv
from lab.agent.instructions import first_message, system_prompt
from lab.agent.kb import KnowledgeBase
from lab.agent.tool_specs import tool_specs
from lab.agent.tools import HarnessRules, error, run_tool
from lab.providers.base import GenerationRequest
from lab.providers.messages import Message, ToolCall, tool_result

StopReason = Literal[
    "closed", "no_tool_call", "cap_turns", "cap_tool_calls", "cap_tokens", "crash", "length"
]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Turn(_Frozen):
    index: int
    request_hash: str
    source: str
    text: str
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    output_tokens: int
    finish_reason: str


class ToolEvent(_Frozen):
    turn: int
    call_id: str
    name: str
    arguments_json: str
    result_json: str
    outcome: Literal["ok", "tool_error", "blocked", "malformed"]


class CaseRun(_Frozen):
    case_id: str
    arm: str
    repeat: int
    stop_reason: StopReason
    turns: tuple[Turn, ...]
    events: tuple[ToolEvent, ...]
    end_state: dict[str, list[dict[str, object]]]


WRITE_TABLES = (
    "service_visits",
    "refunds",
    "replacements",
    "escalations",
    "case_outcomes",
    "approval_requests",
    "audit_log",
)


def run_case(
    facts: CaseFacts,
    message: str,
    arm: Arm,
    caller: ModelCaller,
    kb: KnowledgeBase,
    *,
    repeat: int = 0,
) -> CaseRun:
    env = CaseEnv.open(facts)
    caps = caps_for(arm, facts.kind)
    rules = HarnessRules(**arm.harness.model_dump())
    email = str(env.customer()["email"])
    history: list[Message] = [
        first_message(facts, message, email, attach_images=arm.images == "attach")
    ]
    tools = tool_specs(arm.tools, style=arm.descriptions, strict=arm.strict_schemas)
    system = system_prompt(arm.instructions, env)
    turns: list[Turn] = []
    events: list[ToolEvent] = []
    input_total = 0
    stop: StopReason = "cap_turns"
    for index in range(caps.max_turns):
        env.state.turn = index
        request = GenerationRequest(
            provider=arm.model.provider,
            model=arm.model.model,
            system=system,
            messages=tuple(history),
            tools=tools,
            tool_choice="auto",
            max_output_tokens=arm.model.max_output_tokens,
            reasoning=arm.model.reasoning,
            metadata={"case_id": facts.case_id, "arm": arm.name, "turn": str(index)},
            cache_salt=f"repeat-{repeat}" if repeat else None,
        )
        result, source = caller(request)
        turns.append(_turn(index, result, source))
        input_total += result.input_tokens
        if not result.tool_calls:
            stop = "length" if result.finish_reason == "length" else "no_tool_call"
            break
        history.append(Message(role="assistant", text=result.text, tool_calls=result.tool_calls))
        if len(events) + len(result.tool_calls) > caps.max_tool_calls:
            stop = "cap_tool_calls"
            break
        crashed = _run_calls(env, kb, rules, arm, index, result.tool_calls, history, events)
        if crashed:
            stop = "crash"
            break
        if env.all_closed():
            stop = "closed"
            break
        if input_total > caps.max_input_tokens:
            stop = "cap_tokens"
            break
    run = CaseRun(
        case_id=facts.case_id,
        arm=arm.name,
        repeat=repeat,
        stop_reason=stop,
        turns=tuple(turns),
        events=tuple(events),
        end_state=_end_state(env),
    )
    env.db.close()
    return run


def _turn(index: int, result, source: str) -> Turn:
    return Turn(
        index=index,
        request_hash=result.request_hash,
        source=source,
        text=result.text,
        tool_calls=result.tool_calls,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        finish_reason=result.finish_reason,
    )


def _run_calls(env, kb, rules, arm: Arm, index: int, calls, history, events) -> bool:
    """Run each call and append its result. True if the run must stop (crash arm)."""
    for call in calls:
        try:
            args = call.arguments()
        except ValueError as exc:
            env.audit(call.name, call.arguments_json, "tool_error")
            result, outcome = error(f"could not read the arguments: {exc}"), "malformed"
        else:
            if call.name not in arm.tools:
                env.audit(call.name, call.arguments_json, "tool_error")
                result = error(f"there is no tool called {call.name}")
            else:
                result = run_tool(env, kb, rules, call.name, args)
            outcome = _outcome(result)
        text = json.dumps(result, ensure_ascii=False, default=str)
        events.append(
            ToolEvent(
                turn=index,
                call_id=call.call_id,
                name=call.name,
                arguments_json=call.arguments_json,
                result_json=text,
                outcome=outcome,
            )
        )
        history.append(tool_result(call, text, is_error="error" in result))
        if arm.errors == "raised" and "error" in result:
            return True
    return False


def _outcome(result: dict[str, object]) -> Literal["ok", "tool_error", "blocked"]:
    if "error" not in result:
        return "ok"
    return "blocked" if str(result["error"]).startswith("blocked by the harness") else "tool_error"


def _end_state(env: CaseEnv) -> dict[str, list[dict[str, object]]]:
    state = {table: env.rows(f"SELECT * FROM {table}") for table in WRITE_TABLES}  # noqa: S608
    state["visit_slots"] = env.rows(
        "SELECT v.serial, s.region, s.starts FROM service_visits v"
        " JOIN service_slots s ON s.slot_id = v.slot_id"
    )
    return state
