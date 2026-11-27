"""The case build: reproducible, consistent with the world database, and labelled by policy."""

import shutil
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import pytest

from lab.agent.build import build_dataset, load_facts
from lab.agent.case_draw import expected_for
from lab.agent.cases import KIND_SIZES
from lab.agent.policy import load_policy
from lab.agent.world import is_recalled, load_database

REPO = Path(__file__).resolve().parents[2]
DATASET = Path("datasets") / "halvard-cases"
FACT_FILES = (
    "test",
    "dev",
    "telemetry-test",
    "telemetry-dev",
    "sequences-test",
    "sequences-dev",
    "long-test",
    "long-dev",
)
POLICY = load_policy()


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("build")
    (root / DATASET / "world").mkdir(parents=True)
    shutil.copy(REPO / DATASET / "world" / "schema.sql", root / DATASET / "world" / "schema.sql")
    build_dataset(root)
    return root


@pytest.fixture(scope="module")
def cases(built) -> dict[str, list]:
    return {
        name: load_facts(built / DATASET / "cases" / f"{name}.facts.jsonl") for name in FACT_FILES
    }


@pytest.fixture(scope="module")
def db(built):
    connection = load_database(":memory:", built / DATASET / "world")
    yield connection
    connection.close()


@pytest.mark.parametrize(
    "relative",
    [
        *(f"cases/{name}.facts.jsonl" for name in FACT_FILES),
        "world/orders.csv",
        "world/past_cases.csv",
        "world/retailer_appliances.csv",
        "images/truth.jsonl",
        "telemetry/truth.jsonl",
    ],
)
def test_build_reproduces_the_committed_files(built, relative):
    committed = (REPO / DATASET / relative).read_bytes().replace(b"\r\n", b"\n")
    assert (built / DATASET / relative).read_bytes() == committed


def test_sizes_match_the_case_plan(cases):
    for split in ("test", "dev"):
        assert Counter(c.kind for c in cases[split]) == Counter(KIND_SIZES[split])
    assert len(cases["telemetry-test"]) == 45 and len(cases["telemetry-dev"]) == 15
    for split, size in (("test", 30), ("dev", 10)):
        assert len({c.sequence_id for c in cases[f"sequences-{split}"]}) == size
        assert len(cases[f"long-{split}"]) == size


def test_sequences_carry_their_links_forward(cases):
    by_sequence: dict[str, list] = {}
    for case in cases["sequences-test"] + cases["sequences-dev"]:
        by_sequence.setdefault(case.sequence_id, []).append(case)
    for steps in by_sequence.values():
        assert 3 <= len(steps) <= 5
        assert len({c.customer_id for c in steps}) == 1
        link = steps[0].tags[0]
        decisions = [c.expected[0].decision for c in steps]
        if link == "repair_failed":
            assert decisions[:3] == ["repair_booked", "repair_booked", "replacement"]
        if link == "goodwill":
            reasons = [c.expected[0].reason for c in steps if c.expected[0].reason]
            assert reasons == ["goodwill", "out_of_cover"]
        if link == "preference":
            times = {c.expected[0].visit_time_of_day for c in steps}
            assert len(times) == 1 and None not in times


def test_long_cases_cover_several_appliances(cases):
    for case in cases["long-test"] + cases["long-dev"]:
        assert 4 <= len(case.appliances) == len(case.expected) <= 6


def test_serials_and_ids_are_unique(cases):
    every = [c for group in cases.values() for c in group]
    assert len({c.case_id for c in every}) == len(every)
    # A serial belongs to one case, or to one sequence (a repair that failed comes back).
    owners: dict[str, set[str]] = {}
    for case in every:
        for a in case.appliances:
            owners.setdefault(a.serial, set()).add(case.sequence_id or case.case_id)
    assert all(len(owner) == 1 for owner in owners.values())


def test_every_expected_outcome_is_recomputed_by_policy(cases):
    for case in (c for group in cases.values() for c in group):
        for appliance, expected in zip(case.appliances, case.expected, strict=True):
            assert expected_for(POLICY, appliance, case.region, case.contact_preference) == expected


def _one(db, query: str, *args):
    return db.execute(query, args).fetchone()


def _history_from_database(case) -> bool:
    """Later sequence cases take history from earlier cases in the sequence, not the database."""
    return case.sequence_position in (None, 1)


def test_appliance_facts_agree_with_the_world_database(cases, db):
    for case in (c for group in cases.values() for c in group):
        for a in case.appliances:
            if a.source == "halvard":
                row = _one(
                    db,
                    "SELECT customer_id, delivery_date, plan, price FROM orders WHERE serial = ?",
                    a.serial,
                )
                assert row == (case.customer_id, a.delivered.isoformat(), a.plan, a.price)
            else:
                row = _one(
                    db,
                    "SELECT customer_id, receipt_date FROM retailer_appliances WHERE serial = ?",
                    a.serial,
                )
                assert row == (case.customer_id, a.delivered.isoformat())
            assert a.recalled == is_recalled(a.product, a.serial)
            repairs = _one(
                db,
                "SELECT COUNT(*) FROM past_cases WHERE serial = ? AND fault = ?"
                " AND status = 'closed'"
                " AND outcome = 'repair_booked'",
                a.serial,
                a.fault,
            )[0]
            if _history_from_database(case):
                assert repairs == a.earlier_repairs_same_fault, case.case_id


def test_open_cases_and_goodwill_history_are_planted(cases, db):
    for case in (c for group in cases.values() for c in group):
        for a in case.appliances:
            if a.open_case_ref:
                assert _one(
                    db, "SELECT serial, status FROM past_cases WHERE case_ref = ?", a.open_case_ref
                ) == (
                    a.serial,
                    "open",
                )
            since = (POLICY.as_of - timedelta(days=POLICY.goodwill_once_days)).isoformat()
            goodwill = _one(
                db,
                "SELECT COUNT(*) FROM past_cases WHERE customer_id = ?"
                " AND goodwill_amount IS NOT NULL"
                " AND opened >= ?",
                case.customer_id,
                since,
            )[0]
            if _history_from_database(case):
                assert bool(goodwill) == a.goodwill_in_last_year, case.case_id


def test_withheld_facts_are_not_in_what_the_message_says(cases):
    for case in (c for group in cases.values() for c in group):
        said = " ".join(case.say)
        for a in case.appliances:
            if "order_id" in case.withhold:
                assert str(a.order_id) not in said
            if "serial" in case.withhold:
                assert a.serial not in said
            if "product" in case.withhold:
                assert a.product not in said
        for topic in case.withhold:
            assert topic in case.answers or topic in case.unknown, case.case_id


def test_files_named_by_cases_exist(built, cases):
    for case in (c for group in cases.values() for c in group):
        for a in case.appliances:
            for path in (*a.images, *([a.telemetry] if a.telemetry else [])):
                assert (built / path).is_file(), path


def test_dates_are_before_as_of_and_slots_after(cases, db):
    for case in (c for group in cases.values() for c in group):
        assert all(a.delivered <= POLICY.as_of for a in case.appliances)
    first_slot = _one(db, "SELECT MIN(starts) FROM service_slots")[0]
    assert date.fromisoformat(first_slot[:10]) > POLICY.as_of


def test_no_dash_characters_in_generated_text(built):
    for path in (built / DATASET).rglob("*"):
        if path.suffix in (".jsonl", ".csv", ".log", ".txt"):
            text = path.read_text(encoding="utf-8")
            assert "–" not in text and "—" not in text, path
