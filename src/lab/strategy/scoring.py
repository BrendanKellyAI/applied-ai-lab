"""Apply the rule to a scorecard: gates, autonomy, weighted totals, rank and sensitivity.

Only a use case that passes both gates and has every criterion scored gets a total. The first
pick is the highest total; a tie is broken by error tolerance, then time to evidence, then id.
"""

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict

from lab.strategy.rule import AUTONOMY_ORDER, Autonomy, Rule
from lab.strategy.scorecard import Row

TIE_BREAKERS = ("error_tolerance", "time_to_evidence")


class Scored(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    gates_passed: bool | None
    failed_gates: tuple[str, ...]
    allowed_autonomy: Autonomy | None
    autonomy_exceeded: bool | None
    total: float | None
    rank: int | None


class WeightingResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    weights: dict[str, float]
    first_pick: str | None
    totals: dict[str, float]


class Sensitivity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_pick: str | None
    alternatives: tuple[WeightingResult, ...]
    holds: int
    out_of: int
    picks: dict[str, int]

    @property
    def share(self) -> float:
        return self.holds / self.out_of if self.out_of else 0.0


def gate_status(row: Row, rule: Rule) -> tuple[bool | None, tuple[str, ...]]:
    """True when every gate passes, False when any fails, None while one is undecided."""
    results = [row.gates.get(g) for g in rule.gate_ids]
    failed = tuple(g for g, r in zip(rule.gate_ids, results, strict=True) if r == "fail")
    if failed:
        return False, failed
    if any(r is None for r in results):
        return None, ()
    return True, ()


def autonomy(row: Row, rule: Rule) -> tuple[Autonomy | None, bool | None]:
    """The highest autonomy allowed, and whether the design autonomy goes above it."""
    if row.error_cost is None or row.caught is None or row.reversible is None:
        return None, None
    allowed = rule.autonomy.allowed(row.error_cost, row.caught, row.reversible)
    if row.design_autonomy is None:
        return allowed, None
    exceeded = AUTONOMY_ORDER.index(row.design_autonomy) > AUTONOMY_ORDER.index(allowed)
    return allowed, exceeded


def normalised(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def weighted_total(row: Row, weights: Mapping[str, float]) -> float | None:
    if any(row.scores.get(c) is None for c in weights):
        return None
    return round(sum(weights[c] * (row.scores[c] or 0) for c in weights), 6)


def _order_key(row: Row, total: float) -> tuple:
    return (-total, *(-(row.scores.get(c) or 0) for c in TIE_BREAKERS), row.id)


def totals(rows: Sequence[Row], rule: Rule, weights: Mapping[str, float]) -> dict[str, float]:
    """Totals for the rows eligible to go first: both gates passed and every criterion scored."""
    out = {}
    for row in rows:
        passed, _ = gate_status(row, rule)
        total = weighted_total(row, weights)
        if passed and total is not None:
            out[row.id] = total
    return out


def first_pick(rows: Sequence[Row], rule: Rule, weights: Mapping[str, float]) -> str | None:
    eligible = totals(rows, rule, weights)
    by_id = {r.id: r for r in rows}
    ordered = sorted(eligible, key=lambda i: _order_key(by_id[i], eligible[i]))
    return ordered[0] if ordered else None


def score(rows: Sequence[Row], rule: Rule) -> list[Scored]:
    weights = normalised(rule.weights)
    eligible = totals(rows, rule, weights)
    by_id = {r.id: r for r in rows}
    ranked = sorted(eligible, key=lambda i: _order_key(by_id[i], eligible[i]))
    ranks = {item: n for n, item in enumerate(ranked, start=1)}
    out = []
    for row in rows:
        passed, failed = gate_status(row, rule)
        allowed, exceeded = autonomy(row, rule)
        out.append(
            Scored(
                id=row.id,
                name=row.name,
                gates_passed=passed,
                failed_gates=failed,
                allowed_autonomy=allowed,
                autonomy_exceeded=exceeded,
                total=weighted_total(row, weights) if passed is not False else None,
                rank=ranks.get(row.id),
            )
        )
    return out


def weightings(rule: Rule) -> list[tuple[str, dict[str, float]]]:
    """The alternative weightings the sensitivity check uses, each scaled to sum to 1."""
    spec = rule.sensitivity
    out = [("equal", normalised(spec.equal))]
    for factor, label, wanted in ((0.5, "halved", spec.halve_each), (2, "doubled", spec.double_each)):
        if not wanted:
            continue
        for criterion in rule.criterion_ids:
            changed = {**rule.weights, criterion: rule.weights[criterion] * factor}
            out.append((f"{criterion} {label}", normalised(changed)))
    out += [("ceo", normalised(spec.ceo)), ("regulator", normalised(spec.regulator))]
    return out


def sensitivity(rows: Sequence[Row], rule: Rule) -> Sensitivity:
    base = first_pick(rows, rule, normalised(rule.weights))
    results = []
    for name, weights in weightings(rule):
        results.append(
            WeightingResult(
                name=name,
                weights={k: round(v, 6) for k, v in weights.items()},
                first_pick=first_pick(rows, rule, weights),
                totals=totals(rows, rule, weights),
            )
        )
    picks: dict[str, int] = {}
    for result in results:
        if result.first_pick is not None:
            picks[result.first_pick] = picks.get(result.first_pick, 0) + 1
    holds = sum(1 for r in results if base is not None and r.first_pick == base)
    return Sensitivity(
        base_pick=base,
        alternatives=tuple(results),
        holds=holds,
        out_of=len(results),
        picks=dict(sorted(picks.items(), key=lambda kv: (-kv[1], kv[0]))),
    )
