import json

import pytest

from lab.cache import ResponseCache
from lab.providers.mock import MockProvider
from lab.rag.embed import Embedder, EmbeddingStore
from lab.rag.log import read_log
from lab.rag.pipeline import RunContext, run_condition, select_items
from lab.runner import Runner, RunnerSettings
from tests.rag.conftest import condition_named
from tests.rag.fake_embeddings import FakeEmbeddingsClient
from tests.rag.mock_models import respond as _respond


def _context(episode, library, tmp_path, provider):
    runner = Runner(
        providers={"openai": provider, "anthropic": provider},
        cache=ResponseCache(tmp_path / "cache"),
        limits={},
        settings=RunnerSettings(max_attempts=1),
        sleep=lambda s: None,
    )
    embedder = Embedder(FakeEmbeddingsClient(), "small", EmbeddingStore(tmp_path / "v.sqlite"))
    return RunContext(
        episode=episode,
        library=library,
        embedder=embedder,
        runner=runner,
        results=episode.folder / "results",
    )


def test_full_run_writes_a_log_line_per_item_and_a_summary(episode, library, tmp_path):
    provider = MockProvider(respond=_respond())
    context = _context(episode, library, tmp_path, provider)

    summary = run_condition(context, condition_named(episode, "baseline"), library.test)
    logs = read_log(context.results / "baseline" / "log.jsonl")
    numbers = summary["numbers"]

    assert len(logs) == len(library.test)
    assert (numbers["search"]["total"], numbers["not_found"]["total"]) == (7, 3)
    assert numbers["leaks"]["total"] == 9
    assert numbers["not_found"]["count"] == 2  # the restricted question was answered
    assert summary["models_returned"]["answer"] == ["gpt-6.1-sol-mock-0001"]
    # The restricted question asked by staff and by the public makes one identical request with
    # no filter, so it is sent once for both items.
    assert summary["calls"]["answer"][0]["made"] == len(library.test) - 1
    assert json.loads((context.results / "baseline" / "summary.json").read_text()) == summary


def test_log_traces_each_span(episode, library, tmp_path):
    context = _context(episode, library, tmp_path, MockProvider(respond=_respond()))
    run_condition(context, condition_named(episode, "baseline"), library.test)
    logs = {log.item_id: log for log in read_log(context.results / "baseline" / "log.jsonl")}

    ident = logs["IDENT-000"]
    assert ident.evidence_rank == 1
    assert {s.kind for s in ident.spans} == {"evidence", "distractor"}
    assert ident.spans[0].in_prompt
    assert ident.verdict.correct and ident.code_check
    assert ident.lost_at is None
    restricted = logs["RESTRICT-PUBLIC-000"]
    assert restricted.leaks == ("INT-PRC@1#0",)
    assert restricted.lost_at is None  # unanswerable items have no passage to lose


def test_a_rerun_sends_nothing(episode, library, tmp_path):
    provider = MockProvider(respond=_respond())
    context = _context(episode, library, tmp_path, provider)
    run_condition(context, condition_named(episode, "baseline"), library.test)
    sent = len(provider.calls)

    summary = run_condition(context, condition_named(episode, "baseline"), library.test)

    assert len(provider.calls) == sent
    assert summary["calls"]["answer"][0]["made"] == 0


def test_search_only_condition_makes_no_model_call(episode, library, tmp_path):
    provider = MockProvider(respond=_respond())
    context = _context(episode, library, tmp_path, provider)

    summary = run_condition(context, condition_named(episode, "k-3"), library.test)

    assert provider.calls == []
    assert set(summary["numbers"]) == {"search", "leaks"}
    assert summary["changed"] == ["prompt"]
    log = read_log(context.results / "k-3" / "log.jsonl")[0]
    assert log.answer is None and len(log.prompt_chunks) == 3


def test_unreadable_verdict_is_asked_again_once(episode, library, tmp_path):
    respond = _respond(garbage_once={"What does error E-2194 mean?"})
    context = _context(episode, library, tmp_path, MockProvider(respond=respond))

    summary = run_condition(context, condition_named(episode, "baseline"), library.test)
    logs = {log.item_id: log for log in read_log(context.results / "baseline" / "log.jsonl")}

    assert logs["IDENT-000"].verdict is not None
    assert summary["judge_errors"] == []
    assert len(summary["calls"]["judge"]) == 2


def test_verdict_unreadable_twice_is_recorded_not_dropped(episode, library, tmp_path):
    respond = _respond(always_garbage={"What does error E-2194 mean?"})
    context = _context(episode, library, tmp_path, MockProvider(respond=respond))

    summary = run_condition(context, condition_named(episode, "baseline"), library.test)
    logs = {log.item_id: log for log in read_log(context.results / "baseline" / "log.jsonl")}

    assert summary["judge_errors"] == ["IDENT-000"]
    assert logs["IDENT-000"].verdict is None
    assert logs["IDENT-000"].judge_error.startswith("unparsed")
    assert logs["IDENT-000"].lost_at == "unjudged"


def test_full_run_without_a_runner_is_refused(episode, library, tmp_path):
    context = _context(episode, library, tmp_path, MockProvider())
    context = RunContext(**{**context.__dict__, "runner": None})

    with pytest.raises(RuntimeError, match="runner"):
        run_condition(context, condition_named(episode, "baseline"), library.test)


def test_pilot_takes_the_first_items_of_each_type(library):
    chosen = select_items(library, "test", pilot=True, per_type=1)

    assert len(chosen) == len({i.type for i in library.test})
    assert select_items(library, "dev", pilot=False, per_type=2) == list(library.dev)
    assert len(select_items(library, "both", pilot=False, per_type=2)) == 11
