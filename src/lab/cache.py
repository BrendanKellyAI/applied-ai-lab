"""On-disk response cache, so analysis never pays for the same tokens twice."""

import logging
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from lab.providers.base import GenerationRequest, GenerationResult, request_hash

logger = logging.getLogger(__name__)

# Windows refuses a rename while another process, such as a virus scanner or the search indexer,
# briefly holds the file open. Such a hold clears within moments, so the rename is retried.
REPLACE_ATTEMPTS = 6
REPLACE_WAIT_SECONDS = 0.05


def _replace(source: str, target: Path, sleep=time.sleep) -> None:
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            sleep(REPLACE_WAIT_SECONDS * 2**attempt)


def _git_common_dir(start: Path) -> Path | None:
    """The .git directory shared by every checkout of the repository, or None outside git."""
    try:
        found = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=start,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(found) if found else None


def shared_cache_root(start: Path) -> Path:
    """The main checkout's .cache, also when run from a git worktree.

    Every checkout then shares one cache, so a run started from a worktree never pays again
    for a call another checkout already made.
    """
    common = _git_common_dir(start)
    return (common.parent if common is not None else start) / ".cache"


class _CacheEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request: GenerationRequest
    result: GenerationResult


class ResponseCache:
    """One JSON file per successful result under `<root>/<provider>/<first two hash chars>/`."""

    def __init__(self, root: Path) -> None:
        self._root = root
        # Serialises renames: Windows refuses concurrent replaces of the same file.
        self._write_lock = threading.Lock()

    def path_for(self, request: GenerationRequest) -> Path:
        digest = request_hash(request)
        return self._root / request.provider / digest[:2] / f"{digest}.json"

    def get(self, request: GenerationRequest) -> GenerationResult | None:
        path = self.path_for(request)
        if not path.exists():
            return None
        try:
            entry = _CacheEntry.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as exc:
            logger.warning("Ignoring unreadable cache entry %s: %s", path, exc)
            return None
        if entry.result.request_hash != request_hash(request):
            logger.warning("Ignoring cache entry %s with a mismatched hash", path)
            return None
        return entry.result

    def put(self, request: GenerationRequest, result: GenerationResult) -> None:
        if result.error is not None:
            raise ValueError("Failed results are not cached")
        if result.request_hash != request_hash(request):
            raise ValueError("Result hash does not match the request being cached")
        path = self.path_for(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _CacheEntry(request=request, result=result).model_dump_json(indent=2)
        # Write to a temporary file and rename, so a crash never leaves a half-written entry.
        descriptor, temp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
            with self._write_lock:
                _replace(temp_name, path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
