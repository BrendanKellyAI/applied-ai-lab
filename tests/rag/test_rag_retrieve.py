import pytest

from lab.rag.chunk import StructureChunker
from lab.rag.config import PipelineConfig
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.filter import FilterConfig
from lab.rag.retrieve import build, retrieve
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mini_corpus import REFERENCE


@pytest.fixture
def embedder(tmp_path):
    return Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))


def _pipeline(**changes):
    return PipelineConfig.model_validate({**REFERENCE, **changes})


def _run(library, embedder, pipeline):
    index = build(library, pipeline, embedder)
    return index, retrieve(library.test, index, pipeline, embedder)


def test_every_item_gets_a_prompt_of_k_passages(library, embedder):
    _, results = _run(library, embedder, _pipeline(prompt={"k": 3}))

    assert set(results) == {i.id for i in library.test}
    assert all(len(r.prompt.chunk_ids) == 3 for r in results.values())
    assert results["IDENT-000"].queries == ("What does error E-2194 mean?",)


def test_passthrough_filter_lets_a_staff_chunk_reach_a_public_prompt(library, embedder):
    _, results = _run(library, embedder, _pipeline(prompt={"k": 10}))

    assert "INT-PRC@1#0" in results["RESTRICT-PUBLIC-000"].prompt.chunk_ids
    assert results["RESTRICT-PUBLIC-000"].removed == ()


def test_filter_before_keeps_staff_out_and_logs_what_it_blocked(library, embedder):
    index, results = _run(library, embedder, _pipeline(prompt={"k": 10}, filter={"mode": "before"}))
    public = results["RESTRICT-PUBLIC-000"]
    staff = results["RESTRICT-STAFF-000"]
    blocked = {index.chunks[r.index].chunk_id: r.reason for r in public.removed}

    assert not any(c.startswith("INT-PRC") for c in public.prompt.chunk_ids)
    assert blocked["INT-PRC@1#0"] == "access"
    assert any(c.startswith("INT-PRC") for c in staff.prompt.chunk_ids)
    assert not any(c.startswith("POL-WAR@1") for c in staff.prompt.chunk_ids)


def test_filter_after_ranks_first_then_drops(library, embedder):
    _, results = _run(library, embedder, _pipeline(filter={"mode": "after"}))
    result = results["RESTRICT-PUBLIC-000"]

    assert len(result.ranked) == len(result.searched) - len(result.removed)
    assert result.removed


def test_heading_embedding_reaches_the_index(library, embedder):
    pipeline = _pipeline(chunk={"kind": "structure", "max_tokens": 400, "embed_headings": True})
    index = build(library, pipeline, embedder)

    assert isinstance(pipeline.chunk, StructureChunker)
    assert index.embed_headings


def test_every_filter_mode_is_a_valid_block():
    for mode in ("passthrough", "before", "after"):
        assert _pipeline(filter={"mode": mode}).filter == FilterConfig(mode=mode)
