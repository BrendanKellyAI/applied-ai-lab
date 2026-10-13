import numpy as np

from lab.rag.embed import Embedder, EmbeddingStore, batches
from tests.rag.fake_embeddings import FakeEmbeddingsClient, fake_vector


def _embedder(tmp_path, client=None):
    return Embedder(
        client or FakeEmbeddingsClient(),
        "text-embedding-3-small",
        EmbeddingStore(tmp_path / "vectors.sqlite"),
    )


def test_embeds_through_the_cache(tmp_path):
    client = FakeEmbeddingsClient()
    embed = _embedder(tmp_path, client)

    first = embed(["alpha beta", "gamma"])
    second = embed(["gamma", "alpha beta"])

    assert len(client.calls) == 1
    np.testing.assert_allclose(first[0], second[1])
    np.testing.assert_allclose(first[0], fake_vector("alpha beta"))


def test_cache_survives_a_new_embedder(tmp_path):
    _embedder(tmp_path)(["alpha"])
    client = FakeEmbeddingsClient()

    _embedder(tmp_path, client)(["alpha"])

    assert client.calls == []


def test_duplicate_texts_are_sent_once(tmp_path):
    client = FakeEmbeddingsClient()

    vectors = _embedder(tmp_path, client)(["same", "same", "other"])

    assert client.calls == [["same", "other"]]
    assert vectors.shape[0] == 3


def test_records_reported_tokens_and_model(tmp_path):
    embed = _embedder(tmp_path)
    embed(["one two three"])

    assert embed.tokens_reported == 3
    assert embed.model_returned == "text-embedding-3-small-fake"


def test_models_are_cached_separately(tmp_path):
    client = FakeEmbeddingsClient()
    store = EmbeddingStore(tmp_path / "vectors.sqlite")
    Embedder(client, "small", store)(["text"])
    Embedder(client, "large", store)(["text"])

    assert len(client.calls) == 2


def test_missing_counts_texts_not_yet_cached(tmp_path):
    embed = _embedder(tmp_path)
    embed(["cached"])

    assert embed.missing(["cached", "new", "new"]) == ["new"]


def test_batches_respect_input_and_token_limits():
    texts = [f"t{i}" for i in range(5)]

    groups = batches(texts, count_tokens=lambda t: 100, max_inputs=2, max_tokens=250)

    assert groups == [["t0", "t1"], ["t2", "t3"], ["t4"]]


def test_uncached_text_without_a_client_is_an_error(tmp_path):
    import pytest

    embed = Embedder(None, "small", EmbeddingStore(tmp_path / "vectors.sqlite"))

    with pytest.raises(RuntimeError, match="not in the embedding cache"):
        embed(["new text"])


def test_lookups_span_more_keys_than_one_query_holds(tmp_path):
    store = EmbeddingStore(tmp_path / "vectors.sqlite")
    texts = [f"text {i}" for i in range(1200)]
    store.put("small", texts, np.ones((1200, 3), dtype=np.float32))

    assert len(store.get_many("small", texts + ["absent"])) == 1200
