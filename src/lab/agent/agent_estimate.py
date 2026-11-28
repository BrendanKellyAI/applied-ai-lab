"""Token estimates for an agent run, from a dry run on the mock provider (season5/token-method.md).

The oracle walks each case's expected path with the arm's real system prompt, tools and tool
results, and every request is counted as it would be sent (`o200k_base` for text, OpenAI's
patch rule for images). Agents wander, so each case gets extra turns (half its path again,
before a pilot), each the size of its last request. Output is 120 tokens a turn before a pilot.
The ceiling is every case running to its input token cap.
"""

import json
import math
import statistics
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from lab.agent.caller import ModelCaller
from lab.agent.config import AgentExperiment, Arm, caps_for
from lab.agent.kb import REPO, KeywordKB
from lab.agent.loop import run_case
from lab.agent.mock_agent import oracle
from lab.agent.run import LoadedCase
from lab.cache import ResponseCache
from lab.providers.base import GenerationRequest, GenerationResult
from lab.providers.mock import MockProvider
from lab.rag.estimate import chat_tokens

EXTRA_TURN_SHARE = 0.5
OUTPUT_PER_TURN = 120
IMAGE_PATCH = 32
IMAGE_FACTOR = 1.2
HIGH_DETAIL_PATCHES = 2500


def image_tokens(path: Path) -> int:
    with Image.open(path) as image:
        width, height = image.size
    patches = min(
        math.ceil(width / IMAGE_PATCH) * math.ceil(height / IMAGE_PATCH), HIGH_DETAIL_PATCHES
    )
    return math.ceil(patches * IMAGE_FACTOR)


def request_tokens(request: GenerationRequest) -> int:
    text = [request.system or ""]
    text += [json.dumps(t.model_dump(), sort_keys=True) for t in request.tools or ()]
    images = 0
    for turn in request.turns():
        text.append(turn.text)
        text += [c.arguments_json + c.name for c in turn.tool_calls]
        images += sum(image_tokens(REPO / image.path) for image in turn.images)
    return chat_tokens("\n".join(text)) + images + 4 * len(request.turns())


class CountingMock(MockProvider):
    """The oracle, reporting real token counts for each request it is sent."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        result = super().generate(request)
        return result.model_copy(
            update={"input_tokens": request_tokens(request), "output_tokens": OUTPUT_PER_TURN}
        )


@dataclass(frozen=True)
class ArmEstimate:
    arm: str
    cases: int
    calls: int
    input_tokens: int
    output_tokens: int
    median_case_input: int
    p90_case_input: int
    max_case_input: int
    ceiling_input: int

    def lines(self) -> list[str]:
        return [
            f"{self.arm}: {self.cases} case runs, about {self.calls:,} model calls",
            f"  input {self.input_tokens:,}, output {self.output_tokens:,}",
            f"  input a case: median {self.median_case_input:,}, 90th percentile "
            f"{self.p90_case_input:,}, largest {self.max_case_input:,}",
            f"  ceiling (every case at its input cap): {self.ceiling_input:,}",
        ]


def estimate_arm(experiment: AgentExperiment, arm: Arm, cases: Sequence[LoadedCase]) -> ArmEstimate:
    facts = {c.facts.case_id: c.facts for c in cases}
    dry = arm.model_copy(update={"model": arm.model.model_copy(update={"provider": "mock"})})
    with tempfile.TemporaryDirectory() as folder:
        caller = ModelCaller(
            {"mock": CountingMock(respond=oracle(facts))}, ResponseCache(Path(folder))
        )
        per_case, calls = [], 0
        for case in cases:
            run = run_case(case.facts, case.message, dry, caller, KeywordKB())
            extra = math.ceil(len(run.turns) * EXTRA_TURN_SHARE)
            total = sum(t.input_tokens for t in run.turns) + extra * run.turns[-1].input_tokens
            per_case.append(total)
            calls += len(run.turns) + extra
    repeats = experiment.repeats
    ordered = sorted(per_case)
    return ArmEstimate(
        arm=arm.name,
        cases=len(cases) * repeats,
        calls=calls * repeats,
        input_tokens=sum(per_case) * repeats,
        output_tokens=calls * OUTPUT_PER_TURN * repeats,
        median_case_input=int(statistics.median(ordered)),
        p90_case_input=ordered[int(0.9 * (len(ordered) - 1))],
        max_case_input=ordered[-1],
        ceiling_input=sum(caps_for(arm, c.facts.kind).max_input_tokens for c in cases) * repeats,
    )
