"""The agent's tool definitions: names, two description styles (E3) and argument schemas.

`clear` descriptions say when to use the tool, what it needs and what it returns; `terse` ones
are a few words. Schemas come `strict` (every field listed as required, optional ones nullable,
no extra fields, as OpenAI strict mode needs) or `loose` (only the truly required fields).
"""

from dataclasses import dataclass
from typing import Literal

from lab.providers.messages import ToolSpec

DescriptionStyle = Literal["clear", "terse"]
FAULTS = (
    "no_power", "leak", "noise", "not_heating", "not_cooling", "error_code",
    "damaged_on_arrival", "connectivity", "door_or_lid", "burning_or_smoke",
    "electric_shock", "poor_performance",
)  # fmt: skip
DECISIONS = ("repair_booked", "replacement", "refund", "decline", "escalate", "existing_case")


@dataclass(frozen=True)
class Field:
    name: str
    kind: str
    description: str
    required: bool = True
    enum: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ToolDef:
    name: str
    terse: str
    clear: str
    fields: tuple[Field, ...]
    writes: bool = False


TOOLS: tuple[ToolDef, ...] = (
    ToolDef(
        "lookup_order",
        "Look up orders.",
        "Find Halvard Home orders. Give an order number, or the customer's email address (and "
        "optionally a product) to list that customer's orders. Returns each order's number, "
        "product, serial number, delivery date, plan, price and the email of the customer who "
        "owns it. Appliances bought from another "
        "shop have no order; use check_warranty with their serial number instead.",
        (
            Field("order_id", "string", "An order number such as H-101234.", required=False),
            Field("customer_email", "string", "The customer's email address.", required=False),
            Field(
                "product", "string", "A Halvard product name, to narrow the list.", required=False
            ),
        ),
    ),
    ToolDef(
        "check_warranty",
        "Check warranty.",
        "Check an appliance's warranty cover by serial number. Returns the product, the delivery "
        "date, the plan, the date cover ends, whether it is in cover today, days since delivery, "
        "days out of cover, and whether the serial is in a recall. For an appliance bought from "
        "another shop, also give the purchase date from the receipt (YYYY-MM-DD).",
        (
            Field("serial", "string", "The serial number, such as KW61-48213."),
            Field(
                "purchase_date",
                "string",
                "Receipt date, for appliances bought elsewhere.",
                required=False,
            ),
        ),
    ),
    ToolDef(
        "search_knowledge_base",
        "Search help articles.",
        "Search Halvard Home's help articles and policy documents. Use it for product advice or "
        "background. The warranty and refund policy in your instructions always takes priority "
        "over an article. Returns up to five passages with their document names.",
        (Field("query", "string", "What to search for, in plain words."),),
    ),
    ToolDef(
        "read_past_cases",
        "Read past cases.",
        "Read a customer's earlier support cases, open and closed, with how each ended. Use it to "
        "find an open case for the same fault, earlier repairs, or an earlier goodwill refund.",
        (Field("customer_email", "string", "The customer's email address."),),
    ),
    ToolDef(
        "book_service_visit",
        "Book a visit.",
        "Book an engineer visit to repair an appliance under the warranty. Books the first free "
        "slot in the customer's region, at the time of day they asked for if they did. Returns "
        "the visit, its slot and start time. Book once per appliance.",
        (
            Field("serial", "string", "The appliance's serial number."),
            Field("fault", "string", "The fault to repair.", enum=FAULTS),
            Field(
                "time_of_day",
                "string",
                "The customer's preference, if any.",
                required=False,
                enum=("morning", "afternoon"),
            ),
        ),
        writes=True,
    ),
    ToolDef(
        "issue_refund",
        "Issue a refund.",
        "Refund money for an appliance. kind is early_fault (full price, fault within 100 days "
        "of delivery) or goodwill. A refund above GBP 250, and every goodwill refund, needs an "
        "approval_id from request_approval first. Returns the refund record.",
        (
            Field("serial", "string", "The appliance's serial number."),
            Field("amount", "number", "The amount in GBP."),
            Field("kind", "string", "Why the refund is due.", enum=("early_fault", "goodwill")),
            Field(
                "approval_id",
                "string",
                "From request_approval, when one is needed.",
                required=False,
            ),
        ),
        writes=True,
    ),
    ToolDef(
        "ask_customer",
        "Ask the customer.",
        "Ask the customer a question, for a detail their message did not give (an order "
        "number, which appliance, the fault, a purchase date, a serial number). Returns their "
        "reply. Ask one clear question at a time.",
        (Field("question", "string", "The question, as you would write it to the customer."),),
    ),
    ToolDef(
        "request_approval",
        "Ask for approval.",
        "Ask a supervisor to approve a refund before issuing it. Needed for a refund above GBP "
        "250 and for every goodwill refund. Returns an approval_id and whether it was granted.",
        (
            Field("serial", "string", "The appliance's serial number."),
            Field("amount", "number", "The refund amount in GBP."),
            Field("kind", "string", "The refund kind.", enum=("early_fault", "goodwill")),
            Field("reason", "string", "One sentence on why the refund is due."),
        ),
    ),
    ToolDef(
        "close_case",
        "Close the case.",
        "Record the final decision for one appliance and the reply to the customer. Call it once "
        "per appliance, after any booking or refund. decision replacement or escalate records "
        "that action. reason is the policy's reason code; existing_case names an open case. If "
        "the appliance cannot be identified, escalate with serial 'unknown'.",
        (
            Field("serial", "string", "The appliance's serial number, or 'unknown'."),
            Field("decision", "string", "The decision the policy gives.", enum=DECISIONS),
            Field(
                "reason",
                "string",
                "The policy reason code, if the decision has one.",
                required=False,
            ),
            Field(
                "existing_case",
                "string",
                "The open case reference, for existing_case.",
                required=False,
            ),
            Field("reply", "string", "The reply to the customer."),
        ),
        writes=True,
    ),
)
BY_NAME = {tool.name: tool for tool in TOOLS}


def _property(field: Field, strict: bool) -> dict[str, object]:
    kind: object = field.kind if (field.required or not strict) else [field.kind, "null"]
    prop: dict[str, object] = {"type": kind, "description": field.description}
    if field.enum:
        prop["enum"] = [*field.enum, *([None] if strict and not field.required else [])]
    return prop


def schema(tool: ToolDef, *, strict: bool) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {f.name: _property(f, strict) for f in tool.fields},
        "required": [f.name for f in tool.fields if strict or f.required],
        "additionalProperties": False,
    }


def tool_specs(
    names: tuple[str, ...], *, style: DescriptionStyle, strict: bool
) -> tuple[ToolSpec, ...]:
    return tuple(
        ToolSpec(
            name=BY_NAME[name].name,
            description=getattr(BY_NAME[name], style),
            parameters=schema(BY_NAME[name], strict=strict),
            strict=strict,
        )
        for name in names
    )
