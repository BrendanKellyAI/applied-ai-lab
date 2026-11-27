"""Prompts for writing each case's customer message, and for the blind label check.

Generator: `gemini-3.1-flash-lite` writes the message from the case's `say` and `withhold`
lists, in a persona drawn from the case ID. Label check: `claude-haiku-5-5` reads the message,
what the agent's tools would show, and the policy, without the expected outcome, and states the
decision for each appliance. Both reply with one JSON object.
"""

import hashlib
import json
import random
from pathlib import Path

from lab.agent.case_model import Appliance, CaseFacts
from lab.agent.policy import POLICY_PATH

CHANNELS = ("email", "web form", "chat window")
TONES = ("polite", "brisk", "worried", "fed up", "chatty")
HABITS = ("tidy sentences", "short lines", "a long run-on paragraph", "some typos")

GENERATOR_SYSTEM = (
    "You write realistic customer messages to Halvard Home, an invented UK appliance maker, "
    "for a test set. You are given what the message must say and what it must leave out. "
    "Write only the customer's message, in British English, as the customer would write it, "
    "in the first person. State every point you are given, in your own words; never add facts, "
    "numbers, dates or reference numbers you were not given. Never use internal labels or "
    "field names. Reply with one JSON object and nothing else: "
    '{"message": "<the customer message>"}'
)

LABELLER_SYSTEM = (
    "You check labels for a test set of warranty cases at Halvard Home, an invented appliance "
    "maker. Apply the policy exactly, in the order its rules are listed. For each appliance, "
    "state the one decision the policy gives, with its reason and any refund amount. Reply "
    "with one JSON object and nothing else: "
    '{"outcomes": [{"serial": "...", "decision": "repair_booked | replacement | refund | '
    'decline | escalate | existing_case", "reason": "... or null", "amount": number or null}]}'
)


def persona(case_id: str) -> random.Random:
    """A per case random source that depends only on the case ID, so personas are stable."""
    return random.Random(int(hashlib.sha256(case_id.encode()).hexdigest()[:12], 16))


def word_band(facts: CaseFacts) -> tuple[int, int]:
    if facts.kind == "long":
        return (140, 260)
    return (40, 120)


def generation_prompt(facts: CaseFacts) -> str:
    rng = persona(facts.case_id)
    low, high = word_band(facts)
    lines = [
        f"Channel: {rng.choice(CHANNELS)}. Tone: {rng.choice(TONES)}. "
        f"Writing habit: {rng.choice(HABITS)}.",
        f"Length: {low} to {high} words.",
        "The message must say:",
        *(f"- {point}" for point in facts.say),
    ]
    if facts.withhold:
        lines.append(
            "The message must not give: "
            + ", ".join(topic.replace("_", " ") for topic in facts.withhold)
            + ". Do not hint at them either."
        )
    if "safety" in facts.tags:
        lines.append("Describe the incident plainly enough that the hazard is clear.")
    return "\n".join(lines)


def policy_text(path: Path = POLICY_PATH) -> str:
    """The policy as the label checker sees it: the YAML without its build comments."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.lstrip().startswith("#")).strip()


def labeller_prompt(facts: CaseFacts, message: str) -> str:
    """The message, plus what the agent's tools would show about each appliance."""
    records = [
        {
            "serial": a.serial,
            "product": a.product,
            "bought_from": "Halvard Home" if a.source == "halvard" else "another shop (receipt)",
            "delivery_or_receipt_date": a.delivered.isoformat(),
            "price": a.price,
            "plan": a.plan,
            "recalled": a.recalled,
            "earlier_repairs_for_this_fault": a.earlier_repairs_same_fault,
            "open_case_for_this_fault": a.open_case_ref,
            "goodwill_refund_in_last_365_days": a.goodwill_in_last_year,
            "identifiable": a.identifiable,
            "telemetry_finding": _telemetry_finding(a),
        }
        for a in facts.appliances
    ]
    return "\n\n".join(
        [
            "POLICY\n" + policy_text(),
            "CUSTOMER MESSAGE\n" + message,
            "RECORDS (what the tools show)\n" + json.dumps(records, indent=1),
            "State the decision for each appliance.",
        ]
    )


def _telemetry_finding(appliance: Appliance) -> str | None:
    """What a correct analysis of the attached log finds, for telemetry cases only."""
    if appliance.telemetry is None:
        return None
    if appliance.exclusion:
        return f"the log shows {appliance.exclusion}"
    return "the log shows a genuine defect"
