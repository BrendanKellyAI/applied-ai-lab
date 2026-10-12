"""Stage 3, embed: vectors for chunks and questions, through an on-disk cache.

Ported from v1 S2 E2. One SQLite row per (model, text), keyed by a hash of both, because
embedding calls are batched and a batch rarely repeats exactly. Vectors live in the shared
.cache/ folder and are never committed.
"""

import hashlib
import os
import sqlite3
from collections.abc import Callable, Sequence
from contextlib import closing
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from lab.rag.chunk import count_tokens

# Well inside the API's limits of 2,048 inputs and 300,000 tokens per request.
MAX_INPUTS = 2048
MAX_BATCH_TOKENS = 250_000
# Keys per SELECT, well inside SQLite's limit on query parameters.
_LOOKUP_BATCH = 500


class EmbeddingsClient(Protocol):
    """The part of the OpenAI client this module uses: `client.embeddings.create(...)`."""

    embeddings: Any


def text_key(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()


class EmbeddingStore:
    """Vectors in SQLite. Each operation opens and closes its own connection."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connect() as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, v BLOB)")

    def _connect(self) -> closing[sqlite3.Connection]:
        return closing(sqlite3.connect(self._path))

    def get_many(self, model: str, texts: Sequence[str]) -> dict[str, np.ndarray]:
        """The cached vector of each text that has one."""
        keys = {text_key(model, text): text for text in dict.fromkeys(texts)}
        found: dict[str, np.ndarray] = {}
        key_list = list(keys)
        with self._connect() as db:
            for start in range(0, len(key_list), _LOOKUP_BATCH):
                batch = key_list[start : start + _LOOKUP_BATCH]
                marks = ",".join("?" * len(batch))
                rows = db.execute(f"SELECT key, v FROM vectors WHERE key IN ({marks})", batch)
                for key, blob in rows:
                    found[keys[key]] = np.frombuffer(blob, dtype=np.float32)
        return found

    def put(self, model: str, texts: Sequence[str], vectors: np.ndarray) -> None:
        with self._connect() as db, db:
            db.executemany(
                "INSERT OR REPLACE INTO vectors VALUES (?, ?)",
                [
                    (text_key(model, text), np.asarray(vector, dtype=np.float32).tobytes())
                    for text, vector in zip(texts, vectors, strict=True)
                ],
            )


def batches(
    texts: Sequence[str],
    count_tokens: Callable[[str], int],
    *,
    max_inputs: int = MAX_INPUTS,
    max_tokens: int = MAX_BATCH_TOKENS,
) -> list[list[str]]:
    """Texts grouped so no request passes the input or token limits."""
    groups: list[list[str]] = [[]]
    tokens = 0
    for text in texts:
        size = count_tokens(text)
        if groups[-1] and (len(groups[-1]) >= max_inputs or tokens + size > max_tokens):
            groups.append([])
            tokens = 0
        groups[-1].append(text)
        tokens += size
    return [group for group in groups if group]


class Embedder:
    """Embeds texts through the cache. Counts the tokens the API reports for calls it makes."""

    def __init__(self, client: EmbeddingsClient | None, model: str, store: EmbeddingStore):
        self.client, self.model, self.store = client, model, store
        self.tokens_reported = 0
        self.model_returned: str | None = None

    def missing(self, texts: Sequence[str]) -> list[str]:
        """Distinct texts not yet in the cache, in first-seen order."""
        found = self.store.get_many(self.model, texts)
        return [t for t in dict.fromkeys(texts) if t not in found]

    def __call__(self, texts: Sequence[str]) -> np.ndarray:
        missing = self.missing(texts)
        if missing and self.client is None:
            raise RuntimeError(
                f"{len(missing)} texts are not in the embedding cache and no client was given"
            )
        for group in batches(missing, count_tokens):
            response = self.client.embeddings.create(model=self.model, input=group)
            vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
            self.tokens_reported += response.usage.total_tokens
            self.model_returned = response.model
            self.store.put(self.model, group, vectors)
        found = self.store.get_many(self.model, texts)
        return np.array([found[text] for text in texts])


def openai_client() -> EmbeddingsClient | None:
    """An OpenAI client for embeddings, or None when there is no key."""
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    import openai

    return openai.OpenAI(max_retries=2)
