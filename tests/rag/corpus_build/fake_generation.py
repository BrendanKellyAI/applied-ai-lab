"""A stand-in for the generation and checker models: every prompt the build will send gets a
reply that passes its checks, worked out from the blueprint before the build runs.

`bad_first` names sections whose first draft breaks a rule, to exercise the retry path.
`answerable` names questions the checker should say the library answers.
"""

import json

from lab.rag.build_corpus.build import Blueprint, Scope
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.generate import _base
from lab.rag.build_corpus.questions import (
    FIRST,
    followup_tasks,
    question_tasks,
    subject,
)
from lab.rag.build_corpus.sections import bounds, section_task
from lab.rag.build_corpus.v1 import V1, quote_tasks, sentence_around
from lab.rag.chunk import count_tokens

FILLER = "Halvard Home keeps this guidance clear so that every customer knows what to expect. "


def section_text(config: CorpusConfig, section) -> str:
    low, _ = bounds(config, section)
    blocks = " ".join(section.blocks)
    title = "A notice for customers\n\n" if section.kind == "deleted" else ""
    text = title + blocks
    while count_tokens(text) < low + 10:
        text = title + FILLER + text[len(title) :]
    return text


def question_text(item, facts, task_id: str) -> str:
    """A question that passes its checks and is unique: it carries what it asks about."""
    if task_id.endswith(FIRST):
        first = facts[item.first]
        return f"What should I know about {subject(first)} ({first.attribute}, {item.id})?"
    if item.type == "two_part":
        a, b = (facts[f] for f in item.facts)
        return f"What about {subject(a)} and {subject(b)} ({item.id})?"
    if item.type == "bridge":
        return f"My home is in postcode area {item.area}. What applies ({item.id})?"
    if item.type == "followup":
        return f"And for {subject(facts[item.facts[0]])} ({item.id})?"
    if item.type == "absent_detail":
        return f"What about the {item.held_out.entity} ({item.held_out.attribute})?"
    if item.type == "absent_topic":
        return f"What about {item.topic}?"
    fact = facts[item.facts[0]]
    return f"What should I know about {subject(fact)} ({fact.id.split(':')[0]})?"


class FakeModels:
    def __init__(
        self,
        config: CorpusConfig,
        bp: Blueprint,
        scope: Scope,
        v1: V1,
        *,
        bad_first: frozenset[str] = frozenset(),
        answerable: frozenset[str] = frozenset(),
    ) -> None:
        self.answerable = answerable
        self.table: dict[str, str] = {}
        self.bad: dict[str, str] = {}
        facts = bp.plan.by_id()
        for document, section in scope.sections:
            prompt = section_task(config, document, section).prompt
            self.table[prompt] = section_text(config, section)
            if section.key in bad_first:
                self.bad[prompt] = self.table[prompt] + " It takes 3 weeks."
        plans = {i.id: i for i in scope.items}
        firsts = {}
        for task in question_tasks(config, scope.items, facts):
            item = plans[task.id.removesuffix(FIRST)]
            # Two follow-ups can share a first question; like the cache, one prompt gets one
            # reply, so the first item's wording stands for both.
            self.table.setdefault(task.prompt, question_text(item, facts, task.id))
            if task.id.endswith(FIRST):
                firsts[item.id] = self.table[task.prompt]
        for task in followup_tasks(config, scope.items, facts, firsts):
            self.table[task.prompt] = question_text(plans[task.id], facts, task.id)
        for task in quote_tasks(config, v1):
            question = next(q for q in v1.questions if v1.item_id(q) == task.id)
            text = v1.article(question.article_id).text
            start, end = sentence_around(text, text.index("\n\n") + 3)
            self.table[task.prompt] = text[start:end]
        self.check_system = config.prompts["check_system"].strip()

    def __call__(self, request) -> str:
        if request.system == self.check_system:
            question = request.prompt.split("\n", 1)[0].removeprefix("Question: ")
            answers = question in self.answerable
            return json.dumps({"answers": answers, "passage": None, "reason": "r"})
        if request.prompt in self.bad:
            return self.bad[request.prompt]
        return self.table[_base(request.prompt)]
