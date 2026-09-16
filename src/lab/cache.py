"""On-disk response cache, so analysis never pays for the same tokens twice."""

import logging
import os
import tempfile
import threading
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from lab.providers.base import GenerationRequest, GenerationResult, request_hash

logger = logging.getLogger(__name__)


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
                os.replace(temp_name, path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
