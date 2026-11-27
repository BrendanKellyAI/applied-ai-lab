"""Gate 2 estimate: tokens for writing every case message and checking every label.

Input tokens are counted from the real prompts with `o200k_base` (Claude counts run about 30%
higher; the label check line is scaled up for that). Outputs are given at an expected size and
at the hard ceiling of each call's output limit. A share of cases is allowed to need a second
message and a second check, as in Season 4.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from lab.agent.build import load_facts
from lab.agent.case_model import CaseFacts
from lab.agent.message_prompts import (
    GENERATOR_SYSTEM,
    LABELLER_SYSTEM,
    generation_prompt,
    labeller_prompt,
    word_band,
)
from lab.prices import PricesFile
from lab.rag.estimate import chat_tokens

GENERATOR = ("google", "gemini-3.1-flash-lite")
LABELLER = ("anthropic", "claude-haiku-5-5")
RETRY_SHARE = 0.3
TOKENS_PER_WORD = 1.4
WRAPPER_TOKENS = 15
CLAUDE_FACTOR = 1.3
OUTCOME_TOKENS = 40
GENERATOR_MAX_OUTPUT = {"long": 900, "other": 500}
LABELLER_MAX_OUTPUT = {"long": 1500, "other": 600}


@dataclass(frozen=True)
class Stage:
    stage: str
    provider: str
    model: str
    calls: int
    input_tokens: int
    expected_output: int
    ceiling_output: int

    def cost(self, prices: PricesFile | None, output: int) -> float | None:
        price = prices.price_for(self.provider, self.model) if prices else None
        if price is None or price.input is None or price.output is None:
            return None
        return (self.input_tokens * price.input + output * price.output) / 1_000_000


def _message_tokens(facts: CaseFacts) -> int:
    low, high = word_band(facts)
    return round((low + high) / 2 * TOKENS_PER_WORD) + WRAPPER_TOKENS


def _limit(table: dict[str, int], facts: CaseFacts) -> int:
    return table["long" if facts.kind == "long" else "other"]


def estimate(cases: Sequence[CaseFacts]) -> list[Stage]:
    retry = 1 + RETRY_SHARE
    gen_in = sum(chat_tokens(GENERATOR_SYSTEM) + chat_tokens(generation_prompt(c)) for c in cases)
    gen_out = sum(_message_tokens(c) for c in cases)
    placeholder = "word " * 100
    label_in = sum(
        chat_tokens(LABELLER_SYSTEM)
        + chat_tokens(labeller_prompt(c, placeholder.strip()))
        + _message_tokens(c)
        - chat_tokens(placeholder)
        for c in cases
    )
    label_out = sum(20 + OUTCOME_TOKENS * len(c.appliances) for c in cases)
    return [
        Stage(
            "messages",
            *GENERATOR,
            calls=round(len(cases) * retry),
            input_tokens=round(gen_in * retry),
            expected_output=round(gen_out * retry),
            ceiling_output=round(sum(_limit(GENERATOR_MAX_OUTPUT, c) for c in cases) * retry),
        ),
        Stage(
            "label check",
            *LABELLER,
            calls=round(len(cases) * retry),
            input_tokens=round(label_in * retry * CLAUDE_FACTOR),
            expected_output=round(label_out * retry * CLAUDE_FACTOR),
            ceiling_output=round(sum(_limit(LABELLER_MAX_OUTPUT, c) for c in cases) * retry),
        ),
    ]


def all_cases(cases_dir: Path) -> list[CaseFacts]:
    return [case for path in sorted(cases_dir.glob("*.facts.jsonl")) for case in load_facts(path)]


def format_estimate(stages: Sequence[Stage], prices: PricesFile | None) -> str:
    lines = ["Stage        Model                   Calls   Input    Output (expected / ceiling)"]
    for s in stages:
        lines.append(
            f"{s.stage:<12} {s.model:<23} {s.calls:>5} {s.input_tokens:>9,} "
            f"{s.expected_output:>9,} / {s.ceiling_output:,}"
        )
    expected = [s.cost(prices, s.expected_output) for s in stages]
    ceiling = [s.cost(prices, s.ceiling_output) for s in stages]
    if None not in expected and None not in ceiling:
        lines.append(f"Cost, expected {sum(expected):.2f}; ceiling {sum(ceiling):.2f}")  # type: ignore[arg-type]
    else:
        lines.append("Cost: a price is missing from prices.local.yaml")
    return "\n".join(lines)
