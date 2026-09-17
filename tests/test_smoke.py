from pathlib import Path

import pytest
from typer.testing import CliRunner

from lab.cli import app
from lab.config import ExperimentConfig
from lab.plan import PlanError, build_request
from lab.providers.mock import MockProvider
from lab.raw_log import RunRecord
from lab.smoke import DEFAULT_THINKING_PROMPT, describe, plan_smoke, problems

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


def _invoke(tmp_path: Path, config: Path, *extra: str):
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
            *extra,
        ],
    )


def test_plan_smoke_makes_one_call_per_model_and_mode(tmp_path):
    from lab.config import load_config

    calls = plan_smoke(load_config(_write(tmp_path, MOCK_SMOKE)))

    assert [(c.model_label, c.mode) for c in calls] == [("mock-a", "off"), ("mock-a", "low")]
    assert calls[1].request.show_thinking is True
    assert calls[0].request.prompt == "Reply with the single word: ready"
    assert calls[0].request.metadata == {"experiment": "smoke", "mode": "off"}
    assert calls[1].request.prompt == DEFAULT_THINKING_PROMPT


def test_thinking_prompt_can_be_set_in_config(tmp_path):
    from lab.config import load_config

    text = MOCK_SMOKE.replace("parameters:\n", "parameters:\n  thinking_prompt: Think hard\n")
    calls = plan_smoke(load_config(_write(tmp_path, text)))

    assert calls[1].request.prompt == "Think hard"


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


def _record(
    show_thinking: bool, reasoning: str = "off", **result_overrides
) -> tuple[RunRecord, object]:
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
                            "reasoning": "low" if show_thinking else reasoning,
                            "temperature": None,
                            "max_output_tokens": 50,
                            "show_thinking": show_thinking,
                        }
                    },
                }
            ],
        }
    )
    call = plan_smoke(config)[0]
    result = MockProvider().generate(call.request).model_copy(update=result_overrides)
    record = RunRecord.for_call(call, source="api", attempts=1, result=result)
    return record, call.request


def test_complete_result_has_no_problems():
    record, request = _record(True)

    assert problems(record, request) == []


def test_hidden_thinking_does_not_expect_thinking_fields():
    record, request = _record(False, reasoning_tokens=None, time_to_first_thinking_ms=None)

    assert problems(record, request) == []
    assert "  time_to_first_thinking_ms: not reported" in describe(record, request)


def test_thinking_time_missing_when_model_thought_is_a_problem():
    record, request = _record(True, time_to_first_thinking_ms=None, cached_input_tokens=None)

    assert problems(record, request) == ["time_to_first_thinking_ms not reported"]
    lines = describe(record, request)
    assert "  time_to_first_thinking_ms: NOT REPORTED" in lines
    assert "  cached_input_tokens: not reported" in lines


def test_model_that_did_not_think_leaves_thinking_fields_unverified():
    record, request = _record(True, reasoning_tokens=0, time_to_first_thinking_ms=None)

    warning = (
        "thinking was requested but the model did not think, so the thinking fields are "
        "unverified; use a prompt that needs reasoning"
    )
    assert problems(record, request) == [warning]
    lines = describe(record, request)
    assert "  time_to_first_thinking_ms: not applicable, the model did not think" in lines
    assert f"  WARNING: {warning}" in lines


def test_empty_text_is_a_problem():
    record, request = _record(False, text="")

    assert problems(record, request) == ["text not reported"]


def test_failed_record_is_described():
    record, request = _record(False)
    failed = record.model_copy(update={"result": None, "error": "AuthenticationError: bad"})

    assert "FAILED" in describe(failed, request)[0]
    assert problems(failed, request) == ["call failed: AuthenticationError: bad"]


def test_reasoning_tokens_with_reasoning_off_are_warned():
    record, request = _record(False, reasoning_tokens=37)

    warning = "reasoning is off but 37 reasoning tokens were reported"
    assert problems(record, request) == [warning]
    assert f"  WARNING: {warning}" in describe(record, request)


@pytest.mark.parametrize(("reasoning_tokens", "reasoning"), [(0, "off"), (None, "off")])
def test_no_warning_when_reasoning_off_is_honoured(reasoning_tokens, reasoning):
    record, request = _record(False, reasoning=reasoning, reasoning_tokens=reasoning_tokens)

    assert problems(record, request) == []


def test_smoke_fails_when_reasoning_off_is_not_honoured(tmp_path, monkeypatch):
    from lab.providers import registry
    from lab.providers.mock import MockProvider as RealMock

    class ThinkingAnyway(RealMock):
        def generate(self, request):
            return super().generate(request).model_copy(update={"reasoning_tokens": 12})

    monkeypatch.setattr(registry, "create_provider", lambda name: ThinkingAnyway())
    config = _write(tmp_path, MOCK_SMOKE)

    result = _invoke(tmp_path, config)

    assert result.exit_code == 1
    assert "WARNING: reasoning is off but 12 reasoning tokens were reported" in result.output


def test_fresh_smoke_ignores_cache_and_makes_new_calls(tmp_path):
    config = _write(tmp_path, MOCK_SMOKE)
    _invoke(tmp_path, config)

    fresh = _invoke(tmp_path, config, "--fresh")

    assert fresh.exit_code == 0, fresh.output
    assert "Calls made:             2" in fresh.output
