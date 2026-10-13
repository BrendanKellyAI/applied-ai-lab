import numpy as np
import pytest

from lab.rag.chunk import WholeChunker, chunk_library
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.filter import FilterConfig, allowed, apply_after, keep_mask
from lab.rag.index import build_index, embed_text, words
from lab.rag.search import SearchConfig, fuse, rank, search
from tests.rag.fake_embeddings import FakeEmbeddingsClient


@pytest.fixture
def embedder(tmp_path):
    return Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))


@pytest.fixture
def index(library, embedder):
    return build_index(chunk_library(library.documents, WholeChunker()), embedder)


def _ids(index, hits):
    return [index.chunks[h.index].chunk_id for h in hits]


def test_words_split_codes_like_v1():
    assert words("Error E-2194, please!") == ["error", "e", "2194", "please"]


def test_embed_text_prepends_headings_only_when_asked(library):
    from lab.rag.chunk import StructureChunker

    chunks = chunk_library([library.document("POL-WAR@2")], StructureChunker(max_tokens=400))
    tessa = next(c for c in chunks if "36 months" in c.text)

    assert embed_text(tessa, False) == tessa.text
    assert embed_text(tessa, True).startswith("Warranty > Tessa dishwasher > Cover period\n\n")


def test_keyword_search_finds_the_exact_code(index, embedder):
    question = "What does error E-2194 mean?"
    hits = search(index, question, embedder([question])[0], SearchConfig(method="keyword"))

    assert _ids(index, hits)[0] == "A000@1#0"


def test_vector_search_ranks_every_chunk_up_to_depth(index, embedder):
    question = "descale kettle"
    hits = search(index, question, embedder([question])[0], SearchConfig(method="vector", depth=3))

    assert len(hits) == 3
    assert _ids(index, hits)[0] == "A002@1#0"
    assert hits[0].score >= hits[1].score >= hits[2].score


def test_rank_breaks_ties_in_corpus_order():
    assert rank(np.array([1.0, 2.0, 2.0, 0.5]), depth=4) == [1, 2, 0, 3]


def test_rank_excludes_chunks_outside_the_mask():
    keep = np.array([True, False, True, True])

    assert rank(np.array([1.0, 9.0, 2.0, 0.5]), depth=4, keep=keep) == [2, 0, 3]


def test_fuse_adds_reciprocal_ranks():
    # b is second in one list and first in the other, so it beats a.
    assert fuse([["a", "b", "c"], ["b", "c", "a"]], k=60)[0] == "b"


def test_hybrid_fuses_only_the_top_of_each_ranking(index, embedder):
    question = "What does error E-2194 mean?"
    vector = embedder([question])[0]
    full = search(index, question, vector, SearchConfig(method="hybrid"))
    shallow = search(index, question, vector, SearchConfig(method="hybrid", fuse_depth=2))

    assert len(full) == len(index.chunks)
    assert len(shallow) <= 4
    assert _ids(index, shallow)[0] == "A000@1#0"


def test_filter_rules_read_metadata(index):
    rules = FilterConfig(mode="before")
    by_id = {c.chunk_id: c for c in index.chunks}

    assert not allowed(by_id["INT-PRC@1#0"], "public", rules)
    assert allowed(by_id["INT-PRC@1#0"], "staff", rules)
    assert not allowed(by_id["POL-WAR@1#0"], "staff", rules)
    assert not allowed(by_id["DEL-00@1#0"], "public", rules)
    assert allowed(by_id["A000@1#0"], "public", rules)


def test_access_rule_can_be_switched_off(index):
    by_id = {c.chunk_id: c for c in index.chunks}

    assert allowed(by_id["INT-PRC@1#0"], "public", FilterConfig(mode="before", access=False))
    assert not allowed(by_id["POL-WAR@1#0"], "public", FilterConfig(mode="before", access=False))


def test_filter_before_keeps_a_staff_chunk_out_of_the_ranking(index, embedder):
    question = "Can the Brio kettle claim fee be waived?"
    vector = embedder([question])[0]
    mask = keep_mask(index.chunks, "public", FilterConfig(mode="before"))
    hits = search(index, question, vector, SearchConfig(method="vector"), keep=mask)

    assert "INT-PRC@1#0" not in _ids(index, hits)
    assert keep_mask(index.chunks, "public", FilterConfig(mode="passthrough")) is None


def test_filter_after_drops_ranked_chunks_and_says_why(index, embedder):
    question = "Can the Brio kettle claim fee be waived?"
    hits = search(index, question, embedder([question])[0], SearchConfig(method="vector"))
    kept, removed = apply_after(hits, index.chunks, "public", FilterConfig(mode="after"))

    assert len(kept) + len(removed) == len(hits)
    reasons = {index.chunks[r.index].chunk_id: r.reason for r in removed}
    assert reasons["INT-PRC@1#0"] == "access"
    assert reasons["POL-WAR@1#0"] == "status"
    assert reasons["DEL-00@1#0"] == "status"


def test_filter_after_in_passthrough_removes_nothing(index, embedder):
    hits = search(index, "kettle", embedder(["kettle"])[0], SearchConfig(method="vector"))

    kept, removed = apply_after(hits, index.chunks, "public", FilterConfig(mode="passthrough"))

    assert (kept, removed) == (hits, [])
