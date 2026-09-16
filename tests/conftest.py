from collections.abc import Callable

import pytest

from lab.plan import PlannedCall, make_call_id
from lab.providers.base import GenerationRequest

CallFactory = Callable[..., PlannedCall]


def build_call(
    model: str = "mock-a",
    mode: str = "standard",
    reasoning: str | None = "off",
    prompt: str | None = None,
    **cell: str | int | float | bool,
) -> PlannedCall:
    cell = cell or {"item": 0}
    request = GenerationRequest(
        provider="mock",
        model=model,
        prompt=prompt or f"{model} {mode} {sorted(cell.items())}",
        max_output_tokens=50,
        temperature=0.0,
        reasoning=reasoning,
        metadata={"experiment": "test"},
    )
    return PlannedCall(
        call_id=make_call_id(model_label=model, mode=mode, cell=cell),
        model_label=model,
        mode=mode,
        cell=cell,
        request=request,
    )


@pytest.fixture
def make_call() -> CallFactory:
    return build_call
