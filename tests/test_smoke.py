from pathlib import Path

import pytest
from typer.testing import CliRunner

from lab.cli import app
from lab.config import ExperimentConfig
from lab.plan import PlanError, build_request
from lab.providers.mock import MockProvider
from lab.raw_log import RunRecord
from lab.smoke import describe, missing_fields, plan_smoke

runner = CliRunner()

MOCK_SMOKE = """
experiment: smoke
seed: 1
parameters:
  prompt: "Reply with the single word: ready"
models:
  - provider: mock
    model: mock-a
    modes:
      off: { reasoning: off, temperature: null, max_output_tokens: 16 }
      low: { reasoning: low, temperature: null, max_output_tokens: 256, show_thinking: true }
limits:
  mock: { max_concurrency: 2, requests_per_minute: 600000 }
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "smoke.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _invoke(tmp_path: Path, config: Path):
    return runner.invoke(
        app,
        [
            "smoke",
            "--config",
            str(config),
            "--cache-dir",
            str(tmp_path / ".cache"),
            "--env-file",
            str(tmp_path / "no.env"),
        ],
    )


def test_plan_smoke_makes_one_call_per_model_and_mode(tmp_path):
    from lab.config import load_config

    calls = plan_smoke(load_config(_write(tmp_path, MOCK_SMOKE)))

    assert [(c.model_label, c.mode) for c in calls] == [("mock-a", "off"), ("mock-a", "low")]
    assert calls[1].request.show_thinking is True
    assert calls[0].request.prompt == "Reply with the single word: ready"
    assert calls[0].request.metadata == {"experiment": "smoke", "mode": "off"}


def test_build_request_rejects_unknown_mode(tmp_path):
    from lab.config import load_config

    model = load_config(_write(tmp_path, MOCK_SMOKE)).models[0]

    with pytest.raises(PlanError, match="no mode 'high'"):
        build_request(model, "high", prompt="hi")


def test_smoke_prints_every_field_and_second_run_makes_no_calls(tmp_path):
    config = _write(tmp_path, MOCK_SMOKE)

    first = _invoke(tmp_path, config)
    second = _invoke(tmp_path, config)

    assert first.exit_code == 0, first.output
    for field in ("model_returned", "time_to_first_answer_token_ms", "time_to_first_thinking_ms"):
        assert field in first.output
    assert "Calls made:             2" in first.output
    assert second.exit_code == 0, second.output
    assert "Calls made:             0" in second.output


def test_smoke_skips_providers_without_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = _write(
        tmp_path,
        MOCK_SMOKE.replace(
            "provider: mock\n    model: mock-a", "provider: openai\n    model: gpt-5.6-luna"
        ),
    )

    result = _invoke(tmp_path, config)

    assert result.exit_code == 1
    assert "Skipping openai: set OPENAI_API_KEY" in result.output
    assert "No API keys found" in result.output


def test_smoke_reports_config_errors_without_traceback(tmp_path):
    result = _invoke(tmp_path, tmp_path / "missing.yaml")

    assert result.exit_code == 2
    assert "Config file not found" in result.output


def _record(expects_thinking: bool, **result_overrides) -> RunRecord:
    config = ExperimentConfig.model_validate(
        {
            "experiment": "smoke",
            "seed": 1,
            "models": [
                {
                    "provider": "mock",
                    "model": "mock-a",
                    "modes": {
                        "m": {
                            "reasoning": "low" if expects_thinking else "off",
                            "temperature": None,
                            "max_output_tokens": 50,
                            "show_thinking": expects_thinking,
                        }
                    },
                }
            ],
        }
    )
    call = plan_smoke(config)[0]
    result = MockProvider().generate(call.request).model_copy(update=result_overrides)
    return RunRecord.for_call(call, source="api", attempts=1, result=result)


def test_missing_thinking_fields_are_flagged_only_when_thinking_was_requested():
    hidden = _record(False)
    shown_but_absent = _record(True, time_to_first_thinking_ms=None, cached_input_tokens=None)

    assert missing_fields(hidden, expects_thinking=False) == []
    assert missing_fields(shown_but_absent, expects_thinking=True) == ["time_to_first_thinking_ms"]
    assert "  time_to_first_thinking_ms: NOT REPORTED" in describe(shown_but_absent, True)
    assert "  cached_input_tokens: not reported" in describe(shown_but_absent, True)


def test_empty_text_is_flagged():
    record = _record(False, text="")

    assert missing_fields(record, expects_thinking=False) == ["text"]


def test_failed_record_is_described():
    record = _record(False).model_copy(update={"result": None, "error": "AuthenticationError: bad"})

    assert "FAILED" in describe(record, False)[0]
    assert missing_fields(record, False) == ["result"]
