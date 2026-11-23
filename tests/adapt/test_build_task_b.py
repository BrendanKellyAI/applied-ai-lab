"""The Task B build end to end on a tiny config, with offline stand-ins for both models."""

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.build_tasks.config import TaskBuildConfig
from lab.adapt.build_tasks.estimate import estimate_task_b, format_estimate
from lab.adapt.build_tasks.passages import (
    NOT_FOUND,
    passages,
    policy_sections,
    split_passages,
    usable,
)
from lab.adapt.build_tasks.prompts_b import (
    CHECK_SYSTEM,
    NOT_FOUND_ANSWER,
    QA_SYSTEM,
    REWRITE_SYSTEM,
)
from lab.adapt.build_tasks.task_b import (
    build_task_b,
    check_qa,
    check_rewrite,
    plan_b_seeds,
    write_b_review_sample,
)
from lab.adapt.style import CLOSE, OPENING, check_reply
from lab.adapt.style import NOT_FOUND as NOT_FOUND_SENTENCE
from lab.cache import ResponseCache
from lab.cli import app
from lab.providers.mock import MockProvider
from lab.rag.corpus import load_library
from lab.runner import Runner, RunnerSettings

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "datasets" / "halvard-tasks"
LIBRARY = load_library(ROOT / "datasets" / "halvard")
STYLE = (SOURCE / "style-guide.md").read_text(encoding="utf-8")


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "halvard-tasks"
    folder.mkdir()
    for name in ("routes.yaml", "style-guide.md"):
        shutil.copy(SOURCE / name, folder / name)
    config = yaml.safe_load((SOURCE / "config.yaml").read_text(encoding="utf-8"))
    config["task_b"]["library"] = str(ROOT / "datasets" / "halvard")
    config["task_b"]["splits"] = {"train": 12, "dev": 3, "test": 6}
    config["task_b"]["pilot_seeds"] = 4
    (folder / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return folder


class FakeModels:
    """Generator: a question and answer, then a reply that passes every style check, except
    that each first rewrite draft has no opening. Checker: says yes, except that it calls
    every `unsupported_every`th answer unsupported."""

    def __init__(self, unsupported_every: int = 0) -> None:
        self.unsupported_every = unsupported_every
        self.supports = 0

    def __call__(self, request) -> str:
        if request.system == QA_SYSTEM:
            return self._qa(request.prompt)
        if request.system == REWRITE_SYSTEM:
            return self._rewrite(request.prompt)
        assert request.system == CHECK_SYSTEM
        if "passage_answers" in request.prompt:
            return json.dumps({"passage_answers": False})
        if "all_facts_kept" in request.prompt:
            return json.dumps({"all_facts_kept": True, "facts_added": False})
        self.supports += 1
        ok = not (self.unsupported_every and self.supports % self.unsupported_every == 0)
        return json.dumps({"supported": ok, "answers_question": True})

    def _qa(self, prompt: str) -> str:
        number = abs(hash(prompt)) % 100000
        question = f"What does the passage say, question {number}?"
        if "does not answer" in prompt:
            return json.dumps({"question": question, "answer": NOT_FOUND_ANSWER})
        return json.dumps({"question": question, "answer": f"It says fact {number}."})

    def _rewrite(self, prompt: str) -> str:
        cite = re.search(r"Cite the source in exactly this form: (.+)", prompt)
        if cite:
            middle = f"{cite.group(1)} " + "that the cover applies as set out. " * 8
        else:
            middle = NOT_FOUND_SENTENCE
        opening = OPENING if "Your draft:" in prompt else "Hello."
        reply = f"{opening}\n\n{middle.strip()}\n\n{CLOSE[0]}\n{CLOSE[1]}"
        return json.dumps({"reply": reply})


def _runner(tmp_path: Path, fake: FakeModels) -> Runner:
    provider = MockProvider(respond=fake, supported_reasoning=("minimal", "off"))
    return Runner(
        providers={"google": provider, "anthropic": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("task-b")
    folder = _folder(tmp_path)
    config = TaskBuildConfig.load(folder / "config.yaml")
    log = build_task_b(
        _runner(tmp_path, FakeModels(unsupported_every=5)),
        config,
        LIBRARY,
        STYLE,
        folder / "task-b",
        pilot=False,
    )
    return folder, config, log


def _rows(folder: Path, split: str) -> list[dict]:
    text = (folder / "task-b" / f"{split}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_build_keeps_each_split_and_every_target_passes_the_style_checks(built):
    folder, config, log = built
    assert log["kept"] == config.task_b.splits
    for split in config.task_b.splits:
        for row in _rows(folder, split):
            source = row["source"]
            from lab.adapt.style import Source

            report = check_reply(row["target_reply"], Source(**source))
            assert report.all_pass, (row["id"], report.failures())


def test_unsupported_answers_are_dropped_and_logged(built):
    folder, _, log = built
    assert log["unsupported"]
    kept = {row["id"] for split in ("train", "dev", "test") for row in _rows(folder, split)}
    assert not kept & set(log["unsupported"])


def test_first_rewrite_drafts_are_retried(built):
    _, _, log = built
    first, second = log["calls"]["rewrite"]
    assert second["planned"] > 0
    assert not log["rewrite_failed"]


def test_test_items_never_share_a_passage_with_train(built):
    folder, _, _ = built
    train = {row["passage_id"] for row in _rows(folder, "train")}
    test = {row["passage_id"] for row in _rows(folder, "test")}
    assert not train & test


def test_review_sample_is_numbered(built):
    folder, config, _ = built
    review = (folder / "review" / "task-b-test-sample.md").read_text(encoding="utf-8")
    assert review.count("**Question:**") == config.task_b.splits["test"]
    assert "## 1. " in review


def test_pilot_builds_dev_only(tmp_path):
    folder = _folder(tmp_path)
    config = TaskBuildConfig.load(folder / "config.yaml")
    log = build_task_b(
        _runner(tmp_path, FakeModels()), config, LIBRARY, STYLE, folder / "pilot-b", pilot=True
    )
    assert log["kept"] == {"dev": 4}


def test_passages_use_current_public_documents_only():
    found = passages(LIBRARY)
    keys = {p.id.split("#")[0] for p in found}
    assert not any(key.startswith(("INT-", "DEL-")) for key in keys)
    assert "POL-WAR@1" not in keys and "POL-WAR@2" in keys
    assert all(usable(d) for d in LIBRARY.documents if d.key in keys)


def test_policy_sections_are_labelled_with_their_parent():
    warranty = LIBRARY.document("POL-WAR@2")
    labels = [p.section for p in policy_sections(warranty)]
    assert "Registering your appliance" in labels
    assert "Brio kettle: Cover period" in labels


def test_passage_split_is_reproducible_and_covers_every_passage():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    found = passages(LIBRARY)
    cuts = split_passages(found, config.task_b, config.seed)
    assert cuts == split_passages(found, config.task_b, config.seed)
    assert sum(len(v) for v in cuts.values()) == len(found)


def test_seed_plan_has_the_not_found_share_and_varies_repeat_prompts():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seeds = plan_b_seeds(config, LIBRARY, pilot=False)
    test = [s for s in seeds if s.split == "test"]
    assert sum(s.kind == NOT_FOUND for s in test) == round(len(test) * 0.10)
    assert len({(s.passage.id, s.variant) for s in seeds}) == len(seeds)


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("nope", "not valid JSON"),
        ('{"question": 1}', "question"),
        ('{"question": "", "answer": "a"}', "one to three sentences"),
        ('{"question": "q?", "answer": ""}', "under 90 words"),
    ],
)
def test_qa_checks(text, problem):
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seed = next(s for s in plan_b_seeds(config, LIBRARY, pilot=True) if s.kind != NOT_FOUND)
    assert problem in check_qa(seed, text)


def test_not_found_answer_must_be_exact():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seed = next(s for s in plan_b_seeds(config, LIBRARY, pilot=False) if s.kind == NOT_FOUND)
    assert "must be exactly" in check_qa(seed, '{"question": "q?", "answer": "No idea."}')
    good = json.dumps({"question": "q?", "answer": NOT_FOUND_ANSWER})
    assert check_qa(seed, good) is None
    assert "not valid JSON" in check_rewrite(seed, "nope")
    assert "breaks these rules" in check_rewrite(seed, json.dumps({"reply": "Hi."}))


def test_review_sample_writer_handles_blank_reply_lines(tmp_path):
    row = {
        "id": "B-test-00001",
        "kind": "answerable",
        "passage_id": "A000@1",
        "question": "q?",
        "answer": "a.",
        "target_reply": "Line one.\n\nLine two.",
    }
    path = write_b_review_sample(tmp_path, [row], 1)
    assert "> Line one.\n>\n> Line two." in path.read_text(encoding="utf-8")


def test_estimate_has_four_stages():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seeds = plan_b_seeds(config, LIBRARY, pilot=True)
    costs = estimate_task_b(config, seeds, STYLE, None)
    assert [c.stage for c in costs] == ["qa", "support", "rewrite", "facts"]
    assert "price is missing" in format_estimate(costs, "USD", "Task B")


def test_cli_task_b_estimate_and_bad_task(tmp_path):
    folder = _folder(tmp_path)
    runner = CliRunner()
    base = ["adapt", "build-tasks", "--folder", str(folder), "--prices-path", "none.yaml"]
    result = runner.invoke(app, [*base, "--task", "b", "--estimate"])
    assert result.exit_code == 0, result.output
    assert "rewrite" in result.output
    assert runner.invoke(app, [*base, "--task", "c"]).exit_code == 1


def test_cli_task_b_pilot_build(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import lab.adapt.cli as adapt_cli

    folder = _folder(tmp_path)
    provider = MockProvider(respond=FakeModels(), supported_reasoning=("minimal", "off"))
    available = SimpleNamespace(
        providers={"google": provider, "anthropic": provider}, missing_keys={}
    )
    monkeypatch.setattr(adapt_cli, "available_providers", lambda names: available)
    prices = tmp_path / "prices.yaml"
    prices.write_text(
        yaml.safe_dump(
            {
                "prices": {
                    "google": {"gemini-3.1-flash-lite": {"input": 0.25, "output": 1.5}},
                    "anthropic": {"claude-haiku-5-5": {"input": 0.1, "output": 0.5}},
                },
                "budgets": {"s4-task-b-data": 1.0},
            }
        ),
        encoding="utf-8",
    )
    args = ["adapt", "build-tasks", "--task", "b", "--pilot", "--folder", str(folder)]
    args += ["--prices-path", str(prices), "--cache-dir", str(tmp_path / "cache")]
    args += ["--env-file", str(tmp_path / "none.env")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Kept: {'dev': 4}" in result.output
