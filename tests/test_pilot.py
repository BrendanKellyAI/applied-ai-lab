import itertools

import pytest

from lab.config import ExperimentConfig
from lab.pilot import select_calls
from lab.plan import PlanError, PlannedCall, make_call_id
from lab.providers.base import GenerationRequest

MODELS = [("openai", "gpt"), ("anthropic", "claude"), ("google", "gemini")]


def _config(pilot: dict, call_order: str = "planned") -> ExperimentConfig:
    mode = {"reasoning": "off", "temperature": 0, "max_output_tokens": 10}
    return ExperimentConfig.model_validate(
        {
            "experiment": "demo",
            "seed": 20260916,
            "models": [
                {"provider": provider, "model": model, "modes": {"standard": mode}}
                for provider, model in MODELS
            ],
            "pilot": pilot,
            "call_order": call_order,
        }
    )


def _call(provider: str, model: str, mode: str, cell: dict) -> PlannedCall:
    return PlannedCall(
        call_id=make_call_id(model_label=model, mode=mode, cell=cell),
        model_label=model,
        mode=mode,
        cell=cell,
        request=GenerationRequest(
            provider=provider, model=model, prompt=repr(cell), max_output_tokens=10
        ),
    )


def _lost_in_the_middle_grid() -> list[PlannedCall]:
    grid = itertools.product(MODELS, [4000, 16000, 64000], [0, 25, 50, 75, 100], range(6))
    return [
        _call(
            provider,
            model,
            "standard",
            {"context_length_tokens": length, "position_percent": position, "fact_index": fact},
        )
        for (provider, model), length, position, fact in grid
    ]


def _reasoning_grid() -> list[PlannedCall]:
    tasks = ["extraction", "arithmetic", "state", "puzzle"]
    grid = itertools.product(MODELS, ["off", "high"], tasks, range(30))
    return [
        _call(provider, model, mode, {"task": task, "item": item})
        for (provider, model), mode, task, item in grid
    ]


def test_full_run_returns_every_call_in_planned_order():
    calls = _reasoning_grid()

    assert select_calls(calls, _config({"strategy": "stratified"})) == calls


def test_stratified_pilot_covers_every_model_task_and_mode():
    calls = _reasoning_grid()
    config = _config({"strategy": "stratified", "fraction": 0.05, "strata": ["task", "mode"]})

    pilot = select_calls(calls, config, pilot=True)

    assert len(pilot) == 36
    covered = {(c.model_label, c.mode, c.cell["task"]) for c in pilot}
    assert len(covered) == 3 * 2 * 4


def test_stratified_pilot_is_deterministic():
    calls = _reasoning_grid()
    config = _config({"strategy": "stratified", "strata": ["task", "mode"]})

    first = select_calls(calls, config, pilot=True)
    second = select_calls(calls, config, pilot=True)

    assert [c.call_id for c in first] == [c.call_id for c in second]


def test_stratified_pilot_prefers_coverage_over_fraction():
    calls = _lost_in_the_middle_grid()
    config = _config(
        {
            "strategy": "stratified",
            "fraction": 0.01,
            "strata": ["context_length_tokens", "position_percent"],
        }
    )

    pilot = select_calls(calls, config, pilot=True)

    assert len(pilot) == 45


def test_stratified_pilot_rejects_unknown_stratum():
    config = _config({"strategy": "stratified", "strata": ["colour"]})

    with pytest.raises(PlanError, match="colour"):
        select_calls(_reasoning_grid(), config, pilot=True)


def test_filter_pilot_selects_union_of_rules():
    config = _config(
        {
            "strategy": "filter",
            "include": [
                {"context_length_tokens": 4000, "fact_index": 0},
                {"position_percent": 50, "fact_index": 0},
            ],
        }
    )

    pilot = select_calls(_lost_in_the_middle_grid(), config, pilot=True)

    assert len(pilot) == 21
    assert {c.model_label for c in pilot} == {"gpt", "claude", "gemini"}
    assert {c.cell["context_length_tokens"] for c in pilot} == {4000, 16000, 64000}
    assert {c.cell["position_percent"] for c in pilot} == {0, 25, 50, 75, 100}


def test_filter_pilot_matching_nothing_is_an_error():
    config = _config({"strategy": "filter", "include": [{"fact_index": 99}]})

    with pytest.raises(PlanError, match="no calls"):
        select_calls(_lost_in_the_middle_grid(), config, pilot=True)


def test_provider_filter_keeps_only_that_provider():
    calls = _reasoning_grid()
    config = _config({"strategy": "stratified", "strata": ["task", "mode"]})

    full_pilot = select_calls(calls, config, pilot=True)
    openai_pilot = select_calls(calls, config, pilot=True, provider="openai")

    assert openai_pilot == [c for c in full_pilot if c.request.provider == "openai"]


def test_unknown_provider_is_an_error():
    with pytest.raises(PlanError, match="mistral"):
        select_calls(_reasoning_grid(), _config({"strategy": "stratified"}), provider="mistral")


def test_shuffled_order_is_seeded_and_keeps_every_call():
    calls = _reasoning_grid()
    config = _config({"strategy": "stratified"}, call_order="shuffled")

    first = select_calls(calls, config)
    second = select_calls(calls, config)

    assert first == second
    assert first != calls
    assert sorted(c.call_id for c in first) == sorted(c.call_id for c in calls)


def test_duplicate_call_ids_are_rejected():
    calls = _reasoning_grid()

    with pytest.raises(PlanError, match="Duplicate"):
        select_calls([*calls, calls[0]], _config({"strategy": "stratified"}))


def test_cell_cannot_use_reserved_keys():
    with pytest.raises(ValueError, match="reserved"):
        _call("openai", "gpt", "standard", {"model": "sneaky"})
