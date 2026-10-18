"""`lab strategy`: score use cases against a rule fixed in advance. No API key, no call.

- `lab strategy score <scorecard.csv>` validates a scorecard, applies the gates, totals, ranks
  and runs the sensitivity check, so readers can score their own use cases.
- `lab strategy reveal --through E<N>` writes the Halvard scorecard as it stood after episode N,
  with its slide chart.
- `lab strategy case` writes every result for the Halvard case: the final scorecard, the
  sensitivity check, each reveal step and the charts.
"""

import json
import re
from pathlib import Path
from typing import Annotated, Any

import typer

from lab.config import ConfigError
from lab.strategy.case import Case, load_case
from lab.strategy.charts import SHORT_CRITERIA, export_sensitivity, export_table
from lab.strategy.reveal import new_in, reveal, reveal_steps
from lab.strategy.rule import Rule, load_rule
from lab.strategy.scorecard import Row, read_scorecard, row_record, write_scorecard
from lab.strategy.scoring import Sensitivity, score, sensitivity

strategy_app = typer.Typer(
    help="Score AI use cases against a rule fixed in advance (Season 3).", no_args_is_help=True
)

DEFAULT_CASE = Path("season3/case")
RuleOption = Annotated[Path, typer.Option(help="The rule file.")]
CaseOption = Annotated[Path, typer.Option("--case", help="The case folder.")]


def _fail(exc: Exception) -> typer.Exit:
    typer.echo(f"Error: {exc}", err=True)
    return typer.Exit(code=1)


def _episode(text: str) -> int:
    match = re.fullmatch(r"[Ee]?(\d{1,2})", text.strip())
    if not match:
        raise typer.BadParameter("give an episode such as E5")
    return int(match.group(1))


def format_results(rows: list[Row], rule: Rule, result: Sensitivity) -> str:
    scored = score(rows, rule)
    lines = ["Use case                              Gates  Autonomy allowed  Total  Rank"]
    for s in scored:
        gates = {True: "pass", False: "FAIL", None: "open"}[s.gates_passed]
        allowed = (s.allowed_autonomy or "unset") + (" (above it)" if s.autonomy_exceeded else "")
        total = f"{s.total:.2f}" if s.total is not None else "  ."
        rank = str(s.rank) if s.rank else "."
        lines.append(
            f"{(s.id + ' ' + s.name)[:37]:<37} {gates:<6} {allowed:<17} {total:>5}  {rank:>4}"
        )
    lines += ["", f"First pick: {result.base_pick or 'none yet'}"]
    if result.base_pick:
        verdict = "holds" if result.share >= 0.8 else "is fragile"
        lines.append(
            f"Sensitivity: the pick holds in {result.holds} of {result.out_of} other weightings "
            f"({result.share:.0%}), so it {verdict}."
        )
        others = [
            f"{w.name}: {w.first_pick}"
            for w in result.alternatives
            if w.first_pick != result.base_pick
        ]
        if others:
            lines.append("Where it changes: " + "; ".join(others))
    return "\n".join(lines)


def results_json(rows: list[Row], rule: Rule) -> dict[str, Any]:
    return {
        "rule": {"name": rule.name, "version": rule.version, "weights": rule.weights},
        "rows": [
            {**row_record(row, rule), **s.model_dump()}
            for row, s in zip(rows, score(rows, rule), strict=True)
        ],
    }


def sensitivity_json(result: Sensitivity) -> dict[str, Any]:
    return {**result.model_dump(), "share": round(result.share, 4)}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")


@strategy_app.command("score")
def score_command(
    scorecard: Annotated[Path, typer.Argument(help="A scorecard CSV, such as the template.")],
    rule_path: Annotated[Path, typer.Option("--rule", help="The rule file.")] = DEFAULT_CASE
    / "rule.yaml",
    out: Annotated[Path | None, typer.Option(help="Folder to write JSON results to.")] = None,
) -> None:
    """Validate a scorecard, apply the gates, total, rank and check sensitivity."""
    try:
        rule = load_rule(rule_path)
        rows = read_scorecard(scorecard, rule)
    except ConfigError as exc:
        raise _fail(exc) from exc
    result = sensitivity(rows, rule)
    typer.echo(format_results(rows, rule, result))
    if out is not None:
        _write_json(out / "scorecard.json", results_json(rows, rule))
        _write_json(out / "sensitivity.json", sensitivity_json(result))


def _load(case_dir: Path, rule_path: Path | None) -> tuple[Rule, Case, list[Row]]:
    try:
        rule = load_rule(rule_path or case_dir / "rule.yaml")
        case = load_case(case_dir, rule)
    except ConfigError as exc:
        raise _fail(exc) from exc
    return rule, case, case.rows(rule)


def write_step(rows: list[Row], rule: Rule, through: int, out: Path) -> dict[str, Any]:
    """One reveal step: JSON and CSV beside each other, and the slide chart."""
    step = reveal(rows, rule, through)
    name = f"scorecard-e{through}"
    _write_json(out / f"{name}.json", step)
    added = new_in(rule, through)
    label = None
    if len(added) == 1 or added[-1] == "Weighted total and rank":
        label = _label_for(rule, through)
    footnote = (
        "* above the highest autonomy the table allows"
        if any(r["autonomy_exceeded"] for r in step["rows"])
        else None
    )
    export_table(step, rule, out / "charts", name, highlight_label=label, footnote=footnote)
    return step


def _label_for(rule: Rule, through: int) -> str | None:
    gates = [n for n, g in enumerate(rule.gates, start=1) if g.episode == through]
    criteria = [c for c in rule.criteria if c.episode == through]
    if rule.autonomy.episode == through:
        return "Autonomy"
    if rule.sourcing.episode == through:
        return "Sourcing"
    if criteria:
        return SHORT_CRITERIA.get(criteria[-1].id, criteria[-1].label)
    if gates:
        return f"G{gates[-1]}"
    return None


@strategy_app.command("reveal")
def reveal_command(
    through: Annotated[str, typer.Option(help="The episode, such as E5.")],
    case_dir: CaseOption = DEFAULT_CASE,
    out: Annotated[Path | None, typer.Option(help="Output folder.")] = None,
) -> None:
    """Write the case scorecard as it stood after an episode, with its slide chart."""
    rule, _, rows = _load(case_dir, None)
    episode = _episode(through)
    step = write_step(rows, rule, episode, out or case_dir / "results")
    typer.echo(f"Through E{episode}; new: {', '.join(step['new']) or 'nothing'}")


@strategy_app.command("case")
def case_command(case_dir: CaseOption = DEFAULT_CASE) -> None:
    """Write every result for the case: scorecard, sensitivity, reveal steps and charts."""
    rule, case, rows = _load(case_dir, None)
    out = case_dir / "results"
    for episode in reveal_steps(rule):
        write_step(rows, rule, episode, out)
    write_scorecard(out / "scorecard.csv", rows, rule)
    _write_json(out / "scorecard.json", results_json(rows, rule))
    result = sensitivity(rows, rule)
    _write_json(out / "sensitivity.json", sensitivity_json(result))
    final = reveal(rows, rule, max(reveal_steps(rule)))
    export_table(
        final,
        rule,
        out / "charts",
        "scorecard-final",
        highlight_label=None,
        highlight_pick=result.base_pick,
        footnote="* above the highest autonomy the table allows",
    )
    names = {c.id: c.name for c in case.candidates}
    export_sensitivity(result, names, out / "charts")
    typer.echo(format_results(rows, rule, result))
