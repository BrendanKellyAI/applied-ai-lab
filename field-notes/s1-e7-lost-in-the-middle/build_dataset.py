"""Builds the S1 E7 dataset and plans its calls.

The dataset is fully synthetic facts inserted into public-domain filler text, so nothing here
is under licence and no answer can have appeared in training data.

Paired design: one book per fact, so the same six filler passages carry every position and
length. Only the position of the fact changes within a fact and length, which gives tighter
comparisons from six calls per cell.

Filler text is downloaded from a Project Gutenberg mirror, never from the main site, which is
for human users only under Project Gutenberg's robot policy. Book identifiers are pinned in
config.yaml with the SHA-256 of the mirror file: a download that does not match fails the
build. Built files are gitignored, because they contain Gutenberg text; rerun this builder to
recreate them, byte for byte, from the same seed.

Run directly to build the dataset without making any API calls:

    uv run python field-notes/s1-e7-lost-in-the-middle/build_dataset.py
"""

import hashlib
import json
import random
import re
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from lab.config import ExperimentConfig, load_config
from lab.estimate import default_token_counter  # noqa: F401  (documents the shared tokeniser)
from lab.metadata import DatasetSource
from lab.plan import PlannedCall, build_request, make_call_id

# A mirror, not www.gutenberg.org: the main site blocks automated access.
# Mirror list: https://www.gutenberg.org/MIRRORS.ALL
MIRROR = "https://gutenberg.pglaf.org"
DOWNLOAD_TIMEOUT_SECONDS = 120.0
USER_AGENT = "applied-ai-lab/0.1 (research; contact via github.com/BrendanKellyAI)"

# Project Gutenberg wraps each work in these markers. Everything outside them, including the
# trademark licence, is stripped, leaving only the public-domain work.
START_MARKER = re.compile(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.DOTALL)
END_MARKER = re.compile(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.DOTALL)

# Each passage starts this far into the stripped text, so title pages, prefaces, contents
# lists, and illustration captions are left out and the filler is prose from the first line.
FRONT_MATTER_FRACTION = 0.10
# A sentence ends at one of these, followed by whitespace.
SENTENCE_END = re.compile(r"[.!?][\"'”’)\]]*\s")
# The word before the full stop, used to reject abbreviations such as "Mrs." as sentence ends.
WORD_BEFORE_STOP = re.compile(r"([A-Za-z]+)\.[\"'”’)\]]*\s*$")
# Titles and abbreviations that end in a full stop mid-sentence. Inserting a fact after one of
# these would split a name, for example "Mrs. <fact> Bennet", so they are not boundaries.
ABBREVIATIONS = frozenset(
    # Titles
    ["mr", "mrs", "ms", "messrs", "mme", "mlle", "dr", "prof", "rev", "hon", "esq", "jr", "sr"]
    # Ranks
    + ["capt", "col", "lieut", "lt", "sgt", "gen", "maj", "adm"]
    # Places and references
    + ["st", "mt", "ave", "rd", "no", "vol", "ch", "pp", "fig", "dept"]
    # Latin
    + ["vs", "etc", "ie", "eg", "viz", "cf", "al", "inst", "ult"]
)
# Characters examined before a full stop when checking for an abbreviation. Longer than the
# longest entry above plus its trailing quotes.
LOOKBACK_CHARACTERS = 24

LICENCE = (
    "Public domain in the United States. Project Gutenberg header and footer removed, so the "
    "Project Gutenberg trademark and its licence do not apply to the extracted text. Licence "
    "terms checked 17 September 2026: https://www.gutenberg.org/policy/permission.html"
)

SYSTEM_PROMPT = "Answer using only the document provided. Reply with the value only."
MODE = "standard"

DATASET_DIR = "dataset"
DOCUMENTS_FILE = "documents.jsonl"
MANIFEST_FILE = "manifest.json"
FACTS_FILE = "facts.json"

# Identifier letters, leaving out I, O, and Q, which read as digits in a four-digit answer.
IDENTIFIER_LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"
# Downloaded books are kept here, so a rebuild makes no new requests to the mirror. Gitignored.
GUTENBERG_CACHE = Path(".cache") / "gutenberg"
# Set by tests to build a small dataset. None means the lengths in the config.
CONTEXT_LENGTH_OVERRIDE: tuple[int, ...] | None = None


class DatasetError(RuntimeError):
    """The dataset cannot be built as specified."""


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    sha256: str

    @classmethod
    def from_config(cls, entry: dict) -> "Book":
        return cls(
            id=int(entry["id"]),
            title=str(entry["title"]),
            author=str(entry["author"]),
            sha256=str(entry["sha256"]),
        )


@dataclass(frozen=True)
class Fact:
    identifier: str
    value: str

    @property
    def sentence(self) -> str:
        return f"The maintenance code for turbine {self.identifier} is {self.value}."

    @property
    def question(self) -> str:
        return f"What is the maintenance code for turbine {self.identifier}?"


@dataclass(frozen=True)
class Document:
    fact_index: int
    context_length_tokens: int
    position_percent: int
    text: str
    actual_tokens: int
    actual_position_percent: float
    book_id: int


@dataclass(frozen=True)
class Dataset:
    facts: tuple[Fact, ...]
    documents: tuple[Document, ...]
    books: tuple[Book, ...]


def make_facts(seed: int, count: int) -> tuple[Fact, ...]:
    """Invented turbine codes, generated from the seed so every reader builds the same set."""
    rng = random.Random(seed)
    facts: list[Fact] = []
    identifiers: set[str] = set()
    values: set[str] = set()
    while len(facts) < count:
        identifier = f"{rng.choice(IDENTIFIER_LETTERS)}-{rng.randint(100, 999)}"
        value = f"{rng.randint(1000, 9999)}"
        if identifier in identifiers or value in values:
            continue
        identifiers.add(identifier)
        values.add(value)
        facts.append(Fact(identifier=identifier, value=value))
    return tuple(facts)


def mirror_url(book_id: int) -> str:
    """The mirror path for a book: every digit but the last becomes a folder."""
    digits = str(book_id)
    folders = "/".join(digits[:-1]) if len(digits) > 1 else "0"
    return f"{MIRROR}/{folders}/{book_id}/{book_id}-0.txt"


def fetch_bytes(url: str, timeout: float = DOWNLOAD_TIMEOUT_SECONDS) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DatasetError(
            f"Could not download {url}: {exc}. Check your connection, or copy the file to the "
            "cache folder by hand."
        ) from exc


def verify_checksum(book: Book, raw: bytes) -> None:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != book.sha256:
        raise DatasetError(
            f"Book {book.id} ({book.title}) does not match its pinned checksum.\n"
            f"  expected {book.sha256}\n  found    {digest}\n"
            "The mirror file has changed. Check the text, then update the sha256 in config.yaml "
            "so every reader builds the same dataset."
        )


def strip_gutenberg(text: str) -> str:
    """The work itself, with the Project Gutenberg header and footer removed."""
    start = START_MARKER.search(text)
    end = END_MARKER.search(text)
    if start is None or end is None:
        raise DatasetError(
            "Project Gutenberg start and end markers not found, so the header and footer "
            "cannot be stripped. Check the downloaded file."
        )
    return text[start.end() : end.start()]


def load_book(book: Book, cache_dir: Path) -> str:
    """The stripped text of one book, downloading it once and caching the raw file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{book.id}-0.txt"
    raw = cached.read_bytes() if cached.exists() else fetch_bytes(mirror_url(book.id))
    verify_checksum(book, raw)
    if not cached.exists():
        cached.write_bytes(raw)
    return strip_gutenberg(raw.decode("utf-8"))


def _normalise(text: str) -> str:
    """Tidy line endings and runs of blank lines, so documents are stable across platforms."""
    tidied = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", tidied).strip()


def _passage(text: str) -> str:
    """The prose of a book, skipping its front matter and starting at a paragraph break."""
    start = int(len(text) * FRONT_MATTER_FRACTION)
    break_at = text.find("\n\n", start)
    return text[(break_at + 2) if break_at != -1 else start :].lstrip()


def _is_sentence_end(text: str, stop: int) -> bool:
    """Whether the full stop at `stop` really ends a sentence, rather than an abbreviation.

    Only the few characters before the stop are examined, so this stays linear over a document
    of 64,000 tokens rather than slicing the whole prefix for every candidate.
    """
    if text[stop] != ".":
        return True  # "!" and "?" are not used in abbreviations here.
    window = text[max(0, stop - LOOKBACK_CHARACTERS) : stop + 1]
    found = WORD_BEFORE_STOP.search(window)
    if found is None:
        return True
    word = found.group(1)
    # A single letter is an initial, as in "J. Smith".
    return len(word) > 1 and word.lower() not in ABBREVIATIONS


def sentence_boundaries(text: str) -> list[int]:
    """Character offsets just after each complete sentence, skipping abbreviations."""
    return [
        match.end()
        for match in SENTENCE_END.finditer(text)
        if _is_sentence_end(text, match.start())
    ]


def _last_sentence_end(text: str) -> int:
    """The character offset just after the last complete sentence in `text`."""
    ends = sentence_boundaries(text)
    return ends[-1] if ends else len(text)


def _nearest_sentence_boundary(text: str, offset: int) -> int:
    """The sentence boundary closest to `offset`, so a fact never splits a sentence."""
    boundaries = [0, *sentence_boundaries(text), len(text)]
    return min(boundaries, key=lambda boundary: (abs(boundary - offset), boundary))


def _trim_to_tokens(passage: str, budget: int, count_tokens) -> str:
    """Filler of at most `budget` tokens, ending at a sentence boundary."""
    encoding = _encoding()
    tokens = encoding.encode(passage, disallowed_special=())
    if len(tokens) < budget:
        raise DatasetError(
            f"Filler passage has only {len(tokens)} tokens, fewer than the {budget} needed. "
            "Pin a longer book in config.yaml."
        )
    candidate = encoding.decode(tokens[:budget])
    trimmed = candidate[: _last_sentence_end(candidate)].rstrip()
    if count_tokens(trimmed) > budget:
        # Decoding can split a character across the budget; drop one more sentence.
        trimmed = trimmed[: _last_sentence_end(trimmed[:-1])].rstrip()
    return trimmed


@cache
def _encoding():
    """The o200k_base encoding, the same one the estimator and the 5% length check use."""
    import tiktoken

    return tiktoken.get_encoding("o200k_base")


def _insert_fact(filler: str, fact: Fact, position_percent: int, count_tokens) -> tuple[str, float]:
    """Insert the fact at the sentence boundary closest to the target position.

    Returns the document and the position actually achieved: the share of the filler that comes
    before the fact, in tokens. 0% is the start of the document and 100% is the end, so a fact
    placed as the first or last sentence sits exactly at 0% or 100%.
    """
    if position_percent <= 0:
        return f"{fact.sentence} {filler}", 0.0
    if position_percent >= 100:
        return f"{filler} {fact.sentence}", 100.0

    # The boundary is chosen in tokens, not characters, because prose varies in how many
    # characters a token covers, and the position tolerance is 2%.
    encoding = _encoding()
    tokens = encoding.encode(filler, disallowed_special=())
    target_index = round(len(tokens) * position_percent / 100)
    target_chars = len(encoding.decode(tokens[:target_index]))
    boundary = _nearest_sentence_boundary(filler, target_chars)
    before, after = filler[:boundary].rstrip(), filler[boundary:].lstrip()
    achieved = 100.0 * count_tokens(before) / len(tokens) if tokens else 0.0
    return f"{before} {fact.sentence} {after}", achieved


def build_dataset(
    config: ExperimentConfig,
    folder: Path,
    *,
    lengths: Sequence[int] | None = None,
    cache_dir: Path | None = None,
) -> Dataset:
    """Build every document and write the dataset. Makes no API calls."""
    count_tokens = default_token_counter()
    books = tuple(Book.from_config(entry) for entry in config.parameters["filler_books"])
    facts = make_facts(config.seed, int(config.parameters["facts_per_cell"]))
    if len(books) < len(facts):
        raise DatasetError(
            f"{len(facts)} facts need {len(facts)} pinned books; config.yaml has {len(books)}."
        )
    targets = tuple(lengths or config.parameters["context_lengths_tokens"])
    positions = tuple(config.parameters["positions_percent"])
    cache = cache_dir or GUTENBERG_CACHE

    documents: list[Document] = []
    for fact_index, fact in enumerate(facts):
        book = books[fact_index]
        passage = _passage(_normalise(load_book(book, cache)))
        fact_tokens = count_tokens(f" {fact.sentence} ")
        for target in sorted(targets):
            filler = _trim_to_tokens(passage, target - fact_tokens, count_tokens)
            for position in positions:
                text, achieved = _insert_fact(filler, fact, position, count_tokens)
                documents.append(
                    Document(
                        fact_index=fact_index,
                        context_length_tokens=target,
                        position_percent=position,
                        text=text,
                        actual_tokens=count_tokens(text),
                        actual_position_percent=round(achieved, 3),
                        book_id=book.id,
                    )
                )

    dataset = Dataset(facts=facts, documents=tuple(documents), books=books)
    _write(dataset, folder, config)
    return dataset


def _write(dataset: Dataset, folder: Path, config: ExperimentConfig) -> None:
    out = folder / DATASET_DIR
    out.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "fact_index": d.fact_index,
                "context_length_tokens": d.context_length_tokens,
                "position_percent": d.position_percent,
                "actual_tokens": d.actual_tokens,
                "actual_position_percent": d.actual_position_percent,
                "book_id": d.book_id,
                "text": d.text,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        for d in dataset.documents
    ]
    (out / DOCUMENTS_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (out / FACTS_FILE).write_text(
        json.dumps(
            [
                {"fact_index": i, "identifier": f.identifier, "value": f.value}
                for i, f in enumerate(dataset.facts)
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (out / MANIFEST_FILE).write_text(
        json.dumps(
            {
                "experiment": config.experiment,
                "seed": config.seed,
                "facts": len(dataset.facts),
                "documents": len(dataset.documents),
                "tokeniser": "o200k_base",
                "front_matter_fraction": FRONT_MATTER_FRACTION,
                "mirror": MIRROR,
                "books": [
                    {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "sha256": book.sha256,
                        "licence": LICENCE,
                        "url": mirror_url(book.id),
                    }
                    for book in dataset.books
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_dataset(folder: Path) -> Dataset | None:
    """A dataset already built in `folder`, or None if it is missing."""
    documents_path = folder / DATASET_DIR / DOCUMENTS_FILE
    facts_path = folder / DATASET_DIR / FACTS_FILE
    manifest_path = folder / DATASET_DIR / MANIFEST_FILE
    if not (documents_path.exists() and facts_path.exists() and manifest_path.exists()):
        return None
    facts = tuple(
        Fact(identifier=entry["identifier"], value=entry["value"])
        for entry in json.loads(facts_path.read_text(encoding="utf-8"))
    )
    books = tuple(
        Book(id=b["id"], title=b["title"], author=b["author"], sha256=b["sha256"])
        for b in json.loads(manifest_path.read_text(encoding="utf-8"))["books"]
    )
    documents = []
    for line in documents_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        documents.append(
            Document(
                fact_index=entry["fact_index"],
                context_length_tokens=entry["context_length_tokens"],
                position_percent=entry["position_percent"],
                text=entry["text"],
                actual_tokens=entry["actual_tokens"],
                actual_position_percent=entry["actual_position_percent"],
                book_id=entry["book_id"],
            )
        )
    return Dataset(facts=facts, documents=tuple(documents), books=books)


def user_prompt(document: str, fact: Fact) -> str:
    """The prompt in specification section 6.3."""
    return f"<document>\n{document}\n</document>\n\nQuestion: {fact.question}"


def plan_calls(config: ExperimentConfig, folder: Path) -> list[PlannedCall]:
    """Every planned call: one per model, context length, position, and fact.

    Builds the dataset first if it is missing, so `lab run` and `lab estimate` both work from a
    fresh clone.
    """
    dataset = load_dataset(folder)
    if dataset is None:
        dataset = build_dataset(config, folder, lengths=CONTEXT_LENGTH_OVERRIDE)

    calls: list[PlannedCall] = []
    for document in dataset.documents:
        fact = dataset.facts[document.fact_index]
        prompt = user_prompt(document.text, fact)
        cell = {
            "context_length_tokens": document.context_length_tokens,
            "position_percent": document.position_percent,
            "fact_index": document.fact_index,
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
            licence=LICENCE,
            url=mirror_url(book.id),
            checksum=f"sha256:{book.sha256}",
        )
        for book in (Book.from_config(entry) for entry in config.parameters["filler_books"])
    ]


if __name__ == "__main__":
    here = Path(__file__).parent
    built = build_dataset(load_config(here / "config.yaml"), here)
    print(f"Built {len(built.documents)} documents from {len(built.books)} books.")
    print(f"Written to {here / DATASET_DIR}")
