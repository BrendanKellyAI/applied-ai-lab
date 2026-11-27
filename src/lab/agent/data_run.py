"""The paid case data step, end to end: budget check, messages, label checks, output files."""

import json
from collections.abc import Mapping
from pathlib import Path

from lab.agent.build import load_facts
from lab.agent.data_estimate import estimate
from lab.agent.finalise import build_log, review_list, review_markdown, write_case_files
from lab.agent.write_messages import write_messages
from lab.cache import ResponseCache
from lab.config import ProviderLimits
from lab.prices import PricesFile
from lab.providers.base import Provider
from lab.runner import Runner

BUDGET_KEY = "s5-case-data"
# Moderate pacing: each stage of about 730 calls takes a few minutes.
LIMITS = ProviderLimits(requests_per_minute=120, max_concurrency=6)


class BudgetRefused(Exception):
    """No approved budget, or the estimate's ceiling is above it."""


def check_budget(prices: PricesFile | None, ceiling: float) -> None:
    budget = (prices.budgets or {}).get(BUDGET_KEY) if prices else None
    if budget is None or ceiling > budget:
        raise BudgetRefused(
            f"set budgets.{BUDGET_KEY} in prices.local.yaml once approved (ceiling {ceiling:.2f})"
        )


def run_case_data(
    *,
    cases_dir: Path,
    review_path: Path,
    prices: PricesFile | None,
    providers: Mapping[str, Provider],
    cache_dir: Path,
    retry_discards: bool = False,
) -> dict[str, object]:
    """Write and check every case; or, with `retry_discards`, only the cases the last run
    discarded, keeping every case it accepted with the label it agreed."""
    files = {
        p.name.removesuffix(".facts.jsonl"): load_facts(p)
        for p in sorted(cases_dir.glob("*.facts.jsonl"))
    }
    cases = [c for group in files.values() for c in group]
    check_budget(prices, sum(s.cost(prices, s.ceiling_output) or 0 for s in estimate(cases)))
    runner = Runner(
        providers=providers,
        cache=ResponseCache(cache_dir),
        limits={name: LIMITS for name in providers},
    )
    kept = _accepted_before(cases_dir, files) if retry_discards else {}
    todo = [c for c in cases if c.case_id not in kept]
    report = write_messages(todo, runner, cache_dir / "s5-case-data")
    label_round = 2 if retry_discards else 1
    for entry in report.accepted.values():
        entry["label_round"] = label_round
    report.accepted.update(kept)
    written = write_case_files(files, report, cases_dir)
    log = build_log(files, report, written)
    _write(cases_dir.parent / "build_log.json", json.dumps(log, indent=2))
    _write(
        review_path, review_markdown(review_list(files["test"], report.accepted), report.accepted)
    )
    return log


def _accepted_before(cases_dir: Path, files: dict[str, list]) -> dict[str, dict[str, object]]:
    """Cases an earlier run accepted, with their message, attempt and label round."""
    kept: dict[str, dict[str, object]] = {}
    for name in files:
        path = cases_dir / f"{name}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            kept[row["case_id"]] = {
                "message": row["message"],
                "attempt": row["attempt"],
                "label_round": row.get("label_round", 1),
            }
    return kept


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
