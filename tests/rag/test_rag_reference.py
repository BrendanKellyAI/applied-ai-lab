import inspect
import re
from pathlib import Path

import pytest

from lab.providers.base import GenerationRequest
from lab.providers.capabilities import default_capabilities
from lab.rag import chunk, judge, prompt, score, search
from lab.rag.chunk import FixedChunker
from lab.rag.config import config_id, load_pipeline

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


def test_reference_is_the_last_one_recorded_in_the_history():
    import yaml

    history = yaml.safe_load((SEASON / "reference_history.yaml").read_text(encoding="utf-8"))
    pipeline = load_pipeline(REFERENCE)

    assert config_id(pipeline) == history[-1]["reference_after"]
    assert (pipeline.answer.model, pipeline.answer.reasoning) == ("gpt-6-luna", "off")
    assert (pipeline.judge.provider, pipeline.judge.model) == ("google", "gemini-3.6-flash")


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
