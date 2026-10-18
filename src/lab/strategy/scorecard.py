"""A scorecard: one row per use case, read from and written to CSV.

The CSV is what readers fill in (`season3/templates/scorecard.csv`) and what the case produces
(`season3/case/results/scorecard.csv`). A blank cell means "not decided yet": a criterion left
blank is not scored, and a candidate with any blank criterion gets no total.
"""

import csv
import io
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from lab.config import ConfigError
from lab.strategy.rule import Autonomy, Caught, ErrorCost, Rule

GateResult = Literal["pass", "fail"]

# The columns before and after the criteria, in file order. Criteria columns come from the rule.
LEAD_COLUMNS = (
    "id",
    "name",
    "outcome",
    "metric",
    "owner",
    "gate_outcome",
    "gate_right_tool",
    "redirect",
    "error_cost",
    "caught",
    "reversible",
    "design_autonomy",
)
TAIL_COLUMNS = ("application", "model_access", "notes")


class Row(BaseModel):
    """One use case. Every field but the id and name may be blank while it is being scored."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    outcome: str = ""
    metric: str = ""
    owner: str = ""
    gates: dict[str, GateResult | None]
    redirect: str = ""
    error_cost: ErrorCost | None = None
    caught: Caught | None = None
    reversible: bool | None = None
    design_autonomy: Autonomy | None = None
    scores: dict[str, int | None]
    application: str = ""
    model_access: str = ""
    notes: str = ""

    @field_validator("scores")
    @classmethod
    def _one_to_five(cls, scores: dict[str, int | None]) -> dict[str, int | None]:
        for name, value in scores.items():
            if value is not None and not 1 <= value <= 5:
                raise ValueError(f"{name} must be a whole number from 1 to 5, not {value}")
        return scores


def columns(rule: Rule) -> tuple[str, ...]:
    return LEAD_COLUMNS + rule.criterion_ids + TAIL_COLUMNS


def _blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _bool(value: str | None) -> bool | None:
    value = _blank(value)
    if value is None:
        return None
    lowered = value.lower()
    if lowered in {"yes", "true", "y"}:
        return True
    if lowered in {"no", "false", "n"}:
        return False
    raise ValueError(f"reversible must be yes or no, not {value!r}")


def _int(value: str | None, column: str) -> int | None:
    value = _blank(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{column} must be a whole number from 1 to 5, not {value!r}") from exc


def parse_row(record: dict[str, str], rule: Rule) -> Row:
    return Row(
        id=(record.get("id") or "").strip(),
        name=(record.get("name") or "").strip(),
        outcome=(record.get("outcome") or "").strip(),
        metric=(record.get("metric") or "").strip(),
        owner=(record.get("owner") or "").strip(),
        gates={
            "outcome": _lower(record.get("gate_outcome")),
            "right_tool": _lower(record.get("gate_right_tool")),
        },
        redirect=(record.get("redirect") or "").strip(),
        error_cost=_lower(record.get("error_cost")),
        caught=_lower(record.get("caught")),
        reversible=_bool(record.get("reversible")),
        design_autonomy=_lower(record.get("design_autonomy")),
        scores={c: _int(record.get(c), c) for c in rule.criterion_ids},
        application=(record.get("application") or "").strip(),
        model_access=(record.get("model_access") or "").strip(),
        notes=(record.get("notes") or "").strip(),
    )


def _lower(value: str | None) -> str | None:  # type: ignore[return-value]
    value = _blank(value)
    return value.lower() if value else None


def read_scorecard(path: Path, rule: Rule) -> list[Row]:
    """Read and validate a scorecard CSV. Errors name the row and the problem."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ConfigError(f"Scorecard not found: {path}") from exc
    reader = csv.DictReader(io.StringIO(text))
    expected = set(columns(rule))
    found = set(reader.fieldnames or ())
    missing = sorted(expected - found)
    if missing:
        raise ConfigError(f"{path} is missing columns: {', '.join(missing)}")
    unknown = sorted(found - expected)
    if unknown:
        raise ConfigError(f"{path} has unknown columns: {', '.join(unknown)}")
    rows = []
    for line, record in enumerate(reader, start=2):
        if not any((v or "").strip() for v in record.values()):
            continue
        try:
            rows.append(parse_row(record, rule))
        except (ValidationError, ValueError) as exc:
            raise ConfigError(f"{path}, line {line}: {_message(exc)}") from exc
    ids = [r.id for r in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ConfigError(f"{path}: duplicate ids {', '.join(duplicates)}")
    if not rows:
        raise ConfigError(f"{path} has no use cases")
    return rows


def _message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
    return str(exc)


def row_record(row: Row, rule: Rule) -> dict[str, str]:
    def text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "yes" if value else "no"
        return str(value)

    record = {
        "id": row.id,
        "name": row.name,
        "outcome": row.outcome,
        "metric": row.metric,
        "owner": row.owner,
        "gate_outcome": text(row.gates.get("outcome")),
        "gate_right_tool": text(row.gates.get("right_tool")),
        "redirect": row.redirect,
        "error_cost": text(row.error_cost),
        "caught": text(row.caught),
        "reversible": text(row.reversible),
        "design_autonomy": text(row.design_autonomy),
        **{c: text(row.scores.get(c)) for c in rule.criterion_ids},
        "application": row.application,
        "model_access": row.model_access,
        "notes": row.notes,
    }
    return record


def write_scorecard(path: Path, rows: Sequence[Row], rule: Rule) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns(rule), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row_record(row, rule))
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="\n")
