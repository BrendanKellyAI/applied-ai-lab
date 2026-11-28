"""Shared analysis for Season 5 episodes: resolved counts with intervals, paired comparisons,
billed tokens and cost ratios, and run to run variation. No model calls.

Billed tokens come from the response cache: each turn's request hash finds its result, which
records how much input the provider billed at the cached rate.
"""

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from lab.agent.loop import CaseRun
from lab.agent.score import CaseScore
from lab.rag.compare import exact_mcnemar
from lab.scoring import wilson_interval


def load_scores(folder: Path) -> list[CaseScore]:
    return [
        CaseScore.model_validate_json(line)
        for line in (folder / "scores.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def load_runs(folder: Path) -> list[CaseRun]:
    return [
        CaseRun.model_validate_json(line)
        for line in (folder / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def resolved(scores: Sequence[CaseScore], kinds: Iterable[str] | None = None) -> dict[str, object]:
    wanted = set(kinds) if kinds is not None else None
    chosen = [s for s in scores if wanted is None or s.kind in wanted]
    hits = sum(s.resolved for s in chosen)
    _, low, high = wilson_interval(hits, len(chosen)) if chosen else (0.0, 0.0, 0.0)
    return {"resolved": hits, "of": len(chosen), "low": round(low, 4), "high": round(high, 4)}


def by_kind(scores: Sequence[CaseScore]) -> dict[str, dict[str, object]]:
    return {kind: resolved(scores, [kind]) for kind in sorted({s.kind for s in scores})}


def paired(
    a: Sequence[CaseScore], b: Sequence[CaseScore], kinds: Iterable[str] | None = None
) -> dict[str, object]:
    """Exact McNemar on the cases both arms ran, with the flips each way."""
    wanted = set(kinds) if kinds is not None else None
    b_by = {s.case_id: s for s in b}
    pairs = [
        (s, b_by[s.case_id])
        for s in a
        if s.case_id in b_by and (wanted is None or s.kind in wanted)
    ]
    only_a = [x.case_id for x, y in pairs if x.resolved and not y.resolved]
    only_b = [x.case_id for x, y in pairs if y.resolved and not x.resolved]
    return {
        "cases": len(pairs),
        "a_resolved": sum(x.resolved for x, _ in pairs),
        "b_resolved": sum(y.resolved for _, y in pairs),
        "only_a": only_a,
        "only_b": only_b,
        "p": round(exact_mcnemar(len(only_a), len(only_b)), 6),
    }


@dataclass(frozen=True)
class Billed:
    calls: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int

    def cost(self, price_in: float, price_cached: float, price_out: float) -> float:
        fresh = self.input_tokens - self.cached_input_tokens
        return (
            fresh * price_in
            + self.cached_input_tokens * price_cached
            + self.output_tokens * price_out
        ) / 1e6


def billed(runs: Sequence[CaseRun], cache_root: Path, provider: str = "openai") -> Billed:
    calls = input_tokens = cached = output = 0
    for run in runs:
        for turn in run.turns:
            path = cache_root / provider / turn.request_hash[:2] / f"{turn.request_hash}.json"
            result = json.loads(path.read_text(encoding="utf-8"))["result"] if path.exists() else {}
            calls += 1
            input_tokens += turn.input_tokens
            cached += int(result.get("cached_input_tokens") or 0)
            output += turn.output_tokens
    return Billed(calls, input_tokens, cached, output)


def variation(scores: Sequence[CaseScore]) -> dict[str, object]:
    """Across repeated runs of the same cases: resolved per run, and cases whose result changed."""
    per_case: dict[str, set[bool]] = defaultdict(set)
    totals: Counter[int] = Counter()
    for score in scores:
        per_case[score.case_id].add(score.resolved)
        totals[score.repeat] += score.resolved
    changed = sorted(case for case, results in per_case.items() if len(results) > 1)
    return {
        "cases": len(per_case),
        "resolved_by_run": [totals[r] for r in sorted(totals)],
        "cases_that_changed": len(changed),
        "changed": changed,
    }
