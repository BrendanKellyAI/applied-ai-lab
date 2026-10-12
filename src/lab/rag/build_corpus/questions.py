"""Question prompts and checks, one per item type.

Every question must end with "?", name what it asks about, and never contain the answer. Each
type adds its own rule: a bridge names the postcode area but not the region; a follow-up
names its product but none of the words of what it asks.
"""

import re
from collections.abc import Mapping

from lab.rag.build_corpus.allocate import ItemPlan
from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.facts import Fact
from lab.rag.build_corpus.generate import Task
from lab.rag.index import words
from lab.scoring import contains_match

MAX_WORDS = 40
MAX_FOLLOWUP_WORDS = 10
FIRST = "/first"


def subject(fact: Fact) -> str:
    """How a question must refer to the fact's entity."""
    if fact.scope in ("product", "internal", "deleted"):
        return f"the {fact.entity}"
    if fact.entity is None:
        return "Halvard Home"
    return fact.entity


def required_token(config: CorpusConfig, fact: Fact) -> str:
    """The word or name a question about this fact must contain."""
    if fact.scope in ("product", "internal", "deleted") and fact.entity:
        return fact.entity.split()[0]
    return fact.entity or "Halvard"


def question_tasks(
    config: CorpusConfig, items: list[ItemPlan], facts: Mapping[str, Fact]
) -> list[Task]:
    """First-wave tasks: every question that does not depend on another question."""
    tasks = []
    for item in items:
        if item.type == "followup":
            first = facts[item.first]
            tasks.append(
                Task(id=item.id + FIRST, prompt=_named_prompt(config, first, "a customer"))
            )
        elif item.type == "two_part":
            a, b = (facts[f] for f in item.facts)
            tasks.append(
                Task(
                    id=item.id,
                    prompt=config.prompt(
                        "two_part",
                        fact=a.named,
                        fact_b=b.named,
                        entity=subject(a),
                        entity_b=subject(b),
                    ),
                )
            )
        elif item.type == "bridge":
            region = facts[item.facts[1]]
            tasks.append(
                Task(
                    id=item.id, prompt=config.prompt("bridge", area=item.area, blank=region.blank())
                )
            )
        elif item.type == "absent_detail":
            held = item.held_out
            tasks.append(
                Task(
                    id=item.id,
                    prompt=config.prompt(
                        "absent_detail", entity=f"the {held.entity}", blank=held.blank
                    ),
                )
            )
        elif item.type == "absent_topic":
            tasks.append(Task(id=item.id, prompt=config.prompt("absent_topic", topic=item.topic)))
        else:
            asker = "a member of Halvard Home staff" if item.type == "restricted" else "a customer"
            tasks.append(
                Task(id=item.id, prompt=_named_prompt(config, facts[item.facts[0]], asker))
            )
    return tasks


def followup_tasks(
    config: CorpusConfig,
    items: list[ItemPlan],
    facts: Mapping[str, Fact],
    firsts: Mapping[str, str],
) -> list[Task]:
    """Second-wave tasks: each follow-up turn, written after its first question."""
    return [
        Task(
            id=item.id,
            prompt=config.prompt(
                "followup",
                first=firsts[item.id],
                reply=facts[item.first].named,
                entity=subject(facts[item.facts[0]]),
            ),
        )
        for item in items
        if item.type == "followup" and item.id in firsts
    ]


def _named_prompt(config: CorpusConfig, fact: Fact, asker: str) -> str:
    return config.prompt("question", fact=fact.named, asker=asker, entity=subject(fact))


def check_question(
    config: CorpusConfig, item: ItemPlan, facts: Mapping[str, Fact], task_id: str, text: str
) -> str | None:
    """The first rule the question breaks, worded for the model, or None if it passes."""
    question = text.strip().strip('"').strip()
    if "\n" in question or not question.endswith("?"):
        return "Reply with one question on one line, ending with a question mark."
    if len(question.split()) > MAX_WORDS:
        return f"Keep the question under {MAX_WORDS} words."
    if task_id.endswith(FIRST):
        return _check_named(config, facts[item.first], question)
    if item.type == "followup":
        return _check_followup(config, facts[item.facts[0]], question)
    if item.type == "two_part":
        return _check_all(config, [facts[f] for f in item.facts], question)
    if item.type == "bridge":
        return _check_bridge(config, item, facts[item.facts[1]], question)
    if item.type == "absent_detail":
        return _need(question, item.held_out.entity.split()[0]) or _others(
            config, question, {item.held_out.entity}
        )
    if item.type == "absent_topic":
        return _check_topic(config, item.topic, question)
    return _check_named(config, facts[item.facts[0]], question)


def _check_named(config: CorpusConfig, fact: Fact, question: str) -> str | None:
    return _check_all(config, [fact], question)


def _check_all(config: CorpusConfig, chosen: list[Fact], question: str) -> str | None:
    for fact in chosen:
        for value in (fact.value, fact.old_value):
            if value and contains_match(question, value):
                return f'It gives away the answer, "{value}". Ask without it.'
        problem = _need(question, required_token(config, fact))
        if problem:
            return problem
        if fact.entity == "Extended Care" and "Extended Care Plus" in question:
            return 'It must ask about "Extended Care", not "Extended Care Plus".'
    return _others(config, question, {f.entity for f in chosen if f.entity})


def _check_bridge(config: CorpusConfig, item: ItemPlan, region: Fact, question: str) -> str | None:
    if not re.search(rf"\b{re.escape(item.area)}\b", question):
        return f'It must say the postcode area is "{item.area}".'
    for name in config.regions:
        if name.lower() in question.lower():
            return f'It names the region "{name}"; name the postcode area only.'
    if contains_match(question, region.value):
        return f'It gives away the answer, "{region.value}". Ask without it.'
    return _others(config, question, set())


def _check_followup(config: CorpusConfig, target: Fact, question: str) -> str | None:
    if len(question.split()) > MAX_FOLLOWUP_WORDS:
        return f"Use at most {MAX_FOLLOWUP_WORDS} words."
    problem = _need(question, required_token(config, target))
    if problem:
        return problem
    entity_words = set(words(target.entity or ""))
    stop = set(config.stop_words)
    asked = set(words(target.named)) - stop - entity_words - set(words(target.value))
    shared = sorted(asked & set(words(question)))
    if shared:
        return (
            f"It repeats what is being asked ({', '.join(shared)}). Rely on the earlier "
            "question instead."
        )
    return _others(config, question, {target.entity})


def _check_topic(config: CorpusConfig, topic: str, question: str) -> str | None:
    key = [w for w in words(topic) if w not in ("the", "halvard")]
    if not set(key) & set(words(question)):
        return f"It must be about {topic}."
    return _others(config, question, set())


def _need(question: str, token: str) -> str | None:
    if not re.search(rf"\b{re.escape(token)}\b", question):
        return f'It must name "{token}".'
    return None


def _others(config: CorpusConfig, question: str, allowed: set) -> str | None:
    for product in config.products:
        if product in allowed:
            continue
        brand = product.split()[0]
        if re.search(rf"\b{re.escape(brand)}\b", question):
            return f"It names the {product}; do not name any other product."
    return None


def clean(text: str) -> str:
    return text.strip().strip('"').strip()
