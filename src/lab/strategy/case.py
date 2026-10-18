"""The Halvard Home case: candidates and evidenced scores, turned into scorecard rows.

`candidates.yaml` holds each use case's facts; `scores.yaml` holds the gates, scores and
sourcing, each score citing a measured result or a stated assumption.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from lab.config import ConfigError
from lab.strategy.rule import Autonomy, Caught, ErrorCost, Rule
from lab.strategy.scorecard import Row


class Outcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    statement: str
    metric: str
    owner: str


class DataNeed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    needs: str
    exists: bool
    note: str


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    summary: str
    why_in_set: str
    outcome: Outcome
    volume: str
    user: str
    wrong: str
    data: DataNeed
    vendor: str
    design_autonomy: Autonomy
    error_cost: ErrorCost
    caught: Caught
    reversible: bool


class Measured(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    figure: str


class Score(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    score: int = Field(ge=1, le=5)
    measured: Measured | None = None
    assumption: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _evidence(self) -> "Score":
        if (self.measured is None) == (self.assumption is None):
            raise ValueError("each score cites exactly one of measured or assumption")
        return self

    @property
    def evidence_kind(self) -> Literal["measured", "assumption"]:
        return "measured" if self.measured is not None else "assumption"


class GateCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    result: Literal["pass", "fail"]
    reason: str


class SourcingCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    application: str
    model_access: str
    reason: str


class StopCriteria(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate: str
    written: str
    success_metric: str
    threshold: str
    time_box: str
    stop_condition: str
    reviewer: str


class CandidateScores(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gates: dict[str, GateCall]
    scores: dict[str, Score] = Field(default_factory=dict)
    redirect: str = ""
    sourcing: SourcingCall


class Case(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidates: tuple[Candidate, ...]
    scores: dict[str, CandidateScores]
    stop_criteria: StopCriteria | None = None

    def rows(self, rule: Rule) -> list[Row]:
        return [_row(c, self.scores[c.id], rule) for c in self.candidates]


def _row(candidate: Candidate, scored: CandidateScores, rule: Rule) -> Row:
    return Row(
        id=candidate.id,
        name=candidate.name,
        outcome=candidate.outcome.statement,
        metric=candidate.outcome.metric,
        owner=candidate.outcome.owner,
        gates={g: scored.gates[g].result if g in scored.gates else None for g in rule.gate_ids},
        redirect=scored.redirect,
        error_cost=candidate.error_cost,
        caught=candidate.caught,
        reversible=candidate.reversible,
        design_autonomy=candidate.design_autonomy,
        scores={
            c: scored.scores[c].score if c in scored.scores else None for c in rule.criterion_ids
        },
        application=scored.sourcing.application,
        model_access=scored.sourcing.model_access,
        notes="",
    )


def _yaml(path: Path) -> dict:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Case file not found: {path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    return raw


def load_case(folder: Path, rule: Rule) -> Case:
    """Load candidates.yaml and scores.yaml from a case folder and check they agree with the
    rule: every candidate scored, gates and criteria named as the rule names them, and every
    candidate that passes both gates scored on every criterion."""
    candidates = _yaml(folder / "candidates.yaml").get("candidates", [])
    scores = _yaml(folder / "scores.yaml")
    try:
        case = Case.model_validate(
            {
                "candidates": candidates,
                "scores": scores.get("candidates", {}),
                "stop_criteria": scores.get("stop_criteria"),
            }
        )
    except ValidationError as exc:
        raise ConfigError(f"{folder} is not a valid case:\n{exc}") from exc
    problems = _problems(case, rule)
    if problems:
        raise ConfigError(f"{folder}: " + "; ".join(problems))
    return case


def _problems(case: Case, rule: Rule) -> list[str]:
    problems = []
    ids = [c.id for c in case.candidates]
    if sorted(ids) != sorted(case.scores):
        problems.append(f"candidates {sorted(ids)} and scored {sorted(case.scores)} differ")
    for cid, scored in case.scores.items():
        if set(scored.gates) != set(rule.gate_ids):
            problems.append(f"{cid} must give every gate: {list(rule.gate_ids)}")
        unknown = set(scored.scores) - set(rule.criterion_ids)
        if unknown:
            problems.append(f"{cid} scores unknown criteria {sorted(unknown)}")
        failed = any(g.result == "fail" for g in scored.gates.values())
        if failed and not scored.redirect:
            problems.append(f"{cid} fails a gate but has no redirect")
        if not failed and set(scored.scores) != set(rule.criterion_ids):
            problems.append(f"{cid} passes both gates but is not scored on every criterion")
    return problems
