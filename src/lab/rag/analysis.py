"""Reading a run's log back for claims, charts and the scoreboard. Shared by every episode."""

import json
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from lab.rag.corpus import Library, Span
from lab.rag.log import ItemLog, read_log
from lab.rag.score import ItemScore, Proportion, SeasonNumbers, season_numbers
from lab.scoring import contains_match

# Where an answerable item's passage was lost, in pipeline order. "unjudged" has no verdict.
BEFORE_PROMPT = ("chunk", "search", "filter", "rerank")
INSIDE_PROMPT = ("prompt", "answer")
STAGE_ORDER = (*BEFORE_PROMPT, *INSIDE_PROMPT, "unjudged")


def load_condition(results: Path, condition: str) -> tuple[list[ItemLog], dict[str, Any]]:
    folder = results / condition
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    return read_log(folder / "log.jsonl"), summary


def item_scores(logs: Iterable[ItemLog]) -> list[ItemScore]:
    return [
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


def numbers(logs: Sequence[ItemLog], k: int) -> SeasonNumbers:
    return season_numbers(item_scores(logs), k)


def of_type(logs: Iterable[ItemLog], *types: str) -> list[ItemLog]:
    return [log for log in logs if log.type in types]


def recall(logs: Sequence[ItemLog], k: int) -> Proportion:
    hits = sum(1 for log in logs if log.evidence_rank is not None and log.evidence_rank <= k)
    return Proportion.of(hits, len(logs))


def recall_by_type(logs: Sequence[ItemLog], k: int) -> dict[str, Proportion]:
    types = sorted({log.type for log in logs if log.answerable})
    return {t: recall(of_type(logs, t), k) for t in types}


def is_right(log: ItemLog) -> bool:
    return log.verdict is not None and log.verdict.correct and log.verdict.faithful


def is_wrong(log: ItemLog) -> bool:
    """An answerable item with a verdict that is not both correct and faithful."""
    return log.answerable and log.verdict is not None and not is_right(log)


def lost_at_counts(logs: Iterable[ItemLog]) -> Counter:
    """Wrong answerable items by the first stage that lost their passage."""
    return Counter(log.lost_at or "answer" for log in logs if is_wrong(log))


def declined(logs: Sequence[ItemLog]) -> Proportion:
    count = sum(1 for log in logs if log.verdict is not None and log.verdict.declined)
    return Proportion.of(count, len(logs))


def below(a: Proportion, b: Proportion) -> bool:
    """`a` sits below `b`: the intervals do not overlap."""
    return a.high < b.low


def stale_in_prompt(log: ItemLog) -> bool:
    return any(t.kind == "stale" and t.in_prompt for t in log.spans)


def changed_value(current: str, old: str) -> tuple[str, str]:
    """The differing part of two versions of a sentence, widened to whole tokens.

    "The period is 24 months." and "The period is 12 months." give ("24", "12").
    """
    start = 0
    while start < min(len(current), len(old)) and current[start] == old[start]:
        start += 1
    end = 0
    while end < min(len(current), len(old)) - start and current[-1 - end] == old[-1 - end]:
        end += 1

    def widen(text: str) -> str:
        left, right = start, len(text) - end
        while left > 0 and (text[left - 1].isalnum() or text[left - 1] in "£."):
            left -= 1
        while right < len(text) and (text[right].isalnum() or text[right] in "%."):
            right += 1
        return text[left:right].rstrip(".")

    return widen(current), widen(old)


def gives_old_value(answer: str, current: str, old: str) -> bool:
    return contains_match(answer, old) and not contains_match(answer, current)


def version_values(log: ItemLog, library: Library) -> tuple[str, str] | None:
    """The current and old value of a version item, from its evidence and stale spans."""
    spans = {t.kind: t.span for t in log.spans}
    if "evidence" not in spans or "stale" not in spans:
        return None
    return changed_value(span_text(library, spans["evidence"]), span_text(library, spans["stale"]))


def span_text(library: Library, span: Span) -> str:
    return library.span_text(span)


def first(logs: Iterable[ItemLog], rule: Callable[[ItemLog], bool]) -> ItemLog | None:
    """The first log in item id order that meets `rule`."""
    return next((log for log in sorted(logs, key=lambda log: log.item_id) if rule(log)), None)


def evidence_in_prompt(log: ItemLog) -> bool:
    evidence = [t for t in log.spans if t.kind == "evidence"]
    return bool(evidence) and all(t.in_prompt for t in evidence)
