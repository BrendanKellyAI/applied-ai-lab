"""Every rule in the Season 5 policy that the Season 2 corpus also states must agree with it."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2] / "datasets"
POLICY = yaml.safe_load((ROOT / "halvard-cases" / "policy.yaml").read_text(encoding="utf-8"))
WARRANTY = (ROOT / "halvard" / "documents" / "POL-WAR@2.md").read_text(encoding="utf-8")
RETURNS = (ROOT / "halvard" / "documents" / "POL-RET@2.md").read_text(encoding="utf-8")
PRODUCTS = yaml.safe_load((ROOT / "halvard-tasks" / "routes.yaml").read_text(encoding="utf-8"))[
    "products"
]


def test_policy_lists_exactly_the_season_4_products():
    assert sorted(POLICY["products"]) == sorted(PRODUCTS)


@pytest.mark.parametrize("product", sorted(POLICY["products"]))
def test_cover_period_matches_the_corpus(product):
    months = POLICY["products"][product]["cover_months"]
    assert f"The {product} is covered for {months} months from the date of delivery." in WARRANTY


@pytest.mark.parametrize(
    ("plan", "label"),
    [("extended_care", "Extended Care"), ("extended_care_plus", "Extended Care Plus")],
)
def test_plan_extensions_match_the_corpus(plan, label):
    months = POLICY["cover"]["extensions_months"][plan]
    assert f"{label} extends the standard warranty by {months} months." in WARRANTY


def test_cosmetic_reporting_window_matches_the_corpus():
    days = POLICY["exclusions"]["cosmetic_report_days"]
    assert f"Cosmetic damage must be reported within {days} days of delivery." in WARRANTY


def test_early_fault_refund_window_matches_the_corpus():
    days = POLICY["early_fault_refund"]["within_days_of_delivery"]
    sentence = f"An appliance that develops a fault within {days} days of delivery can be returned"
    assert sentence in RETURNS


def test_cover_starts_at_delivery_as_the_corpus_says():
    assert POLICY["cover"]["starts"] == "delivery_date"
    assert "does not set the start of the main warranty period" in WARRANTY


EXCLUSION_PHRASES = sorted(v for v in POLICY["exclusions"].values() if isinstance(v, str))


@pytest.mark.parametrize("phrase", EXCLUSION_PHRASES)
def test_every_exclusion_quotes_the_corpus(phrase):
    assert phrase in WARRANTY
