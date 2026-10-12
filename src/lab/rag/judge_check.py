"""The judge check (S2 E3): how often does the judge agree with a person?

`draw` takes a finished run, picks a sample stratified by item type and by the judge's
outcome, and writes a marking sheet that shows each item exactly as the judge saw it, with the
judge's verdict hidden. A person marks the three verdict fields in `judge_check.csv`. `report`
then compares the marks with the judge, field by field, with Wilson intervals, and lists every
disagreement. The judge is trusted only to the level this shows.
"""

import csv
import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from lab.config import ConfigError, ProviderLimits
from lab.providers.base import ProviderName
from lab.rag.chunk import Chunk, chunk_library
from lab.rag.config import ModelSpec, PipelineConfig
from lab.rag.corpus import Item, Library
from lab.rag.judge import Verdict, judge_instructions, judge_prompt
from lab.rag.log import ItemLog
from lab.rag.score import Proportion

FIELDS = ("declined", "correct", "faithful")
CSV_COLUMNS = ("n", "item_id", *FIELDS, "note")
SHEET = "judge_check.md"
MARKS = "judge_check.csv"
SAMPLE = "sample.json"
REPORT = "agreement.json"
_YES = {"y", "yes", "true", "1"}
_NO = {"n", "no", "false", "0"}


class CheckConfig(BaseModel):
    """`judge_check.yaml`: which run to check, and how to sample it. Paths are relative to it.

    With `second_judge` set, a second model marks the whole sample by the same rules, and a
    person marks only the `hand` items where the two models disagree most.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run: Path
    library: Path
    out: Path
    size: int = Field(default=50, gt=0)
    per_type: int = Field(default=3, gt=0)
    seed: int
    second_judge: ModelSpec | None = None
    hand: int | None = Field(default=None, gt=0)
    limits: dict[ProviderName, ProviderLimits] = Field(default_factory=dict)


def load_check_config(path: Path) -> CheckConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        config = CheckConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"{path} is not a valid judge check config:\n{exc}") from exc
    here = path.parent
    paths = ("run", "library", "out")
    return config.model_copy(update={p: (here / getattr(config, p)).resolve() for p in paths})


def outcome(verdict: Verdict) -> str:
    """The judge's call in one word, used to spread the sample across verdicts."""
    if verdict.declined:
        return "declined"
    return "right" if verdict.correct and verdict.faithful else "wrong"


def draw_sample(logs: Sequence[ItemLog], *, size: int, per_type: int, seed: int) -> list[str]:
    """Item ids in marking order: `per_type` from every type, then the rest at random.

    Within a type, items are taken in turn from each of the judge's outcomes, rarest first, so
    a type the judge mostly passed still contributes an item it failed. Items the judge could
    not mark are left out: there is no verdict to check.
    """
    rng = random.Random(seed)
    judged = sorted((g for g in logs if g.verdict is not None), key=lambda g: g.item_id)
    by_type: dict[str, list[ItemLog]] = defaultdict(list)
    for log in judged:
        by_type[log.type].append(log)
    if per_type * len(by_type) > size:
        raise ValueError(
            f"{per_type} per type across {len(by_type)} types is more than the sample of {size}"
        )
    chosen = [i for t in sorted(by_type) for i in _from_type(by_type[t], per_type, rng)]
    rest = [g.item_id for g in judged if g.item_id not in set(chosen)]
    rng.shuffle(rest)
    sample = chosen + rest[: size - len(chosen)]
    rng.shuffle(sample)
    return sample


def _from_type(logs: list[ItemLog], count: int, rng: random.Random) -> list[str]:
    groups: dict[str, list[str]] = defaultdict(list)
    for log in logs:
        groups[outcome(log.verdict)].append(log.item_id)
    for ids in groups.values():
        rng.shuffle(ids)
    queues = [groups[k] for k in sorted(groups, key=lambda k: (len(groups[k]), k))]
    picked: list[str] = []
    while len(picked) < count and any(queues):
        for queue in queues:
            if queue and len(picked) < count:
                picked.append(queue.pop(0))
    return picked


def chunk_lookup(library: Library, pipeline: dict[str, Any]) -> dict[str, Chunk]:
    """Every chunk of the run, rebuilt from the library and the run's chunker settings."""
    chunker = PipelineConfig.model_validate(pipeline).chunk
    return {c.chunk_id: c for c in chunk_library(library.documents, chunker)}


def judge_prompt_hash() -> str:
    """Identifies the judge's instructions: marks made against one judge do not check another."""
    return hashlib.sha256(judge_instructions().encode("utf-8")).hexdigest()[:12]


def write_sheet(
    out: Path,
    sample: Sequence[str],
    logs: Sequence[ItemLog],
    library: Library,
    chunks: dict[str, Chunk],
) -> list[Path]:
    """The marking sheet and the blank marks file for `sample`. Refuses to overwrite marks
    that have been started."""
    marks = out / MARKS
    if marks.exists() and _has_marks(marks):
        raise FileExistsError(f"{marks} already holds marks; move it before drawing again")
    out.mkdir(parents=True, exist_ok=True)
    by_id = {g.item_id: g for g in logs}
    items = {i.id: i for i in library.test + library.dev}
    blocks = [_sheet_header(len(sample))]
    for n, item_id in enumerate(sample, start=1):
        blocks.append(_sheet_item(n, items[item_id], by_id[item_id], chunks))
    sheet = out / SHEET
    sheet.write_text("\n\n".join(blocks) + "\n", encoding="utf-8", newline="\n")
    with marks.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for n, item_id in enumerate(sample, start=1):
            writer.writerow([n, item_id, "", "", "", ""])
    return [sheet, marks]


def write_record(out: Path, record: dict[str, Any]) -> Path:
    """`sample.json`: the run, the judge's instructions hash, the sample and what was marked."""
    out.mkdir(parents=True, exist_ok=True)
    path = out / SAMPLE
    path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    return path


def read_record(out: Path) -> dict[str, Any]:
    return json.loads((out / SAMPLE).read_text(encoding="utf-8"))


def _sheet_header(count: int) -> str:
    return "\n\n".join(
        [
            "# Judge check: marking sheet",
            f"{count} items, each shown exactly as the judge saw it. The judge's verdicts are "
            f"not shown. For each item, fill in `declined`, `correct` and `faithful` in "
            f"`{MARKS}` with y or n, and add a note where the call was close.",
            "Mark by the same rules the judge was given:",
            "\n".join(f"> {line}" if line else ">" for line in _rules()),
        ]
    )


def _rules() -> list[str]:
    """The judge's instructions without the reply format, which is for the model only."""
    lines = judge_instructions().strip().splitlines()
    end = next((i for i, line in enumerate(lines) if line.startswith("Reply with")), len(lines))
    return "\n".join(lines[:end]).rstrip().splitlines()


def _sheet_item(n: int, item: Item, log: ItemLog, chunks: dict[str, Chunk]) -> str:
    passages = [chunks[c] for c in log.prompt_chunks]
    answer = log.answer.text if log.answer else ""
    return f"---\n\n## {n}. {item.id}\n\n{judge_prompt(item, passages, answer)}"


def _has_marks(path: Path) -> bool:
    with path.open(encoding="utf-8", newline="") as handle:
        return any(any(row.get(f, "").strip() for f in FIELDS) for row in csv.DictReader(handle))


class Mark(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    declined: bool
    correct: bool
    faithful: bool
    note: str = ""


def read_marks(path: Path, sample: Sequence[str]) -> list[Mark]:
    """The person's marks, one per sampled item. Refuses blanks, unknown values and ids."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    problems: list[str] = []
    marks: list[Mark] = []
    for row in rows:
        item_id = (row.get("item_id") or "").strip()
        values = {f: _yes_no(row.get(f, "")) for f in FIELDS}
        bad = [f for f, v in values.items() if v is None]
        if bad:
            problems.append(f"{item_id or 'a row'}: {', '.join(bad)} not marked y or n")
            continue
        marks.append(Mark(item_id=item_id, note=(row.get("note") or "").strip(), **values))
    ids = [m.item_id for m in marks]
    unknown = sorted(set(ids) - set(sample))
    missing = sorted(set(sample) - {r.get("item_id", "").strip() for r in rows})
    if unknown:
        problems.append(f"not in the sample: {', '.join(unknown)}")
    if missing:
        problems.append(f"missing from the marks: {', '.join(missing)}")
    if len(ids) != len(set(ids)):
        problems.append("an item is marked twice")
    if problems:
        raise ValueError("The marks cannot be read yet:\n  " + "\n  ".join(problems))
    return marks


def _yes_no(value: str | None) -> bool | None:
    text = (value or "").strip().lower()
    return True if text in _YES else False if text in _NO else None


class FieldAgreement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agree: Proportion
    judge_yes_hand_no: int
    judge_no_hand_yes: int


def agreement(marks: Sequence[Mark], logs: Sequence[ItemLog]) -> dict[str, Any]:
    """Agreement on each field, on the answer number's verdict (correct and faithful), and of
    the code check with the person on items that have key values; then every disagreement."""
    by_id = {g.item_id: g for g in logs}
    pairs = [(m, by_id[m.item_id]) for m in marks]
    fields = {f: _field(pairs, lambda v, f=f: getattr(v, f)) for f in FIELDS}
    fields["right"] = _field(pairs, lambda v: v.correct and v.faithful)
    coded = [(m, g) for m, g in pairs if g.code_check is not None]
    code = Proportion.of(sum(1 for m, g in coded if g.code_check == m.correct), len(coded))
    return {
        "items": len(pairs),
        "fields": {k: v.model_dump() for k, v in fields.items()},
        "code_check_with_hand_on_correct": code.model_dump(),
        "disagreements": [_disagreement(m, g) for m, g in pairs if _differs(m, g.verdict)],
    }


def _field(pairs, read) -> FieldAgreement:
    judge = [read(g.verdict) for _, g in pairs]
    hand = [read(m) for m, _ in pairs]
    both = list(zip(judge, hand, strict=True))
    return FieldAgreement(
        agree=Proportion.of(sum(1 for j, h in both if j == h), len(both)),
        judge_yes_hand_no=sum(1 for j, h in both if j and not h),
        judge_no_hand_yes=sum(1 for j, h in both if h and not j),
    )


def _differs(mark: Mark, verdict: Verdict) -> bool:
    return any(getattr(mark, f) != getattr(verdict, f) for f in FIELDS)


def _disagreement(mark: Mark, log: ItemLog) -> dict[str, Any]:
    verdict = log.verdict
    return {
        "item_id": log.item_id,
        "type": log.type,
        "fields": [f for f in FIELDS if getattr(mark, f) != getattr(verdict, f)],
        "judge": {f: getattr(verdict, f) for f in FIELDS},
        "hand": {f: getattr(mark, f) for f in FIELDS},
        "judge_reason": verdict.reason,
        "note": mark.note,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [f"Judge check, {report['items']} items"]
    for name, field in report["fields"].items():
        agree = field["agree"]
        lines.append(
            f"  {name}: {agree['count']}/{agree['total']} agree "
            f"({agree['low']:.0%} to {agree['high']:.0%}); judge yes, hand no "
            f"{field['judge_yes_hand_no']}; judge no, hand yes {field['judge_no_hand_yes']}"
        )
    code = report["code_check_with_hand_on_correct"]
    lines.append(f"  code check with hand, correct: {code['count']}/{code['total']}")
    lines.append(f"  disagreements: {len(report['disagreements'])}")
    for d in report["disagreements"]:
        lines.append(f"    {d['item_id']} ({d['type']}): {', '.join(d['fields'])}")
    return "\n".join(lines)
