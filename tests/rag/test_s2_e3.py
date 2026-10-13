import json
from pathlib import Path

from lab.experiments import load_sibling

E3 = Path(__file__).parents[2] / "episodes" / "s2-e3-measuring"


def test_committed_claims_match_the_committed_report():
    claims = load_sibling(E3 / "claims.py")
    report = json.loads((E3 / "judge-check" / "agreement.json").read_text(encoding="utf-8"))
    committed = json.loads((E3 / "claims.json").read_text(encoding="utf-8"))

    assert claims.evaluate(report) == committed
    assert [c["held"] for c in committed] == [False, True, True, False]


def test_a3_is_untested_when_no_marked_item_splits():
    claims = load_sibling(E3 / "claims.py")
    report = {
        "models": {"right": {"count": 50}, "declined": {"count": 50}},
        "key_split": {"hand_marked": 0, "hand_sides_with_judge": 0},
        "code_check_on_hand": {"judge_matches_hand": 1, "code_matches_hand": 0},
    }
    a3 = claims.evaluate(report)[2]

    assert a3["tested"] is False and a3["held"] is False
