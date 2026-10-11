"""The model calls of a run, sent in waves through the harness runner.

Each wave is a list of PlannedCalls, so it gets the harness's checks before sending, retries,
resume, raw log and cache. Request metadata is left out of the request hash, so the same
prompt to the same model is served from the cache in any episode.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lab.plan import PlannedCall, make_call_id
from lab.providers.base import GenerationRequest, GenerationResult
from lab.rag.chunk import Chunk
from lab.rag.config import ModelSpec
from lab.rag.corpus import Item
from lab.rag.judge import (
    JudgeParseError,
    Verdict,
    judge_instructions,
    judge_prompt,
    parse_verdict,
    retry_prompt,
)
from lab.rag.retrieve import Retrieval
from lab.raw_log import latest_successful, load_records
from lab.runner import Runner, RunSummary


class Judged(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict: Verdict | None
    result: GenerationResult | None
    retried: bool
    error: str | None


def request_for(
    spec: ModelSpec, *, system: str, prompt: str, episode: str, stage: str
) -> GenerationRequest:
    return GenerationRequest(
        provider=spec.provider,
        model=spec.model,
        system=system,
        prompt=prompt,
        max_output_tokens=spec.max_output_tokens,
        temperature=None,
        reasoning=spec.reasoning,
        metadata={"experiment": episode, "stage": stage},
    )


def planned(request: GenerationRequest, *, stage: str, item_id: str, condition: str) -> PlannedCall:
    cell = {"item": item_id, "condition": condition}
    return PlannedCall(
        call_id=make_call_id(model_label=request.model, mode=stage, cell=cell),
        model_label=request.model,
        mode=stage,
        cell=cell,
        request=request,
    )


def run_wave(
    runner: Runner, calls: Sequence[PlannedCall], raw_path: Path
) -> tuple[dict[str, GenerationResult], RunSummary]:
    """Send a wave and return each item's successful result, keyed by item id."""
    summary = runner.run(calls, raw_path)
    latest = latest_successful(load_records(raw_path))
    results = {}
    for call in calls:
        record = latest.get(call.call_id)
        if record is not None and record.result is not None:
            results[str(call.cell["item"])] = record.result
    return results, summary


def answer_calls(
    items: Sequence[Item],
    retrievals: Mapping[str, Retrieval],
    spec: ModelSpec,
    *,
    episode: str,
    condition: str,
) -> list[PlannedCall]:
    return [
        planned(
            request_for(
                spec,
                system=retrievals[item.id].prompt.system,
                prompt=retrievals[item.id].prompt.prompt,
                episode=episode,
                stage="answer",
            ),
            stage="answer",
            item_id=item.id,
            condition=condition,
        )
        for item in items
    ]


def judge_prompts(
    items: Sequence[Item],
    retrievals: Mapping[str, Retrieval],
    answers: Mapping[str, GenerationResult],
    chunks_by_id: Mapping[str, Chunk],
) -> dict[str, str]:
    """The judge prompt for every item that has an answer."""
    return {
        item.id: judge_prompt(
            item,
            [chunks_by_id[c] for c in retrievals[item.id].prompt.chunk_ids],
            answers[item.id].text,
        )
        for item in items
        if item.id in answers
    }


def judge(
    runner: Runner,
    prompts: Mapping[str, str],
    spec: ModelSpec,
    *,
    episode: str,
    condition: str,
    folder: Path,
) -> tuple[dict[str, Judged], list[RunSummary]]:
    """Judge every answer. A reply that is not a valid verdict is asked again once, with the
    error; if that fails too, the verdict is None and the error is kept."""
    first, first_summary = run_wave(
        runner, _judge_calls(prompts, spec, "judge", episode, condition), folder / "raw-judge.jsonl"
    )
    judged: dict[str, Judged] = {}
    retries: dict[str, str] = {}
    for item_id, result in first.items():
        try:
            judged[item_id] = Judged(
                verdict=parse_verdict(result.text), result=result, retried=False, error=None
            )
        except JudgeParseError as exc:
            retries[item_id] = retry_prompt(prompts[item_id], str(exc))
    summaries = [first_summary]
    if retries:
        second, second_summary = run_wave(
            runner,
            _judge_calls(retries, spec, "judge-retry", episode, condition),
            folder / "raw-judge-retry.jsonl",
        )
        summaries.append(second_summary)
        for item_id in retries:
            judged[item_id] = _parse_retry(second.get(item_id))
    return judged, summaries


def _parse_retry(result: GenerationResult | None) -> Judged:
    if result is None:
        return Judged(verdict=None, result=None, retried=True, error="judge call failed")
    try:
        return Judged(verdict=parse_verdict(result.text), result=result, retried=True, error=None)
    except JudgeParseError as exc:
        return Judged(verdict=None, result=result, retried=True, error=f"unparsed: {exc}")


def _judge_calls(
    prompts: Mapping[str, str], spec: ModelSpec, stage: str, episode: str, condition: str
) -> list[PlannedCall]:
    return [
        planned(
            request_for(
                spec, system=judge_instructions(), prompt=prompt, episode=episode, stage=stage
            ),
            stage=stage,
            item_id=item_id,
            condition=condition,
        )
        for item_id, prompt in prompts.items()
    ]
