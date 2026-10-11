import pytest

from tests.rag.mini_corpus import write_library


@pytest.fixture
def library_dir(tmp_path):
    return write_library(tmp_path / "halvard")


@pytest.fixture
def library(library_dir):
    from lab.rag.corpus import load_library

    return load_library(library_dir)
