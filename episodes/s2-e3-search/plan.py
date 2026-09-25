"""The parts of S2 E3 that are fixed in code before any model is called.

Identifiers and their look-alikes, which article gets which brief, which articles carry which
question type, and the word checks. Nothing here calls a model or the network.
"""

import random
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CONFIG = HERE / "config.yaml"

KINDS = {"error code": "E", "part number": "KX"}
IDENTIFIER = re.compile(r"\b(?:E|KX)-\d{4}\b")
WORD = re.compile(r"\w+")


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# Identifiers --------------------------------------------------------------------------------


def one_digit_apart(a: str, b: str) -> bool:
    """Same prefix, and the digits differ by one changed digit or one swap of adjacent digits."""
    prefix_a, digits_a = a.split("-")
    prefix_b, digits_b = b.split("-")
    if prefix_a != prefix_b or digits_a == digits_b:
        return False
    differ = [i for i in range(4) if digits_a[i] != digits_b[i]]
    if len(differ) == 1:
        return True
    if len(differ) != 2:
        return False
    i, j = differ
    return j == i + 1 and digits_a[i] == digits_b[j] and digits_a[j] == digits_b[i]


def _swap(digits: str, rng: random.Random) -> str | None:
    options = [i for i in range(3) if digits[i] != digits[i + 1]]
    if not options:
        return None
    i = rng.choice(options)
    return digits[:i] + digits[i + 1] + digits[i] + digits[i + 2 :]


def _change(digits: str, rng: random.Random) -> str:
    i = rng.randrange(4)
    new = rng.choice([d for d in "0123456789" if d != digits[i]])
    return digits[:i] + new + digits[i + 1 :]


@dataclass(frozen=True)
class IdentifierGroup:
    kind: str
    target: str
    lookalikes: tuple[str, ...]

    @property
    def members(self) -> tuple[str, ...]:
        return (self.target, *self.lookalikes)


def make_identifier_groups(seed: int, count: int) -> list[IdentifierGroup]:
    """`count` targets, alternating error codes and part numbers, each with one look-alike made
    by swapping two adjacent digits and one made by changing a digit.

    No identifier is one digit apart from any identifier outside its own group, so the only
    near-misses in the corpus are the intended ones.
    """
    rng = random.Random(seed)
    groups: list[IdentifierGroup] = []
    used: list[str] = []
    while len(groups) < count:
        kind = list(KINDS)[len(groups) % 2]
        prefix = KINDS[kind]
        digits = f"{rng.randint(1000, 9999)}"
        swapped = _swap(digits, rng)
        if swapped is None:
            continue
        changed = _change(digits, rng)
        members = [f"{prefix}-{d}" for d in (digits, swapped, changed)]
        if len(set(members)) < 3 or changed == swapped:
            continue
        if any(m == u or one_digit_apart(m, u) for m in members for u in used):
            continue
        groups.append(IdentifierGroup(kind, members[0], tuple(members[1:])))
        used += members
    return groups


# Briefs and roles ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Brief:
    article_id: str
    product: str
    topic: str
    identifier: str | None = None
    kind: str | None = None
    # "target" or "lookalike" for identifier articles, else None.
    role: str | None = None
    group: int | None = None


def make_briefs(config: dict) -> list[Brief]:
    """Every article's brief, in a fixed order: identifier groups first, then the rest."""
    rng = random.Random(config["seed"])
    pairs = [(p, t) for p in config["products"] for t in config["topics"]]
    rng.shuffle(pairs)
    pairs = pairs[: config["articles"]]
    groups = make_identifier_groups(config["seed"], config["identifier_targets"])
    briefs = []
    for g, group in enumerate(groups):
        for m, identifier in enumerate(group.members):
            product, topic = pairs[len(briefs)]
            briefs.append(
                Brief(f"A{len(briefs):03d}", product, topic, identifier, group.kind,
                      "target" if m == 0 else "lookalike", g)
            )
    while len(briefs) < len(pairs):
        product, topic = pairs[len(briefs)]
        briefs.append(Brief(f"A{len(briefs):03d}", product, topic))
    return briefs


def question_plan(config: dict, briefs: list[Brief]) -> dict[str, list[str]]:
    """The article ids each question type is asked about, in order."""
    n = config["questions_per_type"]
    plain = [b.article_id for b in briefs if b.identifier is None]
    return {
        "identifier": [b.article_id for b in briefs if b.role == "target"][:n],
        "paraphrase": plain[:n],
        "shared": plain[n : 2 * n],
    }


def pilot_selection(config: dict, briefs: list[Brief]) -> tuple[list[Brief], dict[str, list[str]]]:
    """The pilot's articles and questions: a subset of the full run, so nothing is paid twice."""
    pilot = config["pilot"]
    full = question_plan(config, briefs)
    q = pilot["questions_per_type"]
    groups = set(range(pilot["identifier_targets"]))
    chosen = {b.article_id for b in briefs if b.group in groups}
    plan = {
        "identifier": [a for a in full["identifier"] if a in chosen][:q],
        "paraphrase": full["paraphrase"][:q],
        "shared": full["shared"][:q],
    }
    remaining = pilot["articles"] - len(chosen)
    half = remaining // 2
    chosen |= set(full["paraphrase"][:half]) | set(full["shared"][: remaining - half])
    return [b for b in briefs if b.article_id in chosen], plan


# Word checks --------------------------------------------------------------------------------


def words(text: str) -> list[str]:
    """Lower-cased runs of word characters: how BM25 is tokenised, so E-4471 is e and 4471."""
    return WORD.findall(text.lower())


def content_words(text: str, stop_words: set[str]) -> set[str]:
    return set(words(text)) - stop_words


def shared_words(question: str, article: str, stop_words: set[str]) -> set[str]:
    return content_words(question, stop_words) & content_words(article, stop_words)


def identifiers_in(text: str) -> list[str]:
    return IDENTIFIER.findall(text)
