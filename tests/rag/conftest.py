import pytest
import yaml

from lab.rag.config import load_episode
from tests.rag.mini_corpus import REFERENCE, write_library


@pytest.fixture
def library_dir(tmp_path):
    return write_library(tmp_path / "halvard")


@pytest.fixture
def library(library_dir):
    from lab.rag.corpus import load_library

    return load_library(library_dir)


@pytest.fixture
def episode(tmp_path, library_dir):
    season = tmp_path / "season2"
    season.mkdir()
    reference = dict(REFERENCE, chunk={"kind": "whole"})
    (season / "reference.yaml").write_text(yaml.safe_dump(reference), encoding="utf-8")
    folder = tmp_path / "episodes" / "s2-e2-first-rag-system"
    folder.mkdir(parents=True)
    config = {
        "episode": "s2-e2-first-rag-system",
        "base": "../../season2/reference.yaml",
        "library": str(library_dir),
        "conditions": [
            {"name": "baseline"},
            {"name": "k-3", "changes": {"prompt": {"k": 3}}, "measure": "search"},
        ],
    }
    (folder / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return load_episode(folder / "config.yaml")


def condition_named(episode, name):
    return next(c for c in episode.conditions if c.name == name)
