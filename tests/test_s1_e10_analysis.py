"""The S1 E10 analysis (specification sections 7.5 and 7.6).

Records are built by hand, so the statistics, the highlight rules, and the report are checked
against known accuracies and token counts without any API call.
"""

import csv
import shutil
from pathlib import Path

import pytest

from lab.config import load_config
from lab.experiments import load_sibling
from lab.plan import PlannedCall, build_request, make_call_id
from lab.providers.base import GenerationResult, request_hash
from lab.raw_log import RunRecord

FIELD_NOTE = Path("field-notes/s1-e10-reasoning-vs-standard")
CONFIG_PATH = FIELD_NOTE / "config.yaml"

LOWEST = "lowest"
HIGH = "high"
EXTRACTION = "extraction"
PUZZLE = "constraint-puzzle"


@pytest.fixture(scope="module")
def module():
    return load_sibling(FIELD_NOTE / "analyse.py")


@pytest.fixture(scope="module")
def metrics():
    return load_sibling(FIELD_NOTE / "metrics.py")


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def items(module):
    return module._items(FIELD_NOTE)


@pytest.fixture(scope="module")
def models(config):
    return [model.display_label for model in config.models]


@pytest.fixture
def folder(tmp_path):
    """A field note folder with the committed items but no results of its own."""
    shutil.copytree(FIELD_NOTE / "tasks", tmp_path / "tasks")
    return tmp_path


@pytest.fixture
def no_charts(module, monkeypatch):
    """Skip chart rendering, which is slow. TestCharts exercises it directly."""
    monkeypatch.setattr(module, "_charts", lambda *args, **kwargs: [])


def _record(
    config,
    *,
    model_index: int = 0,
    mode: str = LOWEST,
    task: str = EXTRACTION,
    index: int = 0,
    text: str = "ANSWER: 0000",
    output_tokens: int = 40,
    reasoning_tokens: int | None = 0,
    first_answer_ms: float | None = 500.0,
    first_thinking_ms: float | None = None,
    total_latency_ms: float = 900.0,
    finish_reason: str = "stop",
    failed: bool = False,
) -> RunRecord:
    model = config.models[model_index]
    cell = {"task": task, "item_index": index}
    request = build_request(model, mode, prompt="prompt")
    call = PlannedCall(
        call_id=make_call_id(model_label=model.display_label, mode=mode, cell=cell),
        model_label=model.display_label,
        mode=mode,
        cell=cell,
        request=request,
    )
    if failed:
        return RunRecord.for_call(call, source="api", attempts=1, error="boom")
    result = GenerationResult(
        request_hash=request_hash(request),
        provider=model.provider,
        model_requested=model.model,
        model_returned=f"{model.model}-20260918",
        text=text,
        input_tokens=300,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cached_input_tokens=None,
        time_to_first_answer_token_ms=first_answer_ms,
        time_to_first_thinking_ms=first_thinking_ms,
        total_latency_ms=total_latency_ms,
        finish_reason=finish_reason,
        timestamp_utc="2026-09-18T12:00:00+00:00",
    )
    return RunRecord.for_call(call, source="api", attempts=1, result=result)


def _answers(items, task: str, index: int) -> str:
    return next(item.answer for item in items if item.task == task and item.index == index)


def _grid(
    config,
    items,
    *,
    correct_in_high: int,
    correct_in_lowest: int,
    count: int = 10,
    model_index: int = 0,
    task: str = EXTRACTION,
    high_output_tokens: int = 1000,
):
    """One model, one task, `count` items, with the given number right in each mode."""
    records = []
    for index in range(count):
        answer = _answers(items, task, index)
        for mode, right in ((LOWEST, correct_in_lowest), (HIGH, correct_in_high)):
            text = f"ANSWER: {answer}" if index < right else "ANSWER: nothing"
            records.append(
                _record(
                    config,
                    model_index=model_index,
                    mode=mode,
                    task=task,
                    index=index,
                    text=text,
                    output_tokens=high_output_tokens if mode == HIGH else 50,
                    first_thinking_ms=300.0 if mode == HIGH else None,
                    first_answer_ms=1500.0 if mode == HIGH else 500.0,
                )
            )
    return records


def _every_model(config, items, *, correct_in_high, correct_in_lowest, **kwargs):
    """The same grid run by all three models, which is what the pooled highlight rule needs."""
    return [
        record
        for index in range(len(config.models))
        for record in _grid(
            config,
            items,
            correct_in_high=correct_in_high,
            correct_in_lowest=correct_in_lowest,
            model_index=index,
            **kwargs,
        )
    ]


class TestScoring:
    def test_the_right_integer_is_correct(self, metrics):
        assert metrics.score("ANSWER: 4842", "4842", "integer") == (True, "4842")

    def test_a_different_integer_is_wrong(self, metrics):
        correct, answer = metrics.score("ANSWER: 4843", "4842", "integer")
        assert not correct
        assert answer == "4843"

    def test_a_missing_answer_line_is_wrong_and_unparsed(self, metrics):
        assert metrics.score("I think it is 4842.", "4842", "integer") == (False, None)

    def test_an_ordered_list_matches_whatever_the_spacing(self, metrics):
        correct, _ = metrics.score(
            "ANSWER: audit,balancing,flushing", "audit, balancing, flushing", "ordered-list"
        )
        assert correct

    def test_an_ordered_list_given_without_commas_still_matches(self, metrics):
        correct, _ = metrics.score(
            "ANSWER: audit balancing flushing", "audit, balancing, flushing", "ordered-list"
        )
        assert correct

    def test_a_different_order_is_wrong(self, metrics):
        correct, _ = metrics.score(
            "ANSWER: balancing, audit, flushing", "audit, balancing, flushing", "ordered-list"
        )
        assert not correct

    def test_case_does_not_matter(self, metrics):
        correct, _ = metrics.score(
            "ANSWER: Audit, Balancing, Flushing", "audit, balancing, flushing", "ordered-list"
        )
        assert correct


class TestOutcomes:
    def test_every_successful_record_is_scored(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=8, correct_in_lowest=4), items
        )
        assert len(scored) == 20

    def test_a_record_for_an_unknown_item_is_left_out(self, metrics, config, items):
        stray = _record(config, task=EXTRACTION, index=999)
        assert metrics.outcomes([stray], items) == []

    def test_failed_calls_are_not_scored(self, metrics, config, items):
        assert metrics.outcomes([_record(config, failed=True)], items) == []


class TestStatistics:
    def test_accuracy_counts_the_right_answers(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=8, correct_in_lowest=4), items
        )
        found = metrics.accuracy(metrics.select(scored, mode=HIGH))
        assert (found.correct, found.trials) == (8, 10)
        assert found.low < found.point < found.high

    def test_accuracy_of_nothing_is_none(self, metrics):
        assert metrics.accuracy([]) is None

    def test_the_gain_is_paired_over_the_same_items(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=8, correct_in_lowest=4), items
        )
        found = metrics.gain(scored, lowest_mode=LOWEST, high_mode=HIGH)
        assert found.pairs == 10
        assert found.change == pytest.approx(0.4)

    def test_an_item_answered_in_only_one_mode_is_not_paired(self, metrics, config, items):
        records = [_record(config, mode=HIGH, index=0), _record(config, mode=LOWEST, index=1)]
        assert (
            metrics.gain(metrics.outcomes(records, items), lowest_mode=LOWEST, high_mode=HIGH)
            is None
        )

    def test_a_clear_gain_excludes_zero(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=10, correct_in_lowest=0), items
        )
        assert metrics.gain(scored, lowest_mode=LOWEST, high_mode=HIGH).significant

    def test_no_change_includes_zero(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=5, correct_in_lowest=5), items
        )
        assert not metrics.gain(scored, lowest_mode=LOWEST, high_mode=HIGH).significant

    def test_the_ninetieth_percentile_is_a_measured_value(self, metrics):
        assert metrics.percentile_90(list(range(1, 11))) == 9

    def test_percentiles_and_medians_of_nothing_are_none(self, metrics):
        assert metrics.percentile_90([]) is None
        assert metrics.median([]) is None
        assert metrics.mean([]) is None

    def test_missing_measurements_are_left_out_rather_than_counted_as_zero(self, metrics):
        assert metrics.median([None, 4.0, None]) == 4.0

    def test_the_comparison_reports_every_ratio(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=8, correct_in_lowest=4), items
        )
        found = metrics.compare(
            scored,
            model=config.models[0].display_label,
            task=EXTRACTION,
            lowest_mode=LOWEST,
            high_mode=HIGH,
        )
        assert found.output_token_multiple == pytest.approx(20.0)
        assert found.extra_output_tokens == pytest.approx(950.0)
        assert found.latency_multiple == pytest.approx(1.0)
        assert found.first_answer_token_multiple == pytest.approx(3.0)
        assert found.accuracy_change_points == pytest.approx(40.0)
        assert found.points_per_thousand_tokens == pytest.approx(40.0 / 0.95)

    def test_points_per_thousand_tokens_is_none_when_nothing_extra_was_spent(
        self, metrics, config, items
    ):
        records = [_record(config, mode=mode, index=0, output_tokens=50) for mode in (LOWEST, HIGH)]
        found = metrics.compare(
            metrics.outcomes(records, items),
            model=config.models[0].display_label,
            task=EXTRACTION,
            lowest_mode=LOWEST,
            high_mode=HIGH,
        )
        assert found.points_per_thousand_tokens is None

    def test_the_token_multiple_uses_billed_output_tokens(self, metrics, config, items):
        scored = metrics.outcomes(
            _grid(config, items, correct_in_high=8, correct_in_lowest=4), items
        )
        assert metrics.token_multiple(
            scored, task=EXTRACTION, lowest_mode=LOWEST, high_mode=HIGH
        ) == pytest.approx(20.0)


class TestHighlightRules:
    def test_the_biggest_clear_gain_is_highlighted(self, module, metrics, config, items, models):
        scored = metrics.outcomes(
            _every_model(config, items, correct_in_high=10, correct_in_lowest=0), items
        )
        assert module.best_gain_task(scored, (EXTRACTION, PUZZLE), models) == 0

    def test_a_gain_inside_chance_is_not_highlighted(self, module, metrics, config, items, models):
        scored = metrics.outcomes(
            _every_model(config, items, correct_in_high=6, correct_in_lowest=5), items
        )
        assert module.best_gain_task(scored, (EXTRACTION, PUZZLE), models) is None

    def test_a_pooled_gain_is_not_enough_when_one_model_went_the_other_way(
        self, module, metrics, config, items, models
    ):
        """Pooling the same 30 items across three models narrows the interval more than the
        data warrants, so every model must move the same way before the bar is painted."""
        records = _grid(config, items, correct_in_high=10, correct_in_lowest=0, model_index=0)
        records += _grid(config, items, correct_in_high=10, correct_in_lowest=0, model_index=1)
        records += _grid(config, items, correct_in_high=2, correct_in_lowest=8, model_index=2)
        scored = metrics.outcomes(records, items)
        pooled = metrics.gain(
            metrics.select(scored, task=EXTRACTION), lowest_mode=LOWEST, high_mode=HIGH
        )
        assert pooled.significant
        assert module.best_gain_task(scored, (EXTRACTION,), models) is None

    def test_the_largest_token_multiple_is_highlighted(self, module):
        assert module.largest_multiple_task([2.0, 9.0, 3.0]) == 1

    def test_nothing_is_highlighted_when_no_task_used_more_tokens(self, module):
        assert module.largest_multiple_task([1.0, 0.5, None]) is None

    def test_the_best_value_point_is_highlighted(self, module):
        points = [("A", "Extract", 100.0, 1.0), ("B", "Puzzle", 4000.0, 30.0)]
        assert module.best_value_point(points) == ("A", "Extract")

    def test_no_point_gained_accuracy_means_no_highlight(self, module):
        assert module.best_value_point([("A", "Extract", 100.0, -2.0)]) is None

    def test_the_longest_wait_before_the_answer_is_highlighted(self, module):
        rows = [("a", 100.0, 900.0), ("b", None, 400.0), ("c", 200.0, 1800.0)]
        assert module.longest_thinking_gap(rows) == 2

    def test_no_thinking_anywhere_means_no_highlight(self, module):
        assert module.longest_thinking_gap([("a", None, 400.0)]) is None


class TestSummary:
    def test_it_writes_a_row_per_scored_call(self, module, config, items, folder, no_charts):
        module.analyse(config, folder, _grid(config, items, correct_in_high=8, correct_in_lowest=4))
        rows = list(csv.DictReader((folder / "results" / "summary.csv").open(encoding="utf-8")))
        assert len(rows) == 20
        assert list(rows[0]) == list(module.SUMMARY_COLUMNS)

    def test_it_records_the_reasoning_level_each_mode_ran_with(
        self, module, config, items, folder, no_charts
    ):
        module.analyse(config, folder, _grid(config, items, correct_in_high=8, correct_in_lowest=4))
        rows = list(csv.DictReader((folder / "results" / "summary.csv").open(encoding="utf-8")))
        levels = {row["mode"]: row["reasoning"] for row in rows}
        assert levels == {LOWEST: "off", HIGH: "high"}

    def test_it_records_whether_thinking_was_shown(self, module, config, items, folder, no_charts):
        module.analyse(config, folder, _grid(config, items, correct_in_high=8, correct_in_lowest=4))
        rows = list(csv.DictReader((folder / "results" / "summary.csv").open(encoding="utf-8")))
        shown = {row["mode"]: row["show_thinking"] for row in rows}
        assert shown == {LOWEST: "False", HIGH: "True"}

    def test_an_unparsed_answer_is_recorded_as_empty(
        self, module, config, items, folder, no_charts
    ):
        records = [_record(config, text="No answer line here.")]
        module.analyse(config, folder, records)
        (row,) = list(csv.DictReader((folder / "results" / "summary.csv").open(encoding="utf-8")))
        assert row["answer_given"] == ""
        assert row["parsed"] == "False"
        assert row["correct"] == "False"


class TestReport:
    def test_it_reports_the_paired_gain_per_task(self, module, config, items, folder, no_charts):
        report = module.analyse(
            config, folder, _grid(config, items, correct_in_high=10, correct_in_lowest=0)
        )
        assert "excludes zero" in report
        assert "+100.0 points" in report

    def test_it_says_when_a_change_is_within_chance(self, module, config, items, folder, no_charts):
        report = module.analyse(
            config, folder, _grid(config, items, correct_in_high=5, correct_in_lowest=5)
        )
        assert "includes zero" in report

    def test_a_full_parse_rate_is_stated(self, module, config, items, folder, no_charts):
        report = module.analyse(
            config, folder, _grid(config, items, correct_in_high=8, correct_in_lowest=4)
        )
        assert "Answer parse rate: 100%" in report

    def test_unparsed_answers_are_named(self, module, config, items, folder, no_charts):
        records = [_record(config, text="I am not going to answer.")]
        report = module.analyse(config, folder, records)
        assert "had no ANSWER line" in report
        assert EXTRACTION in report

    def test_truncated_responses_are_flagged(self, module, config, items, folder, no_charts):
        records = [_record(config, finish_reason="length")]
        report = module.analyse(config, folder, records)
        assert "hit the output limit" in report

    def test_no_truncation_is_stated_plainly(self, module, config, items, folder, no_charts):
        report = module.analyse(config, folder, [_record(config)])
        assert "No response hit its output limit" in report

    def test_failed_calls_are_reported(self, module, config, items, folder, no_charts):
        records = [_record(config), _record(config, index=1, failed=True)]
        report = module.analyse(config, folder, records)
        assert "1 call(s) failed" in report

    def test_the_comparison_table_shows_multiples(self, module, config, items, folder, no_charts):
        report = module.analyse(
            config, folder, _grid(config, items, correct_in_high=8, correct_in_lowest=4)
        )
        assert "20.0x" in report

    def test_reasoning_tokens_are_shown_where_reported(
        self, module, config, items, folder, no_charts
    ):
        records = [_record(config, mode=HIGH, reasoning_tokens=800, output_tokens=1000)]
        report = module.analyse(config, folder, records)
        assert "reasoning 800 / 800" in report

    def test_unreported_reasoning_tokens_are_named_as_such(
        self, module, config, items, folder, no_charts
    ):
        records = [_record(config, model_index=2, mode=HIGH, reasoning_tokens=None)]
        report = module.analyse(config, folder, records)
        assert "reasoning not reported" in report

    def test_results_with_nothing_scorable_are_refused(self, module, config, folder):
        with pytest.raises(module.AnalysisError, match="nothing to score"):
            module.analyse(config, folder, [])


class TestCharts:
    def test_it_writes_every_chart(self, module, config, items, folder):
        module.analyse(
            config, folder, _grid(config, items, correct_in_high=10, correct_in_lowest=0)
        )
        written = sorted(path.name for path in (folder / "results" / "charts").iterdir())
        assert "accuracy-by-task-slide.png" in written
        assert "accuracy-by-task-slide.svg" in written
        assert "accuracy-by-task-article.png" in written
        assert "output-token-multiple-by-task-slide.png" in written
        assert "cost-of-accuracy-slide.png" in written
        assert "two-kinds-of-first-token-slide.png" in written

    def test_charts_render_when_no_element_meets_its_rule(self, module, config, items, folder):
        # Identical accuracy and identical token counts in both modes: nothing qualifies.
        records = []
        for index in range(6):
            answer = _answers(items, EXTRACTION, index)
            for mode in (LOWEST, HIGH):
                records.append(_record(config, mode=mode, index=index, text=f"ANSWER: {answer}"))
        module.analyse(config, folder, records)
        assert (folder / "results" / "charts" / "accuracy-by-task-slide.png").exists()

    def test_a_task_run_in_only_one_mode_is_left_off_the_bar_charts(
        self, module, metrics, config, items
    ):
        records = [_record(config, mode=LOWEST, index=index) for index in range(3)]
        scored = metrics.outcomes(records, items)
        assert module.drawable_tasks(scored, (EXTRACTION, PUZZLE)) == []

    def test_bar_charts_are_skipped_when_no_task_has_both_modes(
        self, module, config, items, folder
    ):
        records = [_record(config, mode=LOWEST, index=index) for index in range(3)]
        module.analyse(config, folder, records)
        charts = folder / "results" / "charts"
        assert not (charts / "accuracy-by-task-slide.png").exists()
        assert (charts / "two-kinds-of-first-token-slide.png").exists()


class TestPairedComparisons:
    def test_only_items_answered_in_both_modes_are_compared(self, metrics, config, items):
        """A call that failed in one mode must not tilt the other mode's token average."""
        records = _grid(config, items, correct_in_high=5, correct_in_lowest=5, count=4)
        # One more high call, with no partner in the lowest mode and a far larger token count.
        records.append(
            _record(config, mode=HIGH, index=9, text="ANSWER: nothing", output_tokens=99_000)
        )
        scored = metrics.outcomes(records, items)
        found = metrics.compare(
            scored,
            model=config.models[0].display_label,
            task=EXTRACTION,
            lowest_mode=LOWEST,
            high_mode=HIGH,
        )
        assert found.extra_output_tokens == pytest.approx(950.0)
        assert found.output_token_multiple == pytest.approx(20.0)

    def test_the_token_multiple_uses_the_same_items_on_both_sides(self, metrics, config, items):
        records = _grid(config, items, correct_in_high=5, correct_in_lowest=5, count=4)
        records.append(
            _record(config, mode=HIGH, index=9, text="ANSWER: nothing", output_tokens=99_000)
        )
        scored = metrics.outcomes(records, items)
        assert metrics.token_multiple(
            scored, task=EXTRACTION, lowest_mode=LOWEST, high_mode=HIGH
        ) == pytest.approx(20.0)

    def test_no_cost_per_point_when_high_reasoning_spent_fewer_tokens(self, metrics, config, items):
        """A negative denominator would print the best result as the worst."""
        records = _grid(
            config, items, correct_in_high=8, correct_in_lowest=4, count=6, high_output_tokens=10
        )
        found = metrics.compare(
            metrics.outcomes(records, items),
            model=config.models[0].display_label,
            task=EXTRACTION,
            lowest_mode=LOWEST,
            high_mode=HIGH,
        )
        assert found.extra_output_tokens < 0
        assert found.accuracy_change_points > 0
        assert found.points_per_thousand_tokens is None


class TestFirstTokenRows:
    def test_both_medians_come_from_the_calls_that_reported_thinking(
        self, module, metrics, config, items, models
    ):
        """Otherwise the two ends of the drawn span sit on different populations."""
        records = [
            _record(config, mode=HIGH, index=0, first_thinking_ms=4000.0, first_answer_ms=5000.0),
            _record(config, mode=HIGH, index=1, first_thinking_ms=None, first_answer_ms=200.0),
            _record(config, mode=HIGH, index=2, first_thinking_ms=None, first_answer_ms=200.0),
        ]
        scored = metrics.outcomes(records, items)
        (row,) = module._first_token_rows(scored, models)
        assert row[1] == pytest.approx(4000.0)
        assert row[2] == pytest.approx(5000.0)


class TestFailureCounting:
    def test_one_call_retried_twice_counts_once(self, module, config, items, folder, no_charts):
        records = [
            _record(config),
            _record(config, index=1, failed=True),
            _record(config, index=1, failed=True),
        ]
        report = module.analyse(config, folder, records)
        assert "1 call(s) failed" in report
