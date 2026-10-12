"""Pipeline and episode configuration.

`season2/reference.yaml` is the reference system: one block per stage. An episode's
config.yaml names that file as its base and lists conditions, each overriding stage blocks.
The loader refuses a condition that changes more than one stage unless it says why, so "each
episode changes exactly one stage" is enforced, not only intended.
"""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from lab.config import ConfigError, ProviderLimits
from lab.providers.base import ProviderName, ReasoningLevel
from lab.rag.chunk import FixedChunker, StructureChunker, WholeChunker
from lab.rag.filter import FilterConfig
from lab.rag.prompt import PromptConfig
from lab.rag.rerank import RerankConfig
from lab.rag.rewrite import RewriteConfig
from lab.rag.search import SearchConfig

# The blocks of a pipeline config, in stage order, and the stage number of each.
STAGES: dict[str, int] = {
    "chunk": 2,
    "embed": 3,
    "rewrite": 4,
    "search": 5,
    "filter": 6,
    "rerank": 7,
    "prompt": 8,
    "answer": 9,
    "cite": 10,
    "judge": 11,
}

ChunkConfig = Annotated[FixedChunker | StructureChunker | WholeChunker, Field(discriminator="kind")]


class ModelSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: ProviderName
    model: str = Field(min_length=1)
    reasoning: ReasoningLevel | None
    max_output_tokens: int = Field(gt=0)

    @field_validator("reasoning", mode="before")
    @classmethod
    def _restore_off(cls, value: Any) -> Any:
        # YAML 1.1 reads a bare `off` as false.
        return "off" if value is False else value


class EmbedConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str = "text-embedding-3-small"


class CiteConfig(BaseModel):
    """Stage 10. `parse` maps the answer's [Pn] markers to chunk ids, in the analysis; it makes
    no call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["passthrough", "parse"] = "passthrough"


class PassthroughStage(BaseModel):
    """A stage that is not switched on yet. Its options arrive with the episode that tests it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["passthrough"] = "passthrough"


class PipelineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk: ChunkConfig
    embed: EmbedConfig
    rewrite: RewriteConfig
    search: SearchConfig
    filter: FilterConfig
    rerank: RerankConfig
    prompt: PromptConfig
    answer: ModelSpec
    cite: CiteConfig
    judge: ModelSpec


def config_id(pipeline: PipelineConfig) -> str:
    """A short hash of every setting, written into every result and log line."""
    canonical = json.dumps(pipeline.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


class Condition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    changes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    # `search` stops after the prompt is built: it costs only embeddings.
    measure: Literal["search", "full"] = "full"
    changes_more_than_one_stage: str | None = None


class EpisodeConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str = ""
    base: str
    library: str
    items: Literal["test", "dev", "both"] = "test"
    conditions: list[Condition] = Field(min_length=1)
    limits: dict[ProviderName, ProviderLimits] = Field(default_factory=dict)
    pilot_per_type: int = Field(default=2, gt=0)
    # The episode's pre-registered pass marks, applied by its claims.py.
    pass_marks: dict[str, Any] = Field(default_factory=dict)

    @field_validator("conditions")
    @classmethod
    def _names_unique(cls, conditions: list[Condition]) -> list[Condition]:
        names = [c.name for c in conditions]
        if len(names) != len(set(names)):
            raise ValueError("condition names must be unique")
        return conditions


class ResolvedCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    measure: Literal["search", "full"]
    pipeline: PipelineConfig
    changed: tuple[str, ...]


class Episode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    config: EpisodeConfig
    folder: Path
    library: Path
    base: PipelineConfig
    base_id: str
    conditions: tuple[ResolvedCondition, ...]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    return raw


def load_pipeline(path: Path) -> PipelineConfig:
    try:
        return PipelineConfig.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(f"{path} is not a valid pipeline config:\n{exc}") from exc


def load_episode(path: Path) -> Episode:
    try:
        config = EpisodeConfig.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(f"{path} is not a valid episode config:\n{exc}") from exc
    folder = path.parent
    base = load_pipeline((folder / config.base).resolve())
    return Episode(
        config=config,
        folder=folder,
        library=(folder / config.library).resolve(),
        base=base,
        base_id=config_id(base),
        conditions=tuple(_resolve(base, condition) for condition in config.conditions),
    )


def _resolve(base: PipelineConfig, condition: Condition) -> ResolvedCondition:
    unknown = sorted(set(condition.changes) - set(STAGES))
    if unknown:
        raise ConfigError(f"Condition {condition.name} changes unknown stages: {unknown}")
    blocks = base.model_dump(mode="json")
    for stage, change in condition.changes.items():
        replaces_kind = "kind" in change and change["kind"] != blocks[stage].get("kind")
        blocks[stage] = dict(change) if replaces_kind else {**blocks[stage], **change}
    try:
        pipeline = PipelineConfig.model_validate(blocks)
    except ValidationError as exc:
        raise ConfigError(f"Condition {condition.name} is not valid:\n{exc}") from exc
    changed = tuple(s for s in STAGES if getattr(pipeline, s) != getattr(base, s))
    if len(changed) > 1 and not condition.changes_more_than_one_stage:
        raise ConfigError(
            f"Condition {condition.name} changes {len(changed)} stages "
            f"({', '.join(changed)}). An episode changes one stage; set "
            "changes_more_than_one_stage with the reason if this one must change more."
        )
    return ResolvedCondition(
        name=condition.name, measure=condition.measure, pipeline=pipeline, changed=changed
    )
