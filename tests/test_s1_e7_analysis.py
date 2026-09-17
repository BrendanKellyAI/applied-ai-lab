"""The S1 E7 analysis (specification sections 6.5, 6.6).

Records are built by hand here, so the analysis is checked against known accuracies without
any dataset or API call.
"""

import csv
import importlib.util
from pathlib import Path

import pytest

from lab.config import load_config
from lab.plan import PlannedCall, build_request, make_call_id
from lab.providers.base import GenerationResult, request_hash
from lab.raw_log import RunRecord

FIELD_NOTE = Path("field-notes/s1-e7-lost-in-the-middle")
CONFIG_PATH = FIELD_NOTE / "config.yaml"

LENGTHS = (4000, 16000, 64000)
POSITIONS = (0, 25, 50, 75, 100)
FACTS = 6


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("s1_e7_analyse", FIELD_NOTE / "analyse.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def builder():
    spec = importlib.util.spec_from_file_location(
        "s1_e7_build_dataset_for_analysis", FIELD_NOTE / "build_dataset.py"
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


def _record(
    config,
    *,
    model_index: int,
    length: int,
    position: int,
    fact_index: int,
    text: str,
    finish_reason: str = "stop",
    reasoning_tokens: int | None = 0,
    cached_input_tokens: int | None = 0,
) -> RunRecord:
    model = config.models[model_index]
    cell = {
        "context_length_tokens": length,
        "position_percent": position,
        "fact_index": fact_index,
    }
    request = build_request(model, "standard", prompt="prompt", system="system")
    call = PlannedCall(
        call_id=make_call_id(model_label=model.display_label, mode="standard", cell=cell),
        model_label=model.display_label,
        mode="standard",
        cell=cell,
        request=request,
    )
    result = GenerationResult(
        request_hash=request_hash(request),
        provider=model.provider,
        model_requested=model.model,
        model_returned=f"{model.model}-20260917",
        text=text,
        input_tokens=length,
        output_tokens=8,
        reasoning_tokens=reasoning_tokens,
        cached_input_tokens=cached_input_tokens,
        time_to_first_answer_token_ms=120.0,
        time_to_first_thinking_ms=None,
        total_latency_ms=400.0,
        finish_reason=finish_reason,
        timestamp_utc="2026-09-17T12:00:00+00:00",
    )
    return RunRecord.for_call(call, source="api", attempts=1, result=result)


def _full_grid(config, facts, correct_when=lambda **cell: True) -> list[RunRecord]:
    """One record per model, length, position, and fact."""
    records = []
    for model_index in range(len(config.models)):
        for length in LENGTHS:
            for position in POSITIONS:
                for fact_index in range(FACTS):
                    right = correct_when(
                        model_index=model_index,
                        length=length,
                        position=position,
                        fact_index=fact_index,
                    )
                    value = facts[fact_index].value
                    records.append(
                        _record(
                            config,
                            model_index=model_index,
                            length=length,
                            position=position,
                            fact_index=fact_index,
                            text=value if right else "0000",
                        )
                    )
    return records


@pytest.fixture(scope="module")
def facts(builder, config):
    return builder.make_facts(config.seed, FACTS)


@pytest.fixture
def no_charts(module, monkeypatch):
    """Skip chart rendering, which is slow. TestCharts exercises it directly."""
    monkeypatch.setattr(module, "_charts", lambda *args, **kwargs: [])


class TestScoring:
    def test_a_response_with_the_value_is_correct(self, module, config, facts):
        record = _record(
            config,
            model_index=0,
            length=4000,
            position=0,
            fact_index=0,
            text=f"The code is {facts[0].value}.",
        )

        assert module.score(record, facts) is True

    def test_a_response_with_another_facts_value_is_wrong(self, module, config, facts):
        record = _record(
            config,
            model_index=0,
            length=4000,
            position=0,
            fact_index=0,
            text=facts[1].value,
        )

        assert module.score(record, facts) is False

    def test_a_truncated_response_is_scored_wrong(self, module, config, facts):
        record = _record(
            config,
            model_index=0,
            length=4000,
            position=0,
            fact_index=0,
            text="The maintenance code for turbine",
            finish_reason="length",
        )

        assert module.score(record, facts) is False


class TestSummaryCsv:
    def test_one_row_per_call_with_the_fields_readers_need(
        self, module, config, facts, tmp_path, no_charts
    ):
        records = _full_grid(config, facts)

        module.analyse(config, tmp_path, records)

        with (tmp_path / "results" / "summary.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(records)
        assert set(module.SUMMARY_COLUMNS) <= set(rows[0])

    def test_records_the_reasoning_level_each_mode_ran_with(
        self, module, config, facts, tmp_path, no_charts
    ):
        module.analyse(config, tmp_path, _full_grid(config, facts))

        with (tmp_path / "results" / "summary.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        levels = {row["model"]: row["reasoning"] for row in rows}
        assert levels["GPT-5.6 Terra"] == "off"
        assert levels["Gemini 3.6 Flash"] == "minimal"

    def test_marks_correct_answers(self, module, config, facts, tmp_path, no_charts):
        records = _full_grid(config, facts, correct_when=lambda **cell: cell["position"] == 0)

        module.analyse(config, tmp_path, records)

        with (tmp_path / "results" / "summary.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        at_zero = [row for row in rows if row["position_percent"] == "0"]
        elsewhere = [row for row in rows if row["position_percent"] != "0"]
        assert all(row["correct"] == "True" for row in at_zero)
        assert all(row["correct"] == "False" for row in elsewhere)


class TestAccuracyTable:
    def test_accuracy_and_wilson_interval_per_cell(self, module, config, facts):
        records = _full_grid(config, facts, correct_when=lambda **cell: cell["fact_index"] < 3)

        cells = module.accuracy_by_cell(records, facts)

        cell = cells[("GPT-5.6 Terra", 4000, 0)]
        assert cell.correct == 3
        assert cell.trials == 6
        assert cell.point == pytest.approx(0.5)
        assert 0 < cell.low < 0.5 < cell.high < 1

    def test_covers_every_model_length_and_position(self, module, config, facts):
        cells = module.accuracy_by_cell(_full_grid(config, facts), facts)

        assert len(cells) == 3 * len(LENGTHS) * len(POSITIONS)


class TestReportText:
    def test_reports_accuracy_per_model_and_length(
        self, module, config, facts, tmp_path, no_charts
    ):
        report = module.analyse(config, tmp_path, _full_grid(config, facts))

        assert "GPT-5.6 Terra" in report
        assert "64,000" in report
        assert "100%" in report

    def test_flags_length_finish_reasons(self, module, config, facts, tmp_path, no_charts):
        records = _full_grid(config, facts)
        records.append(
            _record(
                config,
                model_index=2,
                length=64000,
                position=50,
                fact_index=0,
                text="",
                finish_reason="length",
            )
        )

        report = module.analyse(config, tmp_path, records)

        assert "output limit" in report
        assert "1 " in report

    def test_says_so_when_no_response_was_truncated(
        self, module, config, facts, tmp_path, no_charts
    ):
        report = module.analyse(config, tmp_path, _full_grid(config, facts))

        assert "No response hit its output limit" in report

    def test_reports_gemini_reasoning_tokens(self, module, config, facts, tmp_path, no_charts):
        """Decision 25.1: the pilot must say whether Gemini reasoned at `minimal`."""
        records = _full_grid(config, facts)
        records.append(
            _record(
                config,
                model_index=2,
                length=4000,
                position=25,
                fact_index=1,
                text=facts[1].value,
                reasoning_tokens=64,
            )
        )

        report = module.analyse(config, tmp_path, records)

        assert "reasoning tokens" in report.lower()
        assert "Gemini 3.6 Flash" in report

    def test_says_so_when_no_model_reasoned(self, module, config, facts, tmp_path, no_charts):
        report = module.analyse(config, tmp_path, _full_grid(config, facts))

        assert "no reasoning tokens" in report.lower()

    def test_reports_cached_input_tokens(self, module, config, facts, tmp_path, no_charts):
        records = _full_grid(config, facts)
        records.append(
            _record(
                config,
                model_index=0,
                length=64000,
                position=75,
                fact_index=2,
                text=facts[2].value,
                cached_input_tokens=32000,
            )
        )

        report = module.analyse(config, tmp_path, records)

        assert "cached" in report.lower()

    def test_reports_failed_calls(self, module, config, facts, tmp_path, no_charts):
        records = _full_grid(config, facts)
        failed = records[0].model_copy(update={"result": None, "error": "RateLimitError: 429"})
        records.append(failed)

        report = module.analyse(config, tmp_path, records)

        assert "failed" in report.lower()

    def test_refuses_an_empty_set_of_results(self, module, config, tmp_path):
        with pytest.raises(module.AnalysisError, match="no successful"):
            module.analyse(config, tmp_path, [])


class TestCharts:
    def test_writes_a_heatmap_per_model_and_a_position_curve(self, module, config, facts, tmp_path):
        module.analyse(config, tmp_path, _full_grid(config, facts))

        charts = tmp_path / "results" / "charts"
        names = {path.name for path in charts.iterdir()}
        for expected in (
            "accuracy-heatmap-gpt-5-6-terra-slide.png",
            "accuracy-heatmap-gpt-5-6-terra-slide.svg",
            "accuracy-heatmap-gpt-5-6-terra-article.png",
            "accuracy-by-position-64000-slide.png",
        ):
            assert expected in names, sorted(names)

    def test_the_heatmap_highlights_the_largest_drop_from_the_zero_position(
        self, module, config, facts
    ):
        # Model 0 fails only at 50% and 64,000 tokens, so that is the largest drop.
        def correct_when(*, model_index, length, position, fact_index):
            return not (model_index == 0 and length == 64000 and position == 50)

        cells = module.accuracy_by_cell(_full_grid(config, facts, correct_when), facts)

        assert module.largest_drop_cell(cells, "GPT-5.6 Terra") == (64000, 50)

    def test_no_drop_means_no_highlight(self, module, config, facts):
        cells = module.accuracy_by_cell(_full_grid(config, facts), facts)

        assert module.largest_drop_cell(cells, "GPT-5.6 Terra") is None

    def test_the_position_curve_highlights_the_deepest_middle_dip(self, module, config, facts):
        # Only Gemini (model 2) dips at 50% at 64,000 tokens.
        def correct_when(*, model_index, length, position, fact_index):
            return not (model_index == 2 and length == 64000 and position == 50)

        cells = module.accuracy_by_cell(_full_grid(config, facts, correct_when), facts)

        assert module.deepest_dip_model(cells, 64000) == "Gemini 3.6 Flash"

    def test_no_dip_means_no_highlight(self, module, config, facts):
        cells = module.accuracy_by_cell(_full_grid(config, facts), facts)

        assert module.deepest_dip_model(cells, 64000) is None
