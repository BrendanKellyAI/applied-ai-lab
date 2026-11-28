"""An oracle agent for the mock provider: it takes each case's correct path, one tool a turn.

Used to test the loop, tools, customer, approver and scorer end to end with no spend, and for
dry runs that count the tokens a real run's requests would carry. It reads the case's facts, so
it is never a baseline; a real model must find the path itself.
"""

import csv
import json
from collections.abc import Callable, Mapping
from functools import cache

from lab.agent.case_model import Appliance, CaseFacts, ExpectedOutcome
from lab.agent.world import WORLD_DIR
from lab.providers.base import GenerationRequest
from lab.providers.messages import Message, ToolCall
from lab.providers.mock import MockReply

QUESTIONS = {
    "order_id": "What is your order number?",
    "product": "Which appliance is it?",
    "fault": "Could you describe the fault?",
    "purchase_date": "What is the purchase date on your receipt?",
    "serial": "What is the serial number on the rating plate?",
    "which": "Which one is it, and when was it delivered?",
}
Step = Callable[[tuple[Message, ...]], tuple[str, dict[str, object]]]


@cache
def emails() -> dict[str, str]:
    with (WORLD_DIR / "customers.csv").open(encoding="utf-8", newline="") as handle:
        return {row["customer_id"]: row["email"] for row in csv.DictReader(handle)}


def _fixed(name: str, args: dict[str, object]) -> Step:
    return lambda _history: (name, args)


def _refund_with_approval(appliance: Appliance, outcome: ExpectedOutcome) -> Step:
    def step(history: tuple[Message, ...]) -> tuple[str, dict[str, object]]:
        approval = None
        for turn in reversed(history):
            if turn.role == "tool" and "approval_id" in turn.text:
                approval = json.loads(turn.text).get("approval_id")
                break
        args = {"serial": appliance.serial, "amount": outcome.amount, "kind": outcome.reason}
        return "issue_refund", {**args, "approval_id": approval}

    return step


def path(facts: CaseFacts) -> list[Step]:
    email = emails()[facts.customer_id]
    steps: list[Step] = [
        _fixed("ask_customer", {"question": QUESTIONS[t]}) for t in facts.withhold if t in QUESTIONS
    ]
    steps.append(_fixed("read_past_cases", {"customer_email": email}))
    for appliance, outcome in zip(facts.appliances, facts.expected, strict=True):
        steps.extend(_appliance_steps(appliance, outcome))
    return steps


def _appliance_steps(appliance: Appliance, outcome: ExpectedOutcome) -> list[Step]:
    steps: list[Step] = []
    if appliance.order_id:
        steps.append(_fixed("lookup_order", {"order_id": appliance.order_id}))
    if appliance.identifiable:
        args: dict[str, object] = {"serial": appliance.serial}
        if appliance.source == "retailer":
            args["purchase_date"] = appliance.delivered.isoformat()
        steps.append(_fixed("check_warranty", args))
    if outcome.decision == "repair_booked":
        visit = {
            "serial": appliance.serial,
            "fault": appliance.fault,
            "time_of_day": outcome.visit_time_of_day,
        }
        steps.append(_fixed("book_service_visit", visit))
    if outcome.decision == "refund":
        if outcome.approval_needed:
            approval = {
                "serial": appliance.serial,
                "amount": outcome.amount,
                "kind": outcome.reason,
                "reason": "Policy gives this refund.",
            }
            steps.append(_fixed("request_approval", approval))
        steps.append(_refund_with_approval(appliance, outcome))
    close = {
        "serial": appliance.serial,
        "decision": outcome.decision,
        "reason": outcome.reason,
        "existing_case": outcome.existing_case,
        "reply": "Thank you for getting in touch. We have dealt with your appliance.",
    }
    steps.append(_fixed("close_case", close))
    return steps


def oracle(cases: Mapping[str, CaseFacts]) -> Callable[[GenerationRequest], MockReply]:
    """A mock `respond` function that walks each case's path, one tool call a turn."""

    def respond(request: GenerationRequest) -> MockReply:
        facts = cases[request.metadata["case_id"]]
        history = request.messages or ()
        done = sum(1 for m in history if m.role == "tool" and "not closed" not in m.text)
        steps = path(facts)
        if done >= len(steps):
            return MockReply(text="All done.")
        name, args = steps[done](history)
        call = ToolCall(call_id=f"call_{len(history)}", name=name, arguments_json=json.dumps(args))
        return MockReply(text="", tool_calls=(call,))

    return respond
