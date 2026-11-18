"""The scorecard as it stood after episode N: only the columns introduced up to then.

Each teaching episode adds one part of the rule, so each episode's case recap slide shows the
scorecard with that part filled in and everything later still blank.
"""

from collections.abc import Sequence
from typing import Any

from lab.strategy.rule import Rule
from lab.strategy.scorecard import Row, row_record
from lab.strategy.scoring import gate_status, score

# Episodes whose reveal adds something; the others show the previous step unchanged.
OUTCOME_EPISODE = 1
REDIRECT_GATE = "right_tool"


def visible_columns(rule: Rule, through: int) -> dict[str, bool]:
    """Which parts of the rule have been introduced by episode `through`."""
    error_episode = next((c.episode for c in rule.criteria if c.id == "error_tolerance"), 4)
    parts: dict[str, bool] = {"outcome": through >= OUTCOME_EPISODE}
    parts.update({f"gate:{g.id}": g.episode <= through for g in rule.gates})
    parts.update({f"criterion:{c.id}": c.episode <= through for c in rule.criteria})
    parts["error_facts"] = through >= error_episode
    parts["autonomy"] = through >= rule.autonomy.episode
    parts["sourcing"] = through >= rule.sourcing.episode
    return parts


def reveal_steps(rule: Rule) -> list[int]:
    """The episodes that add a column, in order."""
    episodes = {OUTCOME_EPISODE, rule.autonomy.episode, rule.sourcing.episode}
    episodes |= {g.episode for g in rule.gates} | {c.episode for c in rule.criteria}
    return sorted(episodes)


def new_in(rule: Rule, episode: int) -> list[str]:
    """Labels of what episode `episode` adds, for the handover's "one new column"."""
    added = [g.label for g in rule.gates if g.episode == episode]
    added += [c.label for c in rule.criteria if c.episode == episode]
    if rule.autonomy.episode == episode:
        added.append("Autonomy (a setting)")
    if rule.sourcing.episode == episode:
        added.append("Sourcing (a setting)")
    if episode == max(c.episode for c in rule.criteria):
        added.append("Weighted total and rank")
    return added


def mask(row: Row, rule: Rule, through: int) -> Row:
    """The row with every column not yet introduced left blank."""
    seen = visible_columns(rule, through)
    gates = {g: (v if seen[f"gate:{g}"] else None) for g, v in row.gates.items()}
    return row.model_copy(
        update={
            "outcome": row.outcome if seen["outcome"] else "",
            "metric": row.metric if seen["outcome"] else "",
            "owner": row.owner if seen["outcome"] else "",
            "gates": gates,
            "redirect": row.redirect if seen[f"gate:{REDIRECT_GATE}"] else "",
            "error_cost": row.error_cost if seen["error_facts"] else None,
            "caught": row.caught if seen["error_facts"] else None,
            "reversible": row.reversible if seen["autonomy"] else None,
            "design_autonomy": row.design_autonomy if seen["autonomy"] else None,
            "scores": {c: (v if seen[f"criterion:{c}"] else None) for c, v in row.scores.items()},
            "application": row.application if seen["sourcing"] else "",
            "model_access": row.model_access if seen["sourcing"] else "",
        }
    )


def reveal(rows: Sequence[Row], rule: Rule, through: int) -> dict[str, Any]:
    """The scorecard through episode `through`, as a JSON-ready dict."""
    masked = [mask(r, rule, through) for r in rows]
    scored = {s.id: s for s in score(masked, rule)}
    seen = visible_columns(rule, through)
    out_rows = []
    for row in masked:
        result = scored[row.id]
        passed, failed = gate_status(row, rule)
        out_rows.append(
            {
                **row_record(row, rule),
                "gates_passed": passed,
                "failed_gates": list(failed),
                "allowed_autonomy": result.allowed_autonomy if seen["autonomy"] else None,
                "autonomy_exceeded": result.autonomy_exceeded if seen["autonomy"] else None,
                "total": result.total,
                "rank": result.rank,
            }
        )
    return {
        "through": f"E{through}",
        "new": new_in(rule, through),
        "columns": {k: v for k, v in seen.items()},
        "rows": out_rows,
    }
