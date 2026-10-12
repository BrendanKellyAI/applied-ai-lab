"""The Halvard corpus config: company structure, fact families, prompts and item counts."""

from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from lab.config import ConfigError
from lab.rag.config import ModelSpec

Scope = Literal["general", "product", "plan", "region"]


class Attribute(BaseModel):
    """A family of facts: one per entity in its scope, all written from the same templates."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: str
    range: tuple[int, int]
    named: str
    bare: str | None = None
    lead: str | None = None
    twin: str | None = None

    @model_validator(mode="after")
    def _templates(self) -> "Attribute":
        for name in ("named", "bare"):
            template = getattr(self, name)
            if template is not None and template.count("{value}") != 1:
                raise ValueError(f"{self.id}: {name} needs exactly one {{value}}")
        if self.lead is not None and "{value}" in self.lead:
            raise ValueError(f"{self.id}: lead must not hold the value")
        if self.range[0] > self.range[1]:
            raise ValueError(f"{self.id}: range is backwards")
        return self


class SectionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    attributes: tuple[Attribute, ...]
    postcodes: str | None = None


class PolicySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    title: str
    general: tuple[SectionSpec, ...]
    product: tuple[SectionSpec, ...]
    plan: tuple[SectionSpec, ...]
    region: tuple[SectionSpec, ...]


class InternalSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    title: str
    heading: str
    attributes: tuple[Attribute, ...]


class DeletedSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sentence: str
    accessories: tuple[str, ...]


class CorpusConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_version: str
    seed: int
    company: str
    library_date: date
    current_from: date
    previous_from: date
    previous_to: date
    internal_from: date
    generation: ModelSpec
    checker: ModelSpec
    max_attempts: int = Field(gt=0)
    section_tokens: tuple[int, int]
    section_words: str
    article_tokens: tuple[int, int]
    internal_section_tokens: tuple[int, int]
    pack_limit_tokens: int
    products: tuple[str, ...]
    plans: tuple[str, ...]
    regions: dict[str, tuple[str, ...]]
    kinds: dict[str, str]
    policies: tuple[PolicySpec, ...]
    internal: tuple[InternalSpec, ...]
    deleted: DeletedSpec
    absent_topics: tuple[str, ...]
    items: dict[str, tuple[int, int]]
    spare_fraction: float = Field(ge=0)
    pilot_per_type: int = Field(gt=0)
    stop_words: tuple[str, ...]
    prompts: dict[str, str]

    @model_validator(mode="after")
    def _consistent(self) -> "CorpusConfig":
        ids = [a.id for a in self.all_attributes()]
        repeated = sorted({i for i in ids if ids.count(i) > 1})
        if repeated:
            raise ValueError(f"attribute ids repeat: {repeated}")
        unknown_kinds = sorted({a.kind for a in self.all_attributes()} - set(self.kinds))
        if unknown_kinds:
            raise ValueError(f"unknown value kinds: {unknown_kinds}")
        known = set(ids)
        twins = {a.id: a.twin for a in self.all_attributes() if a.twin}
        for attr, twin in twins.items():
            if twin not in known or twins.get(twin) != attr:
                raise ValueError(f"{attr}: twin {twin} must exist and point back")
        areas = [area for areas in self.regions.values() for area in areas]
        if len(areas) != len(set(areas)):
            raise ValueError("a postcode area belongs to more than one region")
        return self

    def all_attributes(self) -> list[Attribute]:
        found = [
            attr
            for policy in self.policies
            for scope in ("general", "product", "plan", "region")
            for section in getattr(policy, scope)
            for attr in section.attributes
        ]
        return found + [attr for doc in self.internal for attr in doc.attributes]

    def prompt(self, name: str, **values: Any) -> str:
        return fill(self.prompts[name], **values)


def fill(template: str, **values: Any) -> str:
    """Replace each {name} given, leaving every other brace alone (prompts show JSON)."""
    for name, value in values.items():
        token = "{" + name + "}"
        if token not in template:
            raise KeyError(f"template has no {token}")
        template = template.replace(token, str(value))
    return template


def load_corpus_config(path: Path) -> CorpusConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return CorpusConfig.model_validate(raw)
    except FileNotFoundError as exc:
        raise ConfigError(f"Corpus config not found: {path}") from exc
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"{path} is not a valid corpus config:\n{exc}") from exc
