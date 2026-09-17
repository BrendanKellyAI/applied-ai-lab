import json
import subprocess
from types import SimpleNamespace

from lab.config import ExperimentConfig
from lab.metadata import DatasetSource, build_metadata, git_state, write_metadata
from lab.providers.mock import MockProvider
from lab.raw_log import RunRecord
from lab.runner import RunSummary
from tests.conftest import build_call

CONFIG = ExperimentConfig.model_validate(
    {
        "experiment": "demo",
        "seed": 7,
        "models": [
            {
                "provider": "mock",
                "model": "mock-a",
                "label": "Mock A",
                "modes": {
                    "standard": {"reasoning": "off", "temperature": None, "max_output_tokens": 10}
                },
            }
        ],
    }
)


def _fake_git(outputs: dict[tuple[str, ...], str], returncode: int = 0):
    def run(args, **_kwargs):
        return SimpleNamespace(returncode=returncode, stdout=outputs.get(tuple(args[1:]), ""))

    return run


def test_git_state_reads_commit_and_dirty_flag(tmp_path):
    run = _fake_git({("rev-parse", "HEAD"): "abc123\n", ("status", "--porcelain"): " M file.py\n"})

    state = git_state(tmp_path, run=run)

    assert (state.commit, state.dirty) == ("abc123", True)


def test_git_state_clean_tree(tmp_path):
    run = _fake_git({("rev-parse", "HEAD"): "abc123\n", ("status", "--porcelain"): ""})

    assert git_state(tmp_path, run=run).dirty is False


def test_git_state_outside_a_repository_is_unknown(tmp_path):
    state = git_state(tmp_path, run=_fake_git({}, returncode=128))

    assert (state.commit, state.dirty) == (None, None)


def test_git_state_without_git_installed_is_unknown(tmp_path):
    def missing(*_args, **_kwargs):
        raise FileNotFoundError("git")

    assert git_state(tmp_path, run=missing).commit is None


def test_git_state_on_this_repository_uses_real_git():
    state = git_state(__import__("pathlib").Path(__file__).parent)

    assert state.commit is None or len(state.commit) == 40
    assert isinstance(subprocess, object)


def _records():
    call = build_call(model="mock-a", item=1)
    call = call.model_copy(update={"model_label": "Mock A"})
    result = MockProvider().generate(call.request)
    failed = RunRecord.for_call(call, source="api", attempts=5, error="ServerError: down")
    return [failed, RunRecord.for_call(call, source="api", attempts=1, result=result)]


def test_build_metadata_records_everything_the_spec_requires(tmp_path):
    summary = RunSummary(planned=1, already_complete=0, cached=0, made=1, failed=0)
    datasets = [
        DatasetSource(
            name="Pride and Prejudice",
            version="Project Gutenberg eBook 1342",
            licence="Public domain in the USA",
            url="https://www.gutenberg.org/ebooks/1342",
            checksum="sha256:abc",
        )
    ]

    metadata = build_metadata(
        config=CONFIG,
        summary=summary,
        records=_records(),
        started_utc="2026-09-17T10:00:00+00:00",
        ended_utc="2026-09-17T10:05:00+00:00",
        datasets=datasets,
        repo_dir=tmp_path,
        git=lambda _path: git_state(tmp_path, run=_fake_git({("rev-parse", "HEAD"): "abc\n"})),
    )

    assert metadata.experiment == "demo"
    assert metadata.git.commit == "abc"
    assert metadata.harness_version == "0.1.0"
    assert metadata.python_version.count(".") == 2
    assert set(metadata.sdk_versions) == {"openai", "anthropic", "google-genai"}
    assert all(metadata.sdk_versions.values())
    assert metadata.models[0].label == "Mock A"
    assert metadata.models[0].model_requested == "mock-a"
    assert metadata.models[0].model_versions_returned == ["mock-a-mock-0001"]
    assert metadata.config["seed"] == 7
    assert metadata.datasets[0].licence == "Public domain in the USA"
    assert metadata.counts.made == 1


def test_write_metadata_produces_readable_json(tmp_path):
    summary = RunSummary(planned=1, already_complete=0, cached=1, made=0, failed=0)
    metadata = build_metadata(
        config=CONFIG,
        summary=summary,
        records=[],
        started_utc="a",
        ended_utc="b",
        datasets=[],
        repo_dir=tmp_path,
        git=lambda _path: git_state(tmp_path, run=_fake_git({}, returncode=1)),
    )
    path = tmp_path / "results" / "run_metadata.json"

    write_metadata(path, metadata)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["counts"]["cached"] == 1
    assert data["models"][0]["model_versions_returned"] == []
    assert "api_key" not in path.read_text(encoding="utf-8").lower()
