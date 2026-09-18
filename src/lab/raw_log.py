"""The append-only results log, `results/raw.jsonl`, that makes runs resumable."""

import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import IO, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from lab.config import CellValue
from lab.plan import PlannedCall
from lab.providers.base import GenerationResult, request_hash

logger = logging.getLogger(__name__)


def _now_utc() -> str:
    return datetime.now(UTC).isoformat()


class RunRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str
    request_hash: str
    model_label: str
    mode: str
    cell: dict[str, CellValue]
    source: Literal["api", "cache"]
    attempts: int
    result: GenerationResult | None
    error: str | None
    recorded_utc: str = Field(default_factory=_now_utc)

    @classmethod
    def for_call(
        cls,
        call: PlannedCall,
        *,
        source: Literal["api", "cache"],
        attempts: int,
        result: GenerationResult | None = None,
        error: str | None = None,
    ) -> Self:
        return cls(
            call_id=call.call_id,
            request_hash=request_hash(call.request),
            model_label=call.model_label,
            mode=call.mode,
            cell=call.cell,
            source=source,
            attempts=attempts,
            result=result,
            error=error,
        )


class RawLogWriter:
    """Thread-safe appender. Each record is flushed to disk as soon as it is written."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._handle: IO[str] | None = None

    def __enter__(self) -> Self:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        needs_newline = _ends_without_newline(self._path)
        self._handle = self._path.open("a", encoding="utf-8", newline="\n")
        if needs_newline:
            self._handle.write("\n")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def append(self, record: RunRecord) -> None:
        if self._handle is None:
            raise RuntimeError("RawLogWriter must be used as a context manager")
        line = record.model_dump_json() + "\n"
        with self._lock:
            self._handle.write(line)
            self._handle.flush()
            os.fsync(self._handle.fileno())


def _ends_without_newline(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    with path.open("rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) != b"\n"


def load_records(path: Path) -> list[RunRecord]:
    """Load every readable record. A line cut short by an interruption is skipped with a warning."""
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(RunRecord.model_validate_json(line))
        except ValidationError:
            logger.warning("Skipping unreadable line %d in %s", number, path)
    return records


def latest_successful(records: list[RunRecord]) -> dict[str, RunRecord]:
    """The last successful record for each call, if it answered the latest request for that call.

    When a prompt or setting changes, the next attempt at a call carries a new request hash. If
    that attempt fails, the earlier success answered a question that is no longer asked, so it
    is not returned. Otherwise an analysis would score an old answer against a new question.
    """
    latest_request = {record.call_id: record.request_hash for record in records}
    return {
        record.call_id: record
        for record in records
        if record.result is not None and record.request_hash == latest_request[record.call_id]
    }
