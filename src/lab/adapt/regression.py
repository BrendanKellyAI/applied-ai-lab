"""S4 E10, what does tuning break: the three prompt sets, and how each is scored.

- **General ability:** Season 1 E10's 120 items (state tracking, constraint puzzles,
  extraction, arithmetic), sent as written, scored by Season 1's own code: the final
  `ANSWER:` line, compared exactly.
- **Format bleed:** 100 ordinary requests that are not triage or customer replies (a frozen
  file in the episode). A reply bleeds when it comes back in a tuned format: a triage object,
  or Halvard's house reply (its fixed opening or sign-off).
- **Declines:** the 120 unanswerable `halvard-v2` test questions, with exactly the prompt Season
  2's reference system sent (its instruction, its five passages, the question), rebuilt from the
  reference run log and checked against the hash of the request it recorded. Judged by Season
  2's judge, shown the same passages.

Every model gets the same messages; there is no system prompt except the reference's own in
the decline set.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from lab.adapt.build_tasks.checks import ReplyError, parse_object
from lab.providers.base import GenerationRequest, request_hash
from lab.rag.chunk import Chunk, StructureChunker, chunk_library
from lab.rag.config import ModelSpec
from lab.rag.corpus import Item, Library
from lab.rag.prompt import build_prompt, instruction
from lab.rag.waves import request_for

HOUSE_OPENING = "Thank you for getting in touch."
HOUSE_CLOSE = "The Halvard Home team"
TRIAGE_KEYS = {"route", "safety"}
# Season 2's reference system (0294479ba987): structure chunks of 1,024 tokens, the
# grounded_cite instruction, and gpt-6-luna with a 2,000 token limit.
REFERENCE_CHUNKER = StructureChunker(max_tokens=1024)
REFERENCE_INSTRUCTION = "grounded_cite"
REFERENCE_ANSWER = ModelSpec(
    provider="openai", model="gpt-6-luna", reasoning="off", max_output_tokens=2000
)


class RegressionError(ValueError):
    """A prompt set that does not match its source."""


def user_rows(rows: Sequence[tuple[str, str]]) -> list[dict]:
    return [{"id": i, "messages": [{"role": "user", "content": text}]} for i, text in rows]


def general_rows(items_path: Path) -> list[dict]:
    """Season 1 E10's items, ids `<task>-<index>` (each task numbers its items from 0)."""
    items = [json.loads(line) for line in items_path.read_text(encoding="utf-8").splitlines()]
    return user_rows([(f"{i['task']}-{i['index']:02d}", i["prompt"]) for i in items])


def general_items(items_path: Path) -> dict[str, dict]:
    """The same items by id, with the expected answer and how to compare it."""
    items = [json.loads(line) for line in items_path.read_text(encoding="utf-8").splitlines()]
    return {f"{i['task']}-{i['index']:02d}": i for i in items}


def bleed_rows(path: Path) -> list[dict]:
    """The format bleed requests: a JSONL of {"id", "request"}."""
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return user_rows([(r["id"], r["request"]) for r in rows])


def reference_prompt(
    item: Item, chunk_ids: Sequence[str], chunks: Mapping[str, Chunk]
) -> tuple[str, str]:
    passages = [chunks[c] for c in chunk_ids]
    return instruction(REFERENCE_INSTRUCTION), build_prompt(item.question, item.history, passages)


def decline_rows(library: Library, log: Path, raw_answer: Path) -> list[dict]:
    """The unanswerable test questions with the reference system's exact prompt. Each rebuilt
    request must hash to the request the reference run recorded, or nothing is returned."""
    chunks = {c.chunk_id: c for c in chunk_library(library.documents, REFERENCE_CHUNKER)}
    prompts = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        prompts[row["item_id"]] = row["prompt_chunks"]
    recorded = {}
    for line in raw_answer.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        recorded[row["cell"]["item"]] = row["request_hash"]
    out = []
    for item in library.test:
        if item.answerable:
            continue
        system, prompt = reference_prompt(item, prompts[item.id], chunks)
        request = request_for(
            REFERENCE_ANSWER, system=system, prompt=prompt, episode="s2", stage="answer"
        )
        if request_hash(request) != recorded[item.id]:
            raise RegressionError(f"{item.id}: the rebuilt prompt differs from the reference's")
        out.append(
            {
                "id": item.id,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }
        )
    return out


def write_rows(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_bytes(text.encode("utf-8"))


def bleed_kind(text: str | None) -> str | None:
    """The tuned format a reply came back in: "triage", "house_reply", or None."""
    if not text:
        return None
    try:
        if set(parse_object(text)) >= TRIAGE_KEYS:
            return "triage"
    except ReplyError:
        pass
    start = text.find("{")
    if start >= 0:
        try:
            if set(parse_object(text[start : text.rfind("}") + 1])) >= TRIAGE_KEYS:
                return "triage"
        except ReplyError:
            pass
    if text.lstrip().startswith(HOUSE_OPENING) or HOUSE_CLOSE in text:
        return "house_reply"
    return None


def judge_requests_with_passages(
    judge: ModelSpec,
    episode: str,
    items: Sequence[Item],
    answers: Mapping[str, str],
    prompts: Mapping[str, Sequence[str]],
    chunks: Mapping[str, Chunk],
) -> dict[str, GenerationRequest]:
    """Season 2's judge, shown the passages the reference gave: for the decline set."""
    from lab.rag.judge import judge_instructions, judge_prompt

    out = {}
    for item in items:
        if item.id not in answers:
            continue
        passages = [chunks[c] for c in prompts[item.id]]
        out[item.id] = request_for(
            judge,
            system=judge_instructions(),
            prompt=judge_prompt(item, passages, answers[item.id]),
            episode=episode,
            stage="judge",
        )
    return out
