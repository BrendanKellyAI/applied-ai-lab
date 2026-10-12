import json

import yaml

from lab.cache import ResponseCache
from lab.providers.mock import MockProvider
from lab.rag.config import config_id, load_episode, load_pipeline
from lab.rag.corpus import Item
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.pipeline import RunContext, run_condition
from lab.rag.rerank import RerankConfig, apply_order, parse_llm_order, rerank
from lab.rag.rewrite import RewriteConfig, needs_call, parse_queries
from lab.runner import Runner, RunnerSettings
from tests.rag.conftest import condition_named
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mini_corpus import REFERENCE

LUNA = {"provider": "openai", "model": "gpt-6-luna", "reasoning": "off"}


def _item(question="How long is the warranty?", history=()):
    return Item(
        id="X-1",
        type="t",
        asker="public",
        question=question,
        answerable=False,
        unanswerable_reason="absent_topic",
        answer="a",
        history=history,
    )


def test_passthrough_stages_serialise_as_before():
    assert RewriteConfig().model_dump() == {"mode": "passthrough"}
    assert RerankConfig().model_dump() == {"mode": "passthrough"}
    assert RewriteConfig(mode="rewrite", model=LUNA).model_dump()["model"]["model"] == "gpt-6-luna"


def test_the_e2_config_id_is_unchanged(tmp_path):
    from pathlib import Path

    root = Path(__file__).parents[2]
    pipeline = load_pipeline(root / "season2" / "reference-e2.yaml")
    assert config_id(pipeline) == "b58f06493698"


def test_split_keeps_up_to_three_lines_and_rewrite_one():
    item = _item()
    assert parse_queries("1. A?\n2. B?\n- C?\nD?", item, "split") == ("A?", "B?", "C?")
    assert parse_queries("warranty period\nBrio kettle", item, "rewrite") == (
        "warranty period Brio kettle",
    )
    assert parse_queries("  \n", item, "rewrite") == (item.question,)


def test_resolve_followup_calls_only_for_items_with_history():
    config = RewriteConfig(mode="resolve_followup", model=LUNA)
    assert not needs_call(_item(), config)
    assert needs_call(_item(history=({"role": "user", "content": "Hi"},)), config)


def test_rerank_reorders_only_the_shortlist():
    scores = {0: 0.1, 1: 0.9, 2: 0.5}
    assert rerank([0, 1, 2, 3, 4], scores, 3) == [1, 2, 0, 3, 4]


def test_llm_order_parsing_drops_unknowns_and_fills_the_rest():
    assert parse_llm_order("3, 1, 9, 3, 2", 3) == [2, 0, 1]
    assert apply_order(6, 4, [2, 0]) == [2, 0, 1, 3, 4, 5]


def _respond(request):
    if "stand-alone" in request.system or "search query" in request.system:
        return "What is the warranty period for the Tessa dishwasher?"
    if "rank passages" in request.system:
        n = request.prompt.count("\n[")
        return ", ".join(str(i) for i in range(n + 1, 0, -1))
    return "answer"


def test_a_run_rewrites_follow_ups_and_reranks_with_a_model(tmp_path, library_dir):
    from lab.rag.corpus import load_library

    season = tmp_path / "season2"
    season.mkdir()
    (season / "reference.yaml").write_text(
        yaml.safe_dump(dict(REFERENCE, chunk={"kind": "whole"})), encoding="utf-8"
    )
    folder = tmp_path / "episodes" / "e6"
    folder.mkdir(parents=True)
    config = {
        "episode": "e6",
        "base": "../../season2/reference.yaml",
        "library": str(library_dir),
        "conditions": [
            {
                "name": "both",
                "measure": "search",
                "changes": {
                    "rewrite": {"mode": "resolve_followup", "model": LUNA},
                    "rerank": {"mode": "llm", "shortlist": 3, "model": LUNA},
                },
                "changes_more_than_one_stage": "test of both stages",
            }
        ],
    }
    (folder / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    episode = load_episode(folder / "config.yaml")
    runner = Runner(
        providers={"openai": MockProvider(respond=_respond)},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    library = load_library(library_dir)
    context = RunContext(
        episode=episode,
        library=library,
        embedder=Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite")),
        runner=runner,
        results=folder / "results",
        cache_root=tmp_path / "cache",
    )
    summary = run_condition(context, condition_named(episode, "both"), library.test)
    logs = [
        json.loads(line)
        for line in (folder / "results" / "both" / "log.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    follow = next(g for g in logs if g["type"] == "followup")
    plain = next(g for g in logs if g["type"] != "followup")
    assert follow["queries"] == ["What is the warranty period for the Tessa dishwasher?"]
    assert plain["queries"][0] != follow["queries"][0]
    assert {"rewrite", "rerank"} <= set(summary["calls"])
    reranked = next(g for g in logs if len(g["searched"]) >= 3)
    assert [r["chunk_id"] for r in reranked["ranked"][:3]] == [
        r["chunk_id"] for r in reranked["searched"][:3]
    ][::-1]
