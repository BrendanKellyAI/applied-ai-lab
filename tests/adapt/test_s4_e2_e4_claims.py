"""S4 E2 to E4 claims scripts: each pass mark is applied as claims.yaml states it."""

import copy
from pathlib import Path

from lab.experiments import load_sibling

EPISODES = Path(__file__).parents[2] / "episodes"
e2 = load_sibling(EPISODES / "s4-e2-instructions-first" / "claims.py")
e3 = load_sibling(EPISODES / "s4-e3-how-many-examples" / "claims.py")
e4 = load_sibling(EPISODES / "s4-e4-making-output-a-contract" / "claims.py")


def _held(claims: list) -> dict[str, bool]:
    return {c.id: c.held for c in claims}


def test_e2_choice_rule_breaks_ties_to_the_earlier_arm():
    analysis = {"arms": {"x": {"fully_right": {"count": 5}}, "y": {"fully_right": {"count": 5}}}}
    assert e2.choose(analysis, ["y", "x"]) == "y"


def test_e2_claims_on_the_test_analysis():
    spec = e2.load_claims_file()
    result = e2.evaluate(e2.load_analysis("test"), e2.load_analysis("dev"), spec)
    assert _held(result) == {"C1": True, "C2": True, "C3": True}


def test_e2_claims_fail_on_the_far_side():
    spec = e2.load_claims_file()
    test = copy.deepcopy(e2.load_analysis("test"))
    for arm in spec["claims"]["C1"]["arms"]:
        test["comparisons"][arm]["p_holm"] = 0.2
    test["arms"]["e2-definitions"]["safety_false_alarms"]["rate"] = 0.1
    test["arms"]["e2-definitions"]["safety_recall"]["rate"] = 0.9
    held = _held(e2.evaluate(test, e2.load_analysis("dev"), spec))
    assert held == {"C1": False, "C2": False, "C3": False}


def test_e3_claims_on_the_test_results():
    arms = ("e3-similar-8", "e3-random-8", "e3-random-8-shuffled")
    by_item = {arm: e3.fully_right_by_item(arm, "test") for arm in arms}
    assert sum(by_item["e3-similar-8"].values()) == 593
    result = e3.evaluate(e3.load_analysis("test"), by_item, e3.load_claims_file())
    assert _held(result) == {"C1": True, "C2": True, "C3": True, "C4": True}


def test_e3_claims_fail_on_the_far_side():
    ids = [f"i{n}" for n in range(100)]
    same = {i: True for i in ids}
    analysis = {
        "reference": "e3-n0",
        "arms": {
            a: {"fully_right": {"count": c}}
            for a, c in {
                "e3-n0": 50,
                "e3-random-2": 50,
                "e3-random-8": 60,
                "e3-similar-8": 60,
                "e3-random-32": 75,
            }.items()
        },
        "comparisons": {
            a: {"p_holm": 0.5}
            for a in ("e3-random-2", "e3-random-8", "e3-similar-8", "e3-random-32")
        },
    }
    by_item = {"e3-similar-8": same, "e3-random-8": same, "e3-random-8-shuffled": same}
    held = _held(e3.evaluate(analysis, by_item, e3.load_claims_file()))
    assert held == {"C1": False, "C2": False, "C3": False, "C4": False}


def test_e4_claims_on_the_test_analysis():
    result = e4.evaluate(e4.load_analysis("test"), e4.load_claims_file())
    assert _held(result) == {"C1": True, "C2": True}


def test_e4_claims_fail_on_the_far_side():
    test = copy.deepcopy(e4.load_analysis("test"))
    test["arms"]["e4-schema"]["json_valid"]["rate"] = 0.99
    test["comparisons"]["e4-schema"]["p_holm"] = 0.01
    assert _held(e4.evaluate(test, e4.load_claims_file())) == {"C1": False, "C2": False}
