"""The Halvard library was frozen on 12 October 2026, before E2 ran.

Every Season 2 result is measured on exactly these files. The manifest pins every document by
SHA-256, and these hashes pin the manifest and the items, so any change to the library fails
here. Changing it means a new corpus version and rerunning every episode already run.
"""

import hashlib
from pathlib import Path

import pytest

from lab.rag.corpus import load_library

LIBRARY = Path(__file__).parents[2] / "datasets" / "halvard"
FROZEN = {
    "manifest.json": "2d40f031d11b6d10606bdc32133ff28a5bd710ee85c89c6b470efa131b0a35c8",
    "test.jsonl": "b2ec6fadf6abcf49b0c064a909233723be9b6b91ece7c111928c30b374489606",
    "dev.jsonl": "fe7fa96fc2fca3b4cbbf6ed20bf3f0de429db3bedc73cbf2cac9157029f40e4b",
}


@pytest.mark.parametrize(("name", "digest"), FROZEN.items())
def test_frozen_files_are_unchanged(name, digest):
    assert hashlib.sha256((LIBRARY / name).read_bytes()).hexdigest() == digest, (
        f"{name} has changed since the corpus was frozen"
    )


def test_frozen_library_loads_with_every_document_checked():
    library = load_library(LIBRARY)

    assert library.corpus_version == "halvard-v2"
    assert (len(library.documents), len(library.test), len(library.dev)) == (344, 520, 100)
