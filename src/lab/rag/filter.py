"""Stage 6, filter: keep only chunks this asker may see, from documents in force today.

Both rules read metadata, never the text. `before` removes chunks before ranking, so a chunk
the asker may not see never takes a place (search.rank). `after` ranks everything and then
drops chunks, so fewer may reach the prompt. `passthrough` keeps everything.
"""

from collections.abc import Sequence
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from lab.rag.chunk import Chunk
from lab.rag.corpus import Access
from lab.rag.search import Hit

Reason = Literal["access", "status"]


class FilterConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["passthrough", "before", "after"] = "passthrough"
    # Staff documents only for staff askers.
    access: bool = True
    # Current documents only: no superseded or deleted versions.
    status: bool = True


class Removed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    reason: Reason


def refusal(chunk: Chunk, asker: Access, config: FilterConfig) -> Reason | None:
    """Why the rules refuse this chunk to this asker, or None if they allow it."""
    if config.access and chunk.access == "staff" and asker != "staff":
        return "access"
    if config.status and chunk.status != "current":
        return "status"
    return None


def allowed(chunk: Chunk, asker: Access, config: FilterConfig) -> bool:
    return refusal(chunk, asker, config) is None


def keep_mask(chunks: Sequence[Chunk], asker: Access, config: FilterConfig) -> np.ndarray | None:
    """For `before`, which chunks may be ranked; otherwise None, meaning all of them."""
    if config.mode != "before":
        return None
    return np.array([allowed(chunk, asker, config) for chunk in chunks], dtype=bool)


def apply_after(
    hits: Sequence[Hit], chunks: Sequence[Chunk], asker: Access, config: FilterConfig
) -> tuple[list[Hit], list[Removed]]:
    """For `after`, the ranked hits split into those kept and those removed, with reasons."""
    if config.mode != "after":
        return list(hits), []
    kept: list[Hit] = []
    removed: list[Removed] = []
    for hit in hits:
        reason = refusal(chunks[hit.index], asker, config)
        if reason is None:
            kept.append(hit)
        else:
            removed.append(Removed(index=hit.index, reason=reason))
    return kept, removed
