"""`results/run_metadata.json`: exactly how a set of results was produced.

A run is often finished in more than one pass: a pilot, the full run, then a retry of calls that
hit a rate limit. The metadata describes the results folder as a whole, from the first pass to
the last, and lists every pass with its own commit, filters, and counts. Writing only the latest
pass would publish a retry of three calls as if it were the whole experiment.
"""

import logging
import os
import platform
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from lab import __version__
from lab.config import ExperimentConfig
from lab.raw_log import RunRecord
from lab.runner import RunSummary

SDK_PACKAGES = ("openai", "anthropic", "google-genai")
# A run's own output is not a change to the code or config that produced it, so results folders
# never make the tree count as dirty. Without this, the first run of every experiment would be
# recorded as dirty, because its results are not committed yet.
RESULTS_PATHSPECS = (
    ":(exclude,glob)field-notes/*/results/**",
    ":(exclude,glob)field-notes/*/results-fresh/**",
)

logger = logging.getLogger(__name__)


class GitState(BaseModel):
    model_config = ConfigDict(frozen=True)

    commit: str | None
    dirty: bool | None


class DatasetSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: str | None = None
    licence: str
    url: str | None = None
    checksum: str | None = None


class ModelRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    provider: str
    model_requested: str
    model_versions_returned: list[str]


class CallCounts(BaseModel):
    """What one pass did."""

    model_config = ConfigDict(frozen=True)

    planned: int
    already_complete: int
    cached: int
    made: int
    failed: int


class RunPass(BaseModel):
    """One `lab run` over this results folder."""

    model_config = ConfigDict(frozen=True)

    started_utc: str
    ended_utc: str
    git: GitState
    pilot: bool
    provider: str | None
    counts: CallCounts


class ResultCounts(BaseModel):
    """The state of the whole grid in this results folder, across every pass."""

    model_config = ConfigDict(frozen=True)

    planned: int
    complete: int
    failed: int
    not_run: int
    # Complete calls whose result was reused from the response cache rather than made anew.
    from_cache: int


class RunMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment: str
    # From the start of the first pass, or the first recorded result if earlier, to the end of
    # the latest pass.
    started_utc: str
    ended_utc: str
    # The latest pass. Every pass's commit is in `passes`.
    git: GitState
    harness_version: str
    python_version: str
    sdk_versions: dict[str, str | None]
    models: list[ModelRun]
    config: dict[str, Any]
    datasets: list[DatasetSource]
    counts: ResultCounts
    passes: list[RunPass]


def git_state(repo_dir: Path, run: Callable[..., Any] = subprocess.run) -> GitState:
    """Commit hash and whether the working tree had uncommitted changes, or unknown."""

    def git(*args: str) -> str | None:
        try:
            completed = run(
                ["git", *args], cwd=repo_dir, capture_output=True, text=True, check=False
            )
        except (FileNotFoundError, OSError):
            return None
        return completed.stdout if completed.returncode == 0 else None

    commit = git("rev-parse", "HEAD")
    if commit is None:
        return GitState(commit=None, dirty=None)
    status = git("status", "--porcelain", "--", ".", *RESULTS_PATHSPECS)
    return GitState(commit=commit.strip(), dirty=None if status is None else bool(status.strip()))


def _sdk_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in SDK_PACKAGES:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return versions


def _models(config: ExperimentConfig, records: Sequence[RunRecord]) -> list[ModelRun]:
    returned: dict[str, set[str]] = {}
    for record in records:
        if record.result is not None:
            returned.setdefault(record.model_label, set()).add(record.result.model_returned)
    return [
        ModelRun(
            label=model.display_label,
            provider=model.provider,
            model_requested=model.model,
            model_versions_returned=sorted(returned.get(model.display_label, set())),
        )
        for model in config.models
    ]


def _result_counts(planned_ids: Sequence[str], records: Sequence[RunRecord]) -> ResultCounts:
    # A call that succeeded on any pass is complete, whatever failures came before or after it.
    succeeded = {record.call_id: record for record in records if record.result is not None}
    attempted = {record.call_id for record in records}
    planned = list(dict.fromkeys(planned_ids))
    complete = [call_id for call_id in planned if call_id in succeeded]
    failed = [call_id for call_id in planned if call_id in attempted and call_id not in succeeded]
    return ResultCounts(
        planned=len(planned),
        complete=len(complete),
        failed=len(failed),
        not_run=len(planned) - len(complete) - len(failed),
        from_cache=sum(1 for call_id in complete if succeeded[call_id].source == "cache"),
    )


def build_metadata(
    *,
    config: ExperimentConfig,
    summary: RunSummary,
    records: Sequence[RunRecord],
    started_utc: str,
    ended_utc: str,
    datasets: Sequence[DatasetSource],
    repo_dir: Path,
    git: Callable[[Path], GitState] = git_state,
    planned_ids: Sequence[str] | None = None,
    previous: "RunMetadata | None" = None,
    pilot: bool = False,
    provider: str | None = None,
) -> RunMetadata:
    """Metadata for the results folder, adding this pass to any earlier ones.

    `planned_ids` is the whole grid, not the calls this pass selected, so a pilot or a
    one-provider retry is never reported as the size of the experiment.
    """
    state = git(repo_dir)
    this_pass = RunPass(
        started_utc=started_utc,
        ended_utc=ended_utc,
        git=state,
        pilot=pilot,
        provider=provider,
        counts=CallCounts(
            planned=summary.planned,
            already_complete=summary.already_complete,
            cached=summary.cached,
            made=summary.made,
            failed=summary.failed,
        ),
    )
    passes = [*(previous.passes if previous else []), this_pass]
    # ISO 8601 UTC timestamps sort as text. The first recorded result covers passes made before
    # the metadata kept a history.
    starts = [passes[0].started_utc, *(record.recorded_utc for record in records)]
    ids = planned_ids if planned_ids is not None else [record.call_id for record in records]
    return RunMetadata(
        experiment=config.experiment,
        started_utc=min(starts),
        ended_utc=ended_utc,
        git=state,
        harness_version=__version__,
        python_version=platform.python_version(),
        sdk_versions=_sdk_versions(),
        models=_models(config, records),
        config=config.model_dump(mode="json"),
        datasets=list(datasets),
        counts=_result_counts(ids, records),
        passes=passes,
    )


def read_metadata(path: Path, experiment: str) -> RunMetadata | None:
    """Earlier metadata for this results folder, or None if there is none that can be used.

    Metadata written before passes were kept, or for another experiment, starts a fresh history
    rather than failing the run.
    """
    if not path.exists():
        return None
    try:
        found = RunMetadata.model_validate_json(path.read_text(encoding="utf-8"))
    except (ValidationError, OSError, UnicodeDecodeError):
        logger.warning("Starting a new pass history: %s is from an older format", path)
        return None
    return found if found.experiment == experiment else None


def write_metadata(path: Path, metadata: RunMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(metadata.model_dump_json(indent=2) + "\n")
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
