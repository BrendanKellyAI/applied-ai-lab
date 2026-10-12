"""S2 E3's claims A1 to A4, as amended in PREREGISTRATION.md, applied to agreement.json.

Run with `uv run python episodes/s2-e3-measuring/claims.py`. Reads the committed report only.
"""

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
# The pass marks, as amended before any mark or call.
A1_RIGHT_AT_LEAST = 45
A2_DECLINED_AT_LEAST = 45


def evaluate(report: dict[str, Any]) -> list[dict[str, Any]]:
    models = report["models"]
    split = report["key_split"]
    code = report["code_check_on_hand"]
    a3_tested = split["hand_marked"] > 0
    return [
        {
            "id": "A1",
            "statement": "The judge and the second model agree on the answer verdict.",
            "held": models["right"]["count"] >= A1_RIGHT_AT_LEAST,
            "detail": models["right"],
        },
        {
            "id": "A2",
            "statement": "The judge and the second model agree on declines.",
            "held": models["declined"]["count"] >= A2_DECLINED_AT_LEAST,
            "detail": models["declined"],
        },
        {
            "id": "A3",
            "statement": "Where the two models split, the judge is right at least as often.",
            "held": a3_tested and 2 * split["hand_sides_with_judge"] >= split["hand_marked"],
            "tested": a3_tested,
            "detail": split,
        },
        {
            "id": "A4",
            "statement": "The judge beats the code check on correctness.",
            "held": code["judge_matches_hand"] > code["code_matches_hand"],
            "detail": code,
        },
    ]


def main() -> None:
    report = json.loads((HERE / "judge-check" / "agreement.json").read_text(encoding="utf-8"))
    claims = evaluate(report)
    (HERE / "claims.json").write_text(
        json.dumps(claims, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    for claim in claims:
        verdict = "held" if claim["held"] else "FAILED"
        print(f"{claim['id']} {verdict}: {claim['statement']}")


if __name__ == "__main__":
    main()
