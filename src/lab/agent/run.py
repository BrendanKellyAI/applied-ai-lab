"""Running an agent experiment: every arm over every case, then scores and a summary per arm.

Results go to `<config folder>/results/<arm>/`: `runs.jsonl` (one trajectory per case and
repeat), `scores.jsonl` and `summary.json`. Model calls are cached, so a rerun is free.
"""

import json
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from lab.agent.caller import ModelCaller
from lab.agent.case_model import CaseFacts
from lab.agent.config import AgentExperiment, Arm
from lab.agent.kb import CORPUS, KeywordKB, KnowledgeBase, ReferenceKB
from lab.agent.loop import CaseRun, run_case
from lab.agent.score import CaseScore, score_case, summarise

CASES_DIR = CORPUS.parent / "halvard-cases" / "cases"


@dataclass(frozen=True)
class LoadedCase:
    facts: CaseFacts
    message: str


def load_cases(
    names: Sequence[str], case_ids: Sequence[str] = (), cases_dir: Path = CASES_DIR
) -> list[LoadedCase]:
    loaded = []
    for name in names:
        for line in (cases_dir / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            message = row.pop("message")
            for extra in ("attempt", "label_round"):
                row.pop(extra, None)
            loaded.append(LoadedCase(CaseFacts.model_validate(row), message))
    if case_ids:
        wanted = set(case_ids)
        loaded = [c for c in loaded if c.facts.case_id in wanted]
    return loaded


def knowledge_base(arm: Arm, caller: ModelCaller, cache_root: Path, folder: Path) -> KnowledgeBase:
    if arm.knowledge_base == "keyword":
        return KeywordKB()
    from lab.config import ProviderLimits
    from lab.runner import Runner

    runner = Runner(
        providers=caller.providers,
        cache=caller.cache,
        limits={name: ProviderLimits(max_concurrency=1) for name in caller.providers},
    )
    return ReferenceKB(runner=runner, cache_root=cache_root, folder=folder)


def run_arm(
    experiment: AgentExperiment,
    arm: Arm,
    cases: Sequence[LoadedCase],
    caller: ModelCaller,
    kb: KnowledgeBase,
    results: Path,
) -> dict[str, object]:
    folder = results / arm.name
    folder.mkdir(parents=True, exist_ok=True)
    jobs = [(case, repeat) for repeat in range(experiment.repeats) for case in cases]

    def one(job: tuple[LoadedCase, int]) -> tuple[CaseRun, CaseScore]:
        case, repeat = job
        run = run_case(case.facts, case.message, arm, caller, kb, repeat=repeat)
        return run, score_case(case.facts, run)

    with ThreadPoolExecutor(max_workers=experiment.concurrency) as pool:
        outcomes = list(pool.map(one, jobs))
    _write_lines(folder / "runs.jsonl", [r.model_dump_json() for r, _ in outcomes])
    _write_lines(folder / "scores.jsonl", [s.model_dump_json() for _, s in outcomes])
    summary = {
        "arm": arm.name,
        "repeats": experiment.repeats,
        **summarise([s for _, s in outcomes]),
    }
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    return summary


def _write_lines(path: Path, lines: Sequence[str]) -> None:
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")


def run_experiment(
    experiment: AgentExperiment,
    caller: ModelCaller,
    results: Path,
    cache_root: Path,
    *,
    cases_dir: Path = CASES_DIR,
    keyword_only: bool = False,
) -> list[dict[str, object]]:
    cases = load_cases(experiment.cases, experiment.case_ids, cases_dir)
    summaries = []
    for arm in experiment.arms:
        if keyword_only:
            kb: KnowledgeBase = KeywordKB()
        else:
            kb = knowledge_base(arm, caller, cache_root, results / arm.name)
        summaries.append(run_arm(experiment, arm, cases, caller, kb, results))
    return summaries
