"""Estimator checks against hand calculations.

Token counts use one token per word, so every expected number below can be worked out by hand.
"""

import pytest

from lab.cache import ResponseCache
from lab.config import ExperimentConfig
from lab.estimate import (
    BudgetError,
    build_report,
    check_budget,
    estimate_run,
    format_report,
)
from lab.plan import PlannedCall, build_request, make_call_id
from lab.prices import ModelPrice, PricesFile
from lab.providers.mock import MockProvider
from lab.raw_log import RunRecord


def words(text: str) -> int:
    return len(text.split())


def _config(**overrides) -> ExperimentConfig:
    base = {
        "experiment": "demo",
        "seed": 1,
        "models": [
            {
                "provider": "mock",
                "model": "mock-a",
                "modes": {
                    "lowest": {"reasoning": "off", "temperature": None, "max_output_tokens": 50},
                    "high": {"reasoning": "high", "temperature": None, "max_output_tokens": 1000},
                },
            }
        ],
        "pilot": {"strategy": "filter", "include": [{"item": 0}]},
    }
    return ExperimentConfig.model_validate({**base, **overrides})


def _calls(config: ExperimentConfig, items: int = 4) -> list[PlannedCall]:
    """Prompts of exactly 10 words, with a 2-word system prompt: 12 input tokens per call."""
    model = config.models[0]
    return [
        PlannedCall(
            call_id=make_call_id(model_label=model.display_label, mode=mode, cell={"item": item}),
            model_label=model.display_label,
            mode=mode,
            cell={"item": item},
            request=build_request(
                model,
                mode,
                system="Be brief.",
                prompt=f"item {item} one two three four five six seven eight",
            ),
        )
        for mode in model.modes
        for item in range(items)
    ]


PRICES = PricesFile(
    currency="USD",
    prices={"mock": {"mock-a": ModelPrice(input=2.0, cached_input=0.2, output=10.0)}},
    budgets={"demo": 1.0},
)


def _record(call: PlannedCall, output_tokens: int) -> RunRecord:
    result = (
        MockProvider().generate(call.request).model_copy(update={"output_tokens": output_tokens})
    )
    return RunRecord.for_call(call, source="api", attempts=1, result=result)


def test_limit_based_estimate_matches_hand_calculation(tmp_path):
    calls = _calls(_config())

    run = estimate_run(
        "full run",
        calls,
        cache=ResponseCache(tmp_path),
        prior_records=[],
        prices=PRICES,
        count_tokens=words,
    )

    lowest, high = sorted(run.groups, key=lambda g: g.mode, reverse=True)
    # 4 calls x 12 tokens = 48 input tokens; high end allows 30% tokeniser variation: 62.4 -> 63
    assert (lowest.mode, lowest.calls, lowest.uncached_calls) == ("lowest", 4, 4)
    assert (lowest.input_tokens.low, lowest.input_tokens.high) == (48, 63)
    # Output bounded by the limit: 4 x 50 = 200
    assert (lowest.output_tokens.low, lowest.output_tokens.high) == (200, 200)
    assert lowest.output_basis == "output limit (upper bound)"
    # Cost: 48 x $2/M + 200 x $10/M = 0.000096 + 0.002 = 0.002096; high 63 x 2/M + 0.002 = 0.002126
    assert lowest.cost.low == pytest.approx(0.002096)
    assert lowest.cost.high == pytest.approx(0.002126)
    # High mode: 4 x 1000 = 4000 output tokens -> $0.04 plus input
    assert high.output_tokens.high == 4000
    assert run.cost.high == pytest.approx(0.002126 + 0.000126 + 0.04)


def test_pilot_usage_replaces_limit_once_enough_samples_exist(tmp_path):
    calls = _calls(_config(), items=10)
    high_calls = [c for c in calls if c.mode == "high"]
    # Pilot usage for the high mode: 100, 200, 300, 400 tokens. Mean 250; 90th percentile 400.
    prior = [
        _record(c, tokens) for c, tokens in zip(high_calls, (100, 200, 300, 400), strict=False)
    ]

    run = estimate_run(
        "full run",
        calls,
        cache=ResponseCache(tmp_path),
        prior_records=prior,
        prices=PRICES,
        count_tokens=words,
    )

    high = next(g for g in run.groups if g.mode == "high")
    # The 4 pilot calls are complete, so 6 remain: low 6 x 250 = 1500, high 6 x 400 = 2400
    assert (high.calls, high.done_calls, high.uncached_calls) == (10, 4, 6)
    assert (high.output_tokens.low, high.output_tokens.high) == (1500, 2400)
    assert high.output_basis == "pilot usage (n=4)"
    lowest = next(g for g in run.groups if g.mode == "lowest")
    assert lowest.output_basis == "output limit (upper bound)"


def test_cached_calls_cost_nothing(tmp_path):
    calls = _calls(_config())
    cache = ResponseCache(tmp_path)
    for call in calls[:3]:
        cache.put(call.request, MockProvider().generate(call.request))

    run = estimate_run(
        "full run", calls, cache=cache, prior_records=[], prices=PRICES, count_tokens=words
    )

    lowest = next(g for g in run.groups if g.mode == "lowest")
    assert (lowest.done_calls, lowest.uncached_calls) == (3, 1)
    assert lowest.input_tokens.low == 12
    assert run.done_calls == 3


def test_missing_price_gives_tokens_without_cost(tmp_path):
    run = estimate_run(
        "full run",
        _calls(_config()),
        cache=ResponseCache(tmp_path),
        prior_records=[],
        prices=None,
        count_tokens=words,
    )

    assert all(group.cost is None for group in run.groups)
    assert run.cost is None
    assert run.missing_prices == ("mock mock-a",)


def test_report_separates_pilot_from_full_run(tmp_path):
    config = _config()

    report = build_report(
        config,
        _calls(config),
        cache=ResponseCache(tmp_path),
        prior_records=[],
        prices=PRICES,
        count_tokens=words,
    )

    assert report.pilot.calls == 2
    assert report.full.calls == 8
    assert report.budget == 1.0
    text = format_report(report)
    for expected in ("Pilot: 2 calls", "Full run: 8 calls", "output limit (upper bound)", "$0.04"):
        assert expected in text
    assert "Budget: $1.00" in text


def test_batch_note_depends_on_whether_latency_is_measured(tmp_path):
    def note(config: ExperimentConfig) -> str:
        report = build_report(
            config,
            _calls(config),
            cache=ResponseCache(tmp_path),
            prior_records=[],
            prices=PRICES,
            count_tokens=words,
        )
        return report.batch_note

    assert "measures latency" in note(_config())
    no_latency = note(_config(measures_latency=False))
    assert "50%" in no_latency
    assert "24 hours" in no_latency


def test_budget_check_uses_high_end_of_estimate(tmp_path):
    run = estimate_run(
        "full run",
        _calls(_config()),
        cache=ResponseCache(tmp_path),
        prior_records=[],
        prices=PRICES,
        count_tokens=words,
    )

    check_budget(run, budget=1.0)
    check_budget(run, budget=None)
    with pytest.raises(BudgetError, match="exceeds the budget"):
        check_budget(run, budget=0.01)


def test_budget_cannot_be_checked_without_prices(tmp_path):
    run = estimate_run(
        "full run",
        _calls(_config()),
        cache=ResponseCache(tmp_path),
        prior_records=[],
        prices=None,
        count_tokens=words,
    )

    with pytest.raises(BudgetError, match="mock mock-a"):
        check_budget(run, budget=1.0)


def test_nothing_left_to_run_passes_any_budget(tmp_path):
    calls = _calls(_config())
    cache = ResponseCache(tmp_path)
    for call in calls:
        cache.put(call.request, MockProvider().generate(call.request))

    run = estimate_run(
        "full run", calls, cache=cache, prior_records=[], prices=None, count_tokens=words
    )

    assert run.uncached_calls == 0
    check_budget(run, budget=0.0)
