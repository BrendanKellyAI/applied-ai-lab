"""Code checks for the invented Halvard Home reply style guide
(datasets/halvard-tasks/style-guide.md).

The same checks build the Task B targets and score every Task B arm. Each rule marked (code) in
the guide has one check here; facts kept and tone are left to the judge.
"""

import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

OPENING = "Thank you for getting in touch."
CLOSE = ("Kind regards,", "The Halvard Home team")
WORD_RANGE = (40, 120)
MAX_PARAGRAPHS = 3
NOT_FOUND = (
    "I'm sorry, I can't find that in our policies. I've passed your question to a colleague who "
    "will reply within two working days."
)
BANNED = (
    "we will refund",
    "we will replace",
    "guaranteed",
    "definitely",
    "we promise",
    "no problem at all",
)
# American spellings the guide rules out, matched as whole words.
AMERICAN = (
    "color",
    "colors",
    "favorite",
    "organize",
    "organized",
    "organizing",
    "center",
    "centers",
    "canceled",
    "canceling",
    "behavior",
    "authorize",
    "authorized",
    "apologize",
    "realize",
    "recognize",
    "customize",
    "fiber",
    "aluminum",
    "gray",
    "license",
    "program",
    "programs",
    "catalog",
    "defense",
    "labor",
    "liter",
    "meter",
    "meters",
    "odor",
    "mold",
)
_LIST_LINE = re.compile(r"^\s*(?:[-*•#]|\d+[.)])\s")
_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")
_APOSTROPHES = str.maketrans({"‘": "'", "’": "'"})


@dataclass(frozen=True)
class Source:
    """Where a reply's answer comes from, so its citation can be checked."""

    kind: str  # "policy", "article" or "not_found"
    name: str  # the policy title or the article title
    section: str | None = None

    def citation(self) -> str | None:
        if self.kind == "policy":
            return f'Our {self.name} policy, section "{self.section}", says'
        if self.kind == "article":
            return f'our help article "{self.name}"'
        return None


class StyleReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    opening: bool
    close: bool
    length: bool
    plain: bool
    citation: bool
    no_banned: bool
    not_found: bool
    british: bool
    words: int
    mean_sentence_words: float

    @property
    def all_pass(self) -> bool:
        return all(getattr(self, name) for name in CHECKS)

    def failures(self) -> tuple[str, ...]:
        return tuple(name for name in CHECKS if not getattr(self, name))


CHECKS = ("opening", "close", "length", "plain", "citation", "no_banned", "not_found", "british")
RULES = {
    "opening": f"open with exactly: {OPENING}",
    "close": "close with the two lines: Kind regards, / The Halvard Home team",
    "length": f"use {WORD_RANGE[0]} to {WORD_RANGE[1]} words in all",
    "plain": f"plain paragraphs only, at most {MAX_PARAGRAPHS}, no lists, headings, bold or emoji",
    "citation": "name the source in the exact citation form",
    "no_banned": "never promise an outcome (banned phrases)",
    "not_found": "when the answer is not available, use exactly the fixed not found sentence",
    "british": "use British spelling",
}


def normalise(text: str) -> str:
    return text.translate(_APOSTROPHES).strip()


def body_of(text: str) -> str:
    """The reply between the opening and the close, where both are present."""
    body = normalise(text)
    if body.startswith(OPENING):
        body = body[len(OPENING) :]
    marker = body.rfind(CLOSE[0])
    if marker != -1:
        body = body[:marker]
    return body.strip()


def check_reply(text: str, source: Source) -> StyleReport:
    reply = normalise(text)
    words = len(reply.split())
    body = body_of(reply)
    return StyleReport(
        opening=reply.startswith(OPENING),
        close=_closes(reply),
        length=WORD_RANGE[0] <= words <= WORD_RANGE[1],
        plain=_plain(reply, body),
        citation=_cites(reply, source),
        no_banned=not any(phrase in reply.lower() for phrase in BANNED),
        not_found=_not_found_ok(body, source),
        british=not american_words(reply),
        words=words,
        mean_sentence_words=_mean_sentence_words(body),
    )


def american_words(text: str) -> list[str]:
    lowered = text.lower()
    return [word for word in AMERICAN if re.search(rf"\b{word}\b", lowered)]


def _closes(reply: str) -> bool:
    lines = [line.strip() for line in reply.splitlines() if line.strip()]
    return tuple(lines[-2:]) == CLOSE


def _plain(reply: str, body: str) -> bool:
    if "**" in reply or _EMOJI.search(reply):
        return False
    if any(_LIST_LINE.match(line) for line in reply.splitlines()):
        return False
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    return len(paragraphs) <= MAX_PARAGRAPHS


def _cites(reply: str, source: Source) -> bool:
    expected = source.citation()
    return True if expected is None else expected in reply


def _not_found_ok(body: str, source: Source) -> bool:
    flat = " ".join(body.split())
    if source.kind == "not_found":
        return flat == NOT_FOUND
    return NOT_FOUND not in flat


def _mean_sentence_words(body: str) -> float:
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if not sentences:
        return 0.0
    return sum(len(s.split()) for s in sentences) / len(sentences)
