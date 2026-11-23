"""Task B passages and seeds.

A passage is one `###` section of a current public policy, or one current public help article.
Internal, deleted and superseded documents are never used. Passages are shuffled and split
before any call, so a test item never shares a passage with a train item.
"""

import math
import random
import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.config import SPLITS, Split, TaskBConfig
from lab.adapt.style import Source
from lab.rag.corpus import Document, Library

GENERAL = "General terms"
NOT_FOUND = "not_found"
ANSWERABLE = "answerable"


class Passage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: str  # "policy" or "article"
    name: str
    section: str | None
    text: str

    def source(self) -> Source:
        return Source(kind=self.kind, name=self.name, section=self.section)


class BSeed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    split: Split
    passage: Passage
    kind: str  # ANSWERABLE or NOT_FOUND
    angle: str
    # How many times this passage has come round before in the split, so that repeat visits
    # get different prompts (the cache would otherwise return the same item).
    variant: int
    tone: str

    def source(self) -> Source:
        if self.kind == NOT_FOUND:
            return Source(kind="not_found", name="")
        return self.passage.source()


def usable(document: Document) -> bool:
    return (
        document.access == "public"
        and document.status == "current"
        and document.family in ("policy", "article")
    )


def passages(library: Library) -> list[Passage]:
    found: list[Passage] = []
    for document in sorted(library.documents, key=lambda d: d.key):
        if not usable(document):
            continue
        if document.family == "article":
            found.append(
                Passage(
                    id=document.key,
                    kind="article",
                    name=document.title,
                    section=None,
                    text=document.body.strip(),
                )
            )
        else:
            found += policy_sections(document)
    return found


def policy_sections(document: Document) -> list[Passage]:
    """Each `###` section, labelled with its `##` parent unless that is the general terms."""
    sections: list[Passage] = []
    parent = None
    heading = None
    lines: list[str] = []

    def close() -> None:
        if heading is not None and "".join(lines).strip():
            label = heading if parent in (None, GENERAL) else f"{parent}: {heading}"
            sections.append(
                Passage(
                    id=f"{document.key}#{label}",
                    kind="policy",
                    name=document.title,
                    section=label,
                    text="\n".join(lines).strip(),
                )
            )

    for line in document.body.splitlines():
        if match := re.match(r"^## (?!#)(.+)", line):
            close()
            parent, heading, lines = match.group(1).strip(), None, []
        elif match := re.match(r"^### (.+)", line):
            close()
            heading, lines = match.group(1).strip(), []
        elif heading is not None:
            lines.append(line)
    close()
    return sections


def split_passages(
    found: Sequence[Passage], config: TaskBConfig, seed: int
) -> dict[Split, list[Passage]]:
    """Shuffle once, then cut in proportion to the split sizes."""
    shuffled = list(found)
    random.Random(f"{seed}:task-b:passages").shuffle(shuffled)
    total = sum(config.splits.values())
    cuts: dict[Split, list[Passage]] = {}
    start = 0
    for index, split in enumerate(SPLITS):
        if index == len(SPLITS) - 1:
            end = len(shuffled)
        else:
            end = start + max(1, round(len(shuffled) * config.splits[split] / total))
        cuts[split] = shuffled[start:end]
        start = end
    return cuts


def draw_b_seeds(
    split: Split,
    n: int,
    split_passages_: Sequence[Passage],
    config: TaskBConfig,
    tones: Sequence[str],
    seed: int,
) -> list[BSeed]:
    """Cycle through the split's passages, each time with the next question angle."""
    rng = random.Random(f"{seed}:task-b:{split}")
    not_found = set(rng.sample(range(n), round(n * config.not_found_share)))
    order = list(split_passages_)
    rng.shuffle(order)
    seeds = []
    for index in range(n):
        passage = order[index % len(order)]
        round_ = index // len(order)
        seeds.append(
            BSeed(
                id=f"B-{split}-{index:05d}",
                split=split,
                passage=passage,
                kind=NOT_FOUND if index in not_found else ANSWERABLE,
                angle=config.angles[round_ % len(config.angles)],
                variant=round_,
                tone=rng.choice(tones),
            )
        )
    return seeds


def b_seed_count(size: int, overgenerate: float) -> int:
    return math.ceil(size * (1 + overgenerate))
