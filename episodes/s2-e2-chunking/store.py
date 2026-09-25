"""An on-disk cache of embeddings, so a rerun never pays twice for the same text.

The same idea as lab.cache, one entry per request hash, but keyed per text rather than per
generation request, because embedding calls are batched and a batch rarely repeats exactly.
Vectors live in .cache/, which is gitignored: they are never committed.
"""

import hashlib
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

# Well inside the API's limits of 2,048 inputs and 300,000 tokens per request.
MAX_INPUTS = 2048
MAX_BATCH_TOKENS = 250_000


def text_key(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()


class EmbeddingStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, v BLOB)")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY, model TEXT, "
            "inputs INTEGER, tokens INTEGER)"
        )

    def get(self, model: str, text: str) -> np.ndarray | None:
        row = self._db.execute(
            "SELECT v FROM vectors WHERE key = ?", (text_key(model, text),)
        ).fetchone()
        return None if row is None else np.frombuffer(row[0], dtype=np.float32)

    def put(self, model: str, texts: Sequence[str], vectors: np.ndarray, tokens: int) -> None:
        with self._db:
            self._db.executemany(
                "INSERT OR REPLACE INTO vectors VALUES (?, ?)",
                [
                    (text_key(model, text), np.asarray(vector, dtype=np.float32).tobytes())
                    for text, vector in zip(texts, vectors, strict=True)
                ],
            )
            self._db.execute(
                "INSERT INTO usage (model, inputs, tokens) VALUES (?, ?, ?)",
                (model, len(texts), tokens),
            )

    def close(self) -> None:
        self._db.close()


def batches(texts: Sequence[str], count_tokens: Callable[[str], int]) -> list[list[str]]:
    """Texts grouped so no request passes the input or token limits."""
    groups: list[list[str]] = [[]]
    tokens = 0
    for text in texts:
        size = count_tokens(text)
        if groups[-1] and (len(groups[-1]) >= MAX_INPUTS or tokens + size > MAX_BATCH_TOKENS):
            groups.append([])
            tokens = 0
        groups[-1].append(text)
        tokens += size
    return [group for group in groups if group]


class Embedder:
    """Embeds texts through the cache. Counts the tokens the API reports for calls it makes."""

    def __init__(self, client, model: str, store: EmbeddingStore, count_tokens) -> None:
        self.client, self.model, self.store = client, model, store
        self.count_tokens = count_tokens
        self.tokens_reported = 0
        self.model_returned: str | None = None

    def __call__(self, texts: Sequence[str]) -> np.ndarray:
        missing = list(dict.fromkeys(t for t in texts if self.store.get(self.model, t) is None))
        for group in batches(missing, self.count_tokens):
            response = self.client.embeddings.create(model=self.model, input=group)
            vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
            self.tokens_reported += response.usage.total_tokens
            self.model_returned = response.model
            self.store.put(self.model, group, vectors, response.usage.total_tokens)
        return np.array([self.store.get(self.model, text) for text in texts])
