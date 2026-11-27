"""After the messages are written: the case files, the build log and Brendan's review list."""

import json
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

from lab.agent.case_model import Appliance, CaseFacts
from lab.agent.write_messages import WriteReport

REVIEW_SIZE = 30
REVIEW_SEED = 30


def write_case_files(
    facts_files: dict[str, list[CaseFacts]], report: WriteReport, cases_dir: Path
) -> dict[str, int]:
    """One `<name>.jsonl` per facts file, holding only accepted cases, each with its message."""
    written = {}
    for name, cases in facts_files.items():
        rows = [
            {**case.model_dump(mode="json"), **report.accepted[case.case_id]}
            for case in cases
            if case.case_id in report.accepted
        ]
        path = cases_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        written[name] = len(rows)
    return written


def build_log(
    facts_files: dict[str, list[CaseFacts]], report: WriteReport, written: dict[str, int]
) -> dict[str, object]:
    kinds = {c.case_id: c.kind for cases in facts_files.values() for c in cases}
    return {
        "cases_written": written,
        "discarded": len(report.discarded),
        "discarded_by_kind": dict(Counter(kinds[c] for c in report.discarded)),
        "discarded_cases": {c: report.problems.get(c, []) for c in report.discarded},
        "accepted_on_attempt": dict(Counter(str(v["attempt"]) for v in report.accepted.values())),
        "failed_checks_fixed_by_a_retry": {
            c: p for c, p in report.problems.items() if c in report.accepted
        },
    }


def review_list(
    cases: Sequence[CaseFacts], accepted: dict[str, dict[str, object]]
) -> list[CaseFacts]:
    """Thirty accepted test cases, spread over the kinds as evenly as thirty allows."""
    by_kind: dict[str, list[CaseFacts]] = defaultdict(list)
    for case in cases:
        if case.case_id in accepted:
            by_kind[case.kind].append(case)
    rng = random.Random(REVIEW_SEED)
    kinds = sorted(by_kind)
    picked: list[CaseFacts] = []
    shares = {k: REVIEW_SIZE // len(kinds) for k in kinds}
    for kind in sorted(kinds, key=lambda k: -len(by_kind[k]))[: REVIEW_SIZE % len(kinds)]:
        shares[kind] += 1
    for kind in kinds:
        picked.extend(rng.sample(by_kind[kind], min(shares[kind], len(by_kind[kind]))))
    return sorted(picked, key=lambda c: c.case_id)


def review_markdown(picked: Sequence[CaseFacts], accepted: dict[str, dict[str, object]]) -> str:
    lines = [
        "# Season 5 case check: 30 test cases for Brendan",
        "",
        "Chosen by code (`lab.agent.finalise.review_list`, seed 30) across the case kinds. For",
        "each, check that the message reads like a real customer, states what the brief says,",
        "and that the expected outcome is what the policy gives. Mark any you disagree with.",
        "",
    ]
    for case in picked:
        lines += [
            f"## {case.case_id} ({case.kind}{', ' + ', '.join(case.tags) if case.tags else ''})",
            "",
        ]
        lines += ["> " + line for line in str(accepted[case.case_id]["message"]).splitlines()]
        lines.append("")
        for appliance, outcome in zip(case.appliances, case.expected, strict=True):
            detail = ", ".join(
                part
                for part in (
                    outcome.reason,
                    f"GBP {outcome.amount:.2f}" if outcome.amount is not None else None,
                    "needs approval" if outcome.approval_needed else None,
                    outcome.existing_case,
                    f"{outcome.visit_time_of_day} visit" if outcome.visit_time_of_day else None,
                )
                if part
            )
            lines.append(
                f"- {appliance.product}, {_bought(appliance)}, delivered "
                f"{appliance.delivered.isoformat()}, plan "
                f"{appliance.plan}: **{outcome.decision}**{' (' + detail + ')' if detail else ''}"
            )
        if case.withhold:
            lines.append(f"- Withheld from the message: {', '.join(case.withhold)}")
        lines += ["- Agree? ", ""]
    return "\n".join(lines)


def _bought(appliance: Appliance) -> str:
    if appliance.order_id:
        return f"order {appliance.order_id}"
    return f"bought elsewhere, serial {appliance.serial}"
