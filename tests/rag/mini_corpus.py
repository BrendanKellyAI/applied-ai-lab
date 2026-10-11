"""A ten-document library and its test items, written to a temporary folder for the tests.

Small enough to read in full, and shaped like the season corpus: articles with a code and its
look-alike, a structured policy with sibling facts under product headings, a superseded version
of that policy, a staff-only document, and a deleted article.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

CORPUS_VERSION = "mini-1"

POLICY_BODY = """# Warranty

Halvard Home appliances carry a warranty against faults in materials and workmanship.

## Brio kettle

### Cover period

The period is 24 months from delivery. It covers the element and the lid hinge.

### Claims

Claims need proof of purchase. Send a photograph of the base plate.

## Tessa dishwasher

### Cover period

The period is 36 months from delivery. It covers the pump and the control board.

### Claims

Claims need proof of purchase. An engineer inspects the unit first.
"""

DOCUMENTS: list[dict[str, Any]] = [
    {
        "meta": {"doc_id": "A000", "title": "Error E-2194 on the Tessa dishwasher"},
        "body": "Error E-2194 means the drain pump is blocked. Clear the filter, then restart.\n",
    },
    {
        "meta": {"doc_id": "A001", "title": "Error E-1294 on the Tessa dishwasher"},
        "body": "Error E-1294 means the door sensor is dirty. Wipe the latch and close the door.\n",
    },
    {
        "meta": {"doc_id": "A002", "title": "Descaling the Brio kettle"},
        "body": "Descale the Brio kettle every 8 weeks in hard water areas. Use citric acid.\n",
    },
    {
        "meta": {"doc_id": "A003", "title": "Connecting the Lumen thermostat to wi-fi"},
        "body": "Hold the dial for 5 seconds until the ring pulses blue, then open the app.\n",
    },
    {
        "meta": {"doc_id": "A004", "title": "Recycling an old Keel washing machine"},
        "body": "Book a free collection of your old machine when the new one is delivered.\n",
    },
    {
        "meta": {
            "doc_id": "POL-WAR",
            "version": 2,
            "title": "Warranty",
            "family": "policy",
            "effective_from": "2026-03-01",
        },
        "body": POLICY_BODY,
    },
    {
        "meta": {
            "doc_id": "POL-WAR",
            "version": 1,
            "title": "Warranty",
            "family": "policy",
            "status": "superseded",
            "effective_from": "2025-03-01",
            "effective_to": "2026-02-28",
            "superseded_by": "POL-WAR@2",
        },
        "body": POLICY_BODY.replace("24 months", "12 months"),
    },
    {
        "meta": {
            "doc_id": "INT-PRC",
            "title": "Goodwill and pricing rules",
            "family": "internal",
            "access": "staff",
        },
        "body": "Staff may waive the Brio kettle claim fee of 15 pounds once per customer.\n",
    },
    {
        "meta": {
            "doc_id": "DEL-00",
            "title": "Recall notice for the Fenwick filter",
            "status": "deleted",
            "deleted_on": "2026-06-30",
        },
        "body": "Stop using Fenwick filter batch 7731 and return it for a refund.\n",
    },
    {
        "meta": {"doc_id": "A005", "title": "Child lock on the Corra hob"},
        "body": "Press the key symbol for 3 seconds to lock the Corra hob controls.\n",
    },
]

_DEFAULTS: dict[str, Any] = {
    "version": 1,
    "family": "article",
    "products": [],
    "access": "public",
    "status": "current",
    "effective_from": None,
    "effective_to": None,
    "superseded_by": None,
    "deleted_on": None,
}


def _bodies() -> dict[tuple[str, int], str]:
    return {(d["meta"]["doc_id"], d["meta"].get("version", 1)): d["body"] for d in DOCUMENTS}


def span(doc_id: str, text: str, version: int = 1) -> dict[str, Any]:
    """A span dict for the first occurrence of `text` in a document body."""
    body = _bodies()[(doc_id, version)]
    start = body.index(text)
    return {"doc_id": doc_id, "version": version, "start": start, "end": start + len(text)}


def _item(id_: str, type_: str, question: str, **fields: Any) -> dict[str, Any]:
    answerable = bool(fields.get("evidence"))
    base: dict[str, Any] = {
        "id": id_,
        "type": type_,
        "asker": "public",
        "history": [],
        "question": question,
        "resolved_question": None,
        "answerable": answerable,
        "evidence": [],
        "heading": None,
        "distractor_spans": [],
        "stale_spans": [],
        "restricted_spans": [],
        "answer": "",
        "key_values": [],
        "unanswerable_reason": None,
    }
    return {**base, **fields}


def item_rows() -> list[dict[str, Any]]:
    return [
        _item(
            "IDENT-000",
            "identifier",
            "What does error E-2194 mean?",
            evidence=[span("A000", "Error E-2194 means the drain pump is blocked.")],
            distractor_spans=[span("A001", "Error E-1294 means the door sensor is dirty.")],
            answer="The drain pump is blocked.",
            key_values=["drain pump"],
        ),
        _item(
            "PARA-000",
            "paraphrase",
            "How often should I get the limescale out of my Brio?",
            evidence=[span("A002", "Descale the Brio kettle every 8 weeks in hard water areas.")],
            answer="Every 8 weeks in hard water areas.",
            key_values=["8 weeks"],
        ),
        _item(
            "POL-HEAD-000",
            "policy_heading",
            "How long is the Tessa dishwasher warranty?",
            evidence=[span("POL-WAR", "The period is 36 months from delivery.", 2)],
            heading="Tessa dishwasher",
            distractor_spans=[span("POL-WAR", "The period is 24 months from delivery.", 2)],
            answer="36 months from delivery.",
            key_values=["36 months"],
        ),
        _item(
            "VERSION-000",
            "version",
            "How long is the Brio kettle warranty?",
            evidence=[span("POL-WAR", "The period is 24 months from delivery.", 2)],
            stale_spans=[span("POL-WAR", "The period is 12 months from delivery.", 1)],
            answer="24 months from delivery.",
            key_values=["24 months"],
        ),
        _item(
            "FOLLOW-000",
            "followup",
            "And for the dishwasher?",
            history=[
                {"role": "user", "content": "How long is the Brio kettle warranty?"},
                {"role": "assistant", "content": "24 months from delivery."},
            ],
            resolved_question="How long is the Tessa dishwasher warranty?",
            evidence=[span("POL-WAR", "The period is 36 months from delivery.", 2)],
            answer="36 months from delivery.",
            key_values=["36 months"],
        ),
        _item(
            "RESTRICT-STAFF-000",
            "restricted_staff",
            "Can the Brio kettle claim fee be waived?",
            asker="staff",
            evidence=[span("INT-PRC", "Staff may waive the Brio kettle claim fee of 15 pounds")],
            answer="Yes, once per customer.",
            key_values=["once per customer"],
        ),
        _item(
            "RESTRICT-PUBLIC-000",
            "restricted_public",
            "Can the Brio kettle claim fee be waived?",
            restricted_spans=[
                span("INT-PRC", "Staff may waive the Brio kettle claim fee of 15 pounds")
            ],
            answer="Not in the public library.",
            unanswerable_reason="restricted",
        ),
        _item(
            "ABSENT-000",
            "absent_detail",
            "What colour is the Lumen thermostat ring when it fails to connect?",
            answer="The library does not say.",
            unanswerable_reason="absent_detail",
        ),
        _item(
            "DELETED-000",
            "deleted",
            "What should I do with Fenwick filter batch 7731?",
            answer="That notice was withdrawn.",
            unanswerable_reason="deleted",
        ),
        _item(
            "TWOPART-000",
            "two_part",
            "How do I lock the Corra hob, and how do I recycle my old Keel washer?",
            evidence=[
                span("A005", "Press the key symbol for 3 seconds"),
                span("A004", "Book a free collection of your old machine"),
            ],
            answer="Hold the key symbol for 3 seconds; book a free collection.",
            key_values=["3 seconds", "free collection"],
        ),
    ]


def dev_rows() -> list[dict[str, Any]]:
    return [
        _item(
            "DEV-PARA-000",
            "paraphrase",
            "How do I get my Lumen onto the home network?",
            evidence=[span("A003", "Hold the dial for 5 seconds until the ring pulses blue")],
            answer="Hold the dial for 5 seconds.",
            key_values=["5 seconds"],
        )
    ]


def document_text(document: dict[str, Any]) -> str:
    meta = {**_DEFAULTS, **document["meta"]}
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    return f"---\n{front}---\n{document['body']}"


def write_library(root: Path) -> Path:
    """Write the documents, items and a manifest under `root`, and return `root`."""
    documents = root / "documents"
    documents.mkdir(parents=True)
    files = {}
    for document in DOCUMENTS:
        meta = document["meta"]
        name = f"{meta['doc_id']}@{meta.get('version', 1)}.md"
        data = document_text(document).encode("utf-8")
        (documents / name).write_bytes(data)
        files[name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "tokens_cl100k": len(data) // 4,
            "tokens_o200k": len(data) // 4,
        }
    for name, items in (("test.jsonl", item_rows()), ("dev.jsonl", dev_rows())):
        lines = [json.dumps(item) for item in items]
        (root / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {"corpus_version": CORPUS_VERSION, "files": files, "long_context_pack": []}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return root
