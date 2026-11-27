"""Tuning job records, the Colab notebook, and the output format added to provider requests."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.definitions import Definitions
from lab.adapt.notebook import render
from lab.adapt.output import output_format
from lab.adapt.run import read_jsonl, write_jsonl
from lab.adapt.tune import (
    JobError,
    cancel,
    find_job,
    launch,
    load_record,
    prepare,
    record_result,
    train_subset,
    validate_rows,
)
from lab.adapt.tune_config import TuneConfig
from lab.cli import app
from lab.providers.anthropic_provider import AnthropicProvider
from lab.providers.base import (
    GenerationRequest,
    OutputFormat,
    UnsupportedSettingError,
    request_hash,
)
from lab.providers.capabilities import default_capabilities
from lab.providers.google_provider import GoogleProvider
from lab.providers.openai_provider import build_params

ROOT = Path(__file__).parents[2]
DATA = ROOT / "datasets" / "halvard-tasks"
DEFINITIONS = Definitions.load(DATA / "routes.yaml")
NOTEBOOK = ROOT / "season4" / "colab" / "lora_job.ipynb"


def _tune(tmp_path: Path, **extra) -> TuneConfig:
    raw = {
        "episode": "s4-test",
        "task": "a",
        "arm": "tuned-50",
        "base_model": "Qwen/Qwen3-0.6B",
        "train_size": 50,
        "eval_splits": ["dev"],
        "data": str(DATA),
        **extra,
    }
    path = tmp_path / "episode" / "tune.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return TuneConfig.load(path)


DEV_IDS = [row["id"] for row in read_jsonl(DATA / "task-a" / "dev.jsonl")]


def _result(tmp_path: Path, attempt: int, status: str = "succeeded", ids=None) -> Path:
    out = tmp_path / "download"
    out.mkdir(exist_ok=True)
    rows = [{"id": i, "text": "{}"} for i in (DEV_IDS if ids is None else ids)]
    write_jsonl(out / "predictions-dev.jsonl", rows)
    path = out / "job_result.json"
    path.write_text(
        json.dumps({"job_id": "s4-test/tuned-50", "attempt": attempt, "status": status}),
        encoding="utf-8",
    )
    return path


def test_prepare_writes_files_and_counts_training_tokens(tmp_path):
    config = _tune(tmp_path)
    record = prepare(config)
    plan = record["plan"]
    assert plan["train"]["examples"] == 50 and plan["eval"]["dev"]["items"] == 200
    tokens = plan["training_tokens_estimate"]
    assert tokens["total"] == tokens["per_epoch"] * 3 > 0
    rows = [json.loads(x) for x in (config.arm_folder / "train.jsonl").read_text().splitlines()]
    assert [m["role"] for m in rows[0]["messages"]] == ["system", "user", "assistant"]
    evals = (config.arm_folder / "eval-dev.jsonl").read_text().splitlines()
    assert len(json.loads(evals[0])["messages"]) == 2
    assert prepare(config)["attempts"] == []


def test_subsets_are_nested_and_size_is_checked(tmp_path):
    small = {i.id for i in train_subset(_tune(tmp_path, train_size=50))}
    large = {i.id for i in train_subset(_tune(tmp_path, train_size=200))}
    assert small < large
    with pytest.raises(JobError, match="more than"):
        train_subset(_tune(tmp_path, train_size=99999))


def test_eval_only_job_and_task_b(tmp_path):
    record = prepare(_tune(tmp_path, train_size=0, arm="untuned"))
    assert record["plan"]["training_tokens_estimate"]["total"] == 0
    b = prepare(_tune(tmp_path, task="b", arm="tuned-b", train_size=5, instructions="short"))
    assert b["plan"]["train"]["examples"] == 5
    with pytest.raises(ValueError, match="instructions must be one of"):
        _tune(tmp_path, instructions="style_guide")


def test_validation_names_each_problem(tmp_path):
    config = _tune(tmp_path)
    rows = [
        {"messages": [{"role": "user", "content": "x"}]},
        {"messages": [{"role": r, "content": c} for r, c in
                      (("system", "s"), ("user", " "), ("assistant", "not json"))]},
    ]  # fmt: skip
    problems = validate_rows(rows, config, DEFINITIONS)
    assert "row 1: roles" in problems[0]
    assert any("empty message" in p for p in problems)
    assert any("not a valid triage object" in p for p in problems)
    short = _tune(tmp_path, training={"max_length": 5})
    long_row = {"messages": [{"role": r, "content": "word " * 20} for r in
                             ("system", "user", "assistant")]}  # fmt: skip
    assert any("max_length" in p for p in validate_rows([long_row], short, DEFINITIONS))
    with pytest.raises(JobError, match="failed validation"):
        prepare(short)


def test_launch_rules_never_relaunch_silently(tmp_path):
    config = _tune(tmp_path)
    folder = config.arm_folder
    with pytest.raises(JobError, match="prepare the job first"):
        launch(folder, "Brendan")
    prepare(config)
    with pytest.raises(JobError, match="who approved"):
        launch(folder, " ")
    launch(folder, "Brendan, 23 November 2026")
    with pytest.raises(JobError, match="still open"):
        launch(folder, "Brendan")
    record_result(folder, _result(tmp_path, 1, "failed"))
    with pytest.raises(JobError, match="--retry-approved"):
        launch(folder, "Brendan")
    launch(folder, "Brendan, retry", retry_approved=True)
    done = record_result(folder, _result(tmp_path, 2))
    assert [a["status"] for a in done["attempts"]] == ["failed", "succeeded"]
    second = done["attempts"][1]
    assert second["predictions"]["dev"]["items"] == 200
    assert second["approved_by"] == "Brendan, retry" and second["result"]["status"] == "succeeded"
    assert (folder / "predictions-dev.jsonl").exists()
    with pytest.raises(JobError, match="has succeeded"):
        launch(folder, "Brendan")
    with pytest.raises(JobError, match="cannot change"):
        prepare(_tune(tmp_path, training={"epochs": 1}))


def test_results_must_match_the_open_attempt(tmp_path):
    config = _tune(tmp_path)
    folder = config.arm_folder
    prepare(config)
    with pytest.raises(JobError, match="no launched attempt"):
        record_result(folder, _result(tmp_path, 1))
    launch(folder, "Brendan")
    with pytest.raises(JobError, match="not the open attempt"):
        record_result(folder, _result(tmp_path, 2))
    bad = _result(tmp_path, 1, "exploded")
    with pytest.raises(JobError, match="unknown status"):
        record_result(folder, bad)
    bad.write_text(json.dumps({"job_id": "other", "attempt": 1, "status": "failed"}))
    with pytest.raises(JobError, match="not s4-test"):
        record_result(folder, bad)
    bad.write_text(json.dumps({"job_id": "s4-test/tuned-50"}))
    with pytest.raises(JobError, match="lacks"):
        record_result(folder, bad)
    with pytest.raises(JobError, match="once each"):
        record_result(folder, _result(tmp_path, 1, ids=DEV_IDS[:5]))
    with pytest.raises(JobError, match="once each"):
        record_result(folder, _result(tmp_path, 1, ids=[*DEV_IDS, DEV_IDS[0]]))
    good = _result(tmp_path, 1)
    (good.parent / "predictions-dev.jsonl").unlink()
    with pytest.raises(JobError, match="needs predictions-dev"):
        record_result(folder, good)
    assert find_job(tmp_path, "s4-test/tuned-50") == folder
    with pytest.raises(JobError, match="no job"):
        find_job(tmp_path, "missing")


def test_cli_tune_and_status(tmp_path):
    config = _tune(tmp_path)
    path = config.folder / "tune.yaml"
    runner = CliRunner()
    prepared = runner.invoke(app, ["adapt", "tune", str(path)])
    assert prepared.exit_code == 0, prepared.output
    assert "Training tokens" in prepared.output and "Attempts: 0" in prepared.output
    refused = runner.invoke(app, ["adapt", "tune", str(path), "--launch"])
    assert refused.exit_code == 1 and "who approved" in refused.output
    launched = runner.invoke(
        app, ["adapt", "tune", str(path), "--launch", "--approved-by", "Brendan"]
    )
    assert launched.exit_code == 0 and "Attempts: 1" in launched.output
    root = ["--root", str(tmp_path)]
    shown = runner.invoke(app, ["adapt", "status", "s4-test/tuned-50", *root])
    assert "Attempt 1: launched" in shown.output
    result = _result(tmp_path, 1)
    recorded = runner.invoke(
        app, ["adapt", "status", "s4-test/tuned-50", *root, "--result", str(result)]
    )
    assert recorded.exit_code == 0 and "Attempt 1: succeeded" in recorded.output
    missing = runner.invoke(app, ["adapt", "status", "nope", *root])
    assert missing.exit_code == 1
    assert load_record(config.arm_folder)["attempts"][0]["approved_by"] == "Brendan"


def test_cli_launch_prepares_first_when_needed(tmp_path):
    path = _tune(tmp_path).folder / "tune.yaml"
    result = CliRunner().invoke(
        app, ["adapt", "tune", str(path), "--launch", "--approved-by", "Brendan"]
    )
    assert result.exit_code == 0 and "Attempts: 1" in result.output


def test_a_launched_job_is_never_rewritten(tmp_path):
    config = _tune(tmp_path)
    folder = config.arm_folder
    prepare(config)
    launch(folder, "Brendan")
    before = (folder / "train.jsonl").read_bytes()
    with pytest.raises(JobError, match="cannot change"):
        prepare(_tune(tmp_path, train_size=60))
    assert (folder / "train.jsonl").read_bytes() == before
    assert prepare(config)["attempts"][0]["status"] == "launched"


def test_a_retry_refuses_files_that_changed(tmp_path):
    config = _tune(tmp_path)
    folder = config.arm_folder
    prepare(config)
    launch(folder, "Brendan")
    record_result(folder, _result(tmp_path, 1, "failed"))
    (folder / "eval-dev.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(JobError, match="differs from the job record"):
        launch(folder, "Brendan", retry_approved=True)


def test_an_open_attempt_with_no_result_can_be_cancelled(tmp_path):
    config = _tune(tmp_path)
    folder = config.arm_folder
    prepare(config)
    with pytest.raises(JobError, match="no launched attempt"):
        cancel(folder, "Brendan", "runtime died")
    launch(folder, "Brendan")
    with pytest.raises(JobError, match="and why"):
        cancel(folder, "Brendan", "")
    root = ["--root", str(tmp_path)]
    runner = CliRunner()
    both = ["--cancel", "--result", str(_result(tmp_path, 1))]
    assert runner.invoke(app, ["adapt", "status", "s4-test/tuned-50", *root, *both]).exit_code == 1
    args = ["adapt", "status", "s4-test/tuned-50", *root, "--cancel"]
    args += ["--approved-by", "Brendan", "--reason", "Colab disconnected"]
    closed = runner.invoke(app, args)
    assert closed.exit_code == 0 and "Attempt 1: cancelled" in closed.output
    attempt = load_record(folder)["attempts"][0]
    assert attempt["reason"] == "Colab disconnected" and attempt["approved_by"] == "Brendan"
    with pytest.raises(JobError, match="--retry-approved"):
        launch(folder, "Brendan")


# Notebook


def test_committed_notebook_matches_the_generator_and_parses():
    assert NOTEBOOK.read_text(encoding="utf-8") == render()
    notebook = json.loads(render())
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            source = "".join(
                line for line in cell["source"] if not line.lstrip().startswith(("%", "!"))
            )
            ast.parse(source)
    text = render()
    assert chr(0x2013) not in text and chr(0x2014) not in text


def _eval_batches():
    from lab.adapt.notebook import EVAL_BATCHES

    namespace: dict = {}
    exec(EVAL_BATCHES, namespace)  # the notebook's own source, so the test runs what Colab runs
    return namespace["eval_batches"]


def test_short_prompts_keep_the_full_eval_batch():
    batches = _eval_batches()([300] * 40, max_new_tokens=160, cap=16, budget=40_000_000)
    assert [len(b) for b in batches] == [16, 16, 8]
    assert [i for b in batches for i in b] == list(range(40))


def test_long_prompts_get_smaller_batches_and_never_none():
    lengths = [300, 300, 3_600, 300, 6_000, 6_000, 300]
    batches = _eval_batches()(lengths, max_new_tokens=400, cap=16, budget=40_000_000)
    # A batch costs its size times (longest prompt + new tokens) squared. (3,600 + 400) squared
    # is 16 million, so two such fit; (6,000 + 400) squared alone is over the budget, and a
    # prompt over the budget still runs, on its own. Order is kept.
    assert batches == [[0, 1], [2, 3], [4], [5], [6]]


def test_the_notebook_is_version_3_with_the_attention_budget():
    text = render()
    assert "s4-lora-job-v3" in text and "EVAL_ATTENTION_BUDGET" in text


# Output format on provider requests


def _request(**extra) -> GenerationRequest:
    return GenerationRequest(
        provider="openai",
        model="gpt-6-luna",
        prompt="JSON please",
        max_output_tokens=50,
        reasoning="off",
        **extra,
    )


def test_an_unset_format_leaves_the_request_hash_unchanged():
    import hashlib

    request = _request()
    # The Season 4 rule; Season 5's fields did not exist then, so they are left out too.
    later_fields = {"messages", "tools", "tool_choice"}
    payload = request.model_dump(
        mode="json", exclude={"stream", "metadata", "output_format", *later_fields}
    )
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert request_hash(request) == hashlib.sha256(canonical.encode()).hexdigest()
    assert request_hash(_request(output_format=OutputFormat(kind="json_mode"))) != (
        request_hash(request)
    )


def test_openai_params_carry_the_format():
    schema = output_format("schema", DEFINITIONS)
    params = build_params(_request(output_format=schema))
    assert params["text"]["format"]["type"] == "json_schema"
    assert params["text"]["format"]["strict"] is True
    mode = build_params(_request(output_format=OutputFormat(kind="json_mode")))
    assert mode["text"] == {"format": {"type": "json_object"}}
    assert "text" not in build_params(_request())


def test_format_rules_and_refusals():
    with pytest.raises(ValueError, match="needs a name"):
        OutputFormat(kind="schema")
    with pytest.raises(ValueError, match="needs a name"):
        OutputFormat(kind="json_mode", name="x", json_schema={})
    table = default_capabilities()
    table.check(_request(output_format=output_format("schema", DEFINITIONS)))
    fmt = OutputFormat(kind="json_mode")
    for provider in (
        AnthropicProvider(client=SimpleNamespace()),
        GoogleProvider(client=SimpleNamespace()),
    ):
        with pytest.raises(UnsupportedSettingError, match="output format"):
            provider.validate(_request(output_format=fmt))


def test_capability_check_refuses_a_format_the_model_lacks(tmp_path):
    from lab.providers.capabilities import CapabilityTable, ModelCapabilities

    table = CapabilityTable(
        {"openai": {"plain": ModelCapabilities(reasoning=("off",), temperature=False)}}
    )
    request = GenerationRequest(
        provider="openai",
        model="plain",
        prompt="p",
        max_output_tokens=5,
        reasoning="off",
        output_format=OutputFormat(kind="json_mode"),
    )
    with pytest.raises(UnsupportedSettingError, match="does not offer json_mode"):
        table.check(request)
