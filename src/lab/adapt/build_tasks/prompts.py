"""Prompts for the Task A generator and the blind labeller. Both reply with one JSON object."""

import json

from lab.adapt.build_tasks.seeds import PLAIN, SAFETY, Seed
from lab.adapt.definitions import Definitions

GENERATOR_SYSTEM = (
    "You write realistic customer messages to Halvard Home, an invented UK appliance maker, "
    "for a test set. You are given what the message must be about. Write only the customer's "
    "message, in British English, as the customer would write it. Never use the internal "
    "field names or labels you are given. Reply with one JSON object and nothing else: "
    '{"message": "<the customer message>"}'
)

KIND_BRIEFS = {
    PLAIN: "",
    SAFETY: "The customer describes a real safety incident; make the hazard clear.",
    "played_down_safety": (
        "The customer describes a real safety incident but plays it down, as if it were minor "
        "(for example 'it gave me a little tingle, probably nothing')."
    ),
    "harmless_safety_word": (
        "Use a heat, fire, burning or smoke word harmlessly, with no incident (for example a hob "
        "that 'gets red hot' as it should, or 'the new dryer is on fire' meaning it is great)."
    ),
    "two_products": "Also mention another Halvard product in passing; the request is not about it.",
    "angry_not_complaint": (
        "The customer is angry and blunt, but asks for the request below, not a formal complaint "
        "or escalation."
    ),
    "unknown_product": "The message is about an appliance Halvard Home does not sell.",
}

ROUTE_BRIEFS = {
    "warranty_claim": "wants the fault repaired or the appliance replaced under its warranty",
    "return_refund": "wants to send the appliance back, cancel the order, or get money back",
    "delivery": "asks about an order that has not arrived yet (date, slot, tracking or access)",
    "servicing_booking": "wants to book or move a routine service, with nothing wrong with it",
    "spare_part": "wants to buy or identify a spare part, filter or accessory to fit themselves",
    "how_to_use": "asks how to set up, use, clean or understand the appliance",
    "complaint": (
        "makes a formal complaint about how Halvard Home has treated them, and asks for it to "
        "be escalated"
    ),
    "other": "asks about something Halvard Home does not deal with as a support request",
}


def generation_prompt(seed: Seed, definitions: Definitions) -> str:
    label = seed.label
    lines = [
        f"Channel: {seed.channel}. Tone: {seed.tone}. Writing habit: {seed.habit}.",
        f"The customer's first name is {seed.name}; use it only if the channel suits it.",
        f"Length: {seed.length[0]} to {seed.length[1]} words.",
        f"The customer {ROUTE_BRIEFS[label.route]}.",
    ]
    if label.product is not None:
        lines.append(f"The appliance is their Halvard {label.product}; name it.")
    elif seed.kind == "unknown_product":
        lines.append(f"The appliance is a {seed.also_named}; name it.")
    else:
        lines.append("Do not name any appliance.")
    if seed.kind == "two_products" and seed.also_named:
        lines.append(f"The other product to mention in passing: Halvard {seed.also_named}.")
    if label.fault is not None:
        lines.append(f"The problem they describe: {definitions.faults[label.fault]}")
        lines.append("Describe only this one problem, and no other fault or hazard.")
    else:
        lines.append("They describe no fault with the appliance.")
    if KIND_BRIEFS[seed.kind]:
        lines.append(KIND_BRIEFS[seed.kind])
    return "\n".join(lines)


def labeller_system(definitions: Definitions) -> str:
    """The labeller sees the definitions only: never the seed or the intended label."""
    spec = {
        "routes": {name: route.definition for name, route in definitions.routes.items()},
        "precedence": list(definitions.precedence),
        "products": list(definitions.products),
        "product_rule": definitions.product_rule,
        "faults": definitions.faults,
        "fault_rule": definitions.fault_rule,
        "safety": definitions.safety.definition,
    }
    return (
        "You label customer messages to Halvard Home, an invented UK appliance maker, using "
        "these definitions:\n"
        + json.dumps(spec, indent=2, ensure_ascii=False)
        + "\n\nDo not explain your reasoning. Reply with one JSON object and nothing else: "
        '{"route": <route>, "safety": <true or false>, "product": <product or null>, '
        '"fault": <fault or null>}'
    )


def labeller_prompt(message: str) -> str:
    return f"Customer message:\n{message}"
