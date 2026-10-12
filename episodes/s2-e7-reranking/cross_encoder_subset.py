"""The local cross-encoder on E7's 40 distractor items, shortlist 10, search-only.

Run with `uv run --extra rerank python episodes/s2-e7-reranking/cross_encoder_subset.py`.
Needs no API key: the questions' embeddings are cached. Scores are cached too, so the
seconds-per-question figure is only meaningful on a first run; the committed summary.json
records the first run's timing.
"""

from pathlib import Path

from lab.cache import shared_cache_root
from lab.rag.config import ResolvedCondition, config_id, load_episode
from lab.rag.corpus import load_library
from lab.rag.embed import Embedder, EmbeddingStore, openai_client
from lab.rag.pipeline import RunContext, run_condition
from lab.rag.rerank import RerankConfig

HERE = Path(__file__).parent
REVISION = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
NAME = "cross-encoder-10"


def main() -> None:
    episode = load_episode(HERE / "config.yaml")
    library = load_library(episode.library)
    items = [i for i in library.test if i.type == "distractor"]
    pipeline = episode.base.model_copy(update={
        "rerank": RerankConfig(mode="cross_encoder", shortlist=10, revision=REVISION)
    })
    condition = ResolvedCondition(name=NAME, measure="search", pipeline=pipeline,
                                  changed=("rerank",))
    cache = shared_cache_root(HERE)
    # The same store `lab rag run` uses, so the questions' vectors are already cached.
    store = EmbeddingStore(cache / "embeddings" / "s2.sqlite")
    embedder = Embedder(openai_client(), pipeline.embed.model, store)
    context = RunContext(episode=episode, library=library, embedder=embedder, runner=None,
                         results=HERE / "results", cache_root=cache)
    summary = run_condition(context, condition, items)
    print(NAME, config_id(pipeline), summary["numbers"], summary.get("rerank_timing"))


if __name__ == "__main__":
    main()
