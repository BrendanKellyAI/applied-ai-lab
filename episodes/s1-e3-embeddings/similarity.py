"""S1 E3, Embeddings: texts with similar meaning land close together, even with no shared words.

Run from the repository root:

    uv run python episodes/s1-e3-embeddings/similarity.py

Needs OPENAI_API_KEY, either in the repository's .env file or set in your environment.
Writes results/embeddings.json, which chart.py and the tests read, so neither needs a key.
See README.md in this folder.
"""

from dotenv import load_dotenv

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
# Everything below this line matches the slides.
load_dotenv()

import numpy as np
from openai import OpenAI

client = OpenAI()
query = "How do I get my money back?"
phrases = ["refund policy", "money back", "return an item",
           "reset password", "can't log in", "locked account",
           "Dublin weather"]
result = client.embeddings.create(
    model="text-embedding-3-small", input=[query, *phrases])
vectors = np.array([item.embedding for item in result.data])
q, rows = vectors[0], vectors[1:]
norms = np.linalg.norm(rows, axis=1) * np.linalg.norm(q)
scores = rows @ q / norms
for score, phrase in sorted(zip(scores, phrases), reverse=True):
    print(f"{score:.3f}  {phrase}")

# Not on the slides. The pairs test the episode's two warnings, next to a paraphrase and an
# unrelated sentence, because a score only means something beside those yardsticks: scores from
# this model family sit in a compressed range, so "0.8" alone says little.
import json
from datetime import UTC, datetime
from pathlib import Path

MODEL = "text-embedding-3-small"
PAIRS = [
    ("negation", "The drug is safe.", "The drug is not safe."),
    ("numbers", "Shares rose 5% today.", "Shares fell 5% today."),
    ("paraphrase", "The drug is safe.", "The medicine carries no risk."),
    ("unrelated", "The drug is safe.", "The train leaves at noon."),
]
# The rose and fell pair keeps the key "numbers" in the results, but both sentences say 5%, so
# what it tests is direction, and that is how it is shown.
LABELS = {"numbers": "direction"}


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


pair_texts = list(dict.fromkeys(text for _, *pair in PAIRS for text in pair))
pair_result = client.embeddings.create(model=MODEL, input=pair_texts)
pair_vectors = {
    text: np.array(item.embedding)
    for text, item in zip(pair_texts, pair_result.data, strict=True)
}

print()
pair_scores = []
for kind, first, second in PAIRS:
    score = cosine(pair_vectors[first], pair_vectors[second])
    pair_scores.append({"kind": kind, "first": first, "second": second, "score": score})
    print(f"{score:.3f}  {LABELS.get(kind, kind)}: {first} / {second}")

# Every text keeps its vector, so the scores can be checked, or recomputed another way, later.
texts = {query: vectors[0], **dict(zip(phrases, rows, strict=True)), **pair_vectors}
record = {
    "model_requested": MODEL,
    "model_returned": result.model,
    "vector_length": len(vectors[0]),
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "search": {
        "query": query,
        "scores": [
            {"phrase": phrase, "score": float(score)}
            for phrase, score in zip(phrases, scores, strict=True)
        ],
    },
    "pairs": pair_scores,
    "vectors": {text: [float(value) for value in vector] for text, vector in texts.items()},
}
out = Path(__file__).parent / "results" / "embeddings.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
