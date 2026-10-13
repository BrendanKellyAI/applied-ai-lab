"""Stage 1, load documents: the library, its manifest, and the test and dev items.

Every document file is Markdown with YAML front matter, named `<doc_id>@<version>.md`. The
manifest pins each file by SHA-256, so a run can never use a library that differs from the one
the results describe. Spans are character offsets into a document's body, the text after the
front matter.
"""

import hashlib
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

FRONT_MATTER = "---\n"

Access = Literal["public", "staff"]
Status = Literal["current", "superseded", "deleted"]


class CorpusError(ValueError):
    """The library or its items cannot be used as they are."""


class Span(BaseModel):
    """Characters `start` to `end` of one document version's body."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    version: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int

    @model_validator(mode="after")
    def _positive_length(self) -> Self:
        if self.end <= self.start:
            raise ValueError(f"span end {self.end} must be after start {self.start}")
        return self

    @property
    def doc_key(self) -> str:
        return f"{self.doc_id}@{self.version}"


class Document(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    version: int = Field(ge=1)
    title: str
    family: Literal["article", "policy", "internal"]
    products: tuple[str, ...] = ()
    access: Access
    status: Status
    effective_from: date | None = None
    effective_to: date | None = None
    superseded_by: str | None = None
    deleted_on: date | None = None
    body: str

    @property
    def key(self) -> str:
        return f"{self.doc_id}@{self.version}"


class Turn(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["user", "assistant"]
    content: str


class Item(BaseModel):
    """One test or dev question, with what a correct pipeline should find and say."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    asker: Access
    history: tuple[Turn, ...] = ()
    question: str
    resolved_question: str | None = None
    answerable: bool
    evidence: tuple[Span, ...] = ()
    heading: str | None = None
    distractor_spans: tuple[Span, ...] = ()
    stale_spans: tuple[Span, ...] = ()
    restricted_spans: tuple[Span, ...] = ()
    answer: str
    key_values: tuple[str, ...] = ()
    unanswerable_reason: (
        Literal["absent_detail", "absent_topic", "deleted", "restricted"] | None
    ) = None

    @model_validator(mode="after")
    def _answerable_matches_labels(self) -> Self:
        if self.answerable and not self.evidence:
            raise ValueError("an answerable item needs evidence spans")
        if not self.answerable and self.evidence:
            raise ValueError("an unanswerable item cannot have evidence spans")
        if not self.answerable and self.unanswerable_reason is None:
            raise ValueError("an unanswerable item needs an unanswerable_reason")
        return self

    def all_spans(self) -> tuple[Span, ...]:
        return self.evidence + self.distractor_spans + self.stale_spans + self.restricted_spans


class ManifestFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sha256: str
    tokens_cl100k: int = Field(ge=0)
    tokens_o200k: int = Field(ge=0)


class Manifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_version: str
    files: dict[str, ManifestFile]
    long_context_pack: tuple[str, ...] = ()


class Library(BaseModel):
    """Every document version, plus the test and dev items, checked against each other."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_version: str
    documents: tuple[Document, ...]
    test: tuple[Item, ...]
    dev: tuple[Item, ...]
    manifest: Manifest

    def document(self, key: str) -> Document:
        for document in self.documents:
            if document.key == key:
                return document
        raise CorpusError(f"No document {key} in the library")

    def span_text(self, span: Span) -> str:
        return self.document(span.doc_key).body[span.start : span.end]


def parse_document(text: str) -> Document:
    """A document from its file text. The body is everything after the closing `---` line."""
    if not text.startswith(FRONT_MATTER):
        raise CorpusError("A document must start with YAML front matter between --- lines")
    end = text.find("\n" + FRONT_MATTER, len(FRONT_MATTER) - 1)
    if end == -1:
        raise CorpusError("A document's front matter is not closed with a --- line")
    meta = yaml.safe_load(text[len(FRONT_MATTER) : end + 1]) or {}
    body = text[end + 1 + len(FRONT_MATTER) :]
    try:
        return Document.model_validate({**meta, "body": body})
    except ValidationError as exc:
        raise CorpusError(f"Invalid front matter: {exc}") from exc


def load_items(path: Path) -> tuple[Item, ...]:
    items = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(Item.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise CorpusError(f"{path.name} line {number}: {exc}") from exc
    return tuple(items)


def load_library(folder: Path) -> Library:
    """Load and check the library in `folder` against its manifest."""
    manifest = Manifest.model_validate_json((folder / "manifest.json").read_text(encoding="utf-8"))
    documents = tuple(
        _load_document(path, manifest) for path in sorted((folder / "documents").glob("*.md"))
    )
    found = {f"{d.key}.md" for d in documents}
    missing = sorted(set(manifest.files) - found)
    if missing:
        raise CorpusError(f"Files in the manifest are missing: {', '.join(missing)}")
    library = Library(
        corpus_version=manifest.corpus_version,
        documents=documents,
        test=load_items(folder / "test.jsonl"),
        dev=load_items(folder / "dev.jsonl"),
        manifest=manifest,
    )
    _check_spans(library, library.test + library.dev)
    return library


def _load_document(path: Path, manifest: Manifest) -> Document:
    entry = manifest.files.get(path.name)
    if entry is None:
        raise CorpusError(f"{path.name} is not in the manifest")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry.sha256:
        raise CorpusError(
            f"{path.name} does not match the manifest: SHA-256 {digest}, expected {entry.sha256}"
        )
    try:
        document = parse_document(data.decode("utf-8"))
    except CorpusError as exc:
        raise CorpusError(f"{path.name}: {exc}") from exc
    if f"{document.key}.md" != path.name:
        raise CorpusError(f"{path.name} holds {document.key}; the file name must match")
    return document


def _check_spans(library: Library, items: Sequence[Item]) -> None:
    lengths = {d.key: len(d.body) for d in library.documents}
    for item in items:
        for span in item.all_spans():
            length = lengths.get(span.doc_key)
            if length is None or span.end > length:
                raise CorpusError(f"Item {item.id}: span {span} is not inside a document")
