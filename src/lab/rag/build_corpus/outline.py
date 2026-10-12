"""Document outlines: every section the model writes, and the sentences it must contain.

A policy is laid out as
    # Title / intro / ## General terms / ### ... / ## <product> / ### ... /
    ## <plan> / ### ... / ## <region> / ### ...
A staff document has one ## <product> / ### <heading> section per product. A deleted notice is
one block of text with a title line. Code assembles the headings; the model writes only the
text under each lowest heading.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.allocate import Allocation
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.facts import Fact, FactPlan

GENERAL = "General terms"
SectionKind = Literal["intro", "policy", "internal", "deleted"]


class SectionPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    doc_id: str
    kind: SectionKind
    # Level-2 and level-3 headings above the text; empty for an intro or a notice.
    group: str | None = None
    heading: str | None = None
    entity: str | None = None
    # Text that must appear word for word, in this order.
    blocks: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    accessory: str | None = None


class DocumentPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    title: str
    family: Literal["policy", "internal", "article"]
    sections: tuple[SectionPlan, ...]


def block(fact: Fact, allocation: Allocation) -> str:
    """How a fact is written in its section."""
    form = allocation.form(fact.id)
    if form == "bare":
        return fact.bare
    if form == "two":
        return f"{fact.lead} {fact.bare}"
    return fact.named


def outline(config: CorpusConfig, plan: FactPlan, allocation: Allocation) -> list[DocumentPlan]:
    # Within a section: the postcode sentence first, then the config's attribute order.
    order = {a.id: n for n, a in enumerate(config.all_attributes())}
    facts = sorted(plan.facts, key=lambda f: (f.scope != "postcode", order.get(f.attribute, 0)))
    documents = [_policy(config, policy, facts, allocation) for policy in config.policies]
    documents += [_internal(config, doc, facts) for doc in config.internal]
    documents += [_deleted(fact) for fact in facts if fact.scope == "deleted"]
    return documents


def _section(
    doc_id: str,
    group: str,
    heading: str,
    entity: str | None,
    facts: list[Fact],
    allocation: Allocation,
    kind: SectionKind = "policy",
) -> SectionPlan:
    return SectionPlan(
        key=f"{doc_id}/{group}/{heading}",
        doc_id=doc_id,
        kind=kind,
        group=group,
        heading=heading,
        entity=entity,
        blocks=tuple(block(f, allocation) for f in facts),
        fact_ids=tuple(f.id for f in facts),
    )


def _matching(facts: list[Fact], doc_id: str, heading: str, entity: str | None) -> list[Fact]:
    """The facts of one section, in the order `facts` holds them."""
    return [f for f in facts if f.doc_id == doc_id and f.heading == heading and f.entity == entity]


def _policy(config, policy, facts: list[Fact], allocation: Allocation) -> DocumentPlan:
    doc_id = policy.doc_id
    sections = [SectionPlan(key=f"{doc_id}/intro", doc_id=doc_id, kind="intro")]
    for spec in policy.general:
        sections.append(
            _section(
                doc_id,
                GENERAL,
                spec.heading,
                None,
                _matching(facts, doc_id, spec.heading, None),
                allocation,
            )
        )
    for scope, entities in (
        ("product", config.products),
        ("plan", config.plans),
        ("region", tuple(config.regions)),
    ):
        for entity in entities:
            for spec in getattr(policy, scope):
                sections.append(
                    _section(
                        doc_id,
                        entity,
                        spec.heading,
                        entity,
                        _matching(facts, doc_id, spec.heading, entity),
                        allocation,
                    )
                )
    return DocumentPlan(
        doc_id=doc_id, title=policy.title, family="policy", sections=tuple(sections)
    )


def _internal(config, doc, facts: list[Fact]) -> DocumentPlan:
    sections = [
        SectionPlan(
            key=f"{doc.doc_id}/{entity}/{doc.heading}",
            doc_id=doc.doc_id,
            kind="internal",
            group=entity,
            heading=doc.heading,
            entity=entity,
            blocks=tuple(f.named for f in _matching(facts, doc.doc_id, doc.heading, entity)),
            fact_ids=tuple(f.id for f in _matching(facts, doc.doc_id, doc.heading, entity)),
        )
        for entity in config.products
    ]
    return DocumentPlan(
        doc_id=doc.doc_id, title=doc.title, family="internal", sections=tuple(sections)
    )


def _deleted(fact: Fact) -> DocumentPlan:
    section = SectionPlan(
        key=f"{fact.doc_id}/notice",
        doc_id=fact.doc_id,
        kind="deleted",
        entity=fact.entity,
        blocks=(fact.named,),
        fact_ids=(fact.id,),
        accessory=fact.accessory,
    )
    return DocumentPlan(doc_id=fact.doc_id, title="", family="article", sections=(section,))


def render_document(document: DocumentPlan, texts: dict[str, str]) -> str:
    """The document body: code's headings around the model's text for each section.

    A section with no text (a pilot builds only some) is left out with its heading.
    """
    if document.family == "article":
        return texts[document.sections[0].key].strip() + "\n"
    parts = [f"# {document.title}"]
    group = None
    for section in document.sections:
        if section.key not in texts:
            continue
        if section.group is not None and section.group != group:
            group = section.group
            parts.append(f"## {group}")
        if section.heading is not None:
            parts.append(f"### {section.heading}")
        parts.append(texts[section.key].strip())
    return "\n\n".join(parts) + "\n"
