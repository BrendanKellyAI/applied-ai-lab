"""An offline stand-in for the OpenAI embeddings endpoint.

Each text becomes a bag-of-words vector over hashed buckets, so texts sharing words are close,
which is enough for search tests to behave like search without a network.
"""

import hashlib
import re
from types import SimpleNamespace

import numpy as np

DIMENSIONS = 256


def fake_vector(text: str) -> list[float]:
    vector = np.zeros(DIMENSIONS, dtype=np.float32)
    for word in re.findall(r"\w+", text.lower()):
        bucket = int(hashlib.sha256(word.encode()).hexdigest(), 16) % DIMENSIONS
        vector[bucket] += 1.0
    if not vector.any():
        vector[0] = 1.0
    return vector.tolist()


class FakeEmbeddingsClient:
    """Mimics `client.embeddings.create(model=..., input=[...])` and counts the calls."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.embeddings = SimpleNamespace(create=self._create)

    def _create(self, *, model: str, input: list[str]) -> SimpleNamespace:
        self.calls.append(list(input))
        return SimpleNamespace(
            model=f"{model}-fake",
            data=[SimpleNamespace(embedding=fake_vector(text)) for text in input],
            usage=SimpleNamespace(total_tokens=sum(len(t.split()) for t in input)),
        )
