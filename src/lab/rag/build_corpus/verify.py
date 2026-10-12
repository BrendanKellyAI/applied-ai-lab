"""The unanswerable check: the checker model reads the top 20 passages from keyword search and
the top 20 from vector search, over what a public asker may see, and must agree that none
answers the question. An item it disputes is replaced by a spare, not argued over.
"""

import json
from collections.abc import Sequence

from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.generate import Task
from lab.rag.chunk import FixedChunker, chunk_library
from lab.rag.corpus import Document, Item
from lab.rag.filter import FilterConfig, keep_mask
from lab.rag.index import Embed, Index, build_index
from lab.rag.prompt import numbered
from lab.rag.search import SearchConfig, search

DEPTH = 20
# The reference system's chunking, so the check sees what search will see.
CHUNKER = FixedChunker(size=256)
CHECKED_TYPES = {"absent_detail", "absent_topic", "deleted", "restricted_public"}


def check_index(documents: Sequence[Document], embed: Embed) -> Index:
    return build_index(chunk_library(documents, CHUNKER), embed)


def check_tasks(
    config: CorpusConfig, items: Sequence[Item], index: Index, embed: Embed
) -> list[Task]:
    chosen = [i for i in items if i.type in CHECKED_TYPES]
    vectors = embed([item.question for item in chosen])
    mask = keep_mask(index.chunks, "public", FilterConfig(mode="before"))
    tasks = []
    for item, vector in zip(chosen, vectors, strict=True):
        positions: dict[int, None] = {}
        for method in ("vector", "keyword"):
            hits = search(
                index, item.question, vector, SearchConfig(method=method, depth=DEPTH), keep=mask
            )
            positions.update({hit.index: None for hit in hits})
        passages = "\n\n".join(numbered([index.chunks[p] for p in positions]))
        tasks.append(
            Task(
                id=item.id,
                system=config.prompts["check_system"].strip(),
                prompt=config.prompt("check", question=item.question, passages=passages),
            )
        )
    return tasks


def parse_check(text: str) -> bool:
    """Whether the checker says a passage answers the question. Raises ValueError if unreadable."""
    body = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    found = json.loads(body)
    if not isinstance(found, dict) or not isinstance(found.get("answers"), bool):
        raise ValueError("no true or false answers field")
    return found["answers"]


def check_reply(task_id: str, text: str) -> str | None:
    try:
        parse_check(text)
    except (ValueError, json.JSONDecodeError) as exc:
        return f"Reply with the JSON object only ({exc})."
    return None
