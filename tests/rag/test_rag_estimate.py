from lab.cache import ResponseCache
from lab.prices import ModelPrice, PricesFile
from lab.providers.mock import MockProvider
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.estimate import estimate_condition, format_estimate
from lab.rag.waves import request_for
from tests.rag.conftest import condition_named
from tests.rag.fake_embeddings import FakeEmbeddingsClient

PRICES = PricesFile(
    prices={
        "openai": {
            "gpt-6.1-sol": ModelPrice(input=2.0, output=10.0),
            "text-embedding-3-small": ModelPrice(input=0.02),
        },
        "anthropic": {"claude-sonnet-5-5": ModelPrice(input=2.0, output=10.0)},
    }
)


def _offline(tmp_path):
    return Embedder(None, "text-embedding-3-small", EmbeddingStore(tmp_path / "v.sqlite"))


def _estimate(library, episode, embedder, name="baseline", **kwargs):
    return estimate_condition(
        library,
        library.test,
        condition_named(episode, name),
        embedder,
        episode="s2-e2-first-rag-system",
        **kwargs,
    )


def test_cold_cache_gives_an_upper_bound_with_no_key(library, episode, tmp_path):
    estimate = _estimate(library, episode, _offline(tmp_path), prices=PRICES)

    assert not estimate.exact_prompts
    assert estimate.embedding_texts > 0 and estimate.embedding_tokens > 0
    assert estimate.answer.calls == len(library.test)
    assert estimate.answer.output_tokens == 1000 * len(library.test)
    assert estimate.judge.output_tokens == 400 * len(library.test)
    assert estimate.cost is not None and estimate.cost > 0


def test_warm_cache_gives_exact_prompts_below_the_bound(library, episode, tmp_path):
    cold = _estimate(library, episode, _offline(tmp_path))
    store = EmbeddingStore(tmp_path / "warm.sqlite")
    warm_embedder = Embedder(FakeEmbeddingsClient(), "text-embedding-3-small", store)
    from lab.rag.retrieve import build, retrieve

    pipeline = condition_named(episode, "baseline").pipeline
    retrieve(library.test, build(library, pipeline, warm_embedder), pipeline, warm_embedder)
    warm = _estimate(library, episode, Embedder(None, "text-embedding-3-small", store))

    assert warm.exact_prompts
    assert warm.embedding_tokens == 0
    assert warm.answer.input_tokens <= cold.answer.input_tokens


def test_cached_answers_are_not_counted(library, episode, tmp_path):
    store = EmbeddingStore(tmp_path / "warm.sqlite")
    embedder = Embedder(FakeEmbeddingsClient(), "text-embedding-3-small", store)
    from lab.rag.retrieve import build, retrieve

    pipeline = condition_named(episode, "baseline").pipeline
    retrievals = retrieve(library.test, build(library, pipeline, embedder), pipeline, embedder)
    cache = ResponseCache(tmp_path / "cache")
    first = retrievals[library.test[0].id].prompt
    request = request_for(
        pipeline.answer,
        system=first.system,
        prompt=first.prompt,
        episode="s2-e2-first-rag-system",
        stage="answer",
    )
    cache.put(request, MockProvider().generate(request))

    estimate = _estimate(library, episode, embedder, cache=cache)

    assert estimate.answer.cached == 1


def test_search_only_estimate_has_no_model_calls(library, episode, tmp_path):
    estimate = _estimate(library, episode, _offline(tmp_path), name="k-3")

    assert estimate.answer is None and estimate.judge is None


def test_unknown_prices_say_so(library, episode, tmp_path):
    estimate = _estimate(library, episode, _offline(tmp_path), prices=None)
    text = format_estimate("s2-e2", [estimate], budget=10.0, currency="USD")

    assert estimate.cost is None
    assert "price unknown" in text
    assert "Budget: 10.00 USD" in text
