"""Facts: every planted sentence in the library, with its value, made in code from the seed.

One fact per attribute per entity in the attribute's scope, except the held-out pairs that
absent-detail questions ask about. Version facts also get an old value for the superseded
policy. Values are drawn smallest range first, so narrow ranges are never starved.
"""

import random
from collections.abc import Iterable, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.catalogue import Attribute, CorpusConfig, fill
from lab.rag.build_corpus.values import ValuePool

FactScope = Literal["general", "product", "plan", "region", "internal", "deleted", "postcode"]


class Fact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    attribute: str
    doc_id: str
    scope: FactScope
    heading: str
    entity: str | None
    kind: str
    value: str
    named: str
    bare: str | None = None
    lead: str | None = None
    twin: str | None = None
    old_value: str | None = None
    # Deleted articles only: the accessory the notice is about.
    accessory: str | None = None

    def blank(self) -> str:
        """The bare sentence (or the named one) with the value replaced by a gap."""
        return (self.bare or self.named).replace(self.value, "...")


class HeldOut(BaseModel):
    """An attribute deliberately not stated for one product: the gap an absent-detail asks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    attribute: str
    doc_id: str
    heading: str
    entity: str
    blank: str


class FactPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    facts: tuple[Fact, ...]
    held_out: tuple[HeldOut, ...]

    def by_id(self) -> dict[str, Fact]:
        return {fact.id: fact for fact in self.facts}


def fact_id(attribute: str, entity: str | None) -> str:
    return attribute if entity is None else f"{attribute}:{entity}"


def plan_facts(
    config: CorpusConfig,
    rng: random.Random,
    existing_texts: Iterable[str],
    *,
    held_out_count: int,
    version_count: int,
    deleted_count: int,
) -> FactPlan:
    pool = ValuePool(config.kinds, rng, existing_texts)
    slots = list(_slots(config))
    held = _choose_held_out(config, rng, held_out_count)
    held_keys = {(h.attribute, h.entity) for h in held}
    slots = [s for s in slots if (s[0].id, s[3]) not in held_keys]
    # Smallest range first, so a narrow range is filled before wide ones use its values.
    slots.sort(key=lambda s: (s[0].range[1] - s[0].range[0], s[0].id, s[3] or ""))
    facts = {}
    for attribute, doc_id, scope, entity, heading in slots:
        value = pool.draw(attribute.kind, *attribute.range)
        facts[fact_id(attribute.id, entity)] = _fact(
            attribute, doc_id, scope, heading, entity, value
        )
    facts = _with_twins(facts)
    facts = _with_old_values(facts, pool, config, rng, version_count)
    facts.update(_deleted(config, pool, rng, deleted_count))
    facts.update(_postcodes(config))
    return FactPlan(facts=tuple(facts.values()), held_out=tuple(held))


def _slots(config: CorpusConfig):
    for policy in config.policies:
        for section in policy.general:
            for attr in section.attributes:
                yield attr, policy.doc_id, "general", None, section.heading
        for scope, entities in (
            ("product", config.products),
            ("plan", config.plans),
            ("region", tuple(config.regions)),
        ):
            for section in getattr(policy, scope):
                for attr in section.attributes:
                    for entity in entities:
                        yield attr, policy.doc_id, scope, entity, section.heading
    for doc in config.internal:
        for attr in doc.attributes:
            for entity in config.products:
                yield attr, doc.doc_id, "internal", entity, doc.heading


def _fact(
    attribute: Attribute,
    doc_id: str,
    scope: FactScope,
    heading: str,
    entity: str | None,
    value: str,
) -> Fact:
    def render(template: str | None) -> str | None:
        if template is None:
            return None
        values = {"value": value} if "{value}" in template else {}
        if "{entity}" in template:
            values["entity"] = entity
        return fill(template, **values)

    return Fact(
        id=fact_id(attribute.id, entity),
        attribute=attribute.id,
        doc_id=doc_id,
        scope=scope,
        heading=heading,
        entity=entity,
        kind=attribute.kind,
        value=value,
        named=render(attribute.named),
        bare=render(attribute.bare),
        lead=render(attribute.lead),
        twin=attribute.twin,
    )


def _with_twins(facts: dict[str, Fact]) -> dict[str, Fact]:
    """Point each twin attribute at the twin fact for the same entity, where it exists."""
    linked = {}
    for key, fact in facts.items():
        twin = fact_id(fact.twin, fact.entity) if fact.twin else None
        linked[key] = fact.model_copy(update={"twin": twin if twin in facts else None})
    return linked


def _with_old_values(
    facts: dict[str, Fact],
    pool: ValuePool,
    config: CorpusConfig,
    rng: random.Random,
    count: int,
) -> dict[str, Fact]:
    """Give `count` product facts in the policies an old value for the superseded version."""
    candidates = sorted(k for k, f in facts.items() if f.scope == "product")
    attributes = {a.id: a for a in config.all_attributes()}
    chosen = rng.sample(candidates, count)
    updated = dict(facts)
    for key in sorted(chosen, key=lambda k: _width(attributes[facts[k].attribute])):
        attribute = attributes[facts[key].attribute]
        updated[key] = facts[key].model_copy(
            update={"old_value": pool.draw(attribute.kind, *attribute.range)}
        )
    return updated


def _width(attribute: Attribute) -> int:
    return attribute.range[1] - attribute.range[0]


HELD_OUT_PER_ATTRIBUTE = 3


def _choose_held_out(config: CorpusConfig, rng: random.Random, count: int) -> list[HeldOut]:
    """(attribute, product) pairs left unstated, at most three products per attribute, so
    every attribute keeps most of its siblings."""
    pairs = [
        (attr, policy.doc_id, section.heading, entity)
        for policy in config.policies
        for section in policy.product
        for attr in section.attributes
        for entity in config.products
    ]
    rng.shuffle(pairs)
    per_attribute: dict[str, int] = {}
    held = []
    for attr, doc_id, heading, entity in pairs:
        if len(held) == count:
            break
        if per_attribute.get(attr.id, 0) == HELD_OUT_PER_ATTRIBUTE:
            continue
        per_attribute[attr.id] = per_attribute.get(attr.id, 0) + 1
        blank = fill(attr.named, entity=entity, value="...")
        held.append(
            HeldOut(attribute=attr.id, doc_id=doc_id, heading=heading, entity=entity, blank=blank)
        )
    if len(held) < count:
        raise ValueError(f"Only {len(held)} held-out pairs are possible; {count} asked for")
    return held


def _deleted(
    config: CorpusConfig, pool: ValuePool, rng: random.Random, count: int
) -> dict[str, Fact]:
    facts = {}
    for n in range(count):
        entity = rng.choice(config.products)
        accessory = rng.choice(config.deleted.accessories)
        value = pool.draw("batch", 1000, 9999)
        sentence = fill(config.deleted.sentence, accessory=accessory, value=value, entity=entity)
        doc_id = f"DEL-{n:02d}"
        facts[doc_id] = Fact(
            id=doc_id,
            attribute="deleted",
            doc_id=doc_id,
            scope="deleted",
            heading="",
            entity=entity,
            kind="batch",
            value=value,
            named=sentence,
            accessory=accessory,
        )
    return facts


def _postcodes(config: CorpusConfig) -> dict[str, Fact]:
    template = next(s.postcodes for p in config.policies for s in p.region if s.postcodes)
    doc_id = next(p.doc_id for p in config.policies for s in p.region if s.postcodes)
    heading = next(s.heading for p in config.policies for s in p.region if s.postcodes)
    facts = {}
    for region, areas in config.regions.items():
        listed = ", ".join(areas[:-1]) + " and " + areas[-1] if len(areas) > 1 else areas[0]
        key = fact_id("postcodes", region)
        facts[key] = Fact(
            id=key,
            attribute="postcodes",
            doc_id=doc_id,
            scope="postcode",
            heading=heading,
            entity=region,
            kind="postcode",
            value=listed,
            named=fill(template, entity=region, areas=listed),
        )
    return facts


def facts_in(facts: Sequence[Fact], doc_id: str) -> list[Fact]:
    return [fact for fact in facts if fact.doc_id == doc_id]
