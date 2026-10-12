"""Assembly: documents, spans and items from the plan and the generated text.

Superseded policies are made here, in code: the current text with each version fact's value
swapped for its old value, so the two versions differ only where the version questions look.
Every span is found by searching the final text for the exact block that was required, and
must be found exactly once.
"""

import random
from collections.abc import Mapping, Sequence
from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.allocate import Allocation, ItemPlan
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.facts import Fact, FactPlan
from lab.rag.build_corpus.outline import DocumentPlan, block, render_document
from lab.rag.build_corpus.v1 import V1, identifier_span, lookalikes
from lab.rag.corpus import Document, Item, Span, Turn


class AssemblyError(ValueError):
    """The generated text does not hold a required block exactly once."""


class Texts(BaseModel):
    """Everything the model wrote that the library needs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sections: dict[str, str]
    questions: dict[str, str]
    # Follow-up items: the first question, by item id.
    firsts: dict[str, str]
    # v1 paraphrase and shared items: the quoted sentence, by item id.
    quotes: dict[str, str]


def current_version(document: DocumentPlan) -> int:
    return 2 if document.family == "policy" else 1


def build_documents(
    config: CorpusConfig,
    plan: FactPlan,
    allocation: Allocation,
    outline: Sequence[DocumentPlan],
    texts: Texts,
    v1: V1,
) -> list[Document]:
    rng = random.Random(config.seed + 2)
    documents = [
        Document(
            doc_id=a.article_id,
            version=1,
            title=a.title,
            family="article",
            products=(a.product,),
            access="public",
            status="current",
            body=a.text,
        )
        for a in v1.articles
    ]
    facts = plan.by_id()
    for plan_doc in outline:
        if not any(s.key in texts.sections for s in plan_doc.sections):
            continue
        body = render_document(plan_doc, texts.sections)
        documents.extend(_versions(config, plan_doc, body, facts, rng, texts, allocation))
    return documents


def _versions(
    config, plan_doc: DocumentPlan, body: str, facts, rng, texts, allocation
) -> list[Document]:
    if plan_doc.family == "policy":
        old_body = body
        for section in plan_doc.sections:
            if section.key not in texts.sections:
                continue
            for fact_id in section.fact_ids:
                fact = facts[fact_id]
                if fact.old_value:
                    old_body = _swap(old_body, block(fact, allocation), fact)
        common = {"title": plan_doc.title, "family": "policy", "access": "public"}
        return [
            Document(
                doc_id=plan_doc.doc_id,
                version=2,
                status="current",
                effective_from=config.current_from,
                body=body,
                **common,
            ),
            Document(
                doc_id=plan_doc.doc_id,
                version=1,
                status="superseded",
                effective_from=config.previous_from,
                effective_to=config.previous_to,
                superseded_by=f"{plan_doc.doc_id}@2",
                body=old_body,
                **common,
            ),
        ]
    if plan_doc.family == "internal":
        return [
            Document(
                doc_id=plan_doc.doc_id,
                version=1,
                title=plan_doc.title,
                family="internal",
                access="staff",
                status="current",
                effective_from=config.internal_from,
                body=body,
            )
        ]
    section = plan_doc.sections[0]
    days = (config.library_date - config.current_from).days
    return [
        Document(
            doc_id=plan_doc.doc_id,
            version=1,
            title=body.split("\n", 1)[0].strip(),
            family="article",
            products=(section.entity,),
            access="public",
            status="deleted",
            deleted_on=config.current_from + timedelta(days=rng.randrange(days)),
            body=body,
        )
    ]


def _swap(body: str, sentence: str, fact: Fact) -> str:
    """Swap the value for the old one inside the fact's own sentence, which is in the document
    exactly once. A bare count of the value would also match "9 days" inside "19 days"."""
    if body.count(sentence) != 1:
        raise AssemblyError(f"{fact.id}: its sentence is not in its document exactly once")
    return body.replace(sentence, sentence.replace(fact.value, fact.old_value))


def find_span(document: Document, text: str, label: str) -> Span:
    count = document.body.count(text)
    if count != 1:
        raise AssemblyError(f"{label}: found {count} times in {document.key}, not once")
    start = document.body.index(text)
    return Span(
        doc_id=document.doc_id, version=document.version, start=start, end=start + len(text)
    )


class Spans:
    """Where each fact sits in the current documents, and each old value in the old ones."""

    def __init__(
        self,
        documents: Sequence[Document],
        plan: FactPlan,
        allocation: Allocation,
        outline: Sequence[DocumentPlan],
    ) -> None:
        self._docs = {d.key: d for d in documents}
        self._facts = plan.by_id()
        self._allocation = allocation
        self._version = {d.doc_id: current_version(d) for d in outline}

    def of(self, fact_id: str) -> Span:
        fact = self._facts[fact_id]
        document = self._docs[f"{fact.doc_id}@{self._version.get(fact.doc_id, 1)}"]
        return find_span(document, block(fact, self._allocation), fact_id)

    def stale(self, fact_id: str) -> Span:
        fact = self._facts[fact_id]
        old = block(fact, self._allocation).replace(fact.value, fact.old_value)
        return find_span(self._docs[f"{fact.doc_id}@1"], old, f"{fact_id} (old)")

    def document(self, key: str) -> Document:
        return self._docs[key]


def corpus_items(
    plans: Sequence[ItemPlan], plan: FactPlan, spans: Spans, texts: Texts
) -> list[Item]:
    """Items for every plan whose question was written. Restricted plans give two items."""
    facts = plan.by_id()
    items = []
    for item in plans:
        if item.id not in texts.questions:
            continue
        items.extend(_items(item, facts, spans, texts))
    return items


def _answer(chosen: Sequence[Fact]) -> str:
    return " ".join(f.named for f in chosen)


def _items(item: ItemPlan, facts: Mapping[str, Fact], spans: Spans, texts: Texts) -> list[Item]:
    question = texts.questions[item.id]
    chosen = [facts[f] for f in item.facts]
    base = {"question": question, "asker": "public"}
    if item.type in ("absent_detail", "absent_topic"):
        return [
            Item(
                id=item.id,
                type=item.type,
                answerable=False,
                unanswerable_reason=item.type,
                answer="The documents do not say.",
                **base,
            )
        ]
    if item.type == "deleted":
        notice = spans.document(f"{chosen[0].doc_id}@1")
        return [
            Item(
                id=item.id,
                type="deleted",
                answerable=False,
                unanswerable_reason="deleted",
                answer=f"That notice was withdrawn on {notice.deleted_on.isoformat()}.",
                stale_spans=(spans.of(chosen[0].id),),
                **base,
            )
        ]
    if item.type == "restricted":
        span = spans.of(chosen[0].id)
        staff_id = item.id.replace("RESTRICT-", "RESTRICT-STAFF-")
        public_id = item.id.replace("RESTRICT-", "RESTRICT-PUBLIC-")
        return [
            Item(
                id=staff_id,
                type="restricted_staff",
                asker="staff",
                question=question,
                answerable=True,
                evidence=(span,),
                answer=_answer(chosen),
                key_values=(chosen[0].value,),
            ),
            Item(
                id=public_id,
                type="restricted_public",
                answerable=False,
                unanswerable_reason="restricted",
                restricted_spans=(span,),
                answer="Only staff documents give this.",
                **base,
            ),
        ]
    evidence = tuple(spans.of(f.id) for f in chosen)
    valued = [f for f in chosen if f.scope != "postcode"]
    fields = {
        "id": item.id,
        "type": item.type,
        "answerable": True,
        "evidence": evidence,
        "answer": _answer(chosen),
        "key_values": tuple(f.value for f in valued),
        **base,
    }
    if item.type == "policy_heading":
        fields["heading"] = chosen[0].entity
    if item.type == "distractor":
        fields["distractor_spans"] = tuple(spans.of(d) for d in item.distractors)
    if item.type == "version":
        fields["stale_spans"] = (spans.stale(chosen[0].id),)
    if item.type == "followup":
        first = facts[item.first]
        first_question = texts.firsts[item.id]
        fields["history"] = (
            Turn(role="user", content=first_question),
            Turn(role="assistant", content=first.named),
        )
        fields["resolved_question"] = first_question.replace(first.entity, chosen[0].entity)
    return [Item(**fields)]


def v1_items(
    v1: V1, documents: Mapping[str, Document], quotes: Mapping[str, str], wanted: set[str]
) -> list[Item]:
    """Items for the v1 questions whose ids are in `wanted`."""
    items = []
    for question in v1.questions:
        item_id = v1.item_id(question)
        if item_id not in wanted:
            continue
        article = v1.article(question.article_id)
        document = documents[f"{article.article_id}@1"]
        if question.type == "identifier":
            start, end = identifier_span(article)
            evidence = Span(doc_id=article.article_id, version=1, start=start, end=end)
            distractors = tuple(
                Span(doc_id=a.article_id, version=1, start=s, end=e)
                for a in lookalikes(v1, article)
                for s, e in [identifier_span(a)]
            )
        elif item_id in quotes:
            evidence = find_span(document, quotes[item_id], item_id)
            distractors = ()
        else:
            continue
        items.append(
            Item(
                id=item_id,
                type=question.type,
                asker="public",
                question=question.question,
                answerable=True,
                evidence=(evidence,),
                distractor_spans=distractors,
                answer=document.body[evidence.start : evidence.end],
            )
        )
    return items
