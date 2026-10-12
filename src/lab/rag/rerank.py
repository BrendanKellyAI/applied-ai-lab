"""Stage 7, rerank: put the shortlist in a better order before the prompt takes the top k.

- `passthrough`: the search order.
- `cross_encoder`: `BAAI/bge-reranker-v2-m3`, run locally, reads the question and each of the
  top `shortlist` passages together and scores the pair. The model is pinned by revision.
  Scores are cached in SQLite, keyed by the revision, the question and the passage text; the
  time per question is recorded outside the cache, from the scores actually computed.
- `llm`: a cheap chat model reads the question and the numbered shortlist once and returns
  the passage numbers, best first. The fallback if the local model cannot run.

Passages beyond the shortlist keep their search order after it.
"""

import hashlib
import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_serializer

MODEL_ID = "BAAI/bge-reranker-v2-m3"


class RerankModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Literal["openai", "anthropic", "google"]
    model: str
    reasoning: str | None = None
    max_output_tokens: int = 200


class RerankConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["passthrough", "cross_encoder", "llm"] = "passthrough"
    shortlist: int = Field(default=20, gt=0)
    # cross_encoder: the Hugging Face revision of MODEL_ID. llm: the chat model.
    revision: str | None = None
    model: RerankModel | None = None

    @model_serializer(mode="wrap")
    def _compact(self, handler):
        # A stage left at passthrough serialises exactly as it did before the stage had options,
        # so config ids from earlier episodes do not change.
        data = handler(self)
        if self.mode == "passthrough":
            return {"mode": "passthrough"}
        return {k: v for k, v in data.items() if v is not None}


# slide: S2 E7
def rerank(ranked, scores, shortlist):
    """Reorder the top `shortlist` of the ranked passages by
    the reranker's score for each, best first. The rest keep
    their search order."""
    top = sorted(ranked[:shortlist], key=lambda p: -scores[p])
    return top + ranked[shortlist:]


def apply_order(n: int, shortlist: int, top_order: Sequence[int]) -> list[int]:
    """Positions 0..n-1 reordered: `top_order` over the shortlist, the rest unchanged."""
    size = min(shortlist, n)
    seen = [i for i in dict.fromkeys(top_order) if 0 <= i < size]
    seen += [i for i in range(size) if i not in seen]
    return seen + list(range(size, n))


class ScoreCache:
    """Cross-encoder scores in SQLite, one connection per operation (as EmbeddingStore)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS scores (key TEXT PRIMARY KEY, score REAL)")

    @staticmethod
    def key(revision: str, question: str, text: str) -> str:
        raw = "\x1f".join((MODEL_ID, revision, question, text))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_many(self, keys: Sequence[str]) -> dict[str, float]:
        with sqlite3.connect(self._path) as db:
            found = {}
            for start in range(0, len(keys), 500):
                part = keys[start : start + 500]
                marks = ",".join("?" * len(part))
                rows = db.execute(f"SELECT key, score FROM scores WHERE key IN ({marks})", part)
                found.update(dict(rows.fetchall()))
            return found

    def put_many(self, pairs: dict[str, float]) -> None:
        with sqlite3.connect(self._path) as db:
            db.executemany("INSERT OR REPLACE INTO scores VALUES (?, ?)", list(pairs.items()))


class CrossEncoder:
    """The local reranker. Loads lazily, so importing this module needs no torch."""

    def __init__(self, revision: str, cache: ScoreCache, batch: int = 16) -> None:
        self.revision = revision
        self.cache = cache
        self.batch = batch
        self.seconds_computing = 0.0
        self.pairs_computed = 0
        self._model = None

    def _load(self):
        if self._model is None:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._torch = torch
            self._tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=self.revision)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                MODEL_ID, revision=self.revision
            ).eval()
        return self._model

    def scores(self, question: str, texts: Sequence[str]) -> list[float]:
        keys = [ScoreCache.key(self.revision, question, t) for t in texts]
        cached = self.cache.get_many(keys)
        missing = [i for i, k in enumerate(keys) if k not in cached]
        if missing:
            model = self._load()
            start = time.perf_counter()
            new = {}
            for b in range(0, len(missing), self.batch):
                part = missing[b : b + self.batch]
                enc = self._tok(
                    [[question, texts[i]] for i in part],
                    padding=True,
                    truncation=True,
                    max_length=1024,
                    return_tensors="pt",
                )
                with self._torch.no_grad():
                    logits = model(**enc).logits.view(-1).float().tolist()
                new.update({keys[i]: s for i, s in zip(part, logits, strict=True)})
            self.seconds_computing += time.perf_counter() - start
            self.pairs_computed += len(missing)
            self.cache.put_many(new)
            cached.update(new)
        return [cached[k] for k in keys]


def llm_system() -> str:
    from lab.rag.prompt import instruction

    return instruction("rerank_llm")


def llm_prompt(question: str, passages: Sequence[str]) -> str:
    numbered = "\n\n".join(f"[{n}] {text.strip()}" for n, text in enumerate(passages, start=1))
    return f"Question: {question}\n\nPassages:\n{numbered}"


def parse_llm_order(text: str, n: int) -> list[int]:
    """Passage numbers in the reply, as zero-based positions, best first. Unknown or repeated
    numbers are dropped; any passage not named keeps its place after those named."""
    import re

    named = [int(x) - 1 for x in re.findall(r"\d+", text)]
    return [i for i in dict.fromkeys(named) if 0 <= i < n]


def make_reorder(
    config: RerankConfig,
    *,
    runner,
    cache_root: Path,
    index,
    episode: str,
    condition: str,
    folder: Path,
):
    """Stage 7 as a `reorder` for retrieve(), and a dict the run fills with its timing."""
    stats: dict = {}
    if config.mode == "passthrough":
        return None, stats
    if config.mode == "cross_encoder":
        if not config.revision:
            raise ValueError("cross_encoder needs the model revision pinned")
        encoder = CrossEncoder(config.revision, ScoreCache(cache_root / "rerank" / "scores.sqlite"))

        def cross(items, queries, kept):
            orders = {}
            for item in items:
                hits = kept[item.id]
                n = min(config.shortlist, len(hits))
                texts = [index.chunks[h.index].text for h in hits[:n]]
                scores = dict(enumerate(encoder.scores(queries[item.id][0], texts)))
                orders[item.id] = rerank(list(range(len(hits))), scores, n)
            stats.update(
                pairs_computed=encoder.pairs_computed,
                seconds_computing=round(encoder.seconds_computing, 3),
                questions=len(items),
            )
            return orders

        return cross, stats

    from lab.rag.config import ModelSpec
    from lab.rag.waves import planned, request_for, run_wave

    if config.model is None:
        raise ValueError("llm reranking needs a model")
    spec = ModelSpec(
        provider=config.model.provider,
        model=config.model.model,
        reasoning=config.model.reasoning,
        max_output_tokens=config.model.max_output_tokens,
    )

    def llm(items, queries, kept):
        calls, sizes = [], {}
        for item in items:
            hits = kept[item.id]
            n = min(config.shortlist, len(hits))
            sizes[item.id] = (len(hits), n)
            prompt = llm_prompt(queries[item.id][0], [index.chunks[h.index].text for h in hits[:n]])
            calls.append(
                planned(
                    request_for(
                        spec, system=llm_system(), prompt=prompt, episode=episode, stage="rerank"
                    ),
                    stage="rerank",
                    item_id=item.id,
                    condition=condition,
                )
            )
        results, summary = run_wave(runner, calls, folder / "raw-rerank.jsonl")
        stats["summary"] = summary
        orders = {}
        for item in items:
            total, n = sizes[item.id]
            result = results.get(item.id)
            named = parse_llm_order(result.text, n) if result else []
            orders[item.id] = apply_order(total, n, named)
        return orders

    return llm, stats
