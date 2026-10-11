import inspect
import re
from pathlib import Path

import pytest

from lab.providers.base import GenerationRequest
from lab.providers.capabilities import default_capabilities
from lab.rag import chunk, judge, prompt, score, search
from lab.rag.chunk import FixedChunker
from lab.rag.config import load_pipeline

REFERENCE = Path(__file__).parents[2] / "season2" / "reference.yaml"
SLIDE_WIDTH = 64


def test_reference_is_the_e2_baseline():
    pipeline = load_pipeline(REFERENCE)

    assert pipeline.chunk == FixedChunker(size=256, overlap=0)
    assert pipeline.search.method == "vector"
    assert pipeline.filter.mode == "passthrough"
    assert pipeline.prompt.k == 5
    assert (pipeline.answer.model, pipeline.answer.reasoning) == ("gpt-6.1-sol", "low")
    assert (pipeline.judge.model, pipeline.judge.reasoning) == ("claude-sonnet-5-5", "off")


@pytest.mark.parametrize("stage", ["answer", "judge"])
def test_reference_models_pass_the_capability_check(stage):
    spec = getattr(load_pipeline(REFERENCE), stage)
    request = GenerationRequest(
        provider=spec.provider,
        model=spec.model,
        prompt="p",
        max_output_tokens=spec.max_output_tokens,
        reasoning=spec.reasoning,
    )

    default_capabilities().check(request)


def _slide_functions():
    for module in (chunk, judge, prompt, score, search):
        source = inspect.getsource(module)
        for name in re.findall(r"# slide: S2 E\d+\ndef (\w+)", source):
            yield f"{module.__name__}.{name}", getattr(module, name)


def test_there_are_slide_functions():
    assert len(list(_slide_functions())) >= 6


@pytest.mark.parametrize(("name", "function"), list(_slide_functions()))
def test_slide_functions_fit_a_slide(name, function):
    wide = [line for line in inspect.getsource(function).splitlines() if len(line) > SLIDE_WIDTH]

    assert wide == [], f"{name} has lines wider than {SLIDE_WIDTH} characters"
