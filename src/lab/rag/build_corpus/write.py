"""Writing the library: document files, items, the manifest, the long-context pack, and a
review file for the hand check."""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.chunk import count_tokens
from lab.rag.corpus import Document, Item, Manifest, ManifestFile
from lab.rag.estimate import chat_tokens

FIELDS = (
    "doc_id",
    "version",
    "title",
    "family",
    "products",
    "access",
    "status",
    "effective_from",
    "effective_to",
    "superseded_by",
    "deleted_on",
)


def document_text(document: Document) -> str:
    meta = {name: getattr(document, name) for name in FIELDS}
    meta["products"] = list(document.products)
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000)
    return f"---\n{front}---\n{document.body}"


def write_documents(folder: Path, documents: Sequence[Document]) -> dict[str, ManifestFile]:
    target = folder / "documents"
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.md"):
        old.unlink()
    files = {}
    for document in documents:
        data = document_text(document).encode("utf-8")
        (target / f"{document.key}.md").write_bytes(data)
        files[f"{document.key}.md"] = ManifestFile(
            sha256=hashlib.sha256(data).hexdigest(),
            tokens_cl100k=count_tokens(document.body),
            tokens_o200k=chat_tokens(document.body),
        )
    return files


def write_items(path: Path, items: Sequence[Item]) -> None:
    lines = [item.model_dump_json(exclude_defaults=True) for item in items]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def long_context_pack(documents: Sequence[Document], limit: int) -> tuple[str, ...]:
    """The four current policies, then articles in id order, while the total fits `limit`."""
    current = [d for d in documents if d.status == "current" and d.access == "public"]
    ordered = [d for d in current if d.family == "policy"] + sorted(
        (d for d in current if d.family == "article"), key=lambda d: d.doc_id
    )
    pack, total = [], 0
    for document in ordered:
        tokens = chat_tokens(document.body)
        if total + tokens > limit:
            if document.family == "policy":
                raise ValueError(f"The current policies alone pass {limit:,} tokens")
            break
        pack.append(document.key)
        total += tokens
    return tuple(pack)


def write_library(
    folder: Path,
    config: CorpusConfig,
    documents: Sequence[Document],
    test: Sequence[Item],
    dev: Sequence[Item],
    log: dict[str, Any],
) -> Manifest:
    files = write_documents(folder, documents)
    write_items(folder / "test.jsonl", test)
    write_items(folder / "dev.jsonl", dev)
    manifest = Manifest(
        corpus_version=config.corpus_version,
        files=files,
        long_context_pack=long_context_pack(documents, config.pack_limit_tokens),
    )
    (folder / "manifest.json").write_text(
        manifest.model_dump_json(indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    (folder / "build_log.json").write_text(
        json.dumps(log, indent=1, default=str) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def review_text(items: Sequence[Item], documents: Sequence[Document], per_type: int | None) -> str:
    """Items beside their spans, for reading by hand: `per_type` of each type, or all."""
    by_key = {d.key: d for d in documents}

    def show(span) -> str:
        return by_key[span.doc_key].body[span.start : span.end]

    lines = ["# Items for review", ""]
    for item_type in sorted({i.type for i in items}):
        chosen = [i for i in items if i.type == item_type]
        lines.append(f"## {item_type} ({len(chosen)} items)")
        for item in chosen[:per_type] if per_type else chosen:
            lines.append(f"\n### {item.id} ({item.asker})")
            for turn in item.history:
                lines.append(f"- {turn.role}: {turn.content}")
            lines.append(f"- **Question:** {item.question}")
            lines.append(f"- **Answer:** {item.answer}")
            for label, spans in (
                ("Evidence", item.evidence),
                ("Look-alike", item.distractor_spans),
                ("Stale", item.stale_spans),
                ("Restricted", item.restricted_spans),
            ):
                for span in spans:
                    lines.append(f"- {label} ({span.doc_key}): {show(span)}")
        lines.append("")
    return "\n".join(lines) + "\n"
