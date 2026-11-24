"""S4 E8, can fine-tuning teach facts: the training pairs, and the closed-book prompt.

The pairs are generated from the Halvard library's current public passages only, cut the way
Season 2's reference system cut them (one passage per lowest section, at most 1,024 tokens).
Staff-only documents are left out on purpose: a tuned model has no permission filter, so
anything it learns it can repeat to anyone. Superseded and deleted documents are left out
because their facts are no longer true.

A pair whose question is a near duplicate of a dev or test question (character 5-gram Jaccard
over 0.8, the Season 4 rule) is removed and counted, so the tuned model is never trained on
the questions it is scored on.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from lab.adapt.build_tasks.checks import ReplyError, parse_object
from lab.adapt.build_tasks.dedupe import NearDuplicateIndex, shingles
from lab.providers.base import GenerationRequest
from lab.rag.chunk import Chunk, StructureChunker, chunk_library
from lab.rag.config import ModelSpec
from lab.rag.corpus import Item, Library
from lab.rag.prompt import conversation
from lab.rag.waves import request_for

PASSAGE_TOKENS = 1024
NEAR_DUPLICATE = 0.8
FACTS_SHORT = (
    "Answer the Halvard Home customer's question. If you do not know the answer, say that you "
    "could not find it."
)
PAIR_SYSTEM = (
    "You write training data for Halvard Home, an invented UK appliance maker. Everything you "
    "write must come from the passage given; add nothing of your own."
)


class Pair(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    passage_id: str
    doc_key: str
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


def training_passages(library: Library) -> tuple[Chunk, ...]:
    """Current public passages: no staff-only, superseded or deleted document."""
    keep = [d for d in library.documents if d.access == "public" and d.status == "current"]
    return chunk_library(keep, StructureChunker(max_tokens=PASSAGE_TOKENS))


def pair_prompt(passage: Chunk, n: int) -> str:
    return (
        f'Passage, from the Halvard Home document "{passage.title}":\n\n{passage.text}\n\n'
        f"Write {n} different questions a customer might ask that this passage answers, each "
        "with its answer. Vary the wording: some short, some conversational, some naming the "
        "product and some not. Each answer must stand on its own: name the product or policy, "
        "keep every figure exactly as the passage gives it, and use only facts in the passage. "
        'Reply with JSON only: {"pairs": [{"question": "...", "answer": "..."}]}'
    )


def pair_requests(
    passages: Sequence[Chunk], n: int, generator: ModelSpec, episode: str
) -> dict[str, GenerationRequest]:
    return {
        p.chunk_id: request_for(
            generator, system=PAIR_SYSTEM, prompt=pair_prompt(p, n), episode=episode, stage="pairs"
        )
        for p in passages
    }


def parse_pairs(text: str | None, n: int) -> list[tuple[str, str]]:
    """The question and answer strings in a reply; raises ReplyError if not exactly n."""
    if text is None:
        raise ReplyError("no reply")
    found = parse_object(text).get("pairs")
    if not isinstance(found, list) or len(found) != n:
        raise ReplyError(f"expected a list of {n} pairs")
    out = []
    for entry in found:
        if not isinstance(entry, dict):
            raise ReplyError("a pair is not an object")
        q, a = entry.get("question"), entry.get("answer")
        if not isinstance(q, str) or not isinstance(a, str) or not q.strip() or not a.strip():
            raise ReplyError("a pair lacks a question or an answer")
        out.append((q.strip(), a.strip()))
    return out


def build_pairs(
    passages: Sequence[Chunk],
    replies: Mapping[str, str | None],
    n: int,
    blocked_questions: Mapping[str, str],
) -> tuple[list[Pair], dict]:
    """The pairs that pass every check, in passage order, and a log of what was dropped."""
    blocked = NearDuplicateIndex(blocked_questions)
    pairs: list[Pair] = []
    failed: list[str] = []
    near: list[dict] = []
    repeated = 0
    seen: set[frozenset[str]] = set()
    for passage in passages:
        try:
            found = parse_pairs(replies.get(passage.chunk_id), n)
        except ReplyError:
            failed.append(passage.chunk_id)
            continue
        for k, (question, answer) in enumerate(found):
            pair_id = f"{passage.chunk_id}#{k}"
            match, score = blocked.closest(question)
            if score > NEAR_DUPLICATE:
                near.append({"pair": pair_id, "close_to": match, "similarity": round(score, 3)})
                continue
            key = shingles(question)
            if key in seen:
                repeated += 1
                continue
            seen.add(key)
            pairs.append(
                Pair(
                    id=pair_id,
                    passage_id=passage.chunk_id,
                    doc_key=passage.doc_key,
                    question=question,
                    answer=answer,
                )
            )
    log = {
        "passages": len(passages),
        "pairs_per_passage": n,
        "pairs_kept": len(pairs),
        "passages_failed": failed,
        "near_duplicates_of_dev_or_test": near,
        "repeated_questions": repeated,
        "near_duplicate_threshold": NEAR_DUPLICATE,
    }
    return pairs, log


def blocked_questions(library: Library) -> dict[str, str]:
    """Every dev and test question, resolved or not, keyed by item id."""
    out = {}
    for item in (*library.dev, *library.test):
        out[item.id] = item.question
        if item.resolved_question:
            out[f"{item.id}:resolved"] = item.resolved_question
    return out


def write_pairs(path: Path, pairs: Sequence[Pair]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(p.model_dump(), ensure_ascii=False) + "\n" for p in pairs)
    path.write_bytes(text.encode("utf-8"))


def load_pairs(path: Path) -> list[Pair]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Pair.model_validate_json(line) for line in lines if line.strip()]


def closed_book_user(item: Item) -> str:
    """What a closed-book model reads: any earlier turns, then the question. No passages."""
    if not item.history:
        return item.question
    return f"{conversation(item.history)}\n\nQuestion: {item.question}"
