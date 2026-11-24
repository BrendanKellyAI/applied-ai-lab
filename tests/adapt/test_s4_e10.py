"""S4 E10: the prompt sets, eval-only jobs that load a saved adapter, the scoring and claims."""

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.regression import (
    RegressionError,
    bleed_kind,
    bleed_rows,
    decline_rows,
    general_rows,
)
from lab.adapt.regression_eval import RegressionExperiment, analyse
from lab.adapt.run import write_jsonl
from lab.adapt.tune import JobError, _files, _plan, train_subset
from lab.adapt.tune_config import TuneConfig
from lab.cli import app
from lab.experiments import load_sibling
from lab.providers.mock import MockProvider
from lab.rag.corpus import load_library

ROOT = Path(__file__).parents[2]
E10 = ROOT / "episodes" / "s4-e10-what-does-tuning-break"
S1 = ROOT / "field-notes" / "s1-e10-reasoning-vs-standard" / "tasks" / "items.jsonl"
S2 = ROOT / "field-notes" / "s2-e12-embedding-swap" / "results" / "baseline"
LIBRARY = load_library(ROOT / "datasets" / "halvard")
claims = load_sibling(E10 / "claims.py")


# Prompt sets


def test_committed_sets_match_their_sources():
    def read(name):
        return [json.loads(x) for x in (E10 / "data" / name).read_text("utf-8").splitlines()]

    assert read("general.jsonl") == general_rows(S1)
    assert read("bleed-prompts.jsonl") == bleed_rows(E10 / "data" / "bleed.jsonl")
    assert read("declines.jsonl") == decline_rows(
        LIBRARY, S2 / "log.jsonl", S2 / "raw-answer.jsonl"
    )
    kinds = [r["kind"] for r in read("bleed.jsonl")]
    assert kinds.count("everyday") == 80 and kinds.count("appliance") == 20


def test_decline_rows_refuse_a_prompt_that_differs_from_the_reference(tmp_path):
    raw = tmp_path / "raw-answer.jsonl"
    lines = (S2 / "raw-answer.jsonl").read_text("utf-8").splitlines()
    rows = [json.loads(x) for x in lines]
    for row in rows:
        row["request_hash"] = "0" * 64
    raw.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    with pytest.raises(RegressionError):
        decline_rows(LIBRARY, S2 / "log.jsonl", raw)


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ('{"route": "safety", "safety": true, "product": null, "fault": null}', "triage"),
        ('Sure: {"route": "other", "safety": false} hope that helps', "triage"),
        ("Thank you for getting in touch.\n\nHere is a recipe.", "house_reply"),
        ("Soup.\n\nKind regards,\nThe Halvard Home team", "house_reply"),
        ("Chop the carrots and simmer for 20 minutes.", None),
        ('{"name": "Tom"}', None),
        ("{not json", None),
        ("", None),
        (None, None),
    ],
)
def test_bleed_kind(text, kind):
    assert bleed_kind(text) == kind


# Eval-only jobs


@pytest.mark.parametrize("name", ["tune-base.yaml", "tune-e5.yaml", "tune-e7.yaml"])
def test_eval_jobs_run_the_three_sets_without_training(name):
    job = TuneConfig.load(E10 / name)
    files, rows = _files(job)
    assert rows == [] and train_subset(job) == []
    plan = _plan(job, files, rows)
    assert {k: v["items"] for k, v in plan["eval"].items()} == {
        "general": 120,
        "bleed": 100,
        "declines": 120,
    }
    assert plan["max_new_tokens"] == 400 and plan["train"]["examples"] == 0
    adapter = plan.get("adapter_from")
    if name == "tune-base.yaml":
        assert adapter is None
    else:
        expected = "e5-tuned-short" if name == "tune-e5.yaml" else "e7-tuned-short-b4"
        assert adapter["folder"] == f"{expected}/adapter-1" and len(adapter["sha256"]) == 64


def _eval_job(tmp_path: Path, **extra) -> TuneConfig:
    write_jsonl(
        tmp_path / "set.jsonl", [{"id": "a", "messages": [{"role": "user", "content": "hi"}]}]
    )
    raw = {"episode": "s4-test", "task": "eval", "arm": "x", "base_model": "Qwen/Qwen3-0.6B",
           "base_revision": "c1899de289a04d12100db370d81485cdf75e47ca", "train_size": 0,
           "instructions": "none", "eval_splits": [], "eval_sets": {"s": "set.jsonl"},
           **extra}  # fmt: skip
    path = tmp_path / "tune.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return TuneConfig.load(path)


def test_eval_job_refuses_bad_sets_and_adapters(tmp_path):
    job = _eval_job(tmp_path)
    write_jsonl(
        tmp_path / "set.jsonl", [{"id": "a", "messages": [{"role": "assistant", "content": "x"}]}]
    )
    with pytest.raises(JobError, match="ending with the user"):
        _files(job)
    row = {"id": "a", "messages": [{"role": "user", "content": "x"}]}
    write_jsonl(tmp_path / "set.jsonl", [row, row])
    with pytest.raises(JobError, match="repeat"):
        _files(job)
    write_jsonl(tmp_path / "set.jsonl", [row])
    (tmp_path / "src").mkdir()
    shutil.copy(
        ROOT / "episodes/s4-e7-teaching-a-house-style/results/e7-tuned-short/job.json",
        tmp_path / "src" / "job.json",
    )
    failed = _eval_job(tmp_path, adapter_from="src")
    with pytest.raises(JobError, match="no succeeded"):
        _plan(failed, *_files(failed))
    record = json.loads(
        (
            ROOT / "episodes/s4-e7-teaching-a-house-style/results/e7-tuned-short-b4/job.json"
        ).read_text("utf-8")
    )
    record["plan"]["base_revision"] = "other"
    (tmp_path / "src" / "job.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(JobError, match="different base model"):
        _plan(failed, *_files(failed))


def test_eval_task_rules():
    base = {"episode": "e", "arm": "a", "base_model": "m", "train_size": 0}
    with pytest.raises(ValueError, match="eval_sets"):
        TuneConfig.model_validate(
            {**base, "task": "eval", "instructions": "none", "eval_splits": []}
        )
    with pytest.raises(ValueError, match="no training rows"):
        TuneConfig.model_validate(
            {**base, "task": "eval", "instructions": "none", "eval_sets": {"s": "p"}}
        )
    with pytest.raises(ValueError, match="adapter_from"):
        TuneConfig.model_validate({**base, "task": "a", "adapter_from": "x"})


# Scoring, commands and claims


def _fake_results(folder: Path, arm: str, *, wrong: bool, bleed: bool, decline: bool) -> None:
    out = folder / "results" / arm
    general = [json.loads(x) for x in S1.read_text("utf-8").splitlines()]
    write_jsonl(
        out / "predictions-general.jsonl",
        [
            {
                "id": f"{i['task']}-{i['index']:02d}",
                "text": "ANSWER: 0" if wrong else f"ANSWER: {i['answer']}",
            }
            for i in general
        ],
    )
    reply = '{"route": "other", "safety": false}' if bleed else "Here you go."
    write_jsonl(
        out / "predictions-bleed.jsonl",
        [{"id": f"bleed-{n:03d}", "text": reply} for n in range(100)],
    )
    answer = "I could not find that." if decline else "It is 12 months."
    unanswerable = [i for i in LIBRARY.test if not i.answerable]
    write_jsonl(
        out / "predictions-declines.jsonl", [{"id": i.id, "text": answer} for i in unanswerable]
    )


def _experiment(tmp_path: Path) -> Path:
    raw = yaml.safe_load((E10 / "config.yaml").read_text("utf-8"))
    for key in ("library", "s1_items", "s1_metrics", "s2_log"):
        raw[key] = str((E10 / raw[key]).resolve())
    raw["limits"] = {"google": {"max_concurrency": 32, "requests_per_minute": 1_000_000}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    _fake_results(tmp_path, "e10-base", wrong=False, bleed=False, decline=True)
    _fake_results(tmp_path, "e10-tuned-triage", wrong=True, bleed=True, decline=False)
    _fake_results(tmp_path, "e10-tuned-replies", wrong=True, bleed=True, decline=False)
    return path


def test_regression_run_judges_declines_and_analyse_scores_every_check(tmp_path, monkeypatch):
    import lab.adapt.cli_facts as cli_facts

    config = _experiment(tmp_path)
    runner = CliRunner()
    estimate = runner.invoke(app, ["adapt", "regression-run", str(config), "--estimate"])
    assert estimate.exit_code == 0 and "judge e10-base" in estimate.output

    def respond(request):
        declined = "could not find" in request.prompt
        return json.dumps(
            {"declined": declined, "correct": declined, "faithful": True, "reason": "r"}
        )

    provider = MockProvider(respond=respond, supported_reasoning=("minimal",))
    available = SimpleNamespace(providers={"google": provider}, missing_keys={})
    monkeypatch.setattr(cli_facts, "available_providers", lambda names: available)
    prices = tmp_path / "prices.yaml"
    prices.write_text(
        yaml.safe_dump(
            {
                "prices": {"google": {"gemini-3.6-flash": {"input": 0.75, "output": 3.75}}},
                "budgets": {"s4-e10-what-does-tuning-break": 5.0},
            }
        ),
        encoding="utf-8",
    )
    args = ["adapt", "regression-run", str(config), "--prices-path", str(prices)]
    args += ["--cache-dir", str(tmp_path / "cache"), "--env-file", str(tmp_path / "none")]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "judge-e10-base: made 120" in result.output
    analysed = runner.invoke(app, ["adapt", "regression-analyse", str(config)])
    assert analysed.exit_code == 0, analysed.output
    assert "e10-base: general 120 of 120, bleed 0 of 100, declines 120 of 120" in analysed.output

    result = analyse(RegressionExperiment.load(config))
    triage = result["arms"]["e10-tuned-triage"]
    assert triage["checks"]["bleed"]["count"] == 100 and triage["bleed_kinds"]["triage"] == 100
    per_item = {name: arm["per_item"] for name, arm in result["arms"].items()}
    held = {c.id: c.held for c in claims.evaluate(per_item, claims.load_claims_file())}
    assert held == {"C1": True, "C2": True, "C3": True}
    reversed_ = {**per_item, "e10-tuned-replies": per_item["e10-base"]}
    result_claims = claims.evaluate(reversed_, claims.load_claims_file())
    assert [c.held for c in result_claims] == [False, False, False]
    assert claims.verdict(result_claims[0]) == "Failed"


def test_config_and_preregistration():
    experiment = RegressionExperiment.load(E10 / "config.yaml")
    assert experiment.baseline == "e10-base" and len(experiment.arms) == 3
    text = (E10 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E10 / "claims.yaml").read_text(encoding="utf-8"))
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text
    with pytest.raises(ValueError, match="baseline"):
        RegressionExperiment.model_validate(
            {**yaml.safe_load((E10 / "config.yaml").read_text("utf-8")), "baseline": "nope"}
        )
