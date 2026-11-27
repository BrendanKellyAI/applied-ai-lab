"""Write each case's customer message, check it in code, then check its label blind.

Per case, up to three attempts: the generator writes a message; code checks that it states
what it must and leaves out what it must; the label checker reads it with the records and the
policy and states each decision. A case is accepted when the checker agrees with the expected
outcome; after three attempts it is discarded and reported. Every call goes through the runner,
so responses are cached and a rerun costs nothing.
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from lab.agent.case_model import CaseFacts, ExpectedOutcome
from lab.agent.data_estimate import GENERATOR, GENERATOR_MAX_OUTPUT, LABELLER, LABELLER_MAX_OUTPUT
from lab.agent.message_prompts import (
    GENERATOR_SYSTEM,
    LABELLER_SYSTEM,
    generation_prompt,
    labeller_prompt,
    word_band,
)
from lab.plan import PlannedCall
from lab.providers.base import GenerationRequest
from lab.raw_log import latest_successful, load_records
from lab.runner import Runner

ATTEMPTS = 3
ORDER_PATTERN = re.compile(r"H-\d{6}")
DASHES = {"—": ", ", "–": "-"}


@dataclass
class WriteReport:
    accepted: dict[str, dict[str, object]] = field(default_factory=dict)
    # Every failed check, by case, including for cases a later attempt fixed.
    problems: dict[str, list[str]] = field(default_factory=dict)
    discarded: list[str] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)


def _limit(table: dict[str, int], facts: CaseFacts) -> int:
    return table["long" if facts.kind == "long" else "other"]


def generator_request(facts: CaseFacts, attempt: int) -> GenerationRequest:
    prompt = generation_prompt(facts)
    if attempt > 1:
        prompt += f"\nThis is attempt {attempt}: follow every point exactly."
        numbers = ORDER_PATTERN.findall(" ".join(facts.say))
        if numbers:
            prompt += f" Write these order numbers exactly as given: {', '.join(numbers)}."
    provider, model = GENERATOR
    return GenerationRequest(
        provider=provider,  # type: ignore[arg-type]
        model=model,
        system=GENERATOR_SYSTEM,
        prompt=prompt,
        max_output_tokens=_limit(GENERATOR_MAX_OUTPUT, facts),
        reasoning="minimal",
        metadata={"case_id": facts.case_id, "stage": "message"},
    )


def labeller_request(facts: CaseFacts, message: str) -> GenerationRequest:
    provider, model = LABELLER
    return GenerationRequest(
        provider=provider,  # type: ignore[arg-type]
        model=model,
        system=LABELLER_SYSTEM,
        prompt=labeller_prompt(facts, message),
        max_output_tokens=_limit(LABELLER_MAX_OUTPUT, facts),
        reasoning="off",
        metadata={"case_id": facts.case_id, "stage": "label"},
    )


def parse_json(text: str) -> dict[str, object]:
    """The reply's JSON object; if the model wrote working first, the last full object in it."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        value = _last_object(cleaned)
    if not isinstance(value, dict):
        raise ValueError("reply is not a JSON object")
    return value


def _last_object(text: str) -> dict[str, object]:
    """The outermost JSON object that ends the reply, found by trying each opening brace."""
    decoder = json.JSONDecoder()
    for start in (i for i, ch in enumerate(text) if ch == "{"):
        try:
            value, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and not text[start + end :].strip(" \n`"):
            return value
    raise ValueError("no JSON object at the end of the reply")


def clean_message(text: str) -> str:
    for dash, replacement in DASHES.items():
        text = text.replace(dash, replacement)
    return text.strip()


def message_problems(facts: CaseFacts, message: str) -> list[str]:
    """Code checks: stated facts present, withheld facts absent, length about right."""
    problems = []
    lower = message.lower()
    for number in ORDER_PATTERN.findall(" ".join(facts.say)):
        if number not in message:
            problems.append(f"order number {number} missing")
    said = set(ORDER_PATTERN.findall(" ".join(facts.say)))
    for number in ORDER_PATTERN.findall(message):
        if number not in said:
            problems.append(f"order number {number} was not given")
    for appliance in facts.appliances:
        brand = appliance.product.split()[0].lower()
        named = brand in lower
        if "product" in facts.withhold and named:
            problems.append(f"{appliance.product} named but withheld")
        if "product" not in facts.withhold and not named:
            problems.append(f"{appliance.product} not named")
        if appliance.serial.lower() in lower:
            problems.append("serial number given")
    low, high = word_band(facts)
    words = len(message.split())
    if not low * 0.5 <= words <= high * 1.5:
        problems.append(f"{words} words, outside {low} to {high}")
    return problems


def _norm(value: object) -> str | None:
    if value in (None, "", "null"):
        return None
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def label_disagreements(facts: CaseFacts, reply: dict[str, object]) -> list[str]:
    outcomes = reply.get("outcomes")
    if not isinstance(outcomes, list):
        return ["no outcomes list"]
    by_serial = {str(o.get("serial")): o for o in outcomes if isinstance(o, dict)}
    found = []
    for expected in facts.expected:
        got = by_serial.get(expected.serial)
        if got is None:
            found.append(f"{expected.serial}: no outcome")
            continue
        found.extend(_compare(expected, got))
    return found


def _compare(expected: ExpectedOutcome, got: dict[str, object]) -> list[str]:
    where = expected.serial
    if _norm(got.get("decision")) != expected.decision:
        return [f"{where}: decision {got.get('decision')} not {expected.decision}"]
    problems = []
    reason_counts = expected.reason and expected.decision != "repair_booked"
    if reason_counts and _norm(got.get("reason")) != expected.reason:
        problems.append(f"{where}: reason {got.get('reason')} not {expected.reason}")
    if expected.amount is not None:
        try:
            amount = float(got.get("amount"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            amount = None
        if amount is None or abs(amount - expected.amount) > 0.01:
            problems.append(f"{where}: amount {got.get('amount')} not {expected.amount}")
    return problems


def _planned(request: GenerationRequest, call_id: str, label: str) -> PlannedCall:
    return PlannedCall(call_id=call_id, model_label=label, mode="build", cell={}, request=request)


def _run(runner: Runner, calls: list[PlannedCall], raw_path: Path) -> dict[str, str]:
    if not calls:
        return {}
    runner.run(calls, raw_path)
    latest = latest_successful(load_records(raw_path))
    return {
        call.call_id: latest[call.call_id].result.text  # type: ignore[union-attr]
        for call in calls
        if call.call_id in latest and latest[call.call_id].result is not None
    }


def write_messages(cases: Sequence[CaseFacts], runner: Runner, raw_dir: Path) -> WriteReport:
    report = WriteReport()
    pending = {c.case_id: c for c in cases}
    for attempt in range(1, ATTEMPTS + 1):
        if not pending:
            break
        messages = _generate(runner, raw_dir, pending, attempt, report)
        _check_labels(runner, raw_dir, pending, messages, attempt, report)
    report.discarded = sorted(pending)
    return report


def _generate(
    runner: Runner, raw_dir: Path, pending: dict[str, CaseFacts], attempt: int, report: WriteReport
) -> dict[str, str]:
    calls = [
        _planned(generator_request(f, attempt), f"{f.case_id}-message-{attempt}", GENERATOR[1])
        for f in pending.values()
    ]
    replies = _run(runner, calls, raw_dir / "messages.jsonl")
    messages = {}
    for case_id, facts in pending.items():
        report.attempts[case_id] = attempt
        reply = replies.get(f"{case_id}-message-{attempt}")
        try:
            message = clean_message(str(parse_json(reply or "")["message"]))
        except (ValueError, KeyError) as exc:
            report.problems.setdefault(case_id, []).append(f"attempt {attempt}: bad reply ({exc})")
            continue
        problems = message_problems(facts, message)
        if problems:
            report.problems.setdefault(case_id, []).append(
                f"attempt {attempt}: {'; '.join(problems)}"
            )
            continue
        messages[case_id] = message
    return messages


def _check_labels(
    runner: Runner,
    raw_dir: Path,
    pending: dict[str, CaseFacts],
    messages: dict[str, str],
    attempt: int,
    report: WriteReport,
) -> None:
    calls = [
        _planned(labeller_request(pending[cid], msg), f"{cid}-label-{attempt}", LABELLER[1])
        for cid, msg in messages.items()
    ]
    replies = _run(runner, calls, raw_dir / "labels.jsonl")
    for case_id, message in messages.items():
        try:
            reply = parse_json(replies.get(f"{case_id}-label-{attempt}") or "")
        except ValueError as exc:
            report.problems.setdefault(case_id, []).append(
                f"attempt {attempt}: label reply ({exc})"
            )
            continue
        disagreements = label_disagreements(pending[case_id], reply)
        if disagreements:
            report.problems.setdefault(case_id, []).append(
                f"attempt {attempt}: {'; '.join(disagreements)}"
            )
            continue
        report.accepted[case_id] = {"message": message, "attempt": attempt}
        del pending[case_id]
