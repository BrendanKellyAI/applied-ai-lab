"""Builds the S2 E6 dataset and plans its calls.

S1 E7's filler, insertion, and prompt, reused rather than rebuilt: the same pinned books (with
one replacement, see config.yaml), the same sentence-boundary insertion in `o200k_base` tokens,
and the same system prompt. What is new is several inserted sentences per document, in four
shapes:

1. single: one maintenance code, as S1 E7.
2. distractors: the same sentence, plus four look-alikes for ids one edit from the target.
3. two-fact: where the turbine is stored, and the access code for that hangar, far apart.
4. two-fact-distractors: shape 3, plus look-alikes for both steps.

Paired design: for a given book, fact set, and length, every shape uses the same filler
passage, and each sentence sits at the same position at every length. Only the inserted
sentences change.

Every check in the build specification (section 3.3) fails the build rather than warning. A
SHA-256 of every document is written to results/dataset_manifest.json, which is committed; the
documents themselves contain Gutenberg text and are gitignored. Check a rebuild against the
manifest without making any API calls:

    uv run python field-notes/s2-e6-distractors-and-two-facts/build_dataset.py --check
"""

import argparse
import hashlib
import json
import random
import re
import sys
from bisect import bisect_left
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from lab.config import ExperimentConfig, load_config
from lab.estimate import default_token_counter
from lab.experiments import load_sibling
from lab.metadata import DatasetSource
from lab.plan import PlannedCall, build_request, make_call_id

HERE = Path(__file__).parent
# S1 E7's builder supplies the books, the filler, and the sentence boundaries. Its private
# helpers are used as they are, so both episodes cut filler in exactly the same way.
S1E7 = load_sibling(HERE.parent / "s1-e7-lost-in-the-middle" / "build_dataset.py")
LOOKALIKES = load_sibling(HERE / "lookalikes.py")

SYSTEM_PROMPT = S1E7.SYSTEM_PROMPT
MODE = "standard"
SHAPES = ("single", "distractors", "two-fact", "two-fact-distractors")
SHAPE_LABELS = {
    "single": "Single",
    "distractors": "Distractors",
    "two-fact": "Two-fact",
    "two-fact-distractors": "Two-fact + distractors",
}
TWO_FACT_SHAPES = frozenset({"two-fact", "two-fact-distractors"})

DATASET_DIR = "dataset"
DOCUMENTS_FILE = "documents.jsonl"
MANIFEST_PATH = Path("results") / "dataset_manifest.json"

DISTRACTORS = 4  # look-alike ids per fact set: all four in shape 2, the first two in shape 4
BRIDGED_LOOK_ALIKES = 2  # shape 4: look-alike bridges, each with an access code
UNBRIDGED_HANGARS = 2  # shape 4: further access codes for hangars no turbine is stored in
# Hangars are a digit and a letter, such as 6B. Plain numbers would not do: Moby Dick numbers its
# chapters to 135, so every two-digit number is already in its text.
HANGAR_DIGITS = "123456789"
VALUE_RANGE = (1000, 9999)
# Tries before giving up on spreading sentences under the gap rule. Never reached in practice.
PLACEMENT_TRIES = 1000
DatasetError = S1E7.DatasetError
# Set by tests to build a small dataset. None means the lengths in the config.
CONTEXT_LENGTH_OVERRIDE: tuple[int, ...] | None = None


@dataclass(frozen=True)
class FactSet:
    """Everything invented for one item, and where each sentence goes, in percent."""

    item: int
    book_id: int
    identifier: str
    hangar: str
    maintenance_code: str
    access_code: str
    look_alikes: tuple[str, ...]
    look_alike_codes: tuple[str, ...]  # maintenance codes for the look-alikes, shape 2
    look_alike_hangars: tuple[str, ...]  # first two hold look-alike turbines; last two none
    look_alike_access_codes: tuple[str, ...]  # one per look-alike hangar, shape 4
    bridge_first: bool
    target_position: float
    distractor_positions: tuple[float, ...]
    bridge_position: float
    answer_position: float
    combined_positions: tuple[float, ...]  # shape 4: two look-alike bridges, then four codes


@dataclass(frozen=True)
class Insert:
    role: str
    sentence: str
    position: float


@dataclass(frozen=True)
class Document:
    item: int
    shape: str
    context_length_tokens: int
    book_id: int
    text: str
    actual_tokens: int
    # (role, target position, achieved position) for every inserted sentence
    placements: tuple[tuple[str, float, float], ...]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


# Sentences and questions ------------------------------------------------------------------


def maintenance(identifier: str, value: str) -> str:
    return f"The maintenance code for turbine {identifier} is {value}."


def bridge(identifier: str, hangar: str) -> str:
    return f"Turbine {identifier} is stored in hangar {hangar}."


def access(hangar: str, value: str) -> str:
    return f"The access code for hangar {hangar} is {value}."


def question(fact: FactSet, shape: str) -> str:
    if shape in TWO_FACT_SHAPES:
        return f"What is the access code for the hangar where turbine {fact.identifier} is stored?"
    return f"What is the maintenance code for turbine {fact.identifier}?"


def expected(fact: FactSet, shape: str) -> str:
    return fact.access_code if shape in TWO_FACT_SHAPES else fact.maintenance_code


def distractor_values(fact: FactSet, shape: str) -> tuple[str, ...]:
    """Every value that appears only in a look-alike sentence of this shape."""
    if shape == "distractors":
        return fact.look_alike_codes
    if shape == "two-fact-distractors":
        return (*fact.look_alike_hangars, *fact.look_alike_access_codes)
    return ()


def intermediate(fact: FactSet, shape: str) -> str | None:
    """The hangar the turbine is stored in: the value a two-fact question passes through."""
    return fact.hangar if shape in TWO_FACT_SHAPES else None


def inserts(fact: FactSet, shape: str) -> tuple[Insert, ...]:
    """The sentences a shape inserts, with their roles and target positions."""
    target = Insert(
        "target", maintenance(fact.identifier, fact.maintenance_code), fact.target_position
    )
    if shape == "single":
        return (target,)
    if shape == "distractors":
        return (
            target,
            *(
                Insert("distractor", maintenance(alike, code), position)
                for alike, code, position in zip(
                    fact.look_alikes,
                    fact.look_alike_codes,
                    fact.distractor_positions,
                    strict=True,
                )
            ),
        )
    pair = (
        Insert("bridge", bridge(fact.identifier, fact.hangar), fact.bridge_position),
        Insert("answer", access(fact.hangar, fact.access_code), fact.answer_position),
    )
    if shape == "two-fact":
        return pair
    bridges = tuple(
        Insert("bridge-distractor", bridge(alike, hangar), position)
        for alike, hangar, position in zip(
            fact.look_alikes[:BRIDGED_LOOK_ALIKES],
            fact.look_alike_hangars[:BRIDGED_LOOK_ALIKES],
            fact.combined_positions[:BRIDGED_LOOK_ALIKES],
            strict=True,
        )
    )
    codes = tuple(
        Insert("answer-distractor", access(hangar, code), position)
        for hangar, code, position in zip(
            fact.look_alike_hangars,
            fact.look_alike_access_codes,
            fact.combined_positions[BRIDGED_LOOK_ALIKES:],
            strict=True,
        )
    )
    return (*pair, *bridges, *codes)


# Fact sets --------------------------------------------------------------------------------


_RUN = re.compile(r"[0-9a-z]+")
_ID = re.compile(r"(?<![0-9a-z])[a-z]-[0-9]{3}(?![0-9a-z])")


def whole_tokens(text: str) -> Counter:
    """How often each whole token appears, by the rule the scorer uses.

    The scorer counts a value as present when it is not touching another letter or digit. For a
    value of letters and digits, such as 8352 or 6B, that is a maximal run of them; for an id,
    such as K-417, it is a letter, a hyphen, and three digits with nothing alphanumeric either
    side. One pass over the text, rather than one search per value.
    """
    lowered = text.lower()
    return Counter(_RUN.findall(lowered)) + Counter(_ID.findall(lowered))


def _present(tokens: Counter, value: str) -> bool:
    return tokens[value.lower()] > 0


class _Drawer:
    """Seeded draws that skip anything already used in the item or present in the book."""

    def __init__(self, rng: random.Random, book_text: str) -> None:
        self.rng = rng
        self.tokens = whole_tokens(book_text)
        self.used: set[str] = set()

    def fresh(self, candidate: str) -> bool:
        return candidate not in self.used and not _present(self.tokens, candidate)

    def take(self, make) -> str:
        while True:
            candidate = make()
            if self.fresh(candidate):
                self.used.add(candidate)
                return candidate

    def number(self, low: int, high: int) -> str:
        return self.take(lambda: str(self.rng.randint(low, high)))

    def numbers(self, low: int, high: int, count: int) -> tuple[str, ...]:
        return tuple(self.number(low, high) for _ in range(count))

    def hangar(self) -> str:
        letters = LOOKALIKES.LETTERS
        return self.take(lambda: f"{self.rng.choice(HANGAR_DIGITS)}{self.rng.choice(letters)}")

    def look_alikes(self, target: str, count: int) -> tuple[str, ...]:
        while True:
            drawn = LOOKALIKES.look_alikes(target, count, self.rng)
            if all(self.fresh(alike) for alike in drawn):
                self.used.update(drawn)
                return tuple(drawn)


def spread(rng: random.Random, fixed: Sequence[float], count: int, gap: float) -> tuple[float, ...]:
    """`count` positions in 0% to 100%, at least `gap` points from `fixed` and from each other.

    Each position is drawn uniformly from what is still allowed, to one decimal place.
    """
    for _ in range(PLACEMENT_TRIES):
        chosen: list[float] = []
        for _ in range(count):
            taken = [*fixed, *chosen]
            allowed = [
                position / 10
                for position in range(0, 1001)
                if all(abs(position / 10 - other) >= gap for other in taken)
            ]
            if not allowed:
                break
            chosen.append(rng.choice(allowed))
        if len(chosen) == count:
            return tuple(chosen)
    raise DatasetError(f"Cannot place {count} sentences {gap} points apart around {fixed}")


def _between(rng: random.Random, bounds: Sequence[float]) -> float:
    return round(rng.uniform(bounds[0], bounds[1]), 1)


def make_fact_set(
    rng: random.Random, item: int, book_id: int, book_text: str, parameters: dict
) -> FactSet:
    """One item's invented facts and positions, from the seeded generator.

    Nothing drawn is in the book text or repeated within the item, so every value names exactly
    one sentence in every document built from it.
    """
    draw = _Drawer(rng, book_text)
    letters = LOOKALIKES.LETTERS
    identifier = draw.take(lambda: f"{rng.choice(letters)}-{rng.randint(100, 999)}")
    hangar = draw.hangar()
    maintenance_code, access_code = draw.numbers(*VALUE_RANGE, 2)
    alikes = draw.look_alikes(identifier, DISTRACTORS)
    alike_codes = draw.numbers(*VALUE_RANGE, DISTRACTORS)
    alike_hangars = tuple(draw.hangar() for _ in range(BRIDGED_LOOK_ALIKES + UNBRIDGED_HANGARS))
    alike_access = draw.numbers(*VALUE_RANGE, BRIDGED_LOOK_ALIKES + UNBRIDGED_HANGARS)

    gap = float(parameters["min_gap_points"])
    target_position = _between(rng, parameters["target_range_percent"])
    early = _between(rng, parameters["early_range_percent"])
    late = _between(rng, parameters["late_range_percent"])
    # Alternates within each book, so each book has one item of each order: 6 against 6.
    bridge_first = item % 2 == 0
    bridge_position, answer_position = (early, late) if bridge_first else (late, early)
    return FactSet(
        item=item,
        book_id=book_id,
        identifier=identifier,
        hangar=hangar,
        maintenance_code=maintenance_code,
        access_code=access_code,
        look_alikes=alikes,
        look_alike_codes=alike_codes,
        look_alike_hangars=alike_hangars,
        look_alike_access_codes=alike_access,
        bridge_first=bridge_first,
        target_position=target_position,
        distractor_positions=spread(rng, [target_position], DISTRACTORS, gap),
        bridge_position=bridge_position,
        answer_position=answer_position,
        combined_positions=spread(
            rng,
            [bridge_position, answer_position],
            BRIDGED_LOOK_ALIKES + 2 * UNBRIDGED_HANGARS,
            gap,
        ),
    )


# Filler and insertion ---------------------------------------------------------------------


class Filler:
    """One trimmed filler passage, with its tokens and sentence boundaries worked out once."""

    def __init__(self, text: str, count_tokens) -> None:
        self.text = text
        self.count_tokens = count_tokens
        encoding = S1E7._encoding()
        self.tokens = encoding.encode(text, disallowed_special=())
        self.boundaries = [0, *S1E7.sentence_boundaries(text), len(text)]
        self.whole_tokens = whole_tokens(text)
        self._achieved: dict[int, float] = {}

    def boundary(self, position: float) -> int:
        """The sentence boundary closest to `position` percent of the filler, in tokens."""
        if position <= 0:
            return 0
        if position >= 100:
            return len(self.text)
        encoding = S1E7._encoding()
        target_index = round(len(self.tokens) * position / 100)
        target_chars = len(encoding.decode(self.tokens[:target_index]))
        at = bisect_left(self.boundaries, target_chars)
        nearby = self.boundaries[max(0, at - 1) : at + 1]
        return min(nearby, key=lambda boundary: (abs(boundary - target_chars), boundary))

    def achieved(self, boundary: int) -> float:
        """The share of the filler before `boundary`, in tokens, as S1 E7 measured it."""
        if boundary not in self._achieved:
            before = self.text[:boundary].rstrip()
            self._achieved[boundary] = 100.0 * self.count_tokens(before) / len(self.tokens)
        return self._achieved[boundary]


def place(filler: Filler, sentences: Sequence[Insert]) -> tuple[str, tuple]:
    """Insert every sentence at its boundary. Returns the document and each placement."""
    located = sorted(
        ((filler.boundary(insert.position), insert) for insert in sentences),
        key=lambda pair: pair[0],
    )
    boundaries = [boundary for boundary, _ in located]
    if len(set(boundaries)) != len(boundaries):
        raise DatasetError("Two inserted sentences landed on the same sentence boundary")
    pieces: list[str] = []
    start = 0
    for boundary, insert in located:
        pieces += [filler.text[start:boundary].strip(), insert.sentence]
        start = boundary
    pieces.append(filler.text[start:].strip())
    placements = tuple(
        (insert.role, insert.position, round(filler.achieved(boundary), 3))
        for boundary, insert in located
    )
    return " ".join(piece for piece in pieces if piece), placements


def _insert_tokens(fact: FactSet, shape: str, count_tokens) -> int:
    return sum(count_tokens(f" {insert.sentence} ") for insert in inserts(fact, shape))


# Checks -----------------------------------------------------------------------------------


def edit_distance(a: str, b: str) -> int:
    """Optimal string alignment distance: substitutions, insertions, deletions, and swaps of
    two neighbouring characters each count as one edit."""
    rows = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            best = min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, rows[i - 2][j - 2] + 1)
            rows[i][j] = best
    return rows[len(a)][len(b)]


def check_fact_set(fact: FactSet) -> None:
    """Section 3.3 checks that need only the fact set."""
    for alike in fact.look_alikes:
        if edit_distance(alike, fact.identifier) != 1:
            raise DatasetError(f"{alike} is not exactly one edit from {fact.identifier}")
    values = [
        fact.identifier,
        fact.hangar,
        fact.maintenance_code,
        fact.access_code,
        *fact.look_alikes,
        *fact.look_alike_codes,
        *fact.look_alike_hangars,
        *fact.look_alike_access_codes,
    ]
    if len(set(values)) != len(values):
        raise DatasetError(f"Item {fact.item} repeats an id, hangar, or value")
    for shape in SHAPES:
        asked = whole_tokens(question(fact, shape))
        for value in (expected(fact, shape), intermediate(fact, shape)):
            if value is not None and _present(asked, value):
                raise DatasetError(f"Item {fact.item} {shape}: the question contains {value}")
        clash = {expected(fact, shape), fact.hangar} & set(distractor_values(fact, shape))
        if clash:
            raise DatasetError(f"Item {fact.item} {shape}: a distractor value equals {clash}")


def check_document(document: Document, fact: FactSet, filler: Filler, parameters: dict) -> None:
    """Section 3.3 checks on one built document: absence from the filler, uniqueness, length,
    and position."""
    sentences = inserts(fact, document.shape)
    in_document = whole_tokens(document.text)
    # A hangar is named twice, deliberately: in its bridge and in its access code.
    allowed = sum((whole_tokens(insert.sentence) for insert in sentences), Counter())
    for insert in sentences:
        for value in re.findall(r"[A-Z]-\d{3}|\d+[A-Z]?", insert.sentence):
            if _present(filler.whole_tokens, value):
                raise DatasetError(f"{value} appears in the book text (item {fact.item})")
            if in_document[value.lower()] != allowed[value.lower()]:
                raise DatasetError(f"{value} is not unique in item {fact.item} {document.shape}")
    deviation = abs(document.actual_tokens / document.context_length_tokens - 1) * 100
    if deviation > parameters["length_tolerance_percent"]:
        raise DatasetError(
            f"Item {fact.item} {document.shape} at {document.context_length_tokens:,}: "
            f"{document.actual_tokens:,} tokens is {deviation:.2f}% from target"
        )
    for role, target, achieved in document.placements:
        if abs(achieved - target) > parameters["position_tolerance_points"]:
            raise DatasetError(
                f"Item {fact.item} {document.shape} {role}: placed at {achieved:.2f}%, "
                f"target {target}%"
            )


# Build ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Dataset:
    fact_sets: tuple[FactSet, ...]
    documents: tuple[Document, ...]
    books: tuple


def _books(config: ExperimentConfig) -> tuple:
    return tuple(S1E7.Book.from_config(entry) for entry in config.parameters["filler_books"])


def build_dataset(
    config: ExperimentConfig,
    folder: Path,
    *,
    lengths: Sequence[int] | None = None,
    cache_dir: Path | None = None,
    write: bool = True,
) -> Dataset:
    """Build every fact set and document, run every check, and write the dataset and manifest.

    Makes no API calls.
    """
    parameters = config.parameters
    count_tokens = default_token_counter()
    encoding = S1E7._encoding()
    targets = tuple(sorted(lengths or parameters["context_lengths_tokens"]))
    rng = random.Random(config.seed)
    cache = cache_dir or S1E7.GUTENBERG_CACHE
    per_book = int(parameters["fact_sets_per_book"])

    fact_sets: list[FactSet] = []
    documents: list[Document] = []
    for book_index, book in enumerate(_books(config)):
        passage = S1E7._passage(S1E7._normalise(S1E7.load_book(book, cache)))
        # The longest filler any document uses, a little over the longest target: every
        # shorter filler is its prefix, so a value absent here is absent from all of them.
        longest = encoding.decode(
            encoding.encode(passage, disallowed_special=())[: int(targets[-1] * 1.05)]
        )
        for offset in range(per_book):
            fact = make_fact_set(rng, book_index * per_book + offset, book.id, longest, parameters)
            check_fact_set(fact)
            fact_sets.append(fact)
            # Centred between the shortest and the longest shape, so every shape lands close
            # to the target length.
            inserted = (
                _insert_tokens(fact, "single", count_tokens)
                + _insert_tokens(fact, "two-fact-distractors", count_tokens)
            ) // 2
            for target in targets:
                filler = Filler(
                    S1E7._trim_to_tokens(passage, target - inserted, count_tokens), count_tokens
                )
                for shape in SHAPES:
                    text, placements = place(filler, inserts(fact, shape))
                    document = Document(
                        item=fact.item,
                        shape=shape,
                        context_length_tokens=target,
                        book_id=book.id,
                        text=text,
                        actual_tokens=count_tokens(text),
                        placements=placements,
                    )
                    check_document(document, fact, filler, parameters)
                    documents.append(document)

    dataset = Dataset(fact_sets=tuple(fact_sets), documents=tuple(documents), books=_books(config))
    if write:
        _write(dataset, folder, config)
    return dataset


def deviations(documents: Sequence[Document]) -> dict[str, float]:
    """The largest length and position deviations achieved, for the README."""
    return {
        "max_length_deviation_percent": round(
            max(abs(d.actual_tokens / d.context_length_tokens - 1) * 100 for d in documents), 3
        ),
        "max_position_deviation_points": round(
            max(abs(achieved - target) for d in documents for _, target, achieved in d.placements),
            3,
        ),
    }


def manifest(dataset: Dataset, config: ExperimentConfig) -> dict:
    """What the build made, without any Gutenberg text: committed as the rebuild check."""
    return {
        "experiment": config.experiment,
        "seed": config.seed,
        "tokeniser": "o200k_base",
        "front_matter_fraction": S1E7.FRONT_MATTER_FRACTION,
        "mirror": S1E7.MIRROR,
        "books": [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "sha256": book.sha256,
                "licence": S1E7.LICENCE,
                "url": S1E7.mirror_url(book.id),
            }
            for book in dataset.books
        ],
        **deviations(dataset.documents),
        "fact_sets": [asdict(fact) for fact in dataset.fact_sets],
        "documents": [
            {
                "item": d.item,
                "shape": d.shape,
                "context_length_tokens": d.context_length_tokens,
                "book_id": d.book_id,
                "actual_tokens": d.actual_tokens,
                "placements": [list(placement) for placement in d.placements],
                "sha256": d.sha256,
            }
            for d in dataset.documents
        ],
    }


def _dump(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _write(dataset: Dataset, folder: Path, config: ExperimentConfig) -> None:
    out = folder / DATASET_DIR
    out.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "item": d.item,
                "shape": d.shape,
                "context_length_tokens": d.context_length_tokens,
                "text": d.text,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        for d in dataset.documents
    ]
    (out / DOCUMENTS_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    path = folder / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump(manifest(dataset, config)), encoding="utf-8", newline="\n")


def load_manifest(folder: Path) -> dict | None:
    path = folder / MANIFEST_PATH
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def fact_sets_from(manifest_data: dict) -> tuple[FactSet, ...]:
    """The fact sets recorded in a manifest, so analysis needs no Gutenberg text."""
    fields = FactSet.__dataclass_fields__
    return tuple(
        FactSet(
            **{
                key: tuple(value) if isinstance(value, list) else value
                for key, value in entry.items()
                if key in fields
            }
        )
        for entry in manifest_data["fact_sets"]
    )


def _load_documents(folder: Path, manifest_data: dict) -> dict[tuple, str] | None:
    """Built document texts keyed by (item, shape, length), if they match the manifest."""
    path = folder / DATASET_DIR / DOCUMENTS_FILE
    if not path.exists():
        return None
    texts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            key = (entry["item"], entry["shape"], entry["context_length_tokens"])
            texts[key] = entry["text"]
    for entry in manifest_data["documents"]:
        key = (entry["item"], entry["shape"], entry["context_length_tokens"])
        text = texts.get(key)
        if text is None or hashlib.sha256(text.encode("utf-8")).hexdigest() != entry["sha256"]:
            return None
    return texts


def user_prompt(document: str, asked: str) -> str:
    """S1 E7's prompt: the document in tags, then the question."""
    return f"<document>\n{document}\n</document>\n\nQuestion: {asked}"


def run_lengths(config: ExperimentConfig) -> list[int]:
    """The lengths the run calls: `run_lengths_tokens` if set, otherwise every built length."""
    parameters = config.parameters
    built = CONTEXT_LENGTH_OVERRIDE or parameters["context_lengths_tokens"]
    return sorted(parameters.get("run_lengths_tokens", built))


def run_items(config: ExperimentConfig) -> list[int]:
    """The items the run calls: `run_items` if set, otherwise every item."""
    parameters = config.parameters
    every = len(parameters["filler_books"]) * int(parameters["fact_sets_per_book"])
    return sorted(parameters.get("run_items", range(every)))


def in_run(config: ExperimentConfig, length: int, item: int) -> bool:
    return length in run_lengths(config) and item in run_items(config)


def plan_calls(config: ExperimentConfig, folder: Path) -> list[PlannedCall]:
    """Every planned call: one per model and shape, at each run length and item.

    The dataset is always built in full, so the manifest check covers every document; the run
    calls only the subset the config names (see config.yaml).

    Uses the built documents when they match the committed manifest, and builds them otherwise,
    so `lab run` and `lab estimate` both work from a fresh clone.
    """
    manifest_data = load_manifest(folder)
    texts = _load_documents(folder, manifest_data) if manifest_data else None
    if texts is None:
        dataset = build_dataset(config, folder, lengths=CONTEXT_LENGTH_OVERRIDE)
        manifest_data = manifest(dataset, config)
        texts = {(d.item, d.shape, d.context_length_tokens): d.text for d in dataset.documents}
    facts = fact_sets_from(manifest_data)

    calls: list[PlannedCall] = []
    for entry in manifest_data["documents"]:
        if not in_run(config, entry["context_length_tokens"], entry["item"]):
            continue
        fact = facts[entry["item"]]
        shape = entry["shape"]
        key = (entry["item"], shape, entry["context_length_tokens"])
        prompt = user_prompt(texts[key], question(fact, shape))
        cell = {
            "shape": shape,
            "context_length_tokens": entry["context_length_tokens"],
            "item": entry["item"],
        }
        for model in config.models:
            calls.append(
                PlannedCall(
                    call_id=make_call_id(model_label=model.display_label, mode=MODE, cell=cell),
                    model_label=model.display_label,
                    mode=MODE,
                    cell=cell,
                    request=build_request(
                        model,
                        MODE,
                        prompt=prompt,
                        system=SYSTEM_PROMPT,
                        metadata={"experiment": config.experiment},
                    ),
                )
            )
    return calls


def dataset_sources(config: ExperimentConfig, folder: Path) -> list[DatasetSource]:
    """What went into the dataset, recorded in run_metadata.json."""
    return [
        DatasetSource(
            name=f"{book.title} by {book.author} (Project Gutenberg {book.id})",
            version=f"mirror file {book.id}-0.txt",
            licence=S1E7.LICENCE,
            url=S1E7.mirror_url(book.id),
            checksum=f"sha256:{book.sha256}",
        )
        for book in _books(config)
    ]


def check_rebuild(config: ExperimentConfig, folder: Path) -> list[str]:
    """Rebuild without writing and compare with the committed manifest. Returns differences."""
    committed = load_manifest(folder)
    if committed is None:
        return [f"No manifest at {folder / MANIFEST_PATH}"]
    # Through JSON, so tuples compare equal to the lists the committed file holds.
    rebuilt = json.loads(_dump(manifest(build_dataset(config, folder, write=False), config)))
    if rebuilt == committed:
        return []
    keys = sorted(key for key in {*rebuilt, *committed} if rebuilt.get(key) != committed.get(key))
    return [f"Manifest differs in: {', '.join(keys)}"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="Rebuild and compare with the committed manifest."
    )
    args = parser.parse_args(argv)
    config = load_config(HERE / "config.yaml")
    if args.check:
        differences = check_rebuild(config, HERE)
        print("\n".join(differences) or "Rebuild matches results/dataset_manifest.json.")
        return 1 if differences else 0
    built = build_dataset(config, HERE)
    print(f"Built {len(built.documents)} documents for {len(built.fact_sets)} fact sets.")
    print(json.dumps(deviations(built.documents)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
