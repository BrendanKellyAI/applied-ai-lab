"""The parts of S2 E5 fixed in code: the library, the checks every built item must pass, the
indexes, the prompts, and the grading of a reply. Nothing here calls a model or the network."""

import difflib
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
CONFIG = HERE / "config.yaml"
NOT_FOUND = "NOT_FOUND"
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def e3_config(config: dict, root: Path = ROOT) -> dict:
    return yaml.safe_load((root / config["e3_folder"] / "config.yaml").read_text(encoding="utf-8"))


def chat_model(config: dict, root: Path = ROOT) -> str:
    """The model S2 E3 wrote its articles with, read from its config."""
    return e3_config(config, root)["generation_model"]


def load_e3(config: dict, root: Path = ROOT) -> tuple[list[dict], list[dict]]:
    folder = root / config["e3_folder"]
    corpus = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
    return corpus["articles"], questions["questions"]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Value facts --------------------------------------------------------------------------------


def occurrences(texts, value: str) -> int:
    return sum(text.count(value) for text in texts)


def value_problem(texts: list[str], article: str, sentence: str, value: str) -> str | None:
    """Why a candidate value fails, or None: the sentence must be copied from the article, and the
    value must appear exactly once in the whole library, inside that sentence."""
    if not value.strip() or not sentence.strip():
        return "empty sentence or value"
    if sentence not in article:
        return "the sentence is not copied exactly from the article"
    if value not in sentence:
        return "the value is not inside the sentence"
    if article.count(sentence) != 1:
        return "the sentence appears more than once in the article"
    count = occurrences(texts, value)
    if count != 1:
        return f"the value appears {count} times in the library, not once"
    return None


def replacement_problem(texts: list[str], old: str, new: str) -> str | None:
    """A replacement must be new to the library, and neither value may contain the other, so a
    reply can be graded by substring without one value counting as the other."""
    new = new.strip()
    if not new or "\n" in new:
        return "reply with the value only, on one line"
    if new == old:
        return "the value is unchanged"
    if new in old or old in new:
        return f'"{new}" and "{old}" contain one another'
    if occurrences(texts, new):
        return f'"{new}" already appears in the library'
    return None


def revise(article: str, sentence: str, old: str, new: str) -> str:
    """The article with the one value swapped, inside its sentence, checked by a diff."""
    revised_sentence = sentence.replace(old, new, 1)
    revised = article.replace(sentence, revised_sentence, 1)
    assert_minimal(article, revised, old, new)
    return revised


def assert_minimal(original: str, revised: str, old: str, new: str) -> None:
    """The two versions differ in one place, where the old value became the new one."""
    changes = [op for op in difflib.SequenceMatcher(None, original, revised, autojunk=False)
               .get_opcodes() if op[0] != "equal"]
    if not changes:
        raise AssertionError("the revision changed nothing")
    start, end = changes[0][1], changes[-1][2]
    new_start, new_end = changes[0][3], changes[-1][4]
    at = original.index(old)
    if not (at <= start and end <= at + len(old)):
        raise AssertionError("the revision changed text outside the value")
    if original[:at] + new + original[at + len(old):] != revised:
        raise AssertionError("the revision is not the one value swapped")
    if revised[new_start:new_end] not in new:
        raise AssertionError("the changed text is not part of the new value")


def question_problem(question: str, old: str, new: str) -> str | None:
    if not question.strip():
        return "the question was empty"
    low = question.lower()
    for value in (old, new):
        if value.lower() in low:
            return f'the question contains "{value}"'
    return None


# Unanswerable questions and internal notes --------------------------------------------------


def product_problem(texts: list[str], question: str, product: str) -> str | None:
    if not product.strip() or not question.strip():
        return "empty question or product"
    if product.lower() not in question.lower():
        return "the question does not name the product as given"
    lowered = [t.lower() for t in texts]
    if occurrences(lowered, product.lower()):
        return f'"{product}" appears in the library'
    return None


def longest_shared(note: str, texts: list[str]) -> int:
    """The longest run of characters the note shares with any one text."""
    best = 0
    for text in texts:
        match = difflib.SequenceMatcher(None, note, text, autojunk=False).find_longest_match(
            0, len(note), 0, len(text))
        best = max(best, match.size)
    return best


def note_problem(note: str, texts: list[str], tokens: int, config: dict) -> str | None:
    low, high = config["note_tokens"]
    if not low <= tokens <= high:
        return f"the note is {tokens} tokens, outside {low} to {high}"
    if note in texts:
        return "the note duplicates a public article"
    shared = longest_shared(note, texts)
    if shared >= config["max_shared_chars"]:
        return f"the note copies a run of {shared} characters from a public article"
    return None


# Indexes ------------------------------------------------------------------------------------


def entry(article_id: str, text: str, *, access: str = "public", date: str | None = None,
          version: str = "current") -> dict:
    return {"entry_id": f"{article_id}:{version}", "article_id": article_id, "text": text,
            "access": access, "date": date, "version": version, "sha256": sha256(text)}


def make_index(entries: list[dict], vectors: np.ndarray) -> dict:
    """Entries with their vectors. Each entry is marked latest if no entry of the same article
    has a later date, so a filter can keep the newest version of each."""
    if len(entries) != len(vectors):
        raise ValueError("one vector per entry")
    newest: dict[str, str] = {}
    for e in entries:
        newest[e["article_id"]] = max(newest.get(e["article_id"], ""), e["date"] or "")
    marked = [{**e, "latest": (e["date"] or "") == newest[e["article_id"]]} for e in entries]
    return {"entries": marked, "vectors": np.asarray(vectors, dtype=np.float32)}


def stale_entries(index: dict, sources: dict[str, str]) -> list[str]:
    """Entries whose stored hash no longer matches their current source text."""
    return [e["entry_id"] for e in index["entries"]
            if sha256(sources[e["article_id"]]) != e["sha256"]]


# Prompts and grading ------------------------------------------------------------------------


def answer_prompt(config: dict, question: str, passages: list[dict], *, dated: bool = False,
                  not_found: bool = False) -> str:
    prompts = config["prompts"]
    lines = [prompts["answer"]]
    if not_found:
        lines.append(prompts["not_found"])
    for number, passage in enumerate(passages, start=1):
        header = f"Passage {number}"
        if dated:
            header += f"\nUpdated: {passage['date']}"
        lines.append(f"\n{header}\n{passage['text']}")
    lines.append(f"\nQuestion: {question}")
    return "\n".join(lines)


def grade_value(reply: str, old: str, new: str) -> str:
    has_old, has_new = old in reply, new in reply
    if has_old and has_new:
        return "both"
    return "old" if has_old else "new" if has_new else "neither"


def is_not_found(reply: str) -> bool:
    return reply.strip() == NOT_FOUND


def judge_verdict(reply: str) -> str:
    word = re.sub(r"[^a-z]", "", reply.lower())
    return word if word in ("assert", "decline") else "unclear"


def yes_no(reply: str) -> str:
    word = re.sub(r"[^a-z]", "", reply.lower())
    return word if word in ("yes", "no") else "unclear"


def passages_block(passages: list[dict]) -> str:
    return "\n\n".join(f"Passage {n}\n{p['text']}" for n, p in enumerate(passages, start=1))
