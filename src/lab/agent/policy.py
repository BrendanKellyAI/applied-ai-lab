"""The Halvard warranty and refund rules, and the expected outcome of one appliance's claim.

Every expected end state in `datasets/halvard-cases` is computed here from `policy.yaml` and a
claim's facts, so labels are right by construction. The rule-based approver uses the same code.
All invented; see policy.yaml for which rules also appear in the Season 2 corpus.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any, Literal

import yaml

POLICY_PATH = Path(__file__).resolve().parents[3] / "datasets" / "halvard-cases" / "policy.yaml"

Decision = Literal["repair_booked", "replacement", "refund", "decline", "escalate", "existing_case"]
Plan = Literal["none", "extended_care", "extended_care_plus"]
Exclusion = Literal[
    "misuse", "installation", "supply", "maintenance", "accidental_damage", "commercial_use"
]
Wants = Literal["repair", "refund", "unspecified"]


@dataclass(frozen=True)
class Policy:
    as_of: date
    cover_months: dict[str, int]
    prices: dict[str, float]
    lines: dict[str, str]
    plan_months: dict[str, int]
    cosmetic_report_days: int
    early_refund_days: int
    replacement_after_repairs: int
    goodwill_max_days: int
    goodwill_share: float
    goodwill_once_days: int
    approval_limit: float
    goodwill_needs_approval: bool


def _load(raw: dict[str, Any]) -> Policy:
    products = raw["products"]
    return Policy(
        as_of=date.fromisoformat(str(raw["as_of"])),
        cover_months={name: spec["cover_months"] for name, spec in products.items()},
        prices={name: float(spec["price"]) for name, spec in products.items()},
        lines={name: spec["line"] for name, spec in products.items()},
        plan_months={"none": 0, **raw["cover"]["extensions_months"]},
        cosmetic_report_days=raw["exclusions"]["cosmetic_report_days"],
        early_refund_days=raw["early_fault_refund"]["within_days_of_delivery"],
        replacement_after_repairs=raw["remedies"]["replacement_after_repeat_repairs"],
        goodwill_max_days=raw["goodwill"]["max_days_out_of_cover"],
        goodwill_share=float(raw["goodwill"]["share_of_price"]),
        goodwill_once_days=raw["goodwill"]["once_per_customer_days"],
        approval_limit=float(raw["refunds"]["approval_limit"]),
        goodwill_needs_approval=bool(raw["refunds"]["goodwill_needs_approval"]),
    )


@cache
def load_policy(path: Path = POLICY_PATH) -> Policy:
    return _load(yaml.safe_load(path.read_text(encoding="utf-8")))


def add_months(start: date, months: int) -> date:
    """The same day `months` later, or the month's last day if it is shorter."""
    month_index = start.month - 1 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def cover_end(policy: Policy, product: str, delivered: date, plan: Plan) -> date:
    """The last day of cover: delivery plus the product's months plus any plan's months."""
    return add_months(delivered, policy.cover_months[product] + policy.plan_months[plan])


@dataclass(frozen=True)
class Claim:
    """What is true about one appliance's claim, whether or not the customer has said it yet."""

    product: str
    delivered: date
    price: float
    plan: Plan
    fault: str
    wants: Wants = "unspecified"
    safety: bool = False
    formal_complaint: bool = False
    exclusion: Exclusion | None = None
    # Days from delivery to the customer first reporting cosmetic damage, for that fault only.
    cosmetic_reported_after_days: int | None = None
    recalled: bool = False
    earlier_repairs_same_fault: int = 0
    open_case_ref: str | None = None
    goodwill_in_last_year: bool = False
    # False when the appliance cannot be identified from records, images or the customer.
    identifiable: bool = True


@dataclass(frozen=True)
class Outcome:
    decision: Decision
    reason: str | None = None
    amount: float | None = None
    approval_needed: bool = False
    existing_case: str | None = None


def decide(policy: Policy, claim: Claim) -> Outcome:
    """The one outcome policy.yaml allows, checked in a fixed order so every claim has one."""
    for rule in (_gatekeeping, _cosmetic, _excluded, _early_refund, _in_cover):
        outcome = rule(policy, claim)
        if outcome is not None:
            return outcome
    return _out_of_cover(policy, claim)


def _gatekeeping(policy: Policy, claim: Claim) -> Outcome | None:
    if claim.formal_complaint:
        return Outcome("escalate", "formal_complaint")
    if claim.safety:
        return Outcome("escalate", "safety_incident")
    if claim.open_case_ref is not None:
        return Outcome("existing_case", existing_case=claim.open_case_ref)
    if not claim.identifiable:
        return Outcome("escalate", "facts_unknown")
    return None


def _cosmetic(policy: Policy, claim: Claim) -> Outcome | None:
    if claim.fault != "damaged_on_arrival":
        return None
    days = claim.cosmetic_reported_after_days
    if days is None or days > policy.cosmetic_report_days:
        return Outcome("decline", "cosmetic_late")
    return Outcome("replacement", "damaged_on_arrival")


def _excluded(policy: Policy, claim: Claim) -> Outcome | None:
    return Outcome("decline", claim.exclusion) if claim.exclusion is not None else None


def days_since_delivery(policy: Policy, claim: Claim) -> int:
    return (policy.as_of - claim.delivered).days


def _early_refund(policy: Policy, claim: Claim) -> Outcome | None:
    if claim.wants != "refund" or days_since_delivery(policy, claim) > policy.early_refund_days:
        return None
    return Outcome(
        "refund",
        "early_fault",
        amount=round(claim.price, 2),
        approval_needed=claim.price > policy.approval_limit,
    )


def _in_cover(policy: Policy, claim: Claim) -> Outcome | None:
    if policy.as_of > cover_end(policy, claim.product, claim.delivered, claim.plan):
        return None
    if claim.recalled:
        return Outcome("replacement", "recall")
    if claim.earlier_repairs_same_fault >= policy.replacement_after_repairs:
        return Outcome("replacement", "repeat_repairs")
    return Outcome("repair_booked")


def days_out_of_cover(policy: Policy, claim: Claim) -> int:
    end = cover_end(policy, claim.product, claim.delivered, claim.plan)
    return (policy.as_of - end).days


def _out_of_cover(policy: Policy, claim: Claim) -> Outcome:
    if days_out_of_cover(policy, claim) <= policy.goodwill_max_days and not (
        claim.goodwill_in_last_year
    ):
        amount = round(claim.price * policy.goodwill_share, 2)
        return Outcome(
            "refund",
            "goodwill",
            amount=amount,
            approval_needed=policy.goodwill_needs_approval or amount > policy.approval_limit,
        )
    return Outcome("decline", "out_of_cover")
