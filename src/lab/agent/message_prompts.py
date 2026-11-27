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
from lab.agent.policy import POLICY_PATH, cover_end, load_policy

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
    "state the one decision the policy gives, with its reason and any refund amount. The "
    "records already give each appliance's cover end date and days in or out of cover; use "
    "them as given. Reasons are codes: decline takes out_of_cover, cosmetic_late, misuse, "
    "installation, supply, maintenance, accidental_damage or commercial_use; replacement takes "
    "recall, repeat_repairs or damaged_on_arrival; refund takes early_fault or goodwill; escalate "
    "takes facts_unknown, safety_incident or formal_complaint; repair_booked and existing_case "
    "take null. Reply with one JSON object only, with no working before or after it: "
    '{"outcomes": [{"serial": "...", "decision": "repair_booked | replacement | refund | '
    'decline | escalate | existing_case", "reason": "code or null", "amount": number or null}]}'
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
            **_cover(a),
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
            "RECORDS (what the agent learns from its tools and by asking the customer, so a "
            "detail missing from the message is still known)\n" + json.dumps(records, indent=1),
            "State the decision for each appliance.",
        ]
    )


def _cover(appliance: Appliance) -> dict[str, object]:
    """The dates check_warranty returns: computed by code, as the agent's tool will."""
    policy = load_policy()
    end = cover_end(policy, appliance.product, appliance.delivered, appliance.plan)
    return {
        "cover_ends": end.isoformat(),
        "days_since_delivery": (policy.as_of - appliance.delivered).days,
        "in_cover_today": policy.as_of <= end,
        "days_out_of_cover": max((policy.as_of - end).days, 0),
    }


def _telemetry_finding(appliance: Appliance) -> str | None:
    """What a correct analysis of the attached log finds, for telemetry cases only."""
    if appliance.telemetry is None:
        return None
    if appliance.exclusion:
        return f"the log shows {appliance.exclusion}"
    return "the log shows a genuine defect"
