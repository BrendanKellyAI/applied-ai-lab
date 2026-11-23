"""The prompts each arm sends, built from the frozen definitions and style guide.

Every instruction level adds to the one before it, so an arm's prompt is the previous arm's
prompt plus one named change, which the deck quotes (E2, E7). Worked examples go in the system
prompt, after the instructions: for a fixed set, that prefix is the same on every call and the
provider can cache it.
"""

import json
from collections.abc import Sequence

from lab.adapt.build_tasks.prompts_b import NOT_FOUND_ANSWER
from lab.adapt.definitions import Definitions, Label
from lab.adapt.items import ReplyItem, TriageItem
from lab.adapt.style import Source

# The E2 "when unsure" rule (invented, fixed before any call).
UNSURE_RULE = (
    "When unsure: set safety to true if the message could describe fire, smoke, burning, "
    "sparks, scorching, an electric shock or an injury, even if the customer plays it down; "
    "set product to null unless one Halvard product is clearly what the request is about; set "
    "fault to null unless the customer describes a fault; and choose the route by the "
    "precedence rules, not by the customer's tone."
)
TRIAGE_SHORT = "Triage this Halvard Home customer message as JSON."
REPLY_SHORT = "Write the Halvard Home reply."


def _json_shape(definitions: Definitions) -> str:
    return (
        "Reply with one JSON object and nothing else: "
        f'{{"route": one of {json.dumps(list(definitions.routes))}, '
        '"safety": true or false, '
        f'"product": one of {json.dumps(list(definitions.products))} or null, '
        f'"fault": one of {json.dumps(list(definitions.faults))} or null}}'
    )


def triage_system(level: str, definitions: Definitions) -> str:
    """The system prompt for a Task A instruction level, before any examples."""
    if level == "short":
        return TRIAGE_SHORT
    parts = [
        "Triage this customer message to Halvard Home, a UK appliance maker. "
        + _json_shape(definitions)
    ]
    if level in ("definitions", "policy", "unsure"):
        parts.append(
            "Definitions:\n"
            + json.dumps(
                {
                    "routes": {k: r.definition for k, r in definitions.routes.items()},
                    "faults": definitions.faults,
                    "safety": definitions.safety.definition,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    if level in ("policy", "unsure"):
        parts.append(
            "Routing policy, when a message fits more than one route (the first rule that "
            "applies wins):\n"
            + "\n".join(f"- {rule}" for rule in definitions.precedence)
            + f"\nProduct: {definitions.product_rule}\nFault: {definitions.fault_rule}"
        )
    if level == "unsure":
        parts.append(UNSURE_RULE)
    return "\n\n".join(parts)


def triage_prompt(item: TriageItem) -> str:
    return f"Customer message:\n{item.message}"


def label_json(label: Label) -> str:
    return json.dumps(label.model_dump(), ensure_ascii=False)


def triage_examples(examples: Sequence[TriageItem]) -> str:
    blocks = [f"{triage_prompt(e)}\nJSON: {label_json(e.label)}" for e in examples]
    return "Examples:\n\n" + "\n\n".join(blocks)


def with_examples(system: str, examples: str | None) -> str:
    return system if not examples else f"{system}\n\n{examples}"


def reply_system(level: str, style_guide: str) -> str:
    if level == "short":
        return REPLY_SHORT
    base = (
        "You write replies for Halvard Home, a UK appliance maker, to send to a customer. Use "
        "the answer given, which is correct. Reply with the reply text only."
    )
    if level == "one_line":
        return base
    return f"{base} Follow this house style guide exactly.\n\n{style_guide}"


def where(source: Source) -> str:
    if source.kind == "policy":
        return f'{source.name} policy, section "{source.section}"'
    if source.kind == "article":
        return f'help article "{source.name}"'
    return "none: the answer is not in Halvard Home's policies or help articles"


def reply_prompt(item: ReplyItem) -> str:
    answer = NOT_FOUND_ANSWER if item.kind == "not_found" else item.answer
    return f"Customer question: {item.question}\nAnswer: {answer}\nSource: {where(item.source_ref)}"


def reply_examples(examples: Sequence[ReplyItem]) -> str:
    blocks = [f"{reply_prompt(e)}\nReply:\n{e.target_reply}" for e in examples]
    return "Examples:\n\n" + "\n\n---\n\n".join(blocks)
