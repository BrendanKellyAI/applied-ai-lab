"""The agent loop, tools, customer, approver, harness, scorer and replay, on the mock provider."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lab.agent.caller import BudgetExceeded, ModelCaller
from lab.agent.config import AgentExperiment, Arm, Caps
from lab.agent.env import CaseEnv
from lab.agent.kb import KeywordKB
from lab.agent.loop import run_case
from lab.agent.mock_agent import emails, oracle
from lab.agent.people import NOT_KNOWN, POINT_BACK, approve, customer_reply
from lab.agent.reader_score import score_file
from lab.agent.replay import markdown, svg, write_replay
from lab.agent.run import load_cases, run_arm
from lab.agent.score import score_case
from lab.agent.tools import HarnessRules, check_warranty, lookup_order, run_tool
from lab.cache import ResponseCache
from lab.cli import app
from lab.providers.base import GenerationRequest, ServerError
from lab.providers.messages import ToolCall
from lab.providers.mock import MockProvider, MockReply

DEV = load_cases(["dev"])
BY_ID = {c.facts.case_id: c for c in DEV}
KB = KeywordKB()


def _arm(**fields) -> Arm:
    base = {"name": "t", "model": {"provider": "mock", "model": "m", "reasoning": "off"}}
    return Arm.model_validate({**base, **fields})


def _caller(respond, tmp_path: Path, **kwargs) -> ModelCaller:
    provider = MockProvider(respond=respond)
    return ModelCaller(
        {"mock": provider}, ResponseCache(tmp_path / "cache"), requests_per_minute=10**6, **kwargs
    )


def _first(kind: str, tag: str | None = None):
    return next(c for c in DEV if c.facts.kind == kind and (tag is None or tag in c.facts.tags))


def _script(*steps: list[tuple[str, dict]]):
    """A mock that makes each listed batch of calls on successive turns, then stops."""

    def respond(request: GenerationRequest) -> MockReply:
        turn = sum(1 for m in request.messages or () if m.role == "assistant")
        if turn >= len(steps):
            return MockReply(text="Done.")
        calls = tuple(
            ToolCall(
                call_id=f"c{turn}-{i}",
                name=name,
                arguments_json=json.dumps(args) if isinstance(args, dict) else args,
            )
            for i, (name, args) in enumerate(steps[turn])
        )
        return MockReply(tool_calls=calls)

    return respond


@pytest.mark.parametrize("kind", sorted({c.facts.kind for c in DEV}))
def test_the_oracle_resolves_every_kind(kind, tmp_path):
    cases = [c for c in DEV if c.facts.kind == kind][:3]
    caller = _caller(oracle({c.facts.case_id: c.facts for c in cases}), tmp_path)
    for case in cases:
        run = run_case(case.facts, case.message, _arm(knowledge_base="keyword"), caller, KB)
        score = score_case(case.facts, run)
        assert score.resolved, (case.facts.case_id, score.appliances, score.unsafe_executed)


def _reckless(case):
    serial = case.facts.appliances[0].serial
    return _script(
        [("issue_refund", {"serial": serial, "amount": 9999, "kind": "early_fault"})],
        [("book_service_visit", {"serial": serial, "fault": "leak"})] * 2,
        [("book_service_visit", {"serial": "BK20-10001", "fault": "leak"})],
        [("close_case", {"serial": serial, "decision": "refund", "reply": "Done."})],
    )


def test_unsafe_actions_are_counted_when_executed(tmp_path):
    case = _first("routine")
    run = run_case(case.facts, case.message, _arm(), _caller(_reckless(case), tmp_path), KB)
    score = score_case(case.facts, run)
    assert not score.resolved
    joined = " ".join(score.unsafe_executed)
    assert "refund the policy does not give" in joined and "second write" in joined


def test_a_refund_the_policy_gives_still_needs_its_approval(tmp_path):
    case = next(c for c in DEV if c.facts.expected[0].approval_needed)
    outcome = case.facts.expected[0]
    refund = {"serial": outcome.serial, "amount": outcome.amount, "kind": outcome.reason}
    close = {
        "serial": outcome.serial,
        "decision": "refund",
        "reason": outcome.reason,
        "reply": "Done.",
    }
    steps = _script([("issue_refund", refund)], [("close_case", close)])
    run = run_case(case.facts, case.message, _arm(), _caller(steps, tmp_path), KB)
    score = score_case(case.facts, run)
    assert score.unsafe_executed == (f"refund without a granted approval ({outcome.serial})",)
    assert score.approvals_missed == 1 and not score.resolved


def test_harness_rules_block_the_same_actions(tmp_path):
    case = _first("routine")
    arm = _arm(harness={"refund_limit": True, "idempotency": True, "least_privilege": True})
    run = run_case(case.facts, case.message, arm, _caller(_reckless(case), tmp_path), KB)
    score = score_case(case.facts, run)
    blocked = [e for e in run.events if e.outcome == "blocked"]
    assert {e.name for e in blocked} == {"issue_refund", "book_service_visit"}
    assert score.unsafe_attempted > len(score.unsafe_executed)
    assert not any("refund" in u for u in score.unsafe_executed)
    assert len(run.end_state["visit_slots"]) == 1


@pytest.mark.parametrize(
    ("caps", "steps", "stop"),
    [
        (Caps(max_turns=2), [[("read_past_cases", {"customer_email": "x"})]] * 5, "cap_turns"),
        (
            Caps(max_tool_calls=2),
            [[("read_past_cases", {"customer_email": "x"})] * 3],
            "cap_tool_calls",
        ),
        (
            Caps(max_input_tokens=1),
            [[("read_past_cases", {"customer_email": "x"})]] * 3,
            "cap_tokens",
        ),
        (None, [], "no_tool_call"),
    ],
)
def test_caps_and_stops(caps, steps, stop, tmp_path):
    case = _first("routine")
    run = run_case(
        case.facts, case.message, _arm(caps=caps), _caller(_script(*steps), tmp_path), KB
    )
    assert run.stop_reason == stop
    assert not score_case(case.facts, run).resolved


def test_malformed_and_unknown_calls_go_back_as_errors(tmp_path):
    case = _first("routine")
    steps = _script(
        [("lookup_order", "{not json"), ("fly_to_the_moon", {}), ("lookup_order", {"order_id": 5})]
    )
    run = run_case(case.facts, case.message, _arm(), _caller(steps, tmp_path), KB)
    score = score_case(case.facts, run)
    assert [e.outcome for e in run.events] == ["malformed", "tool_error", "tool_error"]
    assert score.malformed_calls == 1 and score.unknown_tool_calls == 1 and score.wasted_calls == 3


def test_the_crash_arm_stops_on_the_first_error(tmp_path):
    case = _first("routine")
    steps = _script(
        [("lookup_order", {"order_id": "H-000000"})], [("read_past_cases", {"customer_email": "x"})]
    )
    run = run_case(case.facts, case.message, _arm(errors="raised"), _caller(steps, tmp_path), KB)
    assert run.stop_reason == "crash" and len(run.events) == 1


def test_the_customer_answers_withheld_facts_only():
    case = _first("missing_information", "no_product")
    env = CaseEnv.open(case.facts)
    assert case.facts.appliances[0].product in customer_reply(env, "Which appliance is it?")
    assert customer_reply(env, "What colour is your kitchen?") == POINT_BACK
    photo = next(c for c in load_cases(["test"]) if c.facts.unknown)
    assert customer_reply(CaseEnv.open(photo.facts), "What is the serial number?") == NOT_KNOWN


def test_a_pressure_customer_pushes_back_once(tmp_path):
    case = _first("adversarial", "pressure")
    facts = {case.facts.case_id: case.facts}
    run = run_case(case.facts, case.message, _arm(), _caller(oracle(facts), tmp_path), KB)
    closes = [e for e in run.events if e.name == "close_case"]
    assert len(closes) == 2 and "customer replied" in closes[0].result_json
    assert score_case(case.facts, run).resolved


def test_the_approver_grants_only_what_the_policy_gives():
    case = _first("above_limit")
    expected = case.facts.expected[0]
    env = CaseEnv.open(case.facts)
    serial = expected.serial
    assert approve(env, serial, expected.amount, expected.reason)["granted"] is True
    assert approve(env, serial, expected.amount + 50, expected.reason)["granted"] is False
    rows = env.rows("SELECT needed FROM approval_requests")
    assert [r["needed"] for r in rows] == [1, 1]


def test_tools_find_orders_and_need_a_receipt_date_for_retailer_appliances():
    case = _first("routine")
    env = CaseEnv.open(case.facts)
    email = emails()[case.facts.customer_id]
    assert lookup_order(env, customer_email=email)["orders"]
    assert "error" in lookup_order(env)
    assert "error" in lookup_order(env, order_id="H-000000")
    photo = next(c for c in load_cases(["test"]) if c.facts.kind == "photo")
    penv = CaseEnv.open(photo.facts)
    serial = photo.facts.appliances[0].serial
    assert "purchase_date" in check_warranty(penv, serial)["error"]
    assert check_warranty(penv, serial, "2025-01-01")["bought_from"] == "another shop"
    assert "error" in check_warranty(penv, serial, "01/01/2025")
    assert "error" in run_tool(env, KB, HarnessRules(), "lookup_order", {"order_id": "H-1", "x": 1})


def test_replay_shows_every_call(tmp_path):
    case = _first("routine")
    caller = _caller(oracle({case.facts.case_id: case.facts}), tmp_path)
    run = run_case(case.facts, case.message, _arm(), caller, KB)
    text = markdown(run)
    assert "Calls book_service_visit" in text and "Stopped: closed" in text
    assert svg(run).startswith("<svg") and "close_case" in svg(run)
    md, image = write_replay(run, tmp_path / "replays")
    assert md.exists() and image.name.endswith("-slide.svg")


def test_reader_scoring(tmp_path):
    answers = tmp_path / "answers.jsonl"
    lines = []
    for case in DEV:
        outcomes = [
            o.model_dump(include={"serial", "decision", "reason", "amount"})
            for o in case.facts.expected
        ]
        lines.append(json.dumps({"case_id": case.facts.case_id, "outcomes": outcomes}))
    answers.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    result = score_file(answers, "dev")
    assert result["resolved"] == len(DEV) - 1 and list(result["problems"].values()) == [
        ["no answer"]
    ]


def test_the_caller_retries_and_respects_the_budget(tmp_path):
    attempts = {"n": 0}

    class Flaky(MockProvider):
        def generate(self, request):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise ServerError("busy")
            return super().generate(request)

    caller = ModelCaller(
        {"mock": Flaky()}, ResponseCache(tmp_path / "c"), sleep=lambda _s: None,
        budget=0.0000001, prices={"m": (1000.0, 1000.0)},
    )  # fmt: skip
    request = GenerationRequest(
        provider="mock", model="m", prompt="hi", max_output_tokens=5, reasoning="off"
    )
    result, source = caller(request)
    assert source == "api" and attempts["n"] == 2
    assert caller(request)[1] == "cache"
    with pytest.raises(BudgetExceeded):
        caller(request.model_copy(update={"prompt": "again"}))


def test_run_arm_and_the_cli_dry_run(tmp_path):
    cases = DEV[:4]
    experiment = AgentExperiment.model_validate(
        {"experiment": "t", "cases": ["dev"], "arms": [_arm(knowledge_base="keyword").model_dump()]}
    )
    caller = _caller(oracle({c.facts.case_id: c.facts for c in cases}), tmp_path)
    summary = run_arm(experiment, experiment.arms[0], cases, caller, KB, tmp_path / "results")
    assert summary["resolved"] == 4
    config = tmp_path / "exp" / "config.yaml"
    config.parent.mkdir()
    ids = [c.facts.case_id for c in cases]
    config.write_text(
        json.dumps(
            {**experiment.model_dump(mode="json"), "case_ids": ids, "experiment": "cli-dry"}
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["agent", "run", str(config), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert (config.parent / "results-dry-run" / "config" / "t" / "summary.json").exists()
    estimate = CliRunner().invoke(app, ["agent", "estimate", str(config)])
    assert estimate.exit_code == 0 and "ceiling" in estimate.output


def test_a_paid_run_needs_a_budget(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        json.dumps({"experiment": "no-budget", "arms": [_arm().model_dump()]}), encoding="utf-8"
    )
    result = CliRunner().invoke(
        app, ["agent", "run", str(config), "--prices", str(tmp_path / "none.yaml")]
    )
    assert result.exit_code == 2 and "Refusing" in result.output


def test_an_unidentified_appliance_can_be_escalated_as_unknown():
    case = next(c for c in load_cases(["test"]) if c.facts.unknown)
    env = CaseEnv.open(case.facts)
    escalate = {"serial": "unknown", "decision": "escalate", "reason": "facts_unknown"}
    result = run_tool(env, KB, HarnessRules(), "close_case", {**escalate, "reply": "We will call."})
    assert result["appliances_escalated"] == 1 and env.all_closed()
    decline = {"serial": "unknown", "decision": "decline", "reply": "No."}
    bad = run_tool(CaseEnv.open(case.facts), KB, HarnessRules(), "close_case", decline)
    assert "error" in bad


def test_lookup_shows_who_owns_each_order():
    case = _first("routine")
    env = CaseEnv.open(case.facts)
    order = lookup_order(env, order_id=case.facts.appliances[0].order_id)["orders"][0]
    assert order["customer_email"] == emails()[case.facts.customer_id]


def test_the_pipeline_escalates_safety_before_identifying(tmp_path):
    from lab.agent.mock_triage import perfect_triage
    from lab.agent.pipeline import run_pipeline

    case = next(
        c for c in load_cases(["test"]) if "safety" in c.facts.tags and c.facts.kind == "photo"
    )
    caller = _caller(perfect_triage({case.facts.case_id: case.facts}), tmp_path)
    run = run_pipeline(case.facts, case.message, _arm(kind="pipeline"), caller)
    assert score_case(case.facts, run).resolved
