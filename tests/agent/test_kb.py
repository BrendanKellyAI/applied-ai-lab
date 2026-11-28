"""The knowledge base backends, offline: keyword search, and the reference path with a fake
embedder in place of the paid embedding call."""

import hashlib

import numpy as np

from lab.agent.kb import CORPUS, REFERENCE, KeywordKB, ReferenceKB, _query_item, passages_text
from lab.rag.config import load_pipeline
from lab.rag.corpus import load_library
from lab.rag.retrieve import build


def _fake_embed(texts):
    vectors = []
    for text in texts:
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        vectors.append(np.random.default_rng(seed).standard_normal(16))
    return np.array(vectors)


def test_keyword_search_finds_public_current_passages():
    passages = KeywordKB().search("Keel washing machine warranty")
    assert 0 < len(passages) <= 5
    assert all(p["document"] and p["text"] for p in passages)
    assert "[" in passages_text(passages)


def test_a_query_item_passes_the_corpus_checks():
    item = _query_item("How long is the warranty?")
    assert item.asker == "public" and item.id.startswith("agent-")


def test_reference_search_runs_the_s2_retrieval(tmp_path):
    kb = ReferenceKB(runner=None, cache_root=tmp_path, folder=tmp_path)
    pipeline = load_pipeline(REFERENCE)
    index = build(load_library(CORPUS), pipeline, _fake_embed)
    kb.__dict__["_parts"] = (pipeline, _fake_embed, index, None)
    passages = kb.search("Is my kettle still in warranty?")
    assert len(passages) == 5
    assert {"document", "title", "text"} <= set(passages[0])
