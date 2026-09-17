"""`results/run_metadata.json`: exactly how a run was produced."""

import os
import platform
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from lab import __version__
from lab.config import ExperimentConfig
from lab.raw_log import RunRecord
from lab.runner import RunSummary

SDK_PACKAGES = ("openai", "anthropic", "google-genai")


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
    model_config = ConfigDict(frozen=True)

    planned: int
    already_complete: int
    cached: int
    made: int
    failed: int


class RunMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment: str
    started_utc: str
    ended_utc: str
    git: GitState
    harness_version: str
    python_version: str
    sdk_versions: dict[str, str | None]
    models: list[ModelRun]
    config: dict[str, Any]
    datasets: list[DatasetSource]
    counts: CallCounts


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
    status = git("status", "--porcelain")
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
) -> RunMetadata:
    return RunMetadata(
        experiment=config.experiment,
        started_utc=started_utc,
        ended_utc=ended_utc,
        git=git(repo_dir),
        harness_version=__version__,
        python_version=platform.python_version(),
        sdk_versions=_sdk_versions(),
        models=_models(config, records),
        config=config.model_dump(mode="json"),
        datasets=list(datasets),
        counts=CallCounts(
            planned=summary.planned,
            already_complete=summary.already_complete,
            cached=summary.cached,
            made=summary.made,
            failed=summary.failed,
        ),
    )


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
