import random
from pathlib import Path

import pytest

from lab.rag.build_corpus.build import blueprint
from lab.rag.build_corpus.catalogue import load_corpus_config
from lab.rag.build_corpus.questions import check_question
from lab.rag.build_corpus.sections import check_section, section_task
from lab.rag.build_corpus.v1 import Article, check_quote, sentence_around
from lab.rag.build_corpus.verify import check_reply, parse_check
from tests.rag.corpus_build.fake_generation import section_text

CONFIG = Path(__file__).parents[3] / "datasets" / "halvard" / "config.yaml"


@pytest.fixture(scope="module")
def config():
    return load_corpus_config(CONFIG)


@pytest.fixture(scope="module")
def bp(config):
    from lab.rag.build_corpus.v1 import load_v1

    return blueprint(config, load_v1(CONFIG.parent / "v1"))


def _section(bp, key):
    return next((d, s) for d in bp.outline for s in d.sections if s.key == key)


def _item(bp, item_type):
    return next(i for i in bp.allocation.items if i.type == item_type)


# Sections


def test_a_good_section_passes(config, bp):
    _, section = _section(bp, "POL-WAR/Brio kettle/Cover period")

    assert check_section(config, section, section_text(config, section)) is None


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda t, b: t.replace(b, ""), "word for word"),
        (lambda t, b: t + " " + b, "more than once"),
        (lambda t, b: t + " It takes 3 weeks.", "another number"),
        (lambda t, b: t + " It costs £5.", "another number"),
        (lambda t, b: t + " Allow two working days.", "amount in words"),
        (lambda t, b: t + " Unlike the Tessa dishwasher.", "Tessa dishwasher"),
        (lambda t, b: "## Heading\n" + t, "heading"),
        (lambda t, b: "", "empty"),
    ],
)
def test_section_rules(config, bp, change, expected):
    _, section = _section(bp, "POL-WAR/Brio kettle/Cover period")
    text = change(section_text(config, section), section.blocks[0])

    assert expected in check_section(config, section, text)


def test_a_section_must_be_long_enough(config, bp):
    _, section = _section(bp, "POL-WAR/Brio kettle/Cover period")

    assert "tokens long" in check_section(config, section, " ".join(section.blocks))


def test_general_sections_may_name_no_product(config, bp):
    _, section = _section(bp, "POL-WAR/General terms/Making a claim")
    text = section_text(config, section) + " Even the Brio kettle."

    assert "no product" in check_section(config, section, text)


def test_section_prompt_lists_the_sentences_and_the_pair_rule(config, bp):
    two = next(i for i in bp.allocation.items if i.type == "policy_two_sentence")
    document, section = next(
        (d, s) for d in bp.outline for s in d.sections if two.facts[0] in s.fact_ids
    )
    prompt = section_task(config, document, section).prompt

    assert all(f'"{b}"' in prompt for b in section.blocks)
    assert "single space" in prompt
    assert f"other than the {section.entity}" in prompt


def test_intro_internal_and_notice_prompts(config, bp):
    for key in ("POL-WAR/intro", "INT-PRC/Brio kettle/Goodwill and discounts", "DEL-00/notice"):
        document, section = _section(bp, key)
        task = section_task(config, document, section)
        assert task.id == key and "{" not in task.prompt.replace("{value}", "")


# Questions


def test_named_question_rules(config, bp):
    facts = bp.plan.by_id()
    item = _item(bp, "policy_heading")
    fact = facts[item.facts[0]]
    brand = fact.entity.split()[0]

    def check(text):
        return check_question(config, item, facts, item.id, text)

    assert check(f"How long is the cover on my {fact.entity}?") is None
    assert "question mark" in check(f"Tell me about the {fact.entity}.")
    assert "answer" in check(f"Is it {fact.value} for the {fact.entity}?")
    assert brand in check("How long is the cover?")
    assert "other product" in check(f"Is the {fact.entity} like the Mira robot vacuum?") or (
        brand == "Mira"
    )


def test_bridge_question_rules(config, bp):
    facts = bp.plan.by_id()
    item = _item(bp, "bridge")
    region = facts[item.facts[1]].entity

    def check(text):
        return check_question(config, item, facts, item.id, text)

    assert check(f"I live in postcode area {item.area}. When do parts arrive?") is None
    assert "postcode area" in check("When do parts arrive?")
    assert "region" in check(f"I live in {item.area}, in {region}. When?")


def test_followup_question_rules(config, bp):
    facts = bp.plan.by_id()
    item = _item(bp, "followup")
    target = facts[item.facts[0]]
    asked = [w for w in target.named.lower().split() if len(w) > 6][0]

    def check(text):
        return check_question(config, item, facts, item.id, text)

    assert check(f"And for the {target.entity}?") is None
    assert "earlier question" in check(f"And the {asked} for the {target.entity}?")
    assert "at most" in check(f"And what about the {target.entity}, could you tell me more now?")


def test_two_part_needs_both_entities(config, bp):
    facts = bp.plan.by_id()
    item = _item(bp, "two_part")
    a, b = (facts[f] for f in item.facts)
    first = "the " + a.entity if a.scope == "product" else (a.entity or "Halvard")

    problem = check_question(config, item, facts, item.id, f"What about {first}?")

    assert problem is not None


def test_absent_topic_must_stay_on_topic(config, bp):
    item = _item(bp, "absent_topic")
    facts = bp.plan.by_id()

    assert "must be about" in check_question(config, item, facts, item.id, "Is it raining?")


# Quotes and checks


def test_quote_rules():
    article = Article(
        article_id="A",
        product="Brio kettle",
        text="Title line\n\nFirst sentence is here. Second sentence follows now.",
    )

    assert check_quote(article, "First sentence is here.") is None
    assert "word for word" in check_quote(article, "First sentence is there.")
    assert "whole sentence" in check_quote(article, "First")


def test_sentence_around_stops_at_full_stops_and_lines():
    text = "Title\n\nOne two three. Four five six. Seven."

    assert text[slice(*sentence_around(text, text.index("five")))] == "Four five six."
    assert text[slice(*sentence_around(text, 1))] == "Title"


def test_check_replies_parse():
    assert parse_check('{"answers": false, "passage": null, "reason": "r"}') is False
    assert parse_check('```json\n{"answers": true}\n```') is True
    assert check_reply("x", "yes") is not None
    assert check_reply("x", '{"answers": "no"}') is not None


def test_blueprint_is_reproducible(config, bp):
    from lab.rag.build_corpus.v1 import load_v1

    again = blueprint(config, load_v1(CONFIG.parent / "v1"))

    assert again.allocation == bp.allocation
    assert random.Random(config.seed).random() == random.Random(config.seed).random()
