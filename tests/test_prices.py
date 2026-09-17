from datetime import date
from pathlib import Path

import pytest

from lab.config import ConfigError
from lab.prices import load_prices

PRICES = """
currency: USD
prices_checked: 2026-09-17
prices:
  openai:
    gpt-5.6-terra: { input: 2.00, cached_input: 0.20, output: 12.00 }
  google:
    gemini-3.6-flash: { input: , cached_input: , output: }
budgets:
  s1-e7-lost-in-the-middle: 20.00
  s1-e10-reasoning-vs-standard:
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "prices.local.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_prices_and_budgets(tmp_path):
    prices = load_prices(_write(tmp_path, PRICES))

    assert prices.currency == "USD"
    assert prices.prices_checked == date(2026, 9, 17)
    terra = prices.price_for("openai", "gpt-5.6-terra")
    assert (terra.input, terra.cached_input, terra.output) == (2.0, 0.2, 12.0)
    assert prices.budget_for("s1-e7-lost-in-the-middle") == 20.0


def test_blank_values_are_unknown_not_zero(tmp_path):
    prices = load_prices(_write(tmp_path, PRICES))

    gemini = prices.price_for("google", "gemini-3.6-flash")
    assert gemini.input is None
    assert gemini.is_complete is False
    assert prices.price_for("anthropic", "claude-sonnet-5") is None
    assert prices.budget_for("s1-e10-reasoning-vs-standard") is None
    assert prices.budget_for("unknown") is None


def test_missing_file_means_no_prices(tmp_path):
    assert load_prices(tmp_path / "prices.local.yaml") is None


@pytest.mark.parametrize(
    ("find", "replace", "message"),
    [
        ("input: 2.00", "input: -1", "input"),
        ("s1-e7-lost-in-the-middle: 20.00", "s1-e7-lost-in-the-middle: -5", "budgets"),
        ("currency: USD", "currency: USD\nsurprise: true", "surprise"),
    ],
)
def test_invalid_prices_raise_config_error(tmp_path, find, replace, message):
    with pytest.raises(ConfigError, match=message):
        load_prices(_write(tmp_path, PRICES.replace(find, replace)))


def test_example_file_in_repository_is_valid_and_has_no_prices():
    example = Path(__file__).parents[1] / "prices.example.yaml"

    prices = load_prices(example)

    for models in prices.prices.values():
        for price in models.values():
            assert (price.input, price.cached_input, price.output) == (None, None, None)
    assert all(budget is None for budget in prices.budgets.values())
