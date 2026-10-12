import inspect
import re
from pathlib import Path

import pytest

from lab.providers.base import GenerationRequest
from lab.providers.capabilities import default_capabilities
from lab.rag import chunk, judge, prompt, score, search
from lab.rag.chunk import FixedChunker
from lab.rag.config import load_pipeline

SEASON = Path(__file__).parents[2] / "season2"
REFERENCE = SEASON / "reference.yaml"
REFERENCE_E2 = SEASON / "reference-e2.yaml"
SLIDE_WIDTH = 64


def test_e2_reference_is_pinned_as_e2_ran_it():
    pipeline = load_pipeline(REFERENCE_E2)

    assert pipeline.chunk == FixedChunker(size=256, overlap=0)
    assert pipeline.search.method == "vector"
    assert pipeline.filter.mode == "passthrough"
    assert pipeline.prompt.k == 5
    assert (pipeline.answer.model, pipeline.answer.reasoning) == ("gpt-6.1-sol", "low")
    assert (pipeline.judge.model, pipeline.judge.reasoning) == ("claude-sonnet-5-5", "off")


def test_reference_differs_from_e2_only_in_its_cheaper_models():
    now, e2 = load_pipeline(REFERENCE), load_pipeline(REFERENCE_E2)

    assert now.model_copy(update={"answer": e2.answer, "judge": e2.judge}) == e2
    assert (now.answer.model, now.answer.reasoning) == ("gpt-6-luna", "off")
    assert (now.judge.provider, now.judge.model) == ("google", "gemini-3.1-flash-lite")


@pytest.mark.parametrize("path", [REFERENCE, REFERENCE_E2])
@pytest.mark.parametrize("stage", ["answer", "judge"])
def test_reference_models_pass_the_capability_check(stage, path):
    spec = getattr(load_pipeline(path), stage)
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
