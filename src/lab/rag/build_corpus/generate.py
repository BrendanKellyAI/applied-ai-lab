"""Generation with checks: send every task, check every reply in code, and send each failed
task back with the reason, up to a limit. Each attempt is a wave through the harness runner,
so every call is cached and logged, and a rebuild sends nothing.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.catalogue import fill
from lab.rag.config import ModelSpec
from lab.rag.waves import planned, request_for, run_wave
from lab.runner import Runner, RunSummary

Check = Callable[[str, str], str | None]


class Task(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    prompt: str
    system: str | None = None


class Outcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    text: str | None
    attempts: int
    # The reason each failed attempt was sent back, in order.
    problems: tuple[str, ...]
    model_returned: str | None = None


class Generated(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    outcomes: dict[str, Outcome]
    summaries: tuple[RunSummary, ...]

    def failed(self) -> list[Outcome]:
        return [o for o in self.outcomes.values() if o.text is None]


def generate(
    runner: Runner,
    tasks: Sequence[Task],
    spec: ModelSpec,
    check: Check,
    *,
    stage: str,
    folder: Path,
    max_attempts: int,
    retry_template: str,
) -> Generated:
    """Run `tasks` until each passes `check(task_id, text)` or runs out of attempts."""
    prompts = {task.id: task.prompt for task in tasks}
    systems = {task.id: task.system for task in tasks}
    problems: dict[str, list[str]] = {task.id: [] for task in tasks}
    done: dict[str, Outcome] = {}
    summaries: list[RunSummary] = []
    pending = [task.id for task in tasks]
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        calls = [
            planned(
                request_for(
                    spec, system=systems[i], prompt=prompts[i], episode="halvard", stage=stage
                ),
                stage=stage,
                item_id=i,
                condition=f"attempt-{attempt}",
            )
            for i in pending
        ]
        results, summary = run_wave(runner, calls, folder / f"raw-{stage}-{attempt}.jsonl")
        summaries.append(summary)
        still = []
        for task_id in pending:
            result = results.get(task_id)
            problem = "The call failed." if result is None else check(task_id, result.text)
            if problem is None:
                done[task_id] = Outcome(
                    id=task_id,
                    text=result.text.strip(),
                    attempts=attempt,
                    problems=tuple(problems[task_id]),
                    model_returned=result.model_returned,
                )
                continue
            problems[task_id].append(problem)
            draft = "" if result is None else result.text.strip()
            prompts[task_id] = f"{_base(prompts[task_id])}\n\nYour draft:\n{draft}\n\n" + fill(
                retry_template, problem=problem
            )
            still.append(task_id)
        pending = still
    for task_id in pending:
        done[task_id] = Outcome(
            id=task_id, text=None, attempts=max_attempts, problems=tuple(problems[task_id])
        )
    return Generated(outcomes=done, summaries=tuple(summaries))


_DRAFT_MARK = "\n\nYour draft:\n"


def _base(prompt: str) -> str:
    """The original prompt, without any earlier draft and retry note."""
    return prompt.split(_DRAFT_MARK, 1)[0]
