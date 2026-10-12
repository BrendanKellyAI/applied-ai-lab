"""Run one condition of an episode end to end, score it, and write its log and summary.

Waves, in order: embeddings, then search, filter, rerank and prompt (all local), then answer
calls, then judge calls. A search-only condition stops before the answer wave and costs only
embeddings.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lab.cache import shared_cache_root
from lab.providers.base import GenerationResult
from lab.rag.chunk import Chunk
from lab.rag.config import Episode, ResolvedCondition, config_id
from lab.rag.corpus import Item, Library, Span
from lab.rag.embed import Embedder
from lab.rag.index import Index
from lab.rag.log import (
    LOG_DEPTH,
    ItemLog,
    ModelCall,
    RankedChunk,
    RemovedChunk,
    SpanTrace,
    write_log,
)
from lab.rag.rerank import make_reorder
from lab.rag.retrieve import Retrieval, build, retrieve
from lab.rag.rewrite import queries_for_all
from lab.rag.score import (
    ItemScore,
    by_type,
    code_check,
    cut_spans,
    distractor_above,
    evidence_rank,
    first_lost_stage,
    holds,
    leaks,
    season_numbers,
    span_rank,
)
from lab.rag.search import Hit
from lab.rag.waves import Judged, answer_calls, judge, judge_prompts, run_wave
from lab.runner import Runner, RunSummary


@dataclass(frozen=True)
class RunContext:
    episode: Episode
    library: Library
    embedder: Embedder
    runner: Runner | None
    results: Path
    # Where local caches other than the response cache live (the reranker's scores).
    cache_root: Path | None = None


def select_items(library: Library, which: str, *, pilot: bool, per_type: int) -> list[Item]:
    """The items a run uses. A pilot takes the first `per_type` of each type, by id."""
    pool = {"test": library.test, "dev": library.dev, "both": library.test + library.dev}[which]
    if not pilot:
        return list(pool)
    chosen: list[Item] = []
    for item_type in sorted({item.type for item in pool}):
        of_type = sorted((i for i in pool if i.type == item_type), key=lambda i: i.id)
        chosen.extend(of_type[:per_type])
    return chosen


def run_condition(
    context: RunContext, condition: ResolvedCondition, items: Sequence[Item]
) -> dict[str, Any]:
    """Run, score and log one condition; return its summary, also written to summary.json."""
    folder = context.results / condition.name
    pipeline = condition.pipeline
    tokens_before = context.embedder.tokens_reported
    index = build(context.library, pipeline, context.embedder)
    episode_name = context.episode.config.episode
    queries, rewrite_runs = queries_for_all(
        items,
        pipeline.rewrite,
        context.runner,
        episode=episode_name,
        condition=condition.name,
        folder=folder,
    )
    reorder, rerank_stats = make_reorder(
        pipeline.rerank,
        runner=context.runner,
        cache_root=context.cache_root or shared_cache_root(context.results),
        index=index,
        episode=episode_name,
        condition=condition.name,
        folder=folder,
    )
    retrievals = retrieve(items, index, pipeline, context.embedder, queries, reorder)

    answers: dict[str, GenerationResult] = {}
    judged: dict[str, Judged] = {}
    summaries: dict[str, list[RunSummary]] = {}
    if condition.measure == "full":
        if context.runner is None:
            raise RuntimeError("A full run needs a runner with providers for its model calls")
        episode = context.episode.config.episode
        calls = answer_calls(
            items, retrievals, pipeline.answer, episode=episode, condition=condition.name
        )
        answers, answer_summary = run_wave(context.runner, calls, folder / "raw-answer.jsonl")
        chunks_by_id = {chunk.chunk_id: chunk for chunk in index.chunks}
        prompts = judge_prompts(items, retrievals, answers, chunks_by_id)
        judged, judge_summaries = judge(
            context.runner,
            prompts,
            pipeline.judge,
            episode=episode,
            condition=condition.name,
            folder=folder,
        )
        summaries = {"answer": [answer_summary], "judge": judge_summaries}
    if rewrite_runs:
        summaries = {**summaries, "rewrite": rewrite_runs}
    if "summary" in rerank_stats:
        summaries = {**summaries, "rerank": [rerank_stats.pop("summary")]}

    logs = [
        _item_log(
            item,
            retrievals[item.id],
            index,
            condition,
            pipeline.prompt.k,
            answers.get(item.id),
            judged.get(item.id),
        )
        for item in items
    ]
    write_log(folder / "log.jsonl", logs)
    summary = _summary(
        context,
        condition,
        logs,
        pipeline.prompt.k,
        summaries,
        context.embedder.tokens_reported - tokens_before,
    )
    if rerank_stats:
        summary["rerank_timing"] = rerank_stats
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return summary


def _chunks(index: Index, hits: Sequence[Hit]) -> list[Chunk]:
    return [index.chunks[hit.index] for hit in hits]


def _ranked(index: Index, hits: Sequence[Hit]) -> tuple[RankedChunk, ...]:
    return tuple(
        RankedChunk(chunk_id=index.chunks[h.index].chunk_id, score=round(h.score, 6))
        for h in hits[:LOG_DEPTH]
    )


def _item_log(
    item: Item,
    retrieval: Retrieval,
    index: Index,
    condition: ResolvedCondition,
    k: int,
    answer: GenerationResult | None,
    judged: Judged | None,
) -> ItemLog:
    searched = _chunks(index, retrieval.searched)
    filtered = _chunks(index, retrieval.filtered)
    ranked = _chunks(index, retrieval.ranked)
    by_id = {chunk.chunk_id: chunk for chunk in index.chunks}
    prompt = [by_id[c] for c in retrieval.prompt.chunk_ids]
    verdict = judged.verdict if judged else None
    trace = {
        "cut": bool(cut_spans(item.evidence, index.chunks)),
        "searched": evidence_rank(item, searched),
        "filtered": evidence_rank(item, filtered),
        "reranked": evidence_rank(item, ranked),
    }
    return ItemLog(
        item_id=item.id,
        type=item.type,
        asker=item.asker,
        answerable=item.answerable,
        condition=condition.name,
        config_id=config_id(condition.pipeline),
        queries=retrieval.queries,
        searched=_ranked(index, retrieval.searched),
        removed=tuple(
            RemovedChunk(chunk_id=index.chunks[r.index].chunk_id, reason=r.reason)
            for r in retrieval.removed
        ),
        ranked=_ranked(index, retrieval.ranked),
        prompt_chunks=retrieval.prompt.chunk_ids,
        spans=tuple(_span_traces(item, index, searched, filtered, ranked, prompt)),
        evidence_rank=trace["reranked"],
        distractor_above=distractor_above(item, ranked),
        leaks=leaks(item.asker, prompt),
        answer=_call(answer),
        judge=_call(judged.result if judged else None),
        verdict=verdict,
        judge_error=judged.error if judged else None,
        code_check=code_check(item, answer.text) if answer else None,
        lost_at=first_lost_stage(trace, k, verdict) if item.answerable else None,
    )


def _span_traces(
    item: Item,
    index: Index,
    searched: Sequence[Chunk],
    filtered: Sequence[Chunk],
    ranked: Sequence[Chunk],
    prompt: Sequence[Chunk],
) -> list[SpanTrace]:
    kinds: list[tuple[str, tuple[Span, ...]]] = [
        ("evidence", item.evidence),
        ("distractor", item.distractor_spans),
        ("stale", item.stale_spans),
        ("restricted", item.restricted_spans),
    ]
    return [
        SpanTrace(
            kind=kind,
            span=span,
            cut=bool(cut_spans((span,), index.chunks)),
            searched=span_rank(span, searched),
            filtered=span_rank(span, filtered),
            reranked=span_rank(span, ranked),
            in_prompt=any(holds(chunk, span) for chunk in prompt),
        )
        for kind, spans in kinds
        for span in spans
    ]


def _call(result: GenerationResult | None) -> ModelCall | None:
    if result is None:
        return None
    return ModelCall(
        text=result.text,
        model_returned=result.model_returned,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        reasoning_tokens=result.reasoning_tokens,
        finish_reason=result.finish_reason,
    )


def _summary(
    context: RunContext,
    condition: ResolvedCondition,
    logs: Sequence[ItemLog],
    k: int,
    summaries: Mapping[str, list[RunSummary]],
    embedding_tokens: int,
) -> dict[str, Any]:
    scores = [
        ItemScore(
            item_id=log.item_id,
            type=log.type,
            asker=log.asker,
            answerable=log.answerable,
            evidence_rank=log.evidence_rank,
            leaks=log.leaks,
            verdict=log.verdict,
        )
        for log in logs
    ]
    full = condition.measure == "full"
    numbers = season_numbers(scores, k).model_dump()
    if not full:
        numbers = {"search": numbers["search"], "leaks": numbers["leaks"]}
    return {
        "episode": context.episode.config.episode,
        "condition": condition.name,
        "measure": condition.measure,
        "config_id": config_id(condition.pipeline),
        "base_id": context.episode.base_id,
        "changed": list(condition.changed),
        "pipeline": condition.pipeline.model_dump(mode="json"),
        "corpus_version": context.library.corpus_version,
        "items": len(logs),
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "numbers": numbers,
        "by_type": {t: n.model_dump() for t, n in by_type(scores, k).items()} if full else {},
        "models_returned": {
            "answer": sorted({log.answer.model_returned for log in logs if log.answer}),
            "judge": sorted({log.judge.model_returned for log in logs if log.judge}),
            "embedding": context.embedder.model_returned,
        },
        "calls": {stage: [_run_summary(s) for s in runs] for stage, runs in summaries.items()},
        "embedding_tokens_reported": embedding_tokens,
        "judge_errors": sorted(log.item_id for log in logs if log.judge_error),
        "code_check_disagrees_with_judge": sorted(
            log.item_id
            for log in logs
            if log.code_check is not None
            and log.verdict is not None
            and log.code_check != log.verdict.correct
        ),
    }


def _run_summary(summary: RunSummary) -> dict[str, Any]:
    return {
        "planned": summary.planned,
        "already_complete": summary.already_complete,
        "cached": summary.cached,
        "made": summary.made,
        "failed": summary.failed,
        "tokens": {name: vars(totals) for name, totals in summary.tokens_by_provider.items()},
    }
