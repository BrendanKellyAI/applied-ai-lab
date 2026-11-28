"""Scoring a reader's own agent: its decisions per appliance against the expected outcomes.

Input is JSON lines, one per case:
  {"case_id": "D-001", "outcomes": [{"serial": "...", "decision": "...", "reason": "...",
   "amount": null}]}
This checks decisions, reasons and amounts only. The full end state check (bookings, refunds,
approvals, unsafe actions) needs the agent to act through `lab agent env`.
"""

import json
from collections import Counter
from pathlib import Path

from lab.agent.run import load_cases
from lab.agent.write_messages import label_disagreements


def score_file(end_states: Path, cases_name: str) -> dict[str, object]:
    cases = {c.facts.case_id: c.facts for c in load_cases([cases_name])}
    answered: dict[str, dict[str, object]] = {}
    for line in end_states.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            answered[str(row["case_id"])] = row
    resolved, total, problems = Counter(), Counter(), {}
    for case_id, facts in cases.items():
        total[facts.kind] += 1
        row = answered.get(case_id)
        found = ["no answer"] if row is None else label_disagreements(facts, row)
        if found:
            problems[case_id] = found
        else:
            resolved[facts.kind] += 1
    return {
        "cases": len(cases),
        "answered": len(set(answered) & set(cases)),
        "resolved": sum(resolved.values()),
        "resolved_by_kind": {k: f"{resolved[k]} of {total[k]}" for k in sorted(total)},
        "problems": problems,
    }
