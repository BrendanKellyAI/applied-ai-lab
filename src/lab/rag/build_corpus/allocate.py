"""Which facts each test and dev item asks about, and how each fact is written.

Made in code from the seed. A fact is the evidence for at most one item. A fact's form follows
from its item: heading-dependent items need the bare sentence, two-sentence items the lead and
bare pair, and everything else the named sentence. Siblings of a distractor item keep the named
form, so they look alike.
"""

import math
import random
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.facts import Fact, FactPlan, HeldOut

Form = Literal["named", "bare", "two"]
Split = Literal["test", "dev"]

# Item id prefixes, by type.
CODES = {
    "policy_single": "POL-SINGLE",
    "policy_two_sentence": "POL-TWO",
    "policy_heading": "POL-HEAD",
    "distractor": "DISTRACT",
    "two_part": "TWOPART",
    "bridge": "BRIDGE",
    "followup": "FOLLOW",
    "version": "VERSION",
    "restricted": "RESTRICT",
    "absent_detail": "ABSENT",
    "absent_topic": "TOPIC",
    "deleted": "DELETED",
}
# Types the checker may reject: spares are drawn, and the first that pass are kept.
CHECKED = {"restricted", "absent_detail", "absent_topic", "deleted"}
DISTRACTOR_SIBLINGS = 3


class ItemPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    split: Split
    spare: bool = False
    # Evidence facts, in the order the question asks for them.
    facts: tuple[str, ...] = ()
    # Follow-ups: the fact the first turn asked about.
    first: str | None = None
    distractors: tuple[str, ...] = ()
    area: str | None = None
    topic: str | None = None
    held_out: HeldOut | None = None


class Allocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[ItemPlan, ...]
    forms: dict[str, Form]

    def form(self, fact_id: str) -> Form:
        return self.forms.get(fact_id, "named")


def wanted(config: CorpusConfig, item_type: str, split: Split) -> int:
    """How many items to draw: the target, plus spares for types the checker may reject."""
    test, dev = config.items[item_type]
    target = test if split == "test" else dev
    if item_type in CHECKED:
        return target + math.ceil(target * config.spare_fraction)
    return target


def counts_needed(config: CorpusConfig) -> dict[str, int]:
    """Facts the plan must provide for each pool, test and dev together."""
    both = {t: wanted(config, t, "test") + wanted(config, t, "dev") for t in config.items}
    return {
        "held_out": both["absent_detail"],
        "version": both["version"],
        "deleted": both["deleted"],
    }


class _Allocator:
    def __init__(self, config: CorpusConfig, plan: FactPlan, rng: random.Random) -> None:
        self.config = config
        self.facts = plan.by_id()
        self.held_out = list(plan.held_out)
        self.rng = rng
        self.used: set[str] = set()
        self.forms: dict[str, Form] = {}
        self.locked: set[str] = set()
        self.items: list[ItemPlan] = []

    def pool(self, *, scopes: Iterable[str], where=lambda f: True) -> list[Fact]:
        scopes = set(scopes)
        found = [
            f
            for f in self.facts.values()
            if f.scope in scopes and f.id not in self.used and where(f)
        ]
        found.sort(key=lambda f: f.id)
        self.rng.shuffle(found)
        return found

    def take(self, candidates: list[Fact], n: int, item_type: str) -> list[Fact]:
        if len(candidates) < n:
            raise ValueError(f"{item_type}: needs {n} facts, only {len(candidates)} free")
        chosen = candidates[:n]
        self.used.update(f.id for f in chosen)
        return chosen

    def add(self, item_type: str, split: Split, index: int, **fields) -> None:
        prefix = "DEV-" if split == "dev" else ""
        target = self.config.items[item_type][0 if split == "test" else 1]
        self.items.append(
            ItemPlan(
                id=f"{prefix}{CODES[item_type]}-{index:03d}",
                type=item_type,
                split=split,
                spare=index >= target,
                **fields,
            )
        )

    def each(self, item_type: str):
        for split in ("test", "dev"):
            for index in range(wanted(self.config, item_type, split)):
                yield split, index


def allocate(config: CorpusConfig, plan: FactPlan, rng: random.Random) -> Allocation:
    a = _Allocator(config, plan, rng)
    _version(a)
    _distractor(a)
    _followup(a)
    _shaped(a, "policy_heading", "bare")
    _shaped(a, "policy_two_sentence", "two")
    # Bridges need region facts outside the servicing policy, so they draw before the
    # types that can take any fact.
    _bridge(a)
    _single(a)
    _two_part(a)
    _restricted(a)
    _absent(a)
    _deleted(a)
    return Allocation(items=tuple(a.items), forms=a.forms)


def _first(candidates: list[Fact], item_type: str) -> Fact:
    if not candidates:
        raise ValueError(f"{item_type}: no free fact left")
    return candidates[0]


def _version(a: _Allocator) -> None:
    candidates = a.pool(scopes={"product"}, where=lambda f: f.old_value is not None)
    for split, index in a.each("version"):
        (fact,) = a.take(candidates, 1, "version")
        candidates.remove(fact)
        a.add("version", split, index, facts=(fact.id,))


def _siblings(a: _Allocator, fact: Fact) -> list[str]:
    others = sorted(
        f.id for f in a.facts.values() if f.attribute == fact.attribute and f.entity != fact.entity
    )
    return a.rng.sample(others, min(DISTRACTOR_SIBLINGS, len(others)))


def _distractor(a: _Allocator) -> None:
    candidates = a.pool(scopes={"product"}, where=lambda f: f.twin is not None)
    for split, index in a.each("distractor"):
        (fact,) = a.take(candidates, 1, "distractor")
        candidates.remove(fact)
        distractors = (*_siblings(a, fact), fact.twin)
        a.locked.update(distractors)
        a.add("distractor", split, index, facts=(fact.id,), distractors=distractors)


def _followup(a: _Allocator) -> None:
    for split, index in a.each("followup"):
        target = _first(a.pool(scopes={"product"}), "followup")
        firsts = sorted(
            f.id
            for f in a.facts.values()
            if f.attribute == target.attribute and f.entity != target.entity
        )
        a.used.add(target.id)
        a.add("followup", split, index, facts=(target.id,), first=a.rng.choice(firsts))


def _shaped(a: _Allocator, item_type: str, form: Form) -> None:
    candidates = a.pool(scopes={"product"}, where=lambda f: f.id not in a.locked)
    for split, index in a.each(item_type):
        (fact,) = a.take(candidates, 1, item_type)
        candidates.remove(fact)
        a.forms[fact.id] = form
        a.add(item_type, split, index, facts=(fact.id,))


def _single(a: _Allocator) -> None:
    candidates = a.pool(scopes={"general", "product", "plan", "region"})
    for split, index in a.each("policy_single"):
        (fact,) = a.take(candidates, 1, "policy_single")
        candidates.remove(fact)
        a.add("policy_single", split, index, facts=(fact.id,))


def _two_part(a: _Allocator) -> None:
    for split, index in a.each("two_part"):
        candidates = a.pool(scopes={"general", "product", "plan", "region"})
        first = _first(candidates, "two_part")
        second = _first([f for f in candidates if f.doc_id != first.doc_id], "two_part")
        a.used.update((first.id, second.id))
        a.add("two_part", split, index, facts=(first.id, second.id))


def _bridge(a: _Allocator) -> None:
    for split, index in a.each("bridge"):
        fact = _first(a.pool(scopes={"region"}, where=lambda f: f.doc_id != "POL-SER"), "bridge")
        a.used.add(fact.id)
        area = a.rng.choice(a.config.regions[fact.entity])
        postcode = f"postcodes:{fact.entity}"
        a.add("bridge", split, index, facts=(postcode, fact.id), area=area)


def _restricted(a: _Allocator) -> None:
    candidates = a.pool(scopes={"internal"})
    for split, index in a.each("restricted"):
        (fact,) = a.take(candidates, 1, "restricted")
        candidates.remove(fact)
        a.add("restricted", split, index, facts=(fact.id,))


def _absent(a: _Allocator) -> None:
    held = list(a.held_out)
    a.rng.shuffle(held)
    for split, index in a.each("absent_detail"):
        a.add("absent_detail", split, index, held_out=held.pop())
    topics = list(a.config.absent_topics)
    a.rng.shuffle(topics)
    for split, index in a.each("absent_topic"):
        if not topics:
            raise ValueError("absent_topic: not enough topics in the config")
        a.add("absent_topic", split, index, topic=topics.pop())


def _deleted(a: _Allocator) -> None:
    candidates = a.pool(scopes={"deleted"})
    for split, index in a.each("deleted"):
        (fact,) = a.take(candidates, 1, "deleted")
        candidates.remove(fact)
        a.add("deleted", split, index, facts=(fact.id,))
