import csv
import json
from collections import Counter

import pytest
import yaml
from typer.testing import CliRunner

from lab.cli import app
from lab.rag.chunk import WholeChunker, chunk_library
from lab.rag.judge import Verdict
from lab.rag.judge_check import (
    MARKS,
    SAMPLE,
    SHEET,
    agreement,
    draw_sample,
    load_check_config,
    outcome,
    read_marks,
    write_sheet,
)
from lab.rag.log import ItemLog, ModelCall, write_log


def _verdict(declined=False, correct=True, faithful=True):
    return Verdict(declined=declined, correct=correct, faithful=faithful, reason="r")


def _log(item_id, type_="t", verdict=None, chunks=(), code_check=None, answer="An answer."):
    return ItemLog(
        item_id=item_id,
        type=type_,
        asker="public",
        answerable=True,
        condition="baseline",
        config_id="cfg",
        queries=("q",),
        searched=(),
        removed=(),
        ranked=(),
        prompt_chunks=tuple(chunks),
        spans=(),
        evidence_rank=None,
        distractor_above=False,
        leaks=(),
        verdict=verdict,
        code_check=code_check,
        answer=ModelCall(
            text=answer,
            model_returned="m",
            input_tokens=1,
            output_tokens=1,
            reasoning_tokens=0,
            finish_reason="stop",
        ),
    )


def _many(types, per, verdicts):
    return [_log(f"{t}-{n:03d}", t, verdicts[n % len(verdicts)]) for t in types for n in range(per)]


def test_outcome_names_the_judges_call():
    assert outcome(_verdict()) == "right"
    assert outcome(_verdict(correct=False)) == "wrong"
    assert outcome(_verdict(declined=True, correct=False)) == "declined"


def test_sample_takes_per_type_then_fills_to_size():
    logs = _many(["a", "b", "c"], 10, [_verdict()])
    sample = draw_sample(logs, size=10, per_type=3, seed=1)

    assert len(sample) == len(set(sample)) == 10
    counts = Counter(s.split("-")[0] for s in sample)
    assert all(counts[t] >= 3 for t in "abc")


def test_sample_spreads_each_type_across_the_judges_outcomes():
    verdicts = [_verdict()] * 8 + [_verdict(correct=False), _verdict(declined=True)]
    logs = _many(["a"], 10, verdicts)
    picked = draw_sample(logs, size=3, per_type=3, seed=4)
    by_id = {g.item_id: g for g in logs}

    assert {outcome(by_id[i].verdict) for i in picked} == {"right", "wrong", "declined"}


def test_sample_is_fixed_by_the_seed_and_skips_unjudged_items():
    logs = _many(["a", "b"], 6, [_verdict()]) + [_log("a-999", "a", None)]

    first = draw_sample(logs, size=6, per_type=2, seed=7)
    assert first == draw_sample(logs, size=6, per_type=2, seed=7)
    assert "a-999" not in first


def test_sample_refuses_more_per_type_than_it_has_room_for():
    with pytest.raises(ValueError, match="more than the sample"):
        draw_sample(_many(["a", "b"], 3, [_verdict()]), size=3, per_type=2, seed=1)


def _sheet(tmp_path, library):
    chunks = {c.chunk_id: c for c in chunk_library(library.documents, WholeChunker())}
    first = next(iter(chunks))
    logs = [_log(i.id, i.type, _verdict(), chunks=[first]) for i in library.test[:3]]
    sample = [g.item_id for g in logs]
    write_sheet(tmp_path, sample, logs, library, chunks)
    return logs, sample


def test_sheet_shows_what_the_judge_saw_and_hides_the_verdict(tmp_path, library):
    logs, sample = _sheet(tmp_path, library)
    sheet = (tmp_path / SHEET).read_text(encoding="utf-8")

    assert f"## 1. {sample[0]}" in sheet
    assert "Passages given to the system:\n[P1]" in sheet
    assert "System's answer:\nAn answer." in sheet
    assert '"declined": false' not in sheet and "reason" not in sheet.split("---")[1]
    with (tmp_path / MARKS).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["item_id"] for r in rows] == sample and rows[0]["correct"] == ""


def test_drawing_again_never_overwrites_marks(tmp_path, library):
    _, sample = _sheet(tmp_path, library)
    _mark(tmp_path / MARKS, {sample[0]: "y,y,y"})

    with pytest.raises(FileExistsError):
        _sheet(tmp_path, library)


def _mark(path, values):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["item_id"] in values:
            row["declined"], row["correct"], row["faithful"] = values[row["item_id"]].split(",")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_marks_must_be_complete(tmp_path, library):
    _, sample = _sheet(tmp_path, library)
    _mark(tmp_path / MARKS, {sample[0]: "n,Y,yes"})

    with pytest.raises(ValueError, match="not marked y or n"):
        read_marks(tmp_path / MARKS, sample)
    _mark(tmp_path / MARKS, {s: "n,y,y" for s in sample})
    assert [m.correct for m in read_marks(tmp_path / MARKS, sample)] == [True] * 3


def test_marks_must_match_the_sample(tmp_path, library):
    _, sample = _sheet(tmp_path, library)
    _mark(tmp_path / MARKS, {s: "n,y,y" for s in sample})

    with pytest.raises(ValueError, match="missing from the marks: ZZZ"):
        read_marks(tmp_path / MARKS, [*sample, "ZZZ"])


def test_agreement_counts_each_field_and_lists_disagreements(tmp_path, library):
    logs = [
        _log("x1", verdict=_verdict(), code_check=True),
        _log("x2", verdict=_verdict(correct=False), code_check=True),
        _log("x3", verdict=_verdict(faithful=False)),
    ]
    path = tmp_path / "m.csv"
    path.write_text(
        "n,item_id,declined,correct,faithful,note\n1,x1,n,y,y,\n2,x2,n,y,y,close call\n"
        "3,x3,n,y,n,\n",
        encoding="utf-8",
    )
    report = agreement(read_marks(path, ["x1", "x2", "x3"]), logs)

    assert report["fields"]["correct"]["agree"]["count"] == 2
    assert report["fields"]["correct"]["judge_no_hand_yes"] == 1
    assert report["fields"]["faithful"]["agree"]["count"] == 3
    assert report["fields"]["right"]["agree"]["count"] == 2
    assert report["code_check_with_hand_on_correct"] == pytest.approx(
        {
            "count": 2,
            "total": 2,
            "rate": 1.0,
            "low": report["code_check_with_hand_on_correct"]["low"],
            "high": 1.0,
        }
    )
    [d] = report["disagreements"]
    assert d["item_id"] == "x2" and d["fields"] == ["correct"] and d["note"] == "close call"


def test_cli_draws_then_reports(tmp_path, library, library_dir):
    chunks = chunk_library(library.documents, WholeChunker())
    logs = [_log(i.id, i.type, _verdict(), chunks=[chunks[0].chunk_id]) for i in library.test]
    run = tmp_path / "run"
    write_log(run / "log.jsonl", logs)
    summary = {
        "episode": "e",
        "condition": "baseline",
        "config_id": "cfg",
        "pipeline": _pipeline(),
    }
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
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    drawn = runner.invoke(app, ["rag", "judge-check", "draw", str(config)])
    assert drawn.exit_code == 0, drawn.output
    early = runner.invoke(app, ["rag", "judge-check", "report", str(config)])
    assert early.exit_code == 1 and "not marked" in early.output

    out = load_check_config(config).out
    sample = json.loads((out / SAMPLE).read_text(encoding="utf-8"))["items"]
    _mark(out / MARKS, {s: "n,y,y" for s in sample})
    done = runner.invoke(app, ["rag", "judge-check", "report", str(config)])
    assert done.exit_code == 0, done.output
    assert f"correct: {len(logs)}/{len(logs)} agree" in done.output


def _pipeline():
    from tests.rag.mini_corpus import REFERENCE

    return dict(REFERENCE, chunk={"kind": "whole"})


def test_marks_can_leave_out_faithful(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text("n,item_id,declined,correct,faithful,note\n1,x1,n,y,,\n", encoding="utf-8")

    [mark] = read_marks(path, ["x1"], ("declined", "correct"))
    assert mark.correct is True and mark.faithful is None
