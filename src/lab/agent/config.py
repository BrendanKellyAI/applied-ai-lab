"""An agent experiment's config: which cases, and one block per arm. Read from YAML."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from lab.agent.tool_specs import DescriptionStyle
from lab.providers.base import ProviderName, ReasoningLevel

# Every tool except the code tool, which arrives with the sandbox in E10.
NON_CODE_TOOLS = (
    "lookup_order",
    "check_warranty",
    "search_knowledge_base",
    "read_past_cases",
    "book_service_visit",
    "issue_refund",
    "ask_customer",
    "request_approval",
    "close_case",
)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ModelSettings(_Frozen):
    provider: ProviderName
    model: str
    reasoning: ReasoningLevel | None = "off"
    max_output_tokens: int = Field(default=1500, gt=0)


class Caps(_Frozen):
    """Enforced by the loop; a case that hits one is unresolved, with the cap named."""

    max_turns: int = Field(default=16, gt=0)
    max_tool_calls: int = Field(default=24, gt=0)
    max_input_tokens: int = Field(default=150_000, gt=0)


LONG_CAPS = Caps(max_turns=40, max_tool_calls=60, max_input_tokens=600_000)


class Harness(_Frozen):
    refund_limit: bool = False
    idempotency: bool = False
    least_privilege: bool = False


class Arm(_Frozen):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    model: ModelSettings
    instructions: str = "baseline"
    tools: tuple[str, ...] = NON_CODE_TOOLS
    descriptions: DescriptionStyle = "clear"
    strict_schemas: bool = False
    # E3: an error is returned to the model, or ends the run as a crash.
    errors: Literal["returned", "raised"] = "returned"
    harness: Harness = Harness()
    images: Literal["attach", "none"] = "attach"
    knowledge_base: Literal["reference", "keyword"] = "reference"
    caps: Caps | None = None


class AgentExperiment(_Frozen):
    experiment: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str = ""
    # Case files in datasets/halvard-cases/cases, without the .jsonl suffix.
    cases: tuple[str, ...] = ("dev",)
    case_ids: tuple[str, ...] = ()
    repeats: int = Field(default=1, ge=1)
    concurrency: int = Field(default=4, ge=1, le=16)
    requests_per_minute: int = Field(default=120, ge=1)
    arms: tuple[Arm, ...] = Field(min_length=1)


def load_experiment(path: Path) -> AgentExperiment:
    return AgentExperiment.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def caps_for(arm: Arm, kind: str) -> Caps:
    if arm.caps is not None:
        return arm.caps
    return LONG_CAPS if kind == "long" else Caps()
