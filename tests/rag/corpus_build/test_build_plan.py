import random
from collections import Counter
from pathlib import Path

import pytest

from lab.rag.build_corpus.allocate import allocate, counts_needed, wanted
from lab.rag.build_corpus.catalogue import fill, load_corpus_config
from lab.rag.build_corpus.facts import plan_facts
from lab.rag.build_corpus.values import ValuePool, ValuesExhausted
from lab.scoring import contains_match

CONFIG = Path(__file__).parents[3] / "datasets" / "halvard" / "config.yaml"
V1_TEXT = "Hold the button for 12 days. It costs £30.00 and takes 45 minutes."


@pytest.fixture(scope="module")
def config():
    return load_corpus_config(CONFIG)


@pytest.fixture(scope="module")
def plan(config):
    needed = counts_needed(config)
    return plan_facts(
        config,
        random.Random(config.seed),
        [V1_TEXT],
        held_out_count=needed["held_out"],
        version_count=needed["version"],
        deleted_count=needed["deleted"],
    )


@pytest.fixture(scope="module")
def allocation(config, plan):
    return allocate(config, plan, random.Random(config.seed + 1))


def test_values_render_and_singularise():
    pool = ValuePool({"days": "{n} days", "pounds": "£{n}.00"}, random.Random(0))

    assert pool.render("days", 1) == "1 day"
    assert pool.render("days", 3) == "3 days"
    assert pool.render("pounds", 1) == "£1.00"


def test_values_are_never_drawn_twice_and_run_out_cleanly():
    pool = ValuePool({"days": "{n} days"}, random.Random(0))
    drawn = {pool.draw("days", 1, 3) for _ in range(3)}

    assert drawn == {"1 day", "2 days", "3 days"}
    with pytest.raises(ValuesExhausted):
        pool.draw("days", 1, 3)


def test_values_already_in_the_library_are_refused():
    pool = ValuePool({"days": "{n} days"}, random.Random(0), ["Wait 12 days."])

    assert not pool.available("12 days")
    assert pool.available("2 days")


def test_fill_leaves_other_braces_alone():
    assert fill('{"answers": true} {q}', q="Why?") == '{"answers": true} Why?'
    with pytest.raises(KeyError):
        fill("{a}", b=1)


def test_every_planted_value_is_unique_and_new(plan):
    values = [f.value for f in plan.facts if f.kind != "postcode"]
    values += [f.old_value for f in plan.facts if f.old_value]

    assert len(values) == len(set(values))
    assert not any(contains_match(V1_TEXT, v) for v in values)


def test_each_fact_states_its_value_once(plan):
    for fact in plan.facts:
        assert fact.named.count(fact.value) == 1, fact.id
        if fact.bare:
            assert fact.bare.count(fact.value) == 1
            assert fact.entity is None or fact.entity not in fact.bare
        if fact.lead:
            assert fact.value not in fact.lead and fact.entity in fact.lead


def test_held_out_pairs_have_no_fact(plan):
    ids = set(plan.by_id())

    assert plan.held_out
    for held in plan.held_out:
        assert f"{held.attribute}:{held.entity}" not in ids
        assert "..." in held.blank


def test_twins_point_to_the_same_entity_in_another_document(plan):
    facts = plan.by_id()
    for fact in plan.facts:
        if fact.twin:
            twin = facts[fact.twin]
            assert (twin.entity, twin.twin) == (fact.entity, fact.id)
            assert twin.doc_id != fact.doc_id


def test_old_values_differ_from_current(plan, config):
    old = [f for f in plan.facts if f.old_value]

    assert len(old) == counts_needed(config)["version"]
    assert all(f.old_value != f.value and f.scope == "product" for f in old)


def test_postcode_sentence_lists_every_area(plan, config):
    islands = plan.by_id()["postcodes:Island Areas"]

    assert all(area in islands.named for area in config.regions["Island Areas"])


def test_item_counts_match_the_config_with_spares(allocation, config):
    found = Counter((i.type, i.split) for i in allocation.items)

    for item_type in config.items:
        for split in ("test", "dev"):
            assert found[(item_type, split)] == wanted(config, item_type, split)
    non_spare = Counter((i.type, i.split) for i in allocation.items if not i.spare)
    assert non_spare[("absent_detail", "test")] == config.items["absent_detail"][0]


def test_no_fact_is_the_evidence_for_two_items(allocation):
    evidence = [f for i in allocation.items for f in i.facts if not f.startswith("postcodes:")]

    assert len(evidence) == len(set(evidence))


def test_forms_follow_item_types(allocation):
    by_type = {i.facts[0]: i.type for i in allocation.items if i.facts}

    for fact_id, form in allocation.forms.items():
        expected = {"bare": "policy_heading", "two": "policy_two_sentence"}[form]
        assert by_type[fact_id] == expected


def test_distractor_siblings_look_alike_and_keep_the_named_form(allocation, plan):
    facts = plan.by_id()
    for item in (i for i in allocation.items if i.type == "distractor"):
        target = facts[item.facts[0]]
        others = [facts[d] for d in item.distractors]
        assert any(o.doc_id != target.doc_id for o in others)
        assert sum(o.attribute == target.attribute for o in others) >= 2
        assert all(allocation.form(o.id) == "named" for o in others)


def test_bridge_area_belongs_to_the_region(allocation, plan, config):
    facts = plan.by_id()
    for item in (i for i in allocation.items if i.type == "bridge"):
        region_fact = facts[item.facts[1]]
        assert item.area in config.regions[region_fact.entity]
        assert region_fact.doc_id != "POL-SER"


def test_followup_first_turn_shares_the_attribute(allocation, plan):
    facts = plan.by_id()
    for item in (i for i in allocation.items if i.type == "followup"):
        first, target = facts[item.first], facts[item.facts[0]]
        assert first.attribute == target.attribute and first.entity != target.entity


def test_allocation_is_reproducible(config, plan):
    first = allocate(config, plan, random.Random(5))
    second = allocate(config, plan, random.Random(5))

    assert first == second
