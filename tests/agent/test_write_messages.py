"""The paid case data step, run end to end on the mock provider: no network, no spend."""

import json
import shutil
from pathlib import Path

import pytest

from lab.agent.build import load_facts
from lab.agent.data_estimate import all_cases, estimate, format_estimate
from lab.agent.data_run import BudgetRefused, check_budget, run_case_data
from lab.agent.message_prompts import generation_prompt, labeller_prompt, persona
from lab.agent.write_messages import (
    clean_message,
    label_disagreements,
    message_problems,
    parse_json,
)
from lab.prices import ModelPrice, PricesFile
from lab.providers.base import GenerationRequest
from lab.providers.mock import MockProvider

REPO = Path(__file__).resolve().parents[2]
CASES = REPO / "datasets" / "halvard-cases" / "cases"
TEST = load_facts(CASES / "test.facts.jsonl")
BY_ID = {c.case_id: c for c in TEST}
PRICES = PricesFile(
    prices={
        "google": {"gemini-3.1-flash-lite": ModelPrice(input=0.25, output=1.5)},
        "anthropic": {"claude-haiku-5-5": ModelPrice(input=0.1, output=0.5)},
    },
    budgets={"s5-case-data": 5.0},
)


def _message_for(case_id: str) -> str:
    facts = BY_ID[case_id]
    return "Hello. " + " ".join(facts.say) + " Thanks."


def _outcomes(case_id: str, *, wrong: bool = False) -> str:
    facts = BY_ID[case_id]
    outcomes = [
        {
            "serial": o.serial,
            "decision": "decline" if wrong else o.decision,
            "reason": o.reason,
            "amount": o.amount,
        }
        for o in facts.expected
    ]
    return json.dumps({"outcomes": outcomes})


def _mock(stubborn: str, leaky: str) -> MockProvider:
    def respond(request: GenerationRequest) -> str:
        case_id = request.metadata["case_id"]
        if request.metadata["stage"] == "message":
            message = _message_for(case_id)
            if case_id == leaky and "attempt 2" not in request.prompt:
                message += f" Serial {BY_ID[case_id].appliances[0].serial}."
            return "```json\n" + json.dumps({"message": message}) + "\n```"
        return _outcomes(case_id, wrong=case_id == stubborn)

    return MockProvider(respond=respond, supported_reasoning=("off", "minimal"))


@pytest.fixture
def small_dataset(tmp_path) -> Path:
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()
    picked = [c for c in TEST if c.kind in ("routine", "policy_detail")][:4]
    with (cases_dir / "test.facts.jsonl").open("w", encoding="utf-8") as handle:
        for case in picked:
            handle.write(case.model_dump_json() + "\n")
    return cases_dir


def test_end_to_end_accepts_retries_and_discards(small_dataset, tmp_path):
    ids = [c.case_id for c in load_facts(small_dataset / "test.facts.jsonl")]
    stubborn, leaky = ids[0], ids[1]
    mock = _mock(stubborn, leaky)
    log = run_case_data(
        cases_dir=small_dataset,
        review_path=tmp_path / "review.md",
        prices=PRICES,
        providers={"google": mock, "anthropic": mock},
        cache_dir=tmp_path / "cache",
    )
    assert log["cases_written"] == {"test": 3}
    assert list(log["discarded_cases"]) == [stubborn]
    assert leaky in log["failed_checks_fixed_by_a_retry"]
    written = [json.loads(line) for line in (small_dataset / "test.jsonl").read_text().splitlines()]
    assert {row["case_id"] for row in written} == set(ids) - {stubborn}
    assert all(row["message"].startswith("Hello.") for row in written)
    review = (tmp_path / "review.md").read_text(encoding="utf-8")
    assert review.count("\n## ") == 3


def test_a_rerun_is_served_from_the_cache(small_dataset, tmp_path):
    mock = _mock("none", "none")
    kwargs = {
        "cases_dir": small_dataset,
        "review_path": tmp_path / "review.md",
        "prices": PRICES,
        "providers": {"google": mock, "anthropic": mock},
        "cache_dir": tmp_path / "cache",
    }
    run_case_data(**kwargs)
    made = len(mock.calls)
    shutil.rmtree(tmp_path / "cache" / "s5-case-data")
    run_case_data(**kwargs)
    assert len(mock.calls) == made


@pytest.mark.parametrize(
    "prices",
    [
        None,
        PRICES.model_copy(update={"budgets": {}}),
        PRICES.model_copy(update={"budgets": {"s5-case-data": 0.01}}),
    ],
)
def test_budget_is_required_and_must_cover_the_ceiling(prices):
    with pytest.raises(BudgetRefused):
        check_budget(prices, 0.5)


def test_code_checks_catch_leaks_and_missing_facts():
    case = next(c for c in TEST if "no_product" in c.tags)
    named = f"My {case.appliances[0].product} broke. " + "word " * 40
    assert any("named but withheld" in p for p in message_problems(case, named))
    routine = next(c for c in TEST if c.kind == "routine")
    message = "My appliance broke. " + "word " * 40
    problems = message_problems(routine, message)
    assert any("missing" in p for p in problems) and any("not named" in p for p in problems)
    assert any("outside" in p for p in message_problems(routine, "too short"))


def test_label_comparison_needs_decision_reason_and_amount():
    case = next(c for c in TEST if c.expected[0].amount is not None)
    good = json.loads(_outcomes(case.case_id))
    assert label_disagreements(case, good) == []
    wrong_amount = {"outcomes": [{**good["outcomes"][0], "amount": 1.0}]}
    assert label_disagreements(case, wrong_amount)
    assert label_disagreements(case, {"outcomes": []})
    assert label_disagreements(case, {"nothing": 1}) == ["no outcomes list"]


def test_reasons_are_compared_loosely():
    case = next(c for c in TEST if c.expected[0].reason == "out_of_cover")
    reply = {
        "outcomes": [
            {"serial": case.expected[0].serial, "decision": "Decline", "reason": "Out of cover"}
        ]
    }
    assert label_disagreements(case, reply) == []


def test_helpers():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(ValueError):
        parse_json("[1]")
    assert clean_message("one — two – three ") == "one ,  two - three"
    assert persona("T-001").random() == persona("T-001").random()


def test_prompts_carry_the_brief_and_the_records():
    case = next(c for c in TEST if c.withhold)
    prompt = generation_prompt(case)
    assert all(point in prompt for point in case.say) and "must not give" in prompt
    label = labeller_prompt(case, "my message")
    assert "my message" in label and case.appliances[0].serial in label and "expected" not in label


def test_estimate_covers_every_case():
    cases = all_cases(CASES)
    stages = estimate(cases)
    assert [s.calls for s in stages] == [round(len(cases) * 1.3)] * 2
    assert "Cost, expected" in format_estimate(stages, PRICES)
    assert "price is missing" in format_estimate(stages, None)
