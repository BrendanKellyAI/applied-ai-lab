"""Build the Halvard library and test set: plan, write, check, assemble, verify, select, write.

A full build stops if any section fails every attempt, naming it. A pilot builds the Warranty
policy, one staff document, the sections its items need and a few items of every type, and
writes them to pilot/ for reading; it never writes the library itself.
"""

import json
import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lab.rag.build_corpus.allocate import Allocation, ItemPlan, allocate, counts_needed
from lab.rag.build_corpus.assemble import Spans, Texts, build_documents, corpus_items, v1_items
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.facts import FactPlan, plan_facts
from lab.rag.build_corpus.generate import Generated, generate
from lab.rag.build_corpus.outline import DocumentPlan, outline
from lab.rag.build_corpus.questions import (
    FIRST,
    check_question,
    clean,
    followup_tasks,
    question_tasks,
)
from lab.rag.build_corpus.sections import check_section, section_task
from lab.rag.build_corpus.v1 import V1, check_quote, clean_quote, quote_tasks
from lab.rag.build_corpus.verify import check_index, check_reply, check_tasks, parse_check
from lab.rag.build_corpus.write import (
    review_text,
    write_documents,
    write_items,
    write_library,
)
from lab.rag.corpus import Document, Item, load_library
from lab.rag.embed import Embedder
from lab.runner import Runner

PILOT_DOCUMENTS = ("POL-WAR", "INT-PRC")
V1_PILOT_PER_TYPE = 2
REVIEW_PER_TYPE = 3


class BuildError(RuntimeError):
    """The build cannot finish as specified."""


@dataclass(frozen=True)
class Blueprint:
    plan: FactPlan
    allocation: Allocation
    outline: list[DocumentPlan]


@dataclass(frozen=True)
class Scope:
    """What a run builds: which sections, which item plans, and which v1 questions."""

    sections: list[tuple[DocumentPlan, Any]]
    items: list[ItemPlan]
    v1_ids: set[str]


def blueprint(config: CorpusConfig, v1: V1) -> Blueprint:
    rng = random.Random(config.seed)
    needed = counts_needed(config)
    plan = plan_facts(
        config,
        rng,
        [a.text for a in v1.articles],
        held_out_count=needed["held_out"],
        version_count=needed["version"],
        deleted_count=needed["deleted"],
    )
    allocation = allocate(config, plan, rng)
    return Blueprint(plan=plan, allocation=allocation, outline=outline(config, plan, allocation))


def full_scope(bp: Blueprint, v1: V1) -> Scope:
    return Scope(
        sections=[(d, s) for d in bp.outline for s in d.sections],
        items=list(bp.allocation.items),
        v1_ids={v1.item_id(q) for q in v1.questions},
    )


def pilot_scope(config: CorpusConfig, bp: Blueprint, v1: V1) -> Scope:
    items: list[ItemPlan] = []
    for item_type in config.items:
        of_type = [p for p in bp.allocation.items if p.type == item_type and p.split == "test"]
        items.extend(of_type[: config.pilot_per_type])
    needed = set()
    for item in items:
        needed.update(item.facts, item.distractors, [item.first] if item.first else [])
    sections = [
        (d, s)
        for d in bp.outline
        for s in d.sections
        if d.doc_id in PILOT_DOCUMENTS or set(s.fact_ids) & needed
    ]
    v1_ids = {
        v1.item_id(q)
        for kind in ("identifier", "paraphrase", "shared")
        for q in [q for q in v1.questions if q.type == kind][:V1_PILOT_PER_TYPE]
    }
    return Scope(sections=sections, items=items, v1_ids=v1_ids)


@dataclass(frozen=True)
class Builder:
    config: CorpusConfig
    folder: Path
    v1: V1
    runner: Runner
    embedder: Embedder

    def _generate(self, tasks, check, stage: str, spec=None) -> Generated:
        return generate(
            self.runner,
            tasks,
            spec or self.config.generation,
            check,
            stage=stage,
            folder=self.folder / "generation",
            max_attempts=self.config.max_attempts,
            retry_template=self.config.prompts["retry"],
        )

    def sections(self, scope: Scope) -> Generated:
        by_key = {s.key: s for _, s in scope.sections}
        tasks = [section_task(self.config, d, s) for d, s in scope.sections]
        return self._generate(
            tasks, lambda key, text: check_section(self.config, by_key[key], text), "section"
        )

    def questions(self, scope: Scope, bp: Blueprint) -> tuple[Generated, Generated]:
        facts = bp.plan.by_id()
        plans = {i.id: i for i in scope.items}

        def check(task_id: str, text: str) -> str | None:
            item = plans[task_id.removesuffix(FIRST)]
            return check_question(self.config, item, facts, task_id, text)

        first = self._generate(question_tasks(self.config, scope.items, facts), check, "question")
        firsts = {
            k.removesuffix(FIRST): clean(o.text)
            for k, o in first.outcomes.items()
            if k.endswith(FIRST) and o.text
        }
        second = self._generate(
            followup_tasks(self.config, scope.items, facts, firsts), check, "followup"
        )
        return first, second

    def quotes(self, scope: Scope) -> Generated:
        articles = {self.v1.item_id(q): self.v1.article(q.article_id) for q in self.v1.questions}
        tasks = [t for t in quote_tasks(self.config, self.v1) if t.id in scope.v1_ids]
        return self._generate(tasks, lambda i, text: check_quote(articles[i], text), "quote")

    def verify(self, documents: Sequence[Document], items: Sequence[Item]) -> Generated:
        index = check_index(documents, self.embedder)
        tasks = check_tasks(self.config, items, index, self.embedder)
        return self._generate(tasks, check_reply, "check", spec=self.config.checker)


def run_build(builder: Builder, *, pilot: bool) -> dict[str, Any]:
    config, v1 = builder.config, builder.v1
    bp = blueprint(config, v1)
    scope = pilot_scope(config, bp, v1) if pilot else full_scope(bp, v1)

    sections = builder.sections(scope)
    if sections.failed() and not pilot:
        names = ", ".join(sorted(o.id for o in sections.failed()))
        raise BuildError(f"Sections failed every attempt: {names}")
    questions, followups = builder.questions(scope, bp)
    quotes = builder.quotes(scope)
    texts = _texts(sections, questions, followups, quotes)

    documents = build_documents(config, bp.plan, bp.allocation, bp.outline, texts, v1)
    spans = Spans(documents, bp.plan, bp.allocation, bp.outline)
    by_key = {d.key: d for d in documents}
    candidates = corpus_items(scope.items, bp.plan, spans, texts) + v1_items(
        v1, by_key, texts.quotes, scope.v1_ids
    )
    checks = builder.verify(documents, candidates)
    disputed = _disputed(checks)
    duplicates = _duplicates(candidates)
    kept = [i for i in candidates if i.id not in disputed | duplicates]
    test, dev = (kept, []) if pilot else _select(config, scope.items, kept)
    log = _log(sections, questions, followups, quotes, checks, disputed, test, dev)
    log["duplicates"] = sorted(duplicates)

    if pilot:
        _write_pilot(builder.folder / "pilot", documents, test, log)
    else:
        _missing_check(config, scope.items, test, dev)
        write_library(builder.folder, config, documents, test, dev, log)
        library = load_library(builder.folder)
        (builder.folder / "review.md").write_text(
            review_text(library.test + library.dev, library.documents, REVIEW_PER_TYPE),
            encoding="utf-8",
            newline="\n",
        )
    return log


def _texts(
    sections: Generated, questions: Generated, followups: Generated, quotes: Generated
) -> Texts:
    def ok(generated: Generated) -> dict[str, str]:
        return {k: o.text for k, o in generated.outcomes.items() if o.text}

    asked = ok(questions)
    return Texts(
        sections=ok(sections),
        questions={
            **{k: clean(v) for k, v in asked.items() if not k.endswith(FIRST)},
            **{k: clean(v) for k, v in ok(followups).items()},
        },
        firsts={k.removesuffix(FIRST): clean(v) for k, v in asked.items() if k.endswith(FIRST)},
        quotes={k: clean_quote(v) for k, v in ok(quotes).items()},
    )


def _disputed(checks: Generated) -> set[str]:
    """Items the checker could not clear: it found an answer, or never gave a readable verdict."""
    return {k for k, o in checks.outcomes.items() if o.text is None or parse_check(o.text)}


def _duplicates(items: Sequence[Item]) -> set[str]:
    """Items whose question repeats an earlier item's, apart from a restricted pair, which
    shares its question on purpose."""
    seen: dict[str, str] = {}
    repeated = set()
    for item in items:
        key = " ".join(item.question.lower().split())
        if key in seen and seen[key] != _base_id(item):
            repeated.add(item.id)
        seen.setdefault(key, _base_id(item))
    return repeated


def _base_id(item: Item) -> str:
    return item.id.replace("RESTRICT-STAFF-", "RESTRICT-").replace("RESTRICT-PUBLIC-", "RESTRICT-")


def _select(
    config: CorpusConfig, plans: Sequence[ItemPlan], items: Sequence[Item]
) -> tuple[list[Item], list[Item]]:
    """For each type and split, the first items in plan order that survived, up to the target.
    A restricted pair survives only whole."""
    by_base: dict[str, list[Item]] = {}
    for item in items:
        by_base.setdefault(_base_id(item), []).append(item)
    chosen: dict[str, list[Item]] = {"test": [], "dev": []}
    taken: Counter = Counter()
    for plan in plans:
        group = by_base.get(plan.id, [])
        if plan.type == "restricted" and len(group) != 2:
            continue
        if not group:
            continue
        target = config.items[plan.type][0 if plan.split == "test" else 1]
        if taken[(plan.type, plan.split)] < target:
            taken[(plan.type, plan.split)] += 1
            chosen[plan.split].extend(group)
    v1 = [i for i in items if i.type in ("identifier", "paraphrase", "shared")]
    return v1 + chosen["test"], chosen["dev"]


def _missing_check(config: CorpusConfig, plans, test: Sequence[Item], dev: Sequence[Item]):
    found = Counter(
        (p.type, p.split)
        for p in plans
        if any(_base_id(i) == p.id for i in (test if p.split == "test" else dev))
    )
    short = [
        f"{t} {split}: {found[(t, split)]} of {want}"
        for t, (n_test, n_dev) in config.items.items()
        for split, want in (("test", n_test), ("dev", n_dev))
        if found[(t, split)] < want
    ]
    if short:
        raise BuildError("Too few items survived the checks: " + "; ".join(short))


def _summary(generated: Generated) -> dict[str, Any]:
    outcomes = list(generated.outcomes.values())
    return {
        "tasks": len(outcomes),
        "passed": sum(1 for o in outcomes if o.text),
        "attempts": dict(Counter(o.attempts for o in outcomes if o.text)),
        "failed": sorted(o.id for o in outcomes if not o.text),
        "models_returned": sorted({o.model_returned for o in outcomes if o.model_returned}),
        "calls": [
            {
                "made": s.made,
                "cached": s.cached,
                "failed": s.failed,
                "tokens": {n: vars(t) for n, t in s.tokens_by_provider.items()},
            }
            for s in generated.summaries
        ],
        "problems": {o.id: list(o.problems) for o in outcomes if o.problems},
    }


def _log(sections, questions, followups, quotes, checks, disputed, test, dev) -> dict[str, Any]:
    return {
        "sections": _summary(sections),
        "questions": _summary(questions),
        "followups": _summary(followups),
        "quotes": _summary(quotes),
        "checks": _summary(checks),
        "disputed": sorted(disputed),
        "items": {"test": len(test), "dev": len(dev)},
        "by_type": dict(Counter(i.type for i in [*test, *dev])),
    }


def _write_pilot(folder: Path, documents: Sequence[Document], items: Sequence[Item], log) -> None:
    built = [d for d in documents if d.family != "article" or not d.doc_id.startswith("A")]
    write_documents(folder, built)
    write_items(folder / "items.jsonl", items)
    (folder / "review.md").write_text(
        review_text(items, documents, None), encoding="utf-8", newline="\n"
    )
    (folder / "build_log.json").write_text(
        json.dumps(log, indent=1, default=str) + "\n", encoding="utf-8", newline="\n"
    )
