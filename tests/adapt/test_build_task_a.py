"""The Task A build end to end on a tiny config, with offline stand-ins for both models."""

import hashlib
import json
import random
import re
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.build_tasks.checks import (
    ReplyError,
    check_message,
    message_of,
    parse_object,
    product_mentions,
)
from lab.adapt.build_tasks.config import TaskBuildConfig
from lab.adapt.build_tasks.dedupe import NearDuplicateIndex, jaccard, near_duplicates, shingles
from lab.adapt.build_tasks.estimate import estimate_task_a, format_estimate
from lab.adapt.build_tasks.prompts import GENERATOR_SYSTEM, ROUTE_BRIEFS
from lab.adapt.build_tasks.seeds import SAFETY_FAULTS, draw_seeds, kinds_for, seed_count
from lab.adapt.build_tasks.task_a import build_task_a, parse_label, plan_seeds
from lab.adapt.definitions import Definitions, Label
from lab.cache import ResponseCache
from lab.cli import app
from lab.prices import PricesFile
from lab.providers.mock import MockProvider
from lab.runner import Runner, RunnerSettings

SOURCE = Path(__file__).parents[2] / "datasets" / "halvard-tasks"
DEFINITIONS = Definitions.load(SOURCE / "routes.yaml")
ROUTES = list(DEFINITIONS.routes)
FAULTS = [None, *DEFINITIONS.faults]
PRODUCTS = [None, *DEFINITIONS.products]
WORDS = [f"word{n}" for n in range(400)]


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "halvard-tasks"
    folder.mkdir()
    shutil.copy(SOURCE / "routes.yaml", folder / "routes.yaml")
    config = yaml.safe_load((SOURCE / "config.yaml").read_text(encoding="utf-8"))
    config["task_a"]["splits"] = {"train": 30, "dev": 6, "test": 10}
    config["task_a"]["overgenerate"] = 0.3
    config["task_a"]["pilot_seeds"] = 5
    (folder / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return folder


def _code(label: Label) -> str:
    """The label, written into the fake message so the fake labeller can read it back."""
    parts = (
        ROUTES.index(label.route),
        int(label.safety),
        PRODUCTS.index(label.product),
        FAULTS.index(label.fault),
    )
    return "ref " + "x".join(str(p) for p in parts)


def _label_from_prompt(prompt: str) -> Label:
    route = next(name for name, brief in ROUTE_BRIEFS.items() if f"The customer {brief}." in prompt)
    product = re.search(r"their Halvard (.+?); name it", prompt)
    fault = re.search(r"The problem they describe: (.+)", prompt)
    fault_key = None
    if fault:
        fault_key = next(k for k, v in DEFINITIONS.faults.items() if v == fault.group(1).strip())
    return Label(
        route=route,
        safety=fault_key in SAFETY_FAULTS,
        product=product.group(1) if product else None,
        fault=fault_key,
    )


class FakeModels:
    """Generator: a message in the length band naming the right products, with the label coded
    in it. Every first draft is too short. Labeller: reads the code,
    except for messages it is told to get wrong."""

    def __init__(self, *, wrong_route_every: int = 0) -> None:
        self.wrong_route_every = wrong_route_every
        self.labelled = 0

    def __call__(self, request) -> str:
        if request.system == GENERATOR_SYSTEM:
            return self._generate(request.prompt)
        return self._label(request.prompt)

    def _generate(self, prompt: str) -> str:
        label = _label_from_prompt(prompt)
        low, high = map(int, re.search(r"Length: (\d+) to (\d+) words", prompt).groups())
        named = [f"Halvard {label.product}"] if label.product else []
        other = re.search(r"in passing: Halvard (.+?)\.$", prompt, re.MULTILINE)
        if other:
            named.append(f"Halvard {other.group(1)}")
        rng = random.Random(hashlib.sha256(prompt.encode()).hexdigest())
        draft = "Your draft:" in prompt
        count = (low + high) // 2 if draft else 2
        body = " ".join(rng.choice(WORDS) for _ in range(count))
        message = " ".join([*named, body, _code(label)])
        return json.dumps({"message": message})

    def _label(self, prompt: str) -> str:
        self.labelled += 1
        code = re.search(r"ref (\d+)x(\d+)x(\d+)x(\d+)", prompt)
        route, safety, product, fault = map(int, code.groups())
        if self.wrong_route_every and self.labelled % self.wrong_route_every == 0:
            route = (route + 1) % len(ROUTES)
        return json.dumps(
            {
                "route": ROUTES[route],
                "safety": bool(safety),
                "product": PRODUCTS[product],
                "fault": FAULTS[fault],
            }
        )


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
    tmp_path = tmp_path_factory.mktemp("task-a")
    folder = _folder(tmp_path)
    config = TaskBuildConfig.load(folder / "config.yaml")
    fake = FakeModels(wrong_route_every=7)
    log = build_task_a(_runner(tmp_path, fake), config, DEFINITIONS, folder / "task-a", pilot=False)
    return folder, config, log


def _rows(folder: Path, split: str) -> list[dict]:
    text = (folder / "task-a" / f"{split}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_build_keeps_the_configured_size_of_each_split(built):
    folder, config, log = built
    assert log["kept"] == config.task_a.splits
    for split, size in config.task_a.splits.items():
        assert len(_rows(folder, split)) == size


def test_labeller_disagreements_are_discarded_and_counted(built):
    folder, _, log = built
    disagreements = log["label_disagreements"]
    assert disagreements["total"] > 0
    assert disagreements["by_field"] == {"route": disagreements["total"]}
    kept_ids = {row["id"] for split in ("train", "dev", "test") for row in _rows(folder, split)}
    assert not kept_ids & set(disagreements["items"])


def test_rows_carry_the_seeded_label_and_safety_items(built):
    folder, _, log = built
    rows = _rows(folder, "train")
    assert all(Label.model_validate(row["label"]) for row in rows)
    assert log["safety_items_kept"]["train"] == sum(row["label"]["safety"] for row in rows)


def test_short_first_drafts_are_retried_with_the_reason(built):
    _, _, log = built
    first, second = log["generation_attempts"]
    assert first["planned"] > 50
    assert second["planned"] > 0
    assert not log["generation_failed"]


def test_review_sample_lists_test_items_for_hand_checking(built):
    folder, config, _ = built
    review = (folder / "review" / "task-a-test-sample.md").read_text(encoding="utf-8")
    assert review.count("- [ ] label is right") == config.task_a.splits["test"]


def test_rebuild_is_served_from_the_cache(built, tmp_path):
    folder, config, _ = built
    shutil.copytree(folder.parent / "cache", tmp_path / "cache")
    fake = FakeModels(wrong_route_every=7)
    out = tmp_path / "again"
    log = build_task_a(_runner(tmp_path, fake), config, DEFINITIONS, out, pilot=False)
    assert all(a["made"] == 0 for a in log["generation_attempts"])
    assert log["label_calls"]["made"] == 0


def test_pilot_builds_dev_only_without_a_review_sample(tmp_path):
    folder = _folder(tmp_path)
    config = TaskBuildConfig.load(folder / "config.yaml")
    log = build_task_a(
        _runner(tmp_path, FakeModels()), config, DEFINITIONS, folder / "pilot", pilot=True
    )
    assert log["kept"] == {"dev": 5}
    assert not (folder / "review").exists()


def test_seeds_have_exact_safety_and_hard_case_counts():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seeds = draw_seeds("test", 700, config.task_a, DEFINITIONS, config.seed)
    assert sum(s.label.safety for s in seeds) == 70
    assert sum(s.kind == "two_products" for s in seeds) == 56
    for seed in seeds:
        assert seed.label.safety == (seed.label.fault in SAFETY_FAULTS)
        if seed.kind == "unknown_product":
            assert seed.label.product is None and seed.also_named
        if seed.label.fault is not None:
            assert seed.label.product is not None


def test_seeds_are_reproducible_and_differ_by_split():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    first = draw_seeds("dev", 50, config.task_a, DEFINITIONS, config.seed)
    again = draw_seeds("dev", 50, config.task_a, DEFINITIONS, config.seed)
    other = draw_seeds("test", 50, config.task_a, DEFINITIONS, config.seed)
    assert first == again
    assert [s.label for s in first] != [s.label for s in other]


def test_full_plan_draws_overgenerated_seeds_per_split():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seeds = plan_seeds(config, DEFINITIONS, pilot=False)
    assert len(seeds) == sum(seed_count(n, 0.15) for n in (3200, 200, 600)) == 4600
    assert len({s.id for s in seeds}) == len(seeds)


def test_kinds_never_exceed_the_count():
    kinds = kinds_for(10, DEFINITIONS, random.Random(1))
    assert len(kinds) == 10


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("not json", "not valid JSON"),
        ("[1]", "not a JSON object"),
        ('{"message": ""}', 'no "message" string'),
    ],
)
def test_bad_generator_replies_are_sent_back(text, problem):
    seed = draw_seeds(
        "dev", 1, TaskBuildConfig.load(SOURCE / "config.yaml").task_a, DEFINITIONS, 1
    )[0]
    assert problem in check_message(seed, text, DEFINITIONS)


def test_message_checks_catch_leaked_labels_and_wrong_products():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seed = next(
        s
        for s in draw_seeds("dev", 200, config.task_a, DEFINITIONS, config.seed)
        if s.kind == "plain" and s.label.product == "Brio kettle"
    )
    words = " ".join(["fine"] * seed.length[0])
    ok = f"My Brio kettle {words}"
    assert check_message(seed, json.dumps({"message": ok}), DEFINITIONS) is None
    leak = json.dumps({"message": f"{ok} warranty_claim"})
    assert "internal labels" in check_message(seed, leak, DEFINITIONS)
    wrong = json.dumps({"message": f"My Tessa dishwasher {words}"})
    assert "must name: Brio kettle" in check_message(seed, wrong, DEFINITIONS)
    extra = json.dumps({"message": f"{ok} and my Tessa"})
    assert "must not name: Tessa dishwasher" in check_message(seed, extra, DEFINITIONS)
    long = json.dumps({"message": "My Brio kettle " + "word " * 400})
    assert "words; write" in check_message(seed, long, DEFINITIONS)


def test_product_mentions_match_whole_first_words():
    assert product_mentions("the brio is broken", DEFINITIONS.products) == {"Brio kettle"}
    assert product_mentions("a valentine card", DEFINITIONS.products) == set()


def test_parse_helpers():
    assert parse_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert message_of('{"message": " hi "}') == "hi"
    label = parse_label(
        '{"route": "other", "safety": false, "product": null, "fault": null}', DEFINITIONS
    )
    assert label.route == "other"
    with pytest.raises(ReplyError):
        parse_label(
            '{"route": "nowhere", "safety": false, "product": null, "fault": null}', DEFINITIONS
        )


def test_near_duplicates_are_found_above_the_threshold():
    index = NearDuplicateIndex({"t1": "my kettle will not switch on at all", "t2": "zzz"})
    found = near_duplicates(
        {"a": "my kettle will not switch on at all!", "b": "where is my order"}, index, 0.8
    )
    assert list(found) == ["a"]
    assert jaccard(shingles("abc"), shingles("abc")) == 1.0
    assert jaccard(frozenset(), frozenset()) == 1.0


def test_estimate_counts_both_stages_and_prices_them():
    config = TaskBuildConfig.load(SOURCE / "config.yaml")
    seeds = plan_seeds(config, DEFINITIONS, pilot=True)
    prices = PricesFile.model_validate(
        {
            "prices": {
                "google": {"gemini-3.1-flash-lite": {"input": 0.25, "output": 1.5}},
                "anthropic": {"claude-haiku-5-5": {"input": 0.1, "output": 0.5}},
            }
        }
    )
    costs = estimate_task_a(config, DEFINITIONS, seeds, prices)
    assert [c.stage for c in costs] == ["generate", "label"]
    assert costs[1].calls == len(seeds)
    assert all(c.expected_cost is not None for c in costs)
    assert "Total, expected:" in format_estimate(costs, "USD", "Task A")
    unpriced = estimate_task_a(config, DEFINITIONS, seeds, None)
    assert "price is missing" in format_estimate(unpriced, "USD", "Task A")


def test_config_refuses_a_labeller_from_the_generator_provider():
    raw = yaml.safe_load((SOURCE / "config.yaml").read_text(encoding="utf-8"))
    raw["labeller"]["provider"] = "google"
    with pytest.raises(ValueError, match="different provider"):
        TaskBuildConfig.model_validate(raw)


def test_cli_estimate_makes_no_call(tmp_path):
    folder = _folder(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "adapt",
            "build-tasks",
            "--estimate",
            "--folder",
            str(folder),
            "--prices-path",
            "none.yaml",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "generate" in result.output and "label" in result.output


def test_cli_build_needs_a_budget(tmp_path):
    folder = _folder(tmp_path)
    result = CliRunner().invoke(
        app,
        ["adapt", "build-tasks", "--pilot", "--folder", str(folder), "--prices-path", "none.yaml"],
    )
    assert result.exit_code == 1
    assert "budget" in result.output


def _prices(tmp_path: Path, budget: float | None) -> Path:
    raw = {
        "prices": {
            "google": {"gemini-3.1-flash-lite": {"input": 0.25, "output": 1.5}},
            "anthropic": {"claude-haiku-5-5": {"input": 0.1, "output": 0.5}},
        },
        "budgets": {"s4-task-data": budget},
    }
    path = tmp_path / "prices.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


def _patch_providers(monkeypatch, missing: dict | None = None) -> None:
    from types import SimpleNamespace

    import lab.adapt.cli as adapt_cli

    provider = MockProvider(respond=FakeModels(), supported_reasoning=("minimal", "off"))
    available = SimpleNamespace(
        providers={"google": provider, "anthropic": provider}, missing_keys=missing or {}
    )
    monkeypatch.setattr(adapt_cli, "available_providers", lambda names: available)


def _pilot(tmp_path: Path, prices: Path) -> object:
    folder = tmp_path / "halvard-tasks"
    args = ["adapt", "build-tasks", "--pilot", "--folder", str(folder)]
    args += ["--prices-path", str(prices), "--cache-dir", str(tmp_path / "cache")]
    args += ["--env-file", str(tmp_path / "none.env")]
    return CliRunner().invoke(app, args)


def test_cli_pilot_build_writes_the_pilot_split(tmp_path, monkeypatch):
    _folder(tmp_path)
    _patch_providers(monkeypatch)
    result = _pilot(tmp_path, _prices(tmp_path, 1.0))
    assert result.exit_code == 0, result.output
    assert "Kept: {'dev': 5}" in result.output
    assert (tmp_path / "halvard-tasks" / "pilot" / "dev.jsonl").exists()


def test_cli_refuses_a_build_over_budget(tmp_path, monkeypatch):
    _folder(tmp_path)
    _patch_providers(monkeypatch)
    result = _pilot(tmp_path, _prices(tmp_path, 0.000001))
    assert result.exit_code == 1
    assert "over the s4-task-data budget" in result.output


def test_cli_refuses_a_build_without_keys(tmp_path, monkeypatch):
    _folder(tmp_path)
    _patch_providers(monkeypatch, missing={"anthropic": ["ANTHROPIC_API_KEY"]})
    result = _pilot(tmp_path, _prices(tmp_path, 1.0))
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output
