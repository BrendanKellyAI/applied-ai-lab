"""Build Task B: a question and correct answer from one passage, checked by another provider,
then rewritten as a reply in the house style, checked in code and for facts kept.

Every call goes through the harness runner, so it is cached and logged, and a rebuild from the
same seeds sends nothing.
"""

import json
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from lab.adapt.build_tasks.checks import ReplyError, parse_object, undash
from lab.adapt.build_tasks.config import SPLITS, Split, TaskBuildConfig
from lab.adapt.build_tasks.passages import (
    NOT_FOUND,
    BSeed,
    b_seed_count,
    draw_b_seeds,
    passages,
    split_passages,
)
from lab.adapt.build_tasks.prompts_b import (
    CHECK_SYSTEM,
    NOT_FOUND_ANSWER,
    QA_SYSTEM,
    REWRITE_SYSTEM,
    facts_prompt,
    qa_prompt,
    rewrite_prompt,
    support_prompt,
)
from lab.adapt.style import RULES, check_reply
from lab.rag.build_corpus.generate import Generated, Task, generate
from lab.rag.config import ModelSpec
from lab.rag.corpus import Library
from lab.rag.waves import planned, request_for, run_wave
from lab.runner import Runner, RunSummary

RETRY_TEMPLATE = "That draft does not meet the brief: {problem} Reply again with the JSON object."
EPISODE = "s4-task-data"
REVIEW_SAMPLE = 20
MAX_QUESTION_WORDS = 70
MAX_ANSWER_WORDS = 90


def plan_b_seeds(config: TaskBuildConfig, library: Library, *, pilot: bool) -> list[BSeed]:
    task = config.task_b
    cuts = split_passages(passages(library), task, config.seed)
    tones = config.task_a.personas.tone
    if pilot:
        return draw_b_seeds("dev", task.pilot_seeds, cuts["dev"], task, tones, config.seed)
    seeds: list[BSeed] = []
    for split in SPLITS:
        n = b_seed_count(task.splits[split], task.overgenerate)
        seeds += draw_b_seeds(split, n, cuts[split], task, tones, config.seed)
    return seeds


def qa_of(text: str) -> tuple[str, str]:
    value = parse_object(text)
    question, answer = value.get("question"), value.get("answer")
    if not isinstance(question, str) or not isinstance(answer, str):
        raise ReplyError('no "question" and "answer" strings')
    return question.strip(), answer.strip()


def reply_of(text: str) -> str:
    value = parse_object(text)
    reply = value.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise ReplyError('no "reply" string')
    return reply.strip()


def check_qa(seed: BSeed, text: str) -> str | None:
    try:
        question, answer = qa_of(text)
    except ReplyError as exc:
        return f"The reply was {exc}."
    if not question or len(question.split()) > MAX_QUESTION_WORDS:
        return f"The question must be one to three sentences, under {MAX_QUESTION_WORDS} words."
    if seed.kind == NOT_FOUND:
        if answer != NOT_FOUND_ANSWER:
            return f'The answer must be exactly: "{NOT_FOUND_ANSWER}"'
        return None
    if not answer or len(answer.split()) > MAX_ANSWER_WORDS:
        return f"The answer must be one to three sentences, under {MAX_ANSWER_WORDS} words."
    return None


def check_rewrite(seed: BSeed, text: str) -> str | None:
    try:
        reply = reply_of(text)
    except ReplyError as exc:
        return f"The reply was {exc}."
    failures = check_reply(reply, seed.source()).failures()
    if failures:
        return "The reply breaks these rules: " + "; ".join(RULES[f] for f in failures) + "."
    return None


def build_task_b(
    runner: Runner,
    config: TaskBuildConfig,
    library: Library,
    style_guide: str,
    folder: Path,
    *,
    pilot: bool,
) -> dict:
    seeds = plan_b_seeds(config, library, pilot=pilot)
    by_id = {s.id: s for s in seeds}
    raw = folder / "raw"
    qa = _generate(runner, config, seeds, QA_SYSTEM, qa_prompt, check_qa, "task-b-qa", raw)
    pairs = {k: qa_of(o.text) for k, o in qa.outcomes.items() if o.text is not None}
    support_texts, support_summary = _check_wave(
        runner,
        config.labeller,
        {k: support_prompt(by_id[k], *pairs[k]) for k in pairs},
        "task-b-support",
        raw,
    )
    supported = {k: v for k, v in pairs.items() if _supported(by_id[k], support_texts.get(k))}
    rewrites = _generate(
        runner,
        config,
        [by_id[k] for k in supported],
        REWRITE_SYSTEM,
        lambda s: rewrite_prompt(s, *supported[s.id], style_guide),
        check_rewrite,
        "task-b-rewrite",
        raw,
    )
    replies = {k: reply_of(o.text) for k, o in rewrites.outcomes.items() if o.text is not None}
    answerable = {k: v for k, v in replies.items() if by_id[k].kind != NOT_FOUND}
    facts_texts, facts_summary = _check_wave(
        runner,
        config.labeller,
        {k: facts_prompt(supported[k][1], v) for k, v in answerable.items()},
        "task-b-facts",
        raw,
    )
    faithful = {
        k: v
        for k, v in replies.items()
        if by_id[k].kind == NOT_FOUND or _facts_kept(facts_texts.get(k))
    }
    kept = _keep(seeds, supported, faithful, config, pilot=pilot)
    _write(folder, kept)
    log = {
        "dataset_version": config.dataset_version,
        "generator": config.generator.model_dump(),
        "checker": config.labeller.model_dump(),
        "seeds": dict(Counter(s.split for s in seeds)),
        "passages": dict(Counter(s.split for s in {s.passage.id: s for s in seeds}.values())),
        "qa_failed": sorted(k for k, o in qa.outcomes.items() if o.text is None),
        "unsupported": sorted(set(pairs) - set(supported)),
        "rewrite_failed": sorted(k for k, o in rewrites.outcomes.items() if o.text is None),
        "facts_not_kept": sorted(set(replies) - set(faithful)),
        "kept": {split: len(rows) for split, rows in kept.items()},
        "not_found_kept": {
            split: sum(r["kind"] == NOT_FOUND for r in rows) for split, rows in kept.items()
        },
        "calls": {
            "qa": [_summary(s) for s in qa.summaries],
            "support": _summary(support_summary),
            "rewrite": [_summary(s) for s in rewrites.summaries],
            "facts": _summary(facts_summary),
        },
    }
    (folder / "build_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    if not pilot:
        write_b_review_sample(folder.parent / "review", kept.get("test", []), config.seed)
    return log


def _generate(
    runner: Runner,
    config: TaskBuildConfig,
    seeds: Sequence[BSeed],
    system: str,
    prompt: Callable[[BSeed], str],
    check: Callable[[BSeed, str], str | None],
    stage: str,
    raw: Path,
) -> Generated:
    by_id = {s.id: s for s in seeds}
    return generate(
        runner,
        [Task(id=s.id, system=system, prompt=prompt(s)) for s in seeds],
        config.generator,
        lambda seed_id, text: check(by_id[seed_id], text),
        stage=stage,
        folder=raw,
        max_attempts=config.max_attempts,
        retry_template=RETRY_TEMPLATE,
    )


def _check_wave(
    runner: Runner, spec: ModelSpec, prompts: Mapping[str, str], stage: str, raw: Path
) -> tuple[dict[str, str], RunSummary]:
    calls = [
        planned(
            request_for(spec, system=CHECK_SYSTEM, prompt=prompt, episode=EPISODE, stage=stage),
            stage=stage,
            item_id=item_id,
            condition="check",
        )
        for item_id, prompt in prompts.items()
    ]
    results, summary = run_wave(runner, calls, raw / f"raw-{stage}.jsonl")
    return {k: r.text for k, r in results.items()}, summary


def _flag(text: str | None, name: str) -> bool | None:
    if text is None:
        return None
    try:
        value = parse_object(text).get(name)
    except ReplyError:
        return None
    return value if isinstance(value, bool) else None


def _supported(seed: BSeed, text: str | None) -> bool:
    if seed.kind == NOT_FOUND:
        return _flag(text, "passage_answers") is False
    return _flag(text, "supported") is True and _flag(text, "answers_question") is True


def _facts_kept(text: str | None) -> bool:
    return _flag(text, "all_facts_kept") is True and _flag(text, "facts_added") is False


def _keep(
    seeds: Sequence[BSeed],
    pairs: Mapping[str, tuple[str, str]],
    replies: Mapping[str, str],
    config: TaskBuildConfig,
    *,
    pilot: bool,
) -> dict[Split, list[dict]]:
    kept: dict[Split, list[dict]] = {}
    seen: set[str] = set()
    for seed in seeds:
        if seed.id not in replies:
            continue
        question, answer = pairs[seed.id]
        key = " ".join(question.lower().split())
        target = config.task_b.pilot_seeds if pilot else config.task_b.splits[seed.split]
        bucket = kept.setdefault(seed.split, [])
        if key in seen or len(bucket) >= target:
            continue
        seen.add(key)
        source = seed.source()
        bucket.append(
            {
                "id": seed.id,
                "question": undash(question),
                "answer": undash(answer),
                "kind": seed.kind,
                "passage_id": seed.passage.id,
                "source": {"kind": source.kind, "name": source.name, "section": source.section},
                "target_reply": undash(replies[seed.id]),
            }
        )
    return kept


def _write(folder: Path, kept: Mapping[Split, list[dict]]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for split, rows in kept.items():
        lines = [json.dumps(row, ensure_ascii=False) for row in rows]
        (folder / f"{split}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary(summary: RunSummary) -> dict:
    return {
        "planned": summary.planned,
        "made": summary.made,
        "cached": summary.cached,
        "failed": summary.failed,
        "tokens": {
            provider: {"input": t.input_tokens, "output": t.output_tokens}
            for provider, t in summary.tokens_by_provider.items()
        },
    }


def write_b_review_sample(review: Path, test: Sequence[dict], seed: int) -> Path:
    """Test items for Brendan's hand check, numbered so he can reply with any wrong ones."""
    sample = random.Random(f"{seed}:review-b").sample(list(test), min(REVIEW_SAMPLE, len(test)))
    lines = [
        "# Task B test items for hand checking",
        "",
        "For each item, check that the answer is right for the question and that the reply keeps "
        "its facts in the house style. Reply with the numbers of any that are wrong, and why.",
        "",
    ]
    for number, row in enumerate(sorted(sample, key=lambda r: r["id"]), start=1):
        lines += [
            f"## {number}. {row['id']} ({row['kind']}, {row['passage_id']})",
            "",
            f"**Question:** {row['question']}",
            "",
            f"**Answer:** {row['answer']}",
            "",
            "**Reply:**",
            "",
            *[f"> {line}" if line else ">" for line in row["target_reply"].splitlines()],
            "",
        ]
    review.mkdir(parents=True, exist_ok=True)
    path = review / "task-b-test-sample.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
