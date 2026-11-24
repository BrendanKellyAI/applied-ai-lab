"""S4 E8: the training pairs, the closed-book job files, the judge and the scoring, offline."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.build_tasks.checks import ReplyError
from lab.adapt.facts import (
    FACTS_SHORT,
    Pair,
    blocked_questions,
    build_pairs,
    closed_book_user,
    load_pairs,
    pair_prompt,
    pair_requests,
    parse_pairs,
    training_passages,
    write_pairs,
)
from lab.adapt.facts_eval import (
    FactsArm,
    FactsExperiment,
    analyse,
    judge_requests,
    read_verdicts,
    s2_verdict_texts,
    score,
    summarise,
)
from lab.adapt.run import write_jsonl
from lab.adapt.tune import _files, train_subset
from lab.adapt.tune_config import TuneConfig
from lab.cli import app
from lab.providers.mock import MockProvider
from lab.rag.config import ModelSpec
from lab.rag.corpus import load_library

ROOT = Path(__file__).parents[2]
HALVARD = ROOT / "datasets" / "halvard"
LIBRARY = load_library(HALVARD)
S2_LOG = ROOT / "field-notes" / "s2-e12-embedding-swap" / "results" / "baseline" / "raw-judge.jsonl"
GEN = ModelSpec(provider="google", model="gemini-3.1-flash-lite", reasoning="minimal",
                max_output_tokens=1200)  # fmt: skip
FAST = {"google": {"max_concurrency": 32, "requests_per_minute": 1_000_000}}
JUDGE = {"provider": "google", "model": "gemini-3.6-flash", "reasoning": "minimal",
         "max_output_tokens": 300}  # fmt: skip


def _reply(pairs: list[tuple[str, str]]) -> str:
    return json.dumps({"pairs": [{"question": q, "answer": a} for q, a in pairs]})


# Pairs


def test_training_passages_hold_only_current_public_documents():
    passages = training_passages(LIBRARY)
    assert len(passages) == 436
    assert {(p.access, p.status) for p in passages} == {("public", "current")}
    staff = {d.doc_id for d in LIBRARY.documents if d.access == "staff"}
    assert not staff & {p.doc_id for p in passages}


def test_pair_prompt_and_requests_carry_the_passage():
    passage = training_passages(LIBRARY)[0]
    assert passage.text in pair_prompt(passage, 4) and "Write 4 different" in pair_prompt(
        passage, 4
    )
    requests = pair_requests([passage], 4, GEN, "s4-test")
    assert list(requests) == [passage.chunk_id]
    assert requests[passage.chunk_id].model == "gemini-3.1-flash-lite"


def test_parse_pairs_takes_exactly_n_complete_pairs():
    assert parse_pairs(_reply([("Q1", "A1"), ("Q2", "A2")]), 2) == [("Q1", "A1"), ("Q2", "A2")]
    for bad in (None, "no json", _reply([("Q", "A")]), json.dumps({"pairs": ["x", "y"]})):
        with pytest.raises(ReplyError):
            parse_pairs(bad, 2)
    with pytest.raises(ReplyError):
        parse_pairs(json.dumps({"pairs": [{"question": "Q"}, {"question": " ", "answer": "A"}]}), 2)


def test_build_pairs_drops_failures_near_duplicates_and_repeats():
    passages = training_passages(LIBRARY)[:3]
    test_question = LIBRARY.test[0].question
    replies = {
        passages[0].chunk_id: _reply(
            [("How do I reset it?", "Hold the button."), (test_question, "Copied.")]
        ),  # fmt: skip
        passages[1].chunk_id: _reply([("How do I reset it?", "Again."), ("Other?", "Yes.")]),
        passages[2].chunk_id: "not json",
    }
    pairs, log = build_pairs(passages, replies, 2, blocked_questions(LIBRARY))
    assert [p.question for p in pairs] == ["How do I reset it?", "Other?"]
    assert pairs[0].id == f"{passages[0].chunk_id}#0" and pairs[0].doc_key == passages[0].doc_key
    assert log["passages_failed"] == [passages[2].chunk_id]
    assert log["near_duplicates_of_dev_or_test"][0]["close_to"] == LIBRARY.test[0].id
    assert log["repeated_questions"] == 1 and log["pairs_kept"] == 2


def test_blocked_questions_include_resolved_follow_ups_and_pairs_round_trip(tmp_path):
    blocked = blocked_questions(LIBRARY)
    assert len([k for k in blocked if not k.endswith(":resolved")]) == 620
    assert any(k.endswith(":resolved") for k in blocked)
    pairs = [Pair(id="x#0", passage_id="x", doc_key="A000@1", question="Q?", answer="A.")]
    write_pairs(tmp_path / "p" / "pairs.jsonl", pairs)
    assert load_pairs(tmp_path / "p" / "pairs.jsonl") == pairs


def test_closed_book_prompt_is_the_question_and_any_earlier_turns():
    plain = next(i for i in LIBRARY.test if not i.history)
    follow = next(i for i in LIBRARY.test if i.history)
    assert closed_book_user(plain) == plain.question
    text = closed_book_user(follow)
    assert text.startswith("Conversation so far:") and text.endswith(follow.question)


# The tuning job


def _facts_job(tmp_path: Path, size: int) -> TuneConfig:
    pairs = [
        Pair(id=f"p{n}#0", passage_id=f"p{n}", doc_key="A000@1", question=f"Q{n}?", answer="A.")
        for n in range(5)
    ]
    write_pairs(tmp_path / "pairs.jsonl", pairs)
    raw = {
        "episode": "s4-test", "task": "facts", "arm": "e8-x", "base_model": "Qwen/Qwen3-0.6B",
        "train_size": size, "pairs": "pairs.jsonl", "data": str(HALVARD),
        "eval_splits": ["dev"],
    }  # fmt: skip
    path = tmp_path / "tune.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return TuneConfig.load(path)


def test_facts_job_trains_on_pairs_and_evaluates_closed_book(tmp_path):
    job = _facts_job(tmp_path, 3)
    assert len(train_subset(job)) == 3
    files, rows = _files(job)
    assert [m["role"] for m in rows[0]["messages"]] == ["system", "user", "assistant"]
    assert rows[0]["messages"][0]["content"] == FACTS_SHORT
    evals = [json.loads(line) for line in files["eval-dev.jsonl"].splitlines()]
    assert len(evals) == 100 and len(evals[0]["messages"]) == 2


def test_facts_task_needs_pairs_and_only_it():
    with pytest.raises(ValueError, match="pairs"):
        TuneConfig.model_validate(
            {"episode": "e", "task": "facts", "arm": "a", "base_model": "m", "train_size": 0}
        )
    with pytest.raises(ValueError, match="pairs"):
        TuneConfig.model_validate(
            {
                "episode": "e",
                "task": "a",
                "arm": "a",
                "base_model": "m",
                "train_size": 0,
                "pairs": "p.jsonl",
            }  # fmt: skip
        )


# Judging and scoring


def _verdict(correct: bool, declined: bool = False) -> str:
    return json.dumps({"declined": declined, "correct": correct, "faithful": False, "reason": "r"})


def _experiment(tmp_path: Path, arms: list[dict], reference: str) -> FactsExperiment:
    raw = {"episode": "s4-test-facts", "split": "test", "data": str(HALVARD), "judge": JUDGE,
           "reference": reference, "arms": arms}  # fmt: skip
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return FactsExperiment.load(path)


def test_arm_needs_exactly_one_source_and_reference_must_exist(tmp_path):
    with pytest.raises(ValueError):
        FactsArm(name="x")
    with pytest.raises(ValueError):
        FactsArm(name="x", predictions=Path("a"), s2_judge_log=Path("b"))
    with pytest.raises(ValueError, match="reference"):
        _experiment(tmp_path, [{"name": "a", "predictions": "p.jsonl"}], "b")
    with pytest.raises(ValueError, match="unique"):
        _experiment(
            tmp_path,
            [{"name": "a", "predictions": "p"}, {"name": "a", "predictions": "q"}],
            "a",
        )


def test_judge_is_shown_no_passages():
    experiment = FactsExperiment(
        episode="e", data=HALVARD, judge=ModelSpec(**JUDGE),
        arms=(FactsArm(name="a", predictions=Path("p")),), reference="a",
    )  # fmt: skip
    item = LIBRARY.test[0]
    requests = judge_requests(experiment, [item], {item.id: "No idea."})
    assert "Passages given to the system:\n(none)" in requests[item.id].prompt
    assert judge_requests(experiment, [item], {}) == {}


def test_season_two_log_has_a_verdict_for_every_test_item():
    texts = s2_verdict_texts(S2_LOG)
    assert len(texts) == 520
    scores = score(LIBRARY.test, read_verdicts(texts))
    summary = summarise(scores)
    # Season 2's own measure: correct and faithful, 354 of 400; declines 107 of 120.
    assert summary["right_and_faithful"]["count"] == 354
    assert summary["declined_unanswerable"]["count"] == 107


def test_score_counts_right_declines_and_confident_wrong():
    items = [i for i in LIBRARY.test if i.answerable][:2] + [
        i for i in LIBRARY.test if not i.answerable
    ][:2]
    verdicts = read_verdicts(
        {
            items[0].id: _verdict(True),
            items[1].id: _verdict(False),
            items[2].id: _verdict(True, declined=True),
            items[3].id: "unreadable",
        }
    )
    summary = summarise(score(items, verdicts))
    assert summary["right"]["count"] == 1 and summary["right"]["total"] == 2
    assert summary["declined_unanswerable"]["count"] == 1
    assert summary["confident_wrong"]["count"] == 1 and summary["unjudged"] == 1


def test_analyse_reads_both_sources(tmp_path):
    experiment = _experiment(
        tmp_path,
        [
            {"name": "closed", "predictions": "results/closed/predictions-test.jsonl"},
            {"name": "ref", "s2_judge_log": str(S2_LOG)},
        ],
        "ref",
    )
    write_jsonl(
        experiment.verdicts_path("closed"),
        [{"id": i.id, "text": _verdict(False)} for i in LIBRARY.test],
    )
    result = analyse(experiment)
    assert result["arms"]["closed"]["right"]["count"] == 0
    assert result["arms"]["closed"]["confident_wrong"]["count"] == 520
    assert result["arms"]["ref"]["source"] == "season 2 run log"


# CLI


def _prices(tmp_path: Path, episode: str, budget: float) -> Path:
    path = tmp_path / "prices.yaml"
    prices = {"google": {"gemini-3.1-flash-lite": {"input": 0.25, "output": 1.5},
                         "gemini-3.6-flash": {"input": 0.75, "output": 3.75}}}  # fmt: skip
    path.write_text(
        yaml.safe_dump({"prices": prices, "budgets": {episode: budget}}), encoding="utf-8"
    )
    return path


def _patch_provider(monkeypatch, respond) -> None:
    import lab.adapt.cli_facts as cli_facts

    provider = MockProvider(respond=respond, supported_reasoning=("minimal",))
    available = SimpleNamespace(providers={"google": provider}, missing_keys={})
    monkeypatch.setattr(cli_facts, "available_providers", lambda names: available)


def test_cli_pairs_estimates_gates_and_writes(tmp_path, monkeypatch):
    raw = {"episode": "s4-test-pairs", "data": str(HALVARD),
           "generator": GEN.model_dump(), "per_passage": 2, "out": "pairs/pairs.jsonl",
           "limits": FAST}  # fmt: skip
    config = tmp_path / "pairs.yaml"
    config.write_text(yaml.safe_dump(raw), encoding="utf-8")
    runner = CliRunner()
    estimate = runner.invoke(app, ["adapt", "pairs", str(config), "--estimate"])
    assert estimate.exit_code == 0 and "pairs" in estimate.output
    poor = _prices(tmp_path, "s4-test-pairs", 0.0001)
    over = runner.invoke(app, ["adapt", "pairs", str(config), "--prices-path", str(poor)])
    assert over.exit_code == 1 and "ceiling cost" in over.output

    counter = iter(range(10_000))
    _patch_provider(
        monkeypatch,
        lambda request: _reply([(f"Question {next(counter)}?", "An answer.")] * 2),
    )
    prices = _prices(tmp_path, "s4-test-pairs", 5.0)
    args = ["adapt", "pairs", str(config), "--prices-path", str(prices)]
    args += ["--cache-dir", str(tmp_path / "cache"), "--env-file", str(tmp_path / "none")]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    # The mock repeats each question twice, so one of each two is removed as a repeat.
    assert "Kept 436 pairs from 436 passages" in result.output
    assert len(load_pairs(tmp_path / "pairs" / "pairs.jsonl")) == 436
    assert (tmp_path / "pairs" / "pairs-log.json").exists()


def test_cli_facts_run_and_analyse(tmp_path, monkeypatch):
    predictions = tmp_path / "results" / "closed" / "predictions-dev.jsonl"
    write_jsonl(predictions, [{"id": i.id, "text": "I could not find it."} for i in LIBRARY.dev])
    raw = {"episode": "s4-test-facts", "split": "dev", "data": str(HALVARD), "judge": JUDGE,
           "reference": "closed",
           "arms": [{"name": "closed", "predictions": "results/closed/predictions-dev.jsonl"},
                    {"name": "ref", "s2_judge_log": str(S2_LOG)}], "limits": FAST}  # fmt: skip
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(raw), encoding="utf-8")
    runner = CliRunner()
    estimate = runner.invoke(app, ["adapt", "facts-run", str(config), "--estimate"])
    assert estimate.exit_code == 0 and "judge closed" in estimate.output
    _patch_provider(monkeypatch, lambda request: _verdict(False, declined=True))
    prices = _prices(tmp_path, "s4-test-facts", 5.0)
    args = ["adapt", "facts-run", str(config), "--prices-path", str(prices)]
    args += ["--cache-dir", str(tmp_path / "cache"), "--env-file", str(tmp_path / "none")]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "judge-closed: made 100" in result.output
    analysed = runner.invoke(app, ["adapt", "facts-analyse", str(config)])
    assert analysed.exit_code == 0, analysed.output
    assert "closed: right 0 of" in analysed.output
    assert (tmp_path / "results" / "analysis-facts-dev.json").exists()


def test_cli_stops_without_a_key(tmp_path, monkeypatch):
    import lab.adapt.cli_facts as cli_facts

    predictions = tmp_path / "p.jsonl"
    write_jsonl(predictions, [{"id": LIBRARY.dev[0].id, "text": "x"}])
    raw = {"episode": "s4-test-facts", "split": "dev", "data": str(HALVARD), "judge": JUDGE,
           "reference": "c", "arms": [{"name": "c", "predictions": "p.jsonl"}]}  # fmt: skip
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(raw), encoding="utf-8")
    missing = SimpleNamespace(providers={}, missing_keys={"google": ["GOOGLE_API_KEY"]})
    monkeypatch.setattr(cli_facts, "available_providers", lambda names: missing)
    prices = _prices(tmp_path, "s4-test-facts", 5.0)
    args = ["adapt", "facts-run", str(config), "--prices-path", str(prices)]
    args += ["--env-file", str(tmp_path / "none")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1 and "GOOGLE_API_KEY" in result.output
    nobudget = CliRunner().invoke(app, ["adapt", "facts-run", str(config), "--prices-path", "x"])
    assert nobudget.exit_code == 1 and "budget" in nobudget.output
