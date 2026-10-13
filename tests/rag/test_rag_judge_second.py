import json

import yaml
from typer.testing import CliRunner

from lab.cache import ResponseCache
from lab.cli import app
from lab.providers.mock import MockProvider
from lab.rag.chunk import WholeChunker, chunk_library
from lab.rag.config import ModelSpec
from lab.rag.judge import Verdict
from lab.rag.judge_check import Mark
from lab.rag.judge_second import (
    disagreement,
    pick_for_hand,
    read_second,
    run_second,
    second_prompts,
    two_marker_report,
)
from lab.rag.log import write_log
from lab.runner import Runner, RunnerSettings
from tests.rag.test_rag_judge_check import _log, _pipeline

GEMINI = ModelSpec(
    provider="google", model="gemini-3.6-flash", reasoning="medium", max_output_tokens=4000
)


def _v(declined=False, correct=True, faithful=True, reason="r"):
    return Verdict(declined=declined, correct=correct, faithful=faithful, reason=reason)


def _m(item_id, declined=False, correct=True, faithful=True, note=""):
    return Mark(item_id=item_id, declined=declined, correct=correct, faithful=faithful, note=note)


def test_a_split_on_right_outranks_other_differences():
    same = disagreement(_v(), _v())
    declined_only = disagreement(_v(correct=False), _v(declined=True, correct=False))
    split = disagreement(_v(), _v(correct=False))

    assert same == 0 < declined_only < disagreement(_v(), None) < split


def test_hand_items_are_the_strongest_disagreements_in_sample_order():
    first = {i: _v() for i in "abcde"}
    second = {
        "a": _v(),
        "b": _v(declined=True),
        "c": _v(correct=False),
        "d": _v(),
        "e": _v(correct=False),
    }

    assert pick_for_hand(list("abcde"), first, second, 3) == ["c", "e", "b"]
    assert pick_for_hand(list("abcde"), first, second, 5)[3:] == ["a", "d"]


def test_report_compares_models_hand_and_code_check():
    logs = [
        _log("a", verdict=_v(), code_check=True),
        _log("b", verdict=_v(), code_check=True),
        _log("c", verdict=_v(correct=False), code_check=True),
        _log("d", verdict=_v()),
    ]
    second = {"a": _v(), "b": _v(correct=False), "c": _v(), "d": None}
    marks = [_m("b"), _m("c", note="gave both values")]
    report = two_marker_report(list("abcd"), logs, second, marks)

    assert report["second_errors"] == ["d"]
    assert report["models"]["right"]["count"] == 1 and report["models"]["right"]["total"] == 3
    split = report["key_split"]
    assert (split["items"], split["hand_marked"], split["hand_sides_with_judge"]) == (2, 2, 1)
    assert split["hand_sides_with_second"] == 1
    # One item where both models agree, plus one hand-marked split the judge got right.
    assert (report["judge_key_estimate"]["count"], report["judge_key_estimate"]["total"]) == (
        2,
        3,
    )
    assert report["code_check_on_hand"] == {
        "items": 2,
        "judge_matches_hand": 1,
        "code_matches_hand": 2,
    }
    assert {r["item_id"] for r in report["hand_disagreements"]} == {"b", "c"}


def _setup(tmp_path, library, library_dir):
    chunks = chunk_library(library.documents, WholeChunker())
    logs = [_log(i.id, i.type, _v(), chunks=[chunks[0].chunk_id]) for i in library.test]
    run = tmp_path / "run"
    write_log(run / "log.jsonl", logs)
    summary = {"episode": "e", "condition": "baseline", "config_id": "cfg", "pipeline": _pipeline()}
    (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    config = tmp_path / "judge_check.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "run": "run",
                "library": str(library_dir),
                "out": "check",
                "size": len(logs),
                "per_type": 1,
                "seed": 3,
                "hand": 2,
                "second_judge": GEMINI.model_dump(mode="json"),
            }
        ),
        encoding="utf-8",
    )
    return logs, {c.chunk_id: c for c in chunks}, config


def test_second_model_reads_exactly_the_judges_prompt_and_saves_verdicts(
    tmp_path, library, library_dir
):
    logs, chunks, _ = _setup(tmp_path, library, library_dir)
    sample = [g.item_id for g in logs[:3]]
    prompts = second_prompts(sample, logs, library, chunks)
    seen = []

    def respond(request):
        seen.append(request)
        if len(seen) == 1:
            return "not a verdict"
        return json.dumps({"declined": False, "correct": False, "faithful": True, "reason": "r"})

    runner = Runner(
        providers={"google": MockProvider(respond=respond)},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    verdicts, _ = run_second(runner, prompts, GEMINI, tmp_path / "second")

    assert {r.model for r in seen} == {"gemini-3.6-flash"}
    assert seen[0].prompt in prompts.values() and "Reference answer:" in seen[0].prompt
    assert all(v is not None and v.correct is False for v in verdicts.values())
    assert read_second(tmp_path / "second") == verdicts


def test_cli_estimates_without_a_key(tmp_path, library, library_dir):
    _, _, config = _setup(tmp_path, library, library_dir)
    runner = CliRunner()
    assert runner.invoke(app, ["rag", "judge-check", "draw", str(config)]).exit_code == 0

    result = runner.invoke(
        app,
        [
            "rag",
            "judge-check",
            "second",
            str(config),
            "--estimate",
            "--prices-path",
            str(tmp_path / "none.yaml"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "calls to gemini-3.6-flash at reasoning medium" in result.output
    record = json.loads((tmp_path / "check" / "sample.json").read_text(encoding="utf-8"))
    assert "hand" not in record


def test_without_faithful_marks_the_report_keys_on_correct():
    logs = [_log("a", verdict=_v()), _log("b", verdict=_v(faithful=False))]
    second = {"a": _v(correct=False), "b": _v()}
    marks = [
        Mark(item_id="a", declined=False, correct=True),
        Mark(item_id="b", declined=False, correct=True),
    ]
    report = two_marker_report(["a", "b"], logs, second, marks, ("declined", "correct"))

    assert report["key_verdict"] == "correct" and set(report["judge_with_hand"]) == {
        "declined",
        "correct",
    }
    assert report["key_split"]["items"] == 1 and report["key_split"]["hand_sides_with_judge"] == 1
    assert report["hand_disagreements"][0]["item_id"] == "a"
