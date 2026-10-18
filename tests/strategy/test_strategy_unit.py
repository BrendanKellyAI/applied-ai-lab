"""Unit tests for lab.strategy: the rule, scorecard, scoring, case, reveal and CLI."""

import copy
import csv
import io
import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from lab.cli import app
from lab.config import ConfigError
from lab.strategy.case import load_case
from lab.strategy.reveal import mask, new_in, reveal, reveal_steps, visible_columns
from lab.strategy.rule import load_rule
from lab.strategy.scorecard import columns, read_scorecard, write_scorecard
from lab.strategy.scoring import (
    Sensitivity,
    autonomy,
    first_pick,
    gate_status,
    normalised,
    score,
    sensitivity,
    totals,
    weighted_total,
    weightings,
)

ROOT = Path(__file__).parents[2]
CASE = ROOT / "season3" / "case"
RULE_PATH = CASE / "rule.yaml"
CRITERIA = (
    "value",
    "task_fit",
    "error_tolerance",
    "data_readiness",
    "durable_advantage",
    "time_to_evidence",
)

runner = CliRunner()


@pytest.fixture(scope="module")
def rule():
    return load_rule(RULE_PATH)


def make_csv(rule, records):
    """CSV text for the given partial records; absent columns are blank."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns(rule), lineterminator="\n")
    writer.writeheader()
    for item in records:
        writer.writerow({c: item.get(c, "") for c in columns(rule)})
    return buffer.getvalue()


def record(cid, **overrides):
    base = {
        "id": cid,
        "name": f"Case {cid}",
        "gate_outcome": "pass",
        "gate_right_tool": "pass",
        "error_cost": "low",
        "caught": "reviewer",
        "reversible": "yes",
        "design_autonomy": "assist",
        **{c: "3" for c in CRITERIA},
    }
    return {**base, **overrides}


def write_card(tmp_path, rule, records, name="card.csv"):
    path = tmp_path / name
    path.write_text(make_csv(rule, records), encoding="utf-8")
    return path


def rows_for(tmp_path, rule, records):
    return read_scorecard(write_card(tmp_path, rule, records), rule)


# --- rule -------------------------------------------------------------------------------------


def raw_rule():
    return yaml.safe_load(RULE_PATH.read_text(encoding="utf-8"))


def write_rule(tmp_path, data):
    path = tmp_path / "rule.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_rule_committed(rule):
    assert rule.criterion_ids == CRITERIA
    assert rule.gate_ids == ("outcome", "right_tool")
    assert sum(rule.weights.values()) == pytest.approx(1)


def test_load_rule_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_rule(tmp_path / "nope.yaml")


def test_load_rule_bad_yaml(tmp_path):
    path = tmp_path / "rule.yaml"
    path.write_text("a: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_rule(path)


def test_load_rule_weights_not_summing_to_one(tmp_path):
    data = raw_rule()
    data["weights"]["value"] = 0.5
    with pytest.raises(ConfigError, match="sum to 1"):
        load_rule(write_rule(tmp_path, data))


def test_load_rule_missing_anchor(tmp_path):
    data = raw_rule()
    del data["criteria"][0]["anchors"][3]
    with pytest.raises(ConfigError, match="anchors for 1, 3 and 5"):
        load_rule(write_rule(tmp_path, data))


def test_load_rule_weights_missing_a_criterion(tmp_path):
    data = raw_rule()
    del data["weights"]["value"]
    with pytest.raises(ConfigError, match="weight for each criterion"):
        load_rule(write_rule(tmp_path, data))


def test_load_rule_negative_weight(tmp_path):
    data = raw_rule()
    data["sensitivity"]["equal"]["value"] = -1
    with pytest.raises(ConfigError, match="non-negative"):
        load_rule(write_rule(tmp_path, data))


@pytest.mark.parametrize(
    ("cost", "caught", "reversible", "expected"),
    [
        ("low", "reviewer", True, "act"),
        ("low", "reviewer", False, "automate"),
        ("high", "downstream", True, "act"),
        ("high", "downstream", False, "automate"),
        ("high", "reviewer", True, "assist"),
        ("regulatory", "nobody", True, "assist"),
    ],
)
def test_autonomy_table_allowed(rule, cost, caught, reversible, expected):
    assert rule.autonomy.allowed(cost, caught, reversible) == expected


def test_autonomy_act_without_reversible_requirement(rule):
    table = rule.autonomy.model_copy(update={"act_requires_reversible": False})
    assert table.allowed("low", "reviewer", False) == "act"


# --- scorecard --------------------------------------------------------------------------------


def test_scorecard_round_trip(tmp_path, rule):
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A", outcome="o", metric="m", owner="me", notes="n", application="build"),
            record("B", gate_right_tool="fail", redirect="use SQL", reversible="no", value=""),
        ],
    )
    out = tmp_path / "sub" / "out.csv"
    write_scorecard(out, rows, rule)
    assert read_scorecard(out, rule) == rows
    assert rows[1].reversible is False
    assert rows[1].scores["value"] is None
    assert rows[0].reversible is True


def test_scorecard_accepts_bom_and_true(tmp_path, rule):
    path = tmp_path / "card.csv"
    path.write_text(make_csv(rule, [record("A", reversible="TRUE")]), encoding="utf-8-sig")
    assert read_scorecard(path, rule)[0].reversible is True


def test_scorecard_missing_file(tmp_path, rule):
    with pytest.raises(ConfigError, match="not found"):
        read_scorecard(tmp_path / "nope.csv", rule)


def test_scorecard_missing_columns(tmp_path, rule):
    path = tmp_path / "card.csv"
    path.write_text("id,name\nA,B\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="missing columns"):
        read_scorecard(path, rule)


def test_scorecard_unknown_columns(tmp_path, rule):
    path = tmp_path / "card.csv"
    path.write_text(",".join(columns(rule)) + ",extra\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown columns: extra"):
        read_scorecard(path, rule)


@pytest.mark.parametrize("bad", ["0", "6", "-1"])
def test_scorecard_score_out_of_range(tmp_path, rule, bad):
    path = write_card(tmp_path, rule, [record("A", value=bad)])
    with pytest.raises(ConfigError, match="line 2.*1 to 5"):
        read_scorecard(path, rule)


def test_scorecard_score_not_a_number(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A", task_fit="high")])
    with pytest.raises(ConfigError, match="task_fit must be a whole number"):
        read_scorecard(path, rule)


def test_scorecard_bad_reversible(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A", reversible="maybe")])
    with pytest.raises(ConfigError, match="reversible must be yes or no"):
        read_scorecard(path, rule)


def test_scorecard_bad_enum_value(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A", error_cost="huge")])
    with pytest.raises(ConfigError, match="error_cost"):
        read_scorecard(path, rule)


def test_scorecard_duplicate_ids(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A"), record("A"), record("B")])
    with pytest.raises(ConfigError, match="duplicate ids A"):
        read_scorecard(path, rule)


def test_scorecard_empty(tmp_path, rule):
    path = write_card(tmp_path, rule, [])
    with pytest.raises(ConfigError, match="no use cases"):
        read_scorecard(path, rule)


def test_scorecard_blank_rows_skipped(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A"), {}, record("B")])
    assert [r.id for r in read_scorecard(path, rule)] == ["A", "B"]


def test_scorecard_missing_id_names_the_line(tmp_path, rule):
    path = write_card(tmp_path, rule, [record("A"), record("")])
    with pytest.raises(ConfigError, match="line 3"):
        read_scorecard(path, rule)


# --- scoring ----------------------------------------------------------------------------------


def test_gate_status_open_pass_fail(tmp_path, rule):
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A"),
            record("B", gate_right_tool=""),
            record("C", gate_outcome="fail", gate_right_tool=""),
            record("D", gate_outcome="fail", gate_right_tool="fail"),
        ],
    )
    assert gate_status(rows[0], rule) == (True, ())
    assert gate_status(rows[1], rule) == (None, ())
    assert gate_status(rows[2], rule) == (False, ("outcome",))
    assert gate_status(rows[3], rule) == (False, ("outcome", "right_tool"))


def test_autonomy_unset_and_exceeded(tmp_path, rule):
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A", caught=""),
            record("B", design_autonomy=""),
            record("C", error_cost="regulatory", design_autonomy="automate"),
            record("D", design_autonomy="assist"),
        ],
    )
    assert autonomy(rows[0], rule) == (None, None)
    assert autonomy(rows[1], rule) == ("act", None)
    assert autonomy(rows[2], rule) == ("assist", True)
    assert autonomy(rows[3], rule) == ("act", False)


def test_weighted_total_needs_every_criterion(tmp_path, rule):
    rows = rows_for(tmp_path, rule, [record("A"), record("B", value="")])
    weights = normalised(rule.weights)
    assert weighted_total(rows[0], weights) == pytest.approx(3.0)
    assert weighted_total(rows[1], weights) is None


def test_totals_only_for_rows_passing_both_gates_with_every_criterion(tmp_path, rule):
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A"),
            record("B", gate_outcome="fail", redirect="r"),
            record("C", gate_right_tool=""),
            record("D", time_to_evidence=""),
        ],
    )
    assert set(totals(rows, rule, normalised(rule.weights))) == {"A"}
    scored = {s.id: s for s in score(rows, rule)}
    assert scored["A"].total == pytest.approx(3.0)
    assert scored["A"].rank == 1
    assert scored["B"].total is None
    assert scored["B"].gates_passed is False
    assert scored["C"].gates_passed is None
    assert scored["C"].rank is None
    assert scored["D"].total is None


def test_rank_orders_by_total(tmp_path, rule):
    rows = rows_for(
        tmp_path,
        rule,
        [record("A", value="2"), record("B", value="5"), record("C", value="4")],
    )
    assert {s.id: s.rank for s in score(rows, rule)} == {"B": 1, "C": 2, "A": 3}


def test_tie_break_error_tolerance_first(tmp_path, rule):
    equal = normalised(dict.fromkeys(CRITERIA, 1))
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A", value="5", error_tolerance="1"),
            record("B", value="1", error_tolerance="5"),
        ],
    )
    assert totals(rows, rule, equal)["A"] == totals(rows, rule, equal)["B"]
    assert first_pick(rows, rule, equal) == "B"


def test_tie_break_time_to_evidence_when_error_tolerance_ties(tmp_path, rule):
    equal = normalised(dict.fromkeys(CRITERIA, 1))
    rows = rows_for(
        tmp_path,
        rule,
        [
            record("A", value="4", time_to_evidence="2"),
            record("B", value="2", time_to_evidence="4"),
        ],
    )
    assert totals(rows, rule, equal)["A"] == totals(rows, rule, equal)["B"]
    assert first_pick(rows, rule, equal) == "B"


def test_tie_break_falls_back_to_id(tmp_path, rule):
    rows = rows_for(tmp_path, rule, [record("B"), record("A"), record("C")])
    ranks = {s.id: s.rank for s in score(rows, rule)}
    assert ranks == {"A": 1, "B": 2, "C": 3}
    assert first_pick(rows, rule, normalised(rule.weights)) == "A"


def test_first_pick_none_when_nothing_eligible(tmp_path, rule):
    rows = rows_for(tmp_path, rule, [record("A", gate_outcome="fail")])
    assert first_pick(rows, rule, normalised(rule.weights)) is None


def test_weightings_count_with_committed_rule(rule):
    found = weightings(rule)
    names = [n for n, _ in found]
    assert len(names) == 15
    assert names[0] == "equal"
    assert names[-2:] == ["ceo", "regulator"]
    for _, weights in found:
        assert sum(weights.values()) == pytest.approx(1)


def test_weightings_respect_halve_and_double_flags(rule):
    spec = rule.sensitivity.model_copy(update={"halve_each": False, "double_each": False})
    trimmed = rule.model_copy(update={"sensitivity": spec})
    assert [n for n, _ in weightings(trimmed)] == ["equal", "ceo", "regulator"]


def test_sensitivity_counts(tmp_path, rule):
    rows = rows_for(tmp_path, rule, [record("A", value="5"), record("B", value="1")])
    result = sensitivity(rows, rule)
    assert result.base_pick == "A"
    assert result.out_of == 15
    assert result.holds == 15
    assert result.share == 1.0
    assert result.picks == {"A": 15}


def test_sensitivity_with_no_pick(tmp_path, rule):
    rows = rows_for(tmp_path, rule, [record("A", gate_outcome="fail")])
    result = sensitivity(rows, rule)
    assert result.base_pick is None
    assert result.holds == 0
    assert result.picks == {}


def test_sensitivity_share_zero_when_empty():
    empty = Sensitivity(base_pick=None, alternatives=(), holds=0, out_of=0, picks={})
    assert empty.share == 0.0


# --- reveal -----------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def case_rows(rule):
    return load_case(CASE, rule).rows(rule)


def test_reveal_e0_shows_nothing(rule, case_rows):
    step = reveal(case_rows, rule, 0)
    assert step["through"] == "E0"
    assert step["new"] == []
    assert not any(step["columns"].values())
    for row in step["rows"]:
        assert row["outcome"] == ""
        assert row["gate_outcome"] == ""
        assert row["value"] == ""
        assert row["total"] is None
        assert row["rank"] is None
        assert row["allowed_autonomy"] is None


def test_reveal_e2_shows_g2_and_task_fit_but_not_error_tolerance(rule, case_rows):
    step = reveal(case_rows, rule, 2)
    assert step["columns"]["gate:right_tool"] is True
    assert step["columns"]["criterion:task_fit"] is True
    assert step["columns"]["criterion:error_tolerance"] is False
    for row in step["rows"]:
        assert row["gate_right_tool"] in {"pass", "fail"}
        assert row["task_fit"] != "" or row["gate_right_tool"] == "fail"
        assert row["error_tolerance"] == ""
        assert row["error_cost"] == ""
        assert row["caught"] == ""
        assert row["total"] is None
        assert row["design_autonomy"] == ""


def test_reveal_totals_only_at_e11(rule, case_rows):
    for episode in (1, 2, 4, 5, 6, 8):
        assert all(r["total"] is None for r in reveal(case_rows, rule, episode)["rows"])
    final = reveal(case_rows, rule, 11)
    assert any(r["total"] is not None for r in final["rows"])
    assert "Weighted total and rank" in final["new"]


def test_reveal_autonomy_and_sourcing_appear_on_their_episodes(rule, case_rows):
    step = reveal(case_rows, rule, 5)
    assert step["columns"]["autonomy"] is True
    assert all(r["allowed_autonomy"] is not None for r in step["rows"])
    assert all(r["application"] == "" for r in step["rows"])
    assert all(r["application"] != "" for r in reveal(case_rows, rule, 8)["rows"])


def test_mask_leaves_original_row_untouched(rule, case_rows):
    original = case_rows[0]
    masked = mask(original, rule, 0)
    assert masked.outcome == ""
    assert original.outcome != ""
    assert masked.scores == dict.fromkeys(CRITERIA)


def test_reveal_steps_and_new_in(rule):
    assert reveal_steps(rule) == [1, 2, 4, 5, 6, 8, 11]
    assert new_in(rule, 1) == ["G1 Outcome", "Value of the outcome"]
    assert new_in(rule, 5) == ["Autonomy (a setting)"]
    assert new_in(rule, 8) == ["Sourcing (a setting)"]
    assert new_in(rule, 11) == ["Time to evidence", "Weighted total and rank"]
    assert new_in(rule, 3) == []


def test_visible_columns_without_error_tolerance_criterion(rule):
    criteria = tuple(c for c in rule.criteria if c.id != "error_tolerance")
    trimmed = rule.model_copy(update={"criteria": criteria})
    assert visible_columns(trimmed, 3)["error_facts"] is False
    assert visible_columns(trimmed, 4)["error_facts"] is True


# --- case -------------------------------------------------------------------------------------


def copy_case(tmp_path):
    dest = tmp_path / "case"
    shutil.copytree(CASE, dest, ignore=shutil.ignore_patterns("results"))
    return dest


def edit_scores(folder, change):
    path = folder / "scores.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def passing_id(data):
    return next(
        cid
        for cid, c in data["candidates"].items()
        if all(g["result"] == "pass" for g in c["gates"].values())
    )


def failing_id(data):
    return next(
        cid
        for cid, c in data["candidates"].items()
        if any(g["result"] == "fail" for g in c["gates"].values())
    )


def test_load_case_committed(rule):
    case = load_case(CASE, rule)
    assert len(case.rows(rule)) == len(case.candidates)
    assert case.stop_criteria is not None
    kinds = {s.evidence_kind for sc in case.scores.values() for s in sc.scores.values()}
    assert kinds == {"measured", "assumption"}


def test_load_case_missing_file(tmp_path, rule):
    with pytest.raises(ConfigError, match="not found"):
        load_case(tmp_path, rule)


def test_load_case_not_a_mapping(tmp_path, rule):
    folder = copy_case(tmp_path)
    (folder / "scores.yaml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="mapping at the top level"):
        load_case(folder, rule)


def test_load_case_invalid_model(tmp_path, rule):
    folder = copy_case(tmp_path)
    edit_scores(folder, lambda d: d.update({"stop_criteria": {"candidate": "x"}}))
    with pytest.raises(ConfigError, match="not a valid case"):
        load_case(folder, rule)


def test_load_case_failed_gate_without_redirect(tmp_path, rule):
    folder = copy_case(tmp_path)

    def change(data):
        data["candidates"][failing_id(data)]["redirect"] = ""

    edit_scores(folder, change)
    with pytest.raises(ConfigError, match="fails a gate but has no redirect"):
        load_case(folder, rule)


def test_load_case_passing_candidate_missing_a_criterion(tmp_path, rule):
    folder = copy_case(tmp_path)

    def change(data):
        del data["candidates"][passing_id(data)]["scores"]["value"]

    edit_scores(folder, change)
    with pytest.raises(ConfigError, match="not scored on every criterion"):
        load_case(folder, rule)


def test_load_case_unknown_criterion(tmp_path, rule):
    folder = copy_case(tmp_path)

    def change(data):
        scores = data["candidates"][passing_id(data)]["scores"]
        scores["charisma"] = copy.deepcopy(scores["value"])

    edit_scores(folder, change)
    with pytest.raises(ConfigError, match="unknown criteria"):
        load_case(folder, rule)


def test_load_case_missing_gate_and_unscored_candidate(tmp_path, rule):
    folder = copy_case(tmp_path)

    def change(data):
        cid = passing_id(data)
        del data["candidates"][cid]["gates"]["outcome"]
        other = next(k for k in data["candidates"] if k != cid)
        del data["candidates"][other]

    edit_scores(folder, change)
    with pytest.raises(ConfigError) as info:
        load_case(folder, rule)
    assert "must give every gate" in str(info.value)
    assert "differ" in str(info.value)


def test_score_needs_exactly_one_kind_of_evidence(tmp_path, rule):
    folder = copy_case(tmp_path)

    def change(data):
        scores = data["candidates"][passing_id(data)]["scores"]
        scores["value"]["assumption"] = "a"
        scores["value"]["measured"] = {"path": "p", "figure": "f"}

    edit_scores(folder, change)
    with pytest.raises(ConfigError, match="exactly one of measured or assumption"):
        load_case(folder, rule)


# --- CLI and charts ---------------------------------------------------------------------------


def invoke_score(card, *extra):
    return runner.invoke(app, ["strategy", "score", str(card), "--rule", str(RULE_PATH), *extra])


def test_score_command_writes_json(tmp_path, rule):
    card = write_card(
        tmp_path,
        rule,
        [
            record("A", value="5", design_autonomy="act", error_cost="regulatory"),
            record("B", value="2"),
            record("C", gate_outcome="fail", redirect="r"),
        ],
    )
    out = tmp_path / "out"
    result = invoke_score(card, "--out", str(out))
    assert result.exit_code == 0, result.output
    assert "First pick: A" in result.output
    assert "holds in 15 of 15" in result.output
    assert "(above it)" in result.output
    assert "FAIL" in result.output
    scorecard = json.loads((out / "scorecard.json").read_text(encoding="utf-8"))
    sens = json.loads((out / "sensitivity.json").read_text(encoding="utf-8"))
    assert [r["id"] for r in scorecard["rows"]] == ["A", "B", "C"]
    assert scorecard["rule"]["version"] == 1
    assert sens["base_pick"] == "A"
    assert sens["share"] == 1.0


def test_score_command_reports_where_pick_changes(tmp_path, rule):
    card = write_card(
        tmp_path,
        rule,
        [
            record("A", value="5", error_tolerance="1", task_fit="1"),
            record("B", value="1", error_tolerance="5", task_fit="5"),
        ],
    )
    result = invoke_score(card)
    assert result.exit_code == 0, result.output
    assert "Where it changes:" in result.output
    assert "holds in 13 of 15" in result.output


def test_score_command_no_pick_yet(tmp_path, rule):
    card = write_card(tmp_path, rule, [record("A", gate_outcome="", value="")])
    result = invoke_score(card)
    assert result.exit_code == 0, result.output
    assert "First pick: none yet" in result.output
    assert "open" in result.output


def test_score_command_bad_file_exits_1(tmp_path, rule):
    card = write_card(tmp_path, rule, [record("A", value="9")])
    result = invoke_score(card)
    assert result.exit_code == 1
    assert "Error" in result.output


def test_score_command_bad_rule_exits_1(tmp_path, rule):
    card = write_card(tmp_path, rule, [record("A")])
    result = runner.invoke(
        app, ["strategy", "score", str(card), "--rule", str(tmp_path / "missing.yaml")]
    )
    assert result.exit_code == 1


def test_reveal_command_through_e5(tmp_path):
    case_dir = copy_case(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(
        app,
        ["strategy", "reveal", "--through", "E5", "--case", str(case_dir), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert "Through E5; new: Autonomy (a setting)" in result.output
    step = json.loads((out / "scorecard-e5.json").read_text(encoding="utf-8"))
    assert step["through"] == "E5"
    assert list((out / "charts").glob("scorecard-e5*"))


def test_reveal_command_defaults_out_to_case_results(tmp_path):
    case_dir = copy_case(tmp_path)
    result = runner.invoke(app, ["strategy", "reveal", "--through", "2", "--case", str(case_dir)])
    assert result.exit_code == 0, result.output
    assert (case_dir / "results" / "scorecard-e2.json").exists()


def test_reveal_command_bad_episode(tmp_path):
    case_dir = copy_case(tmp_path)
    result = runner.invoke(
        app, ["strategy", "reveal", "--through", "five", "--case", str(case_dir)]
    )
    assert result.exit_code != 0


def test_reveal_command_bad_case_exits_1(tmp_path):
    result = runner.invoke(
        app, ["strategy", "reveal", "--through", "E5", "--case", str(tmp_path / "nope")]
    )
    assert result.exit_code == 1


def test_case_command_writes_everything(tmp_path):
    case_dir = copy_case(tmp_path)
    result = runner.invoke(app, ["strategy", "case", "--case", str(case_dir)])
    assert result.exit_code == 0, result.output
    assert "First pick:" in result.output
    results = case_dir / "results"
    for name in (
        "scorecard.csv",
        "scorecard.json",
        "sensitivity.json",
        "scorecard-e1.json",
        "scorecard-e11.json",
    ):
        assert (results / name).exists(), name
    charts = {p.name for p in (results / "charts").iterdir()}
    assert any(n.startswith("scorecard-final") for n in charts)
    assert any(n.startswith("sensitivity") for n in charts)
    assert any(n.startswith("scorecard-e8") for n in charts)


def test_case_command_bad_case_exits_1(tmp_path):
    result = runner.invoke(app, ["strategy", "case", "--case", str(tmp_path)])
    assert result.exit_code == 1
