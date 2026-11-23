"""The `lab adapt` harness end to end on the frozen task data, with offline stand-in models."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from typer.testing import CliRunner

from lab.adapt.analyse import analyse, write_analysis
from lab.adapt.definitions import Definitions, Label
from lab.adapt.estimate import estimate_experiment
from lab.adapt.examples import fixed_examples, similar_examples
from lab.adapt.experiment import Examples, Experiment
from lab.adapt.items import triage_items
from lab.adapt.output import first_object, output_format, parse_triage, triage_schema
from lab.adapt.prompts import (
    TRIAGE_SHORT,
    UNSURE_RULE,
    reply_system,
    triage_system,
)
from lab.adapt.requests import arm_requests, examples_for, load_inputs
from lab.adapt.run import predictions_path, read_jsonl, run_experiment, write_jsonl
from lab.adapt.score_a import macro_f1, score_item
from lab.adapt.score_b import style_outcome
from lab.cache import ResponseCache
from lab.cli import app
from lab.providers.mock import MockProvider
from lab.runner import Runner, RunnerSettings

ROOT = Path(__file__).parents[2]
DATA = ROOT / "datasets" / "halvard-tasks"
DEFINITIONS = Definitions.load(DATA / "routes.yaml")
DEV = triage_items(DATA, "dev")
ANSWER = {"provider": "openai", "model": "gpt-6-luna", "reasoning": "off", "max_output_tokens": 200}
JUDGE = {"provider": "google", "model": "gemini-3.6-flash", "reasoning": "minimal",
         "max_output_tokens": 300}  # fmt: skip


def _config(tmp_path: Path, task: str, arms: list[dict], **extra) -> Path:
    folder = tmp_path / "episode"
    folder.mkdir(exist_ok=True)
    raw = {
        "episode": f"s4-test-{task}",
        "task": task,
        "split": "dev",
        "limit": 12,
        "data": str(DATA),
        "answer": ANSWER,
        "reference": arms[0]["name"],
        "arms": arms,
        **extra,
    }
    path = folder / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


class Triage:
    """Answers with the true label, except for the "definitions" level and above, where it
    is wrong on every third item; replies to the one-line arm come wrapped in prose."""

    def __init__(self) -> None:
        self.labels = {item.message: item.label for item in triage_items(DATA, "dev")}
        self.calls = 0

    def __call__(self, request) -> str:
        self.calls += 1
        message = request.prompt.removeprefix("Customer message:\n")
        label = self.labels[message].model_dump()
        if "Definitions:" not in (request.system or ""):
            return f"Here you are: {json.dumps(label)}"
        if self.calls % 3 == 0:
            label = {**label, "route": "other"}
        return json.dumps(label)


def _runner(tmp_path: Path, respond) -> Runner:
    provider = MockProvider(respond=respond, supported_reasoning=("off", "minimal"))
    return Runner(
        providers={"openai": provider, "google": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )


# Output contract


def test_parse_finds_the_object_in_prose_and_rejects_bad_values():
    label = DEV[0].label.model_dump()
    assert parse_triage(f"Sure. {json.dumps(label)} Done.", DEFINITIONS).valid
    assert parse_triage("```json\n" + json.dumps(label) + "\n```", DEFINITIONS).valid
    assert parse_triage(None, DEFINITIONS).problem == "no reply"
    assert parse_triage("no json here", DEFINITIONS).problem == "no JSON object"
    bad = parse_triage(json.dumps({**label, "route": "nowhere"}), DEFINITIONS)
    assert not bad.valid and bad.problem.startswith("invalid fields")
    assert first_object('[1] {bad {"a": 1}') == {"a": 1}
    assert first_object("[1, 2]") is None


def test_schema_is_strict_and_formats_follow_the_arm():
    schema = triage_schema(DEFINITIONS)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"route", "safety", "product", "fault"}
    assert None in schema["properties"]["product"]["enum"]
    assert output_format("text", DEFINITIONS) is None
    assert output_format("json_mode", DEFINITIONS).kind == "json_mode"
    assert output_format("schema", DEFINITIONS).json_schema == schema


# Prompts and examples


def test_each_instruction_level_adds_to_the_one_before():
    levels = ["one_line", "definitions", "policy", "unsure"]
    prompts = [triage_system(level, DEFINITIONS) for level in levels]
    for before, after in zip(prompts, prompts[1:], strict=False):
        assert after.startswith(before)
    assert UNSURE_RULE in prompts[-1] and UNSURE_RULE not in prompts[-2]
    assert triage_system("short", DEFINITIONS) == TRIAGE_SHORT
    guide = "GUIDE"
    assert guide in reply_system("style_guide", guide)
    assert guide not in reply_system("one_line", guide)


def test_random_examples_are_fixed_and_shuffling_reorders_them():
    train = list(range(100))
    chosen = fixed_examples(Examples(n=8, seed=3), train)
    assert chosen == fixed_examples(Examples(n=8, seed=3), train)
    shuffled = fixed_examples(Examples(n=8, seed=3, shuffle_seed=1), train)
    assert sorted(shuffled) == sorted(chosen) and shuffled != chosen
    assert fixed_examples(Examples(n=0), train) == []
    with pytest.raises(ValueError, match="examples from"):
        fixed_examples(Examples(n=5), [1, 2])


def test_similar_examples_put_the_nearest_last():
    vectors = {"a": [1, 0], "b": [0.9, 0.1], "c": [0, 1], "q": [1, 0.05]}

    def embed(texts):
        return np.array([vectors[t] for t in texts], dtype=float)

    chosen = similar_examples(Examples(n=2, selection="similar"), ["q"], "abc", "abc", embed)
    assert chosen == [["b", "a"]]
    none = similar_examples(Examples(n=0, selection="similar"), ["q"], "abc", "abc", embed)
    assert none == [[]]
    with pytest.raises(ValueError, match="examples from"):
        similar_examples(Examples(n=9, selection="similar"), ["q"], "abc", "abc", embed)


def test_similar_arm_needs_an_embedder(tmp_path):
    arm = {"name": "near", "instructions": "unsure", "examples": {"n": 2, "selection": "similar"}}
    experiment = Experiment.load(_config(tmp_path, "a", [arm]))
    inputs = load_inputs(experiment)
    with pytest.raises(ValueError, match="needs embeddings"):
        examples_for(experiment.arm("near"), inputs, None)
    blocks = examples_for(experiment.arm("near"), inputs, lambda texts: np.ones((len(texts), 3)))
    assert len(blocks) == 12 and blocks[0].startswith("Examples:")


# Config


@pytest.mark.parametrize(
    ("arms", "extra", "error"),
    [
        ([{"name": "a", "instructions": "x"}], {}, "instructions must be one of"),
        ([{"name": "a"}], {}, "give instructions or predictions"),
        ([{"name": "a", "instructions": "short"}] * 2, {}, "unique"),
        ([{"name": "a", "instructions": "short"}], {"reference": "b"}, "not an arm"),
    ],
)
def test_bad_configs_are_refused(tmp_path, arms, extra, error):
    with pytest.raises(ValueError, match=error):
        Experiment.load(_config(tmp_path, "a", arms, **extra))


def test_task_b_needs_a_judge_and_plain_text(tmp_path):
    with pytest.raises(ValueError, match="needs a judge"):
        Experiment.load(_config(tmp_path, "b", [{"name": "a", "instructions": "one_line"}]))
    arms = [{"name": "a", "instructions": "one_line", "output": "schema"}]
    with pytest.raises(ValueError, match="plain text"):
        Experiment.load(_config(tmp_path, "b", arms, judge=JUDGE))


# Requests, run and analysis


def test_requests_carry_the_format_and_examples(tmp_path):
    arms = [
        {"name": "plain", "instructions": "one_line"},
        {"name": "schema", "instructions": "unsure", "output": "schema", "examples": {"n": 2}},
    ]
    experiment = Experiment.load(_config(tmp_path, "a", arms))
    inputs = load_inputs(experiment)
    plain = arm_requests(experiment, experiment.arm("plain"), inputs)
    schema = arm_requests(experiment, experiment.arm("schema"), inputs)
    assert len(plain) == 12 and all(r.output_format is None for r in plain.values())
    first = next(iter(schema.values()))
    assert first.output_format.kind == "schema" and "Examples:" in first.system
    assert len({r.system for r in schema.values()}) == 1


@pytest.fixture
def task_a(tmp_path):
    external = tmp_path / "episode" / "tuned.jsonl"
    labels = {i.id: i.label.model_dump() for i in DEV[:12]}
    write_jsonl(external, [{"id": k, "text": json.dumps(v)} for k, v in list(labels.items())[:6]])
    arms = [
        {"name": "one-line", "instructions": "one_line"},
        {"name": "definitions", "instructions": "definitions"},
        {"name": "tuned", "predictions": "tuned.jsonl"},
    ]
    experiment = Experiment.load(_config(tmp_path, "a", arms))
    inputs = load_inputs(experiment)
    fake = Triage()
    summaries = run_experiment(_runner(tmp_path, fake), experiment, inputs)
    return experiment, inputs, summaries, fake


def test_run_writes_predictions_and_a_rerun_sends_nothing(task_a, tmp_path):
    experiment, inputs, summaries, fake = task_a
    assert set(summaries) == {"answer-one-line", "answer-definitions"}
    rows = read_jsonl(predictions_path(experiment, "one-line"))
    assert len(rows) == 12 and rows[0]["input_tokens"] is not None
    calls = fake.calls
    run_experiment(_runner(tmp_path, fake), experiment, inputs)
    assert fake.calls == calls


def test_analysis_scores_compares_and_charts(task_a):
    experiment, inputs, _, _ = task_a
    result = analyse(experiment, inputs, None)
    arms = result["arms"]
    assert arms["one-line"]["fully_right"]["count"] == 12
    assert arms["definitions"]["fully_right"]["count"] == 8
    assert arms["tuned"]["fully_right"]["count"] == 6
    assert arms["tuned"]["json_valid"]["count"] == 6
    compared = result["comparisons"]["definitions"]
    assert compared["right_to_wrong"] == 4 and compared["wrong_to_right"] == 0
    assert compared["p_holm"] >= compared["p_value"]
    assert result["cost_ratios"]["tuned"] == {"per_item": None, "per_primary_hit": None}
    path = write_analysis(experiment, result)
    assert json.loads(path.read_text(encoding="utf-8"))["primary_metric"] == "fully_right"
    assert list((experiment.results / "charts").glob("*-slide.svg"))


def test_cost_ratios_use_prices_without_publishing_them(task_a):
    experiment, inputs, _, _ = task_a
    prices = SimpleNamespace(
        price_for=lambda provider, model: SimpleNamespace(input=0.1, output=0.5)
    )
    ratios = analyse(experiment, inputs, prices)["cost_ratios"]
    assert ratios["one-line"] == {"per_item": 1.0, "per_primary_hit": 1.0}
    assert ratios["definitions"]["per_item"] > 1


def test_scores_count_a_missing_reply_as_wrong_everywhere():
    item = next(i for i in DEV if i.label.safety)
    score = score_item(item, None, DEFINITIONS)
    assert not score.valid and not score.fully_right and score.safety_item and not score.flagged
    assert not any(score.fields.values())
    assert macro_f1([item], [score], DEFINITIONS.routes) == 0.0
    assert macro_f1([], [], DEFINITIONS.routes) == 0.0


def test_estimate_counts_every_prompted_arm(tmp_path):
    arms = [
        {"name": "one-line", "instructions": "one_line"},
        {"name": "near", "instructions": "unsure", "examples": {"n": 4, "selection": "similar"}},
        {"name": "tuned", "predictions": "tuned.jsonl"},
    ]
    experiment = Experiment.load(_config(tmp_path, "a", arms))
    costs = estimate_experiment(experiment, load_inputs(experiment), None)
    assert [c.stage for c in costs] == ["answer one-line", "answer near"]
    assert costs[1].input_tokens > costs[0].input_tokens


# Task B


class Replies:
    """Writes the target reply for the style guide arm and a bare answer otherwise; the judge
    keeps facts and prefers whichever reply is the target."""

    def __init__(self) -> None:
        from lab.adapt.items import reply_items

        self.items = reply_items(DATA, "dev")

    def __call__(self, request) -> str:
        if request.system and request.system.startswith("You compare"):
            first = request.prompt.split("Reply 1:\n")[1].split("\n\nReply 2:")[0]
            better = "1" if first.startswith("Thank you") else "2"
            return json.dumps({"better": better})
        if "all_facts_kept" in request.prompt:
            return json.dumps({"all_facts_kept": True, "facts_added": []})
        item = next(i for i in self.items if f"Customer question: {i.question}\n" in request.prompt)
        if "house style guide" in (request.system or ""):
            return item.target_reply
        return item.answer


def test_task_b_run_and_analysis(tmp_path):
    arms = [
        {"name": "one-line", "instructions": "one_line"},
        {"name": "style-guide", "instructions": "style_guide"},
    ]
    experiment = Experiment.load(_config(tmp_path, "b", arms, judge=JUDGE))
    inputs = load_inputs(experiment)
    summaries = run_experiment(_runner(tmp_path, Replies()), experiment, inputs)
    assert "style-style-guide" in summaries and "style-one-line" not in summaries
    result = analyse(experiment, inputs, None)
    styled = result["arms"]["style-guide"]
    assert styled["primary"]["count"] == 12
    assert styled["style_against_reference"]["win"]["count"] == 12
    assert result["arms"]["one-line"]["primary"]["count"] == 0
    costs = estimate_experiment(experiment, inputs, None)
    assert [c.stage for c in costs][-2:] == ["facts judge", "style judge"]


@pytest.mark.parametrize(
    ("first", "second", "outcome"),
    [
        ('{"better": "1"}', '{"better": "2"}', "win"),
        ('{"better": "2"}', '{"better": "1"}', "loss"),
        ('{"better": "1"}', '{"better": "1"}', "tie"),
        ('{"better": "tie"}', None, "tie"),
        ("not json", '{"better": "2"}', "tie"),
    ],
)
def test_style_needs_both_orders_to_agree(first, second, outcome):
    assert style_outcome(first, second) == outcome


# CLI


def test_cli_run_estimate_analyse_and_score(tmp_path, monkeypatch):
    import lab.adapt.cli_run as cli_run

    arms = [{"name": "one-line", "instructions": "one_line"}]
    config = _config(tmp_path, "a", arms)
    runner = CliRunner()
    prices = tmp_path / "prices.yaml"
    prices.write_text(
        yaml.safe_dump(
            {
                "prices": {"openai": {"gpt-6-luna": {"input": 0.1, "output": 0.5}}},
                "budgets": {"s4-test-a": 1.0},
            }
        ),
        encoding="utf-8",
    )
    estimate = runner.invoke(app, ["adapt", "run", str(config), "--estimate"])
    assert estimate.exit_code == 0 and "answer one-line" in estimate.output
    no_budget = runner.invoke(app, ["adapt", "run", str(config), "--prices-path", "none.yaml"])
    assert no_budget.exit_code == 1 and "budget" in no_budget.output

    provider = MockProvider(respond=Triage(), supported_reasoning=("off",))
    available = SimpleNamespace(providers={"openai": provider}, missing_keys={})
    monkeypatch.setattr(cli_run, "available_providers", lambda names: available)
    args = ["adapt", "run", str(config), "--prices-path", str(prices)]
    args += ["--cache-dir", str(tmp_path / "cache"), "--env-file", str(tmp_path / "none")]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "made 12" in result.output

    analysed = runner.invoke(app, ["adapt", "analyse", str(config), "--no-charts"])
    assert analysed.exit_code == 0 and "12 of 12" in analysed.output

    predictions = tmp_path / "mine.jsonl"
    rows = [{"id": i.id, "prediction": i.label.model_dump()} for i in DEV[:5]]
    rows.append({"id": DEV[5].id, "text": "no idea"})
    write_jsonl(predictions, rows)
    base = ["adapt", "score", str(predictions), "--split", "dev", "--data", str(DATA)]
    scored = runner.invoke(app, base)
    assert scored.exit_code == 0, scored.output
    assert json.loads(scored.output)["fully_right"]["count"] == 5
    assert runner.invoke(app, [*base[:3], "--split", "train"]).exit_code == 1
    write_jsonl(predictions, [{"id": "nope", "text": "{}"}])
    assert runner.invoke(app, base).exit_code == 1


def test_cli_run_stops_when_over_budget_or_a_key_is_missing(tmp_path, monkeypatch):
    import lab.adapt.cli_run as cli_run

    config = _config(tmp_path, "a", [{"name": "one-line", "instructions": "one_line"}])
    prices = tmp_path / "prices.yaml"
    prices.write_text(
        yaml.safe_dump(
            {
                "prices": {"openai": {"gpt-6-luna": {"input": 1000, "output": 1000}}},
                "budgets": {"s4-test-a": 0.01},
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    over = runner.invoke(app, ["adapt", "run", str(config), "--prices-path", str(prices)])
    assert over.exit_code == 1 and "over the" in over.output
    prices.write_text(
        yaml.safe_dump(
            {
                "prices": {"openai": {"gpt-6-luna": {"input": 0.1, "output": 0.5}}},
                "budgets": {"s4-test-a": 1.0},
            }
        ),
        encoding="utf-8",
    )
    missing = SimpleNamespace(providers={}, missing_keys={"openai": ["OPENAI_API_KEY"]})
    monkeypatch.setattr(cli_run, "available_providers", lambda names: missing)
    args = ["adapt", "run", str(config), "--prices-path", str(prices)]
    args += ["--env-file", str(tmp_path / "none")]
    result = runner.invoke(app, args)
    assert result.exit_code == 1 and "OPENAI_API_KEY" in result.output


def test_label_round_trips_through_the_prompt_json():
    from lab.adapt.prompts import label_json

    label = Label(route="other", safety=False, product=None, fault=None)
    assert parse_triage(label_json(label), DEFINITIONS).label == label
