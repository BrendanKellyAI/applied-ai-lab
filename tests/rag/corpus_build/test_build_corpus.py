import json
import shutil
from collections import Counter
from pathlib import Path

import pytest

from lab.cache import ResponseCache
from lab.providers.mock import MockProvider
from lab.rag.build_corpus.build import (
    Builder,
    blueprint,
    full_scope,
    pilot_scope,
    run_build,
)
from lab.rag.build_corpus.catalogue import load_corpus_config
from lab.rag.build_corpus.v1 import load_v1
from lab.rag.corpus import load_library
from lab.rag.embed import Embedder, EmbeddingStore
from lab.runner import Runner, RunnerSettings
from lab.scoring import contains_match
from tests.rag.corpus_build.fake_generation import FakeModels, question_text
from tests.rag.fake_embeddings import FakeEmbeddingsClient

SOURCE = Path(__file__).parents[3] / "datasets" / "halvard"
BAD_SECTION = "POL-WAR/Brio kettle/Cover period"


def _folder(tmp_path):
    folder = tmp_path / "halvard"
    folder.mkdir()
    shutil.copy(SOURCE / "config.yaml", folder / "config.yaml")
    shutil.copytree(SOURCE / "v1", folder / "v1")
    return folder


def _builder(folder, tmp_path, fake):
    config = load_corpus_config(folder / "config.yaml")
    provider = MockProvider(respond=fake)
    runner = Runner(
        providers={"openai": provider, "anthropic": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    embedder = Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))
    return Builder(
        config=config, folder=folder, v1=load_v1(folder / "v1"), runner=runner, embedder=embedder
    ), provider


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("build")
    folder = _folder(tmp_path)
    config = load_corpus_config(folder / "config.yaml")
    v1 = load_v1(folder / "v1")
    bp = blueprint(config, v1)
    first_absent = next(i for i in bp.allocation.items if i.type == "absent_detail")
    scope = full_scope(bp, v1)
    fake = FakeModels(
        config,
        bp,
        scope,
        v1,
        bad_first=frozenset({BAD_SECTION}),
        answerable=frozenset({question_text(first_absent, bp.plan.by_id(), first_absent.id)}),
    )
    builder, provider = _builder(folder, tmp_path, fake)
    log = run_build(builder, pilot=False)
    return folder, config, log, provider, builder


def test_the_built_library_loads_and_matches_its_manifest(built):
    folder, config, *_ = built
    library = load_library(folder)

    assert library.corpus_version == "halvard-v2"
    assert len(library.test) == 520
    assert len(library.dev) == 100


def test_item_counts_by_type(built):
    folder, config, *_ = built
    library = load_library(folder)
    found = Counter(i.type for i in library.test)

    assert found["identifier"] == found["paraphrase"] == found["shared"] == 40
    assert found["restricted_staff"] == found["restricted_public"] == 40
    assert found["policy_single"] == 40 and found["deleted"] == 20
    assert sum(1 for i in library.test if i.answerable) == 400


def test_every_answer_value_sits_in_its_evidence(built):
    library = load_library(built[0])
    for item in library.test + library.dev:
        evidence = " ".join(library.span_text(s) for s in item.evidence)
        for value in item.key_values:
            assert contains_match(evidence, value), item.id


def test_document_families(built):
    library = load_library(built[0])
    families = Counter((d.family, d.status, d.access) for d in library.documents)

    assert families[("policy", "current", "public")] == 4
    assert families[("policy", "superseded", "public")] == 4
    assert families[("internal", "current", "staff")] == 4
    assert families[("article", "deleted", "public")] == 32
    assert families[("article", "current", "public")] == 300


def test_superseded_policy_differs_only_at_old_values(built):
    library = load_library(built[0])
    for doc_id in ("POL-WAR", "POL-RET", "POL-SAF", "POL-SER"):
        new = library.document(f"{doc_id}@2").body
        old = library.document(f"{doc_id}@1").body
        assert new != old
        assert len(new.split()) == len(old.split())


def test_version_items_point_at_both_versions(built):
    library = load_library(built[0])
    item = next(i for i in library.test if i.type == "version")

    assert item.evidence[0].version == 2 and item.stale_spans[0].version == 1
    assert item.key_values[0] not in library.span_text(item.stale_spans[0])


def test_restricted_items_come_in_pairs(built):
    library = load_library(built[0])
    staff = next(i for i in library.test if i.type == "restricted_staff")
    public = next(i for i in library.test if i.id == staff.id.replace("STAFF", "PUBLIC"))

    assert staff.question == public.question
    assert library.document(staff.evidence[0].doc_key).access == "staff"
    assert public.restricted_spans == staff.evidence


def test_a_disputed_item_is_replaced_by_a_spare(built):
    folder, config, log, *_ = built
    library = load_library(folder)

    assert len(log["disputed"]) == 1
    assert log["disputed"][0] not in {i.id for i in library.test + library.dev}
    assert sum(1 for i in library.test if i.type == "absent_detail") == 40


def test_a_failed_section_is_retried_with_its_reason(built):
    log = built[2]

    assert log["sections"]["attempts"] == {1: 207, 2: 1}
    assert "another number" in log["sections"]["problems"][BAD_SECTION][0]


def test_followups_carry_the_first_turn(built):
    library = load_library(built[0])
    item = next(i for i in library.test if i.type == "followup")

    assert [t.role for t in item.history] == ["user", "assistant"]
    assert item.resolved_question != item.history[0].content


def test_pack_holds_the_current_policies_within_the_limit(built):
    folder, config, *_ = built
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    pack = manifest["long_context_pack"]

    assert pack[:4] == ["POL-WAR@2", "POL-RET@2", "POL-SAF@2", "POL-SER@2"]
    assert sum(manifest["files"][f"{k}.md"]["tokens_o200k"] for k in pack) <= 120_000


def test_review_file_shows_three_of_each_type(built):
    review = (built[0] / "review.md").read_text(encoding="utf-8")

    assert review.count("### POL-SINGLE-") == 3
    assert "- Evidence (" in review


def test_a_rebuild_sends_nothing(built, tmp_path):
    folder, config, log, provider, builder = built
    sent = len(provider.calls)

    run_build(builder, pilot=False)

    assert len(provider.calls) == sent


def test_pilot_writes_a_review_and_no_library(tmp_path):
    folder = _folder(tmp_path)
    config = load_corpus_config(folder / "config.yaml")
    v1 = load_v1(folder / "v1")
    bp = blueprint(config, v1)
    scope = pilot_scope(config, bp, v1)
    builder, _ = _builder(folder, tmp_path, FakeModels(config, bp, scope, v1))

    log = run_build(builder, pilot=True)

    assert (folder / "pilot" / "review.md").exists()
    assert (folder / "pilot" / "documents" / "POL-WAR@2.md").exists()
    assert not (folder / "manifest.json").exists()
    assert Counter(t for t in log["by_type"]).keys() >= {"policy_single", "bridge", "identifier"}
    assert log["by_type"]["identifier"] == 2


def test_repeated_questions_are_dropped_but_restricted_pairs_kept():
    from lab.rag.build_corpus.build import _duplicates
    from lab.rag.corpus import Item

    def item(id_, question, **fields):
        base = {
            "type": "t",
            "asker": "public",
            "answerable": False,
            "answer": "a",
            "unanswerable_reason": "absent_topic",
        }
        return Item(id=id_, question=question, **{**base, **fields})

    items = [
        item("TOPIC-000", "What about it?"),
        item("TOPIC-001", "what  about it?"),
        item("RESTRICT-PUBLIC-000", "Same?", unanswerable_reason="restricted"),
        item("RESTRICT-STAFF-000", "Same?", unanswerable_reason="restricted"),
    ]

    assert _duplicates(items) == {"TOPIC-001"}


def test_followups_with_the_same_last_turn_are_not_repeats():
    from lab.rag.build_corpus.build import _duplicates
    from lab.rag.corpus import Item, Span, Turn

    def followup(id_, first):
        return Item(
            id=id_,
            type="followup",
            asker="public",
            question="And for the Orrin heat pump?",
            history=(Turn(role="user", content=first), Turn(role="assistant", content="a")),
            answerable=True,
            evidence=(Span(doc_id="D", version=1, start=0, end=1),),
            answer="a",
        )

    items = [
        followup("FOLLOW-000", "How long is cover?"),
        followup("FOLLOW-001", "How much?"),
        followup("FOLLOW-002", "How long is cover?"),
    ]

    assert _duplicates(items) == {"FOLLOW-002"}
