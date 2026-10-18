"""The Halvard Home case as committed: evidence, product names, gates and totals, no dashes."""

import re
from pathlib import Path

import pytest
import yaml

from lab.strategy.case import load_case
from lab.strategy.rule import load_rule
from lab.strategy.scoring import first_pick, normalised, score, sensitivity

ROOT = Path(__file__).parents[2]
CASE = ROOT / "season3" / "case"
DASHES = re.compile("[" + "".join(map(chr, (0x2012, 0x2013, 0x2014, 0x2015, 0x2212))) + "]")


@pytest.fixture(scope="module")
def rule():
    return load_rule(CASE / "rule.yaml")


@pytest.fixture(scope="module")
def case(rule):
    return load_case(CASE, rule)


def test_every_score_cites_evidence_or_an_assumption(case):
    for scored in case.scores.values():
        for s in scored.scores.values():
            assert (s.measured is None) != (s.assumption is None)
            if s.measured is not None:
                assert (ROOT / s.measured.path).exists(), s.measured.path
                assert s.measured.figure


def test_only_c1_c2_cite_measured_accuracy(case):
    for cid, scored in case.scores.items():
        for name in ("task_fit", "error_tolerance"):
            s = scored.scores.get(name)
            if s is not None and s.measured is not None:
                assert cid in {"C1", "C2"}, (cid, name)


def test_product_names_in_the_case_exist_in_the_corpus():
    """Every mention of a product's brand name is that product's full corpus name."""
    config = yaml.safe_load((ROOT / "datasets/halvard/config.yaml").read_text("utf-8"))
    products = config["products"]
    files = [p for p in (ROOT / "season3").rglob("*") if p.suffix in {".md", ".yaml"}]
    text = chr(10).join(p.read_text("utf-8") for p in files)
    for product in products:
        brand = product.split()[0]
        for match in re.finditer(f"(?<![A-Za-z]){brand}(?![A-Za-z])", text):
            assert text.startswith(product, match.start()), text[match.start() : match.start() + 40]
    assert any(p in text for p in products)


def test_gates_redirects_and_totals(case, rule):
    rows = case.rows(rule)
    scored = {s.id: s for s in score(rows, rule)}
    assert scored["C5"].failed_gates == ("right_tool",)
    assert scored["C8"].failed_gates == ("right_tool",)
    assert scored["C5"].total is None and scored["C5"].rank is None
    assert scored["C1"].autonomy_exceeded is True
    assert scored["C2"].autonomy_exceeded is False
    c6 = case.scores["C6"].scores
    expected = sum(rule.weights[k] * c6[k].score for k in rule.weights)
    assert scored["C6"].total == pytest.approx(expected)
    assert first_pick(rows, rule, normalised(rule.weights)) == scored["C6"].id


def test_sensitivity_is_reported_for_fifteen_weightings(case, rule):
    result = sensitivity(case.rows(rule), rule)
    assert result.out_of == 15
    assert result.holds == sum(1 for w in result.alternatives if w.first_pick == result.base_pick)


def test_stop_criteria_name_the_first_pick(case, rule):
    assert case.stop_criteria is not None
    assert case.stop_criteria.candidate == first_pick(case.rows(rule), rule, rule.weights)


@pytest.mark.parametrize("folder", ["season3", "src/lab/strategy", "tests/strategy"])
def test_no_file_contains_a_dash_character(folder):
    for path in (ROOT / folder).rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yaml", ".py", ".csv", ".json"}:
            assert not DASHES.search(path.read_text("utf-8")), path
