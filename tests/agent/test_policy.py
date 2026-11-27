"""The policy engine: each rule, the order they apply in, and the date arithmetic."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from lab.agent.policy import Claim, Outcome, add_months, cover_end, decide, load_policy

POLICY = load_policy()
AS_OF = POLICY.as_of


def _claim(**fields) -> Claim:
    # A Keel washing machine delivered a year ago: in cover (78 months), past the refund window.
    base = Claim(
        product="Keel washing machine",
        delivered=AS_OF - timedelta(days=365),
        price=610.0,
        plan="none",
        fault="leak",
    )
    return replace(base, **fields)


def _delivered_out_of_cover_by(days: int, product: str = "Brio kettle") -> date:
    """A delivery date that leaves the product's cover ended `days` days before as_of."""
    end_target = AS_OF - timedelta(days=days)
    return add_months(end_target, -POLICY.cover_months[product])


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2024, 1, 31), 1, date(2024, 2, 29)),
        (date(2026, 11, 15), 2, date(2027, 1, 15)),
        (date(2026, 3, 15), -3, date(2025, 12, 15)),
    ],
)
def test_add_months_keeps_the_day_or_clamps_it(start, months, expected):
    assert add_months(start, months) == expected


def test_plans_extend_cover_by_the_corpus_months():
    delivered = date(2020, 1, 10)
    plain = cover_end(POLICY, "Tessa dishwasher", delivered, "none")
    extended = cover_end(POLICY, "Tessa dishwasher", delivered, "extended_care")
    assert plain == date(2021, 7, 10)
    assert extended == add_months(plain, 58)


def test_a_covered_fault_books_a_repair():
    assert decide(POLICY, _claim()) == Outcome("repair_booked")


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"recalled": True}, Outcome("replacement", "recall")),
        ({"earlier_repairs_same_fault": 2}, Outcome("replacement", "repeat_repairs")),
        ({"earlier_repairs_same_fault": 1}, Outcome("repair_booked")),
        ({"exclusion": "misuse"}, Outcome("decline", "misuse")),
        ({"safety": True}, Outcome("escalate", "safety_incident")),
        ({"formal_complaint": True}, Outcome("escalate", "formal_complaint")),
        ({"identifiable": False}, Outcome("escalate", "facts_unknown")),
        ({"open_case_ref": "PC-00042"}, Outcome("existing_case", existing_case="PC-00042")),
    ],
)
def test_each_rule_gives_its_outcome(fields, expected):
    assert decide(POLICY, _claim(**fields)) == expected


def test_rules_apply_in_order():
    # A safety incident outranks everything below it, even a recall and a stated exclusion.
    claim = _claim(safety=True, recalled=True, exclusion="misuse", open_case_ref="PC-1")
    assert decide(POLICY, claim).reason == "safety_incident"
    # A formal complaint outranks a safety incident.
    assert decide(POLICY, replace(claim, formal_complaint=True)).reason == "formal_complaint"
    # An exclusion outranks a recall.
    assert decide(POLICY, _claim(exclusion="supply", recalled=True)).reason == "supply"


@pytest.mark.parametrize(
    ("days", "expected"),
    [(7, Outcome("replacement", "damaged_on_arrival")), (8, Outcome("decline", "cosmetic_late"))],
)
def test_cosmetic_damage_must_be_reported_within_seven_days(days, expected):
    claim = _claim(fault="damaged_on_arrival", cosmetic_reported_after_days=days)
    assert decide(POLICY, claim) == expected


def test_cosmetic_damage_with_no_report_date_is_late():
    assert decide(POLICY, _claim(fault="damaged_on_arrival")).reason == "cosmetic_late"


@pytest.mark.parametrize(
    ("product", "price", "approval"),
    [("Brio kettle", 45.0, False), ("Keel washing machine", 610.0, True)],
)
def test_early_fault_refund_is_full_price_and_needs_approval_above_the_limit(
    product, price, approval
):
    claim = _claim(
        product=product, price=price, wants="refund", delivered=AS_OF - timedelta(days=100)
    )
    assert decide(POLICY, claim) == Outcome(
        "refund", "early_fault", amount=price, approval_needed=approval
    )


def test_a_refund_request_after_100_days_gets_the_warranty_remedy_instead():
    claim = _claim(wants="refund", delivered=AS_OF - timedelta(days=101))
    assert decide(POLICY, claim) == Outcome("repair_booked")


def test_goodwill_is_a_quarter_of_the_price_and_always_needs_approval():
    claim = _claim(product="Brio kettle", price=45.0, delivered=_delivered_out_of_cover_by(30))
    assert decide(POLICY, claim) == Outcome(
        "refund", "goodwill", amount=11.25, approval_needed=True
    )


@pytest.mark.parametrize(
    ("days_out", "used", "expected"),
    [
        (90, False, "goodwill"),
        (91, False, "out_of_cover"),
        (10, True, "out_of_cover"),
    ],
)
def test_goodwill_window_and_once_a_year(days_out, used, expected):
    claim = _claim(
        product="Brio kettle",
        price=45.0,
        delivered=_delivered_out_of_cover_by(days_out),
        goodwill_in_last_year=used,
    )
    assert decide(POLICY, claim).reason == expected


def test_last_day_of_cover_is_still_covered():
    claim = _claim(product="Brio kettle", price=45.0, delivered=_delivered_out_of_cover_by(0))
    assert decide(POLICY, claim) == Outcome("repair_booked")
