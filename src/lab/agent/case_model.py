"""The shape of a Season 5 case: its facts, what the customer knows, and the expected end state.

A case's facts are drawn by code before any model call. The customer's message is written later
from `say` and `withhold`; the expected end state is computed from the facts by the policy code.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from lab.agent.policy import Decision, Exclusion, Plan, Wants

Kind = Literal[
    "routine",
    "branching",
    "missing_information",
    "policy_detail",
    "above_limit",
    "photo",
    "adversarial",
    "telemetry",
    "sequence",
    "long",
]
Split = Literal["dev", "test"]
TimeOfDay = Literal["morning", "afternoon"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ExpectedOutcome(_Frozen):
    """What must be true of one appliance after the run."""

    serial: str
    decision: Decision
    reason: str | None = None
    amount: float | None = None
    approval_needed: bool = False
    existing_case: str | None = None
    # A booked visit must be in this region, and at this time of day if the customer asked.
    visit_region: str | None = None
    visit_time_of_day: TimeOfDay | None = None


class Appliance(_Frozen):
    """One appliance in the case, with every fact the policy needs."""

    serial: str
    product: str
    source: Literal["halvard", "retailer"]
    order_id: str | None
    delivered: date
    price: float
    plan: Plan
    fault: str
    wants: Wants = "unspecified"
    safety: bool = False
    formal_complaint: bool = False
    exclusion: Exclusion | None = None
    # How an exclusion is shown: the customer's own words, or the telemetry log.
    exclusion_evidence: Literal["customer", "telemetry"] | None = None
    recalled: bool = False
    earlier_repairs_same_fault: int = 0
    open_case_ref: str | None = None
    goodwill_in_last_year: bool = False
    identifiable: bool = True
    images: tuple[str, ...] = ()
    telemetry: str | None = None


class CaseFacts(_Frozen):
    case_id: str
    split: Split
    kind: Kind
    # Finer labels for analysis: safety, complaint, pressure, duplicate, planted_image,
    # planted_log, recall, repeat_repairs, wrong_order_number, two_of_a_product, and so on.
    tags: tuple[str, ...] = ()
    customer_id: str
    customer_name: str
    region: str
    contact_preference: str | None = None
    appliances: tuple[Appliance, ...]
    # What the message must state, in plain words, and what it must leave out.
    say: tuple[str, ...]
    withhold: tuple[str, ...] = ()
    # The rule-based customer's answers to questions about withheld facts, by topic.
    answers: dict[str, str] = Field(default_factory=dict)
    # Topics the customer cannot answer ("I do not know").
    unknown: tuple[str, ...] = ()
    # A second message the customer sends after a decline, in pressure cases.
    push_back: str | None = None
    expected: tuple[ExpectedOutcome, ...]
    # Actions that must not happen, in the scorer's words.
    must_not: tuple[str, ...] = ()
    sequence_id: str | None = None
    sequence_position: int | None = None
