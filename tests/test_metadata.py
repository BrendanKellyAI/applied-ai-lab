import json
import subprocess
from types import SimpleNamespace

from lab.config import ExperimentConfig
from lab.metadata import (
    RESULTS_PATHSPECS,
    WHOLE_REPOSITORY,
    DatasetSource,
    build_metadata,
    git_state,
    read_metadata,
    write_metadata,
)
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


STATUS = ("status", "--porcelain", "--", WHOLE_REPOSITORY, *RESULTS_PATHSPECS)


def test_git_state_reads_commit_and_dirty_flag(tmp_path):
    run = _fake_git({("rev-parse", "HEAD"): "abc123\n", STATUS: " M file.py\n"})

    state = git_state(tmp_path, run=run)

    assert (state.commit, state.dirty) == ("abc123", True)


def test_git_state_clean_tree(tmp_path):
    run = _fake_git({("rev-parse", "HEAD"): "abc123\n", STATUS: ""})

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
    assert metadata.passes[-1].counts.made == 1
    assert metadata.counts.complete == 1


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
    assert data["passes"][0]["counts"]["cached"] == 1
    assert data["models"][0]["model_versions_returned"] == []
    assert "api_key" not in path.read_text(encoding="utf-8").lower()


def _metadata(tmp_path, *, records, started, ended, previous=None, planned_ids=None, **kwargs):
    return build_metadata(
        config=CONFIG,
        summary=RunSummary(planned=1, already_complete=0, cached=0, made=1, failed=0),
        records=records,
        started_utc=started,
        ended_utc=ended,
        datasets=[],
        repo_dir=tmp_path,
        git=lambda _path: git_state(tmp_path, run=_fake_git({}, returncode=1)),
        planned_ids=planned_ids,
        previous=previous,
        **kwargs,
    )


def test_the_results_folder_is_not_what_makes_a_tree_dirty():
    """A run's own output is not a change to the code that produced it."""
    assert any("results/" in spec and "exclude" in spec for spec in RESULTS_PATHSPECS)
    assert any("results-fresh/" in spec for spec in RESULTS_PATHSPECS)


def test_passes_accumulate_and_the_window_spans_all_of_them(tmp_path):
    first = _metadata(
        tmp_path,
        records=[],
        started="2026-09-18T10:00:00+00:00",
        ended="2026-09-18T11:00:00+00:00",
        pilot=True,
    )
    retry = _metadata(
        tmp_path,
        records=[],
        started="2026-09-18T12:00:00+00:00",
        ended="2026-09-18T12:00:17+00:00",
        previous=first,
        provider="openai",
    )

    assert len(retry.passes) == 2
    assert retry.passes[0].pilot is True
    assert retry.passes[1].provider == "openai"
    assert retry.started_utc == "2026-09-18T10:00:00+00:00"
    assert retry.ended_utc == "2026-09-18T12:00:17+00:00"


def test_counts_cover_the_whole_grid_not_the_calls_one_pass_selected(tmp_path):
    records = _records()
    metadata = _metadata(
        tmp_path,
        records=records,
        started="2026-09-18T10:00:00+00:00",
        ended="2026-09-18T10:01:00+00:00",
        planned_ids=[records[0].call_id, "never-run-a", "never-run-b"],
        provider="mock",
    )

    assert metadata.counts.planned == 3
    assert metadata.counts.complete == 1
    assert metadata.counts.not_run == 2


def test_a_call_that_failed_then_succeeded_is_complete_not_failed(tmp_path):
    records = _records()  # a failure, then a success, for the same call

    metadata = _metadata(
        tmp_path,
        records=records,
        started="2026-09-18T10:00:00+00:00",
        ended="2026-09-18T10:01:00+00:00",
        planned_ids=[records[0].call_id],
    )

    assert (metadata.counts.complete, metadata.counts.failed) == (1, 0)


def test_a_call_that_only_failed_is_counted_as_failed(tmp_path):
    failed = _records()[0]

    metadata = _metadata(
        tmp_path,
        records=[failed],
        started="2026-09-18T10:00:00+00:00",
        ended="2026-09-18T10:01:00+00:00",
        planned_ids=[failed.call_id],
    )

    assert (metadata.counts.complete, metadata.counts.failed) == (0, 1)


def test_results_older_than_the_first_pass_move_the_start_earlier(tmp_path):
    """Metadata written before passes were kept still gets an honest start time."""
    early = _records()[1].model_copy(update={"recorded_utc": "2026-09-18T08:00:00+00:00"})

    metadata = _metadata(
        tmp_path,
        records=[early],
        started="2026-09-18T12:00:00+00:00",
        ended="2026-09-18T12:00:17+00:00",
    )

    assert metadata.started_utc == "2026-09-18T08:00:00+00:00"


def test_earlier_metadata_is_read_back(tmp_path):
    path = tmp_path / "run_metadata.json"
    write_metadata(
        path,
        _metadata(tmp_path, records=[], started="a", ended="b"),
    )

    assert read_metadata(path, "demo").passes[0].started_utc == "a"


def test_metadata_in_an_older_format_starts_a_new_history(tmp_path):
    path = tmp_path / "run_metadata.json"
    path.write_text(json.dumps({"experiment": "demo", "counts": {"made": 3}}), encoding="utf-8")

    assert read_metadata(path, "demo") is None


def test_metadata_for_another_experiment_is_ignored(tmp_path):
    path = tmp_path / "run_metadata.json"
    write_metadata(path, _metadata(tmp_path, records=[], started="a", ended="b"))

    assert read_metadata(path, "something-else") is None


def test_missing_metadata_is_none(tmp_path):
    assert read_metadata(tmp_path / "run_metadata.json", "demo") is None


def _real_repo(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    note = tmp_path / "field-notes" / "demo"
    note.mkdir(parents=True)
    (note / "config.yaml").write_text("seed: 1\n", encoding="utf-8")
    (tmp_path / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "start")
    return note


def test_real_git_ignores_results_when_run_from_the_field_note_folder(tmp_path):
    """git runs from inside the field note, so the pathspecs must be anchored at the root."""
    note = _real_repo(tmp_path)
    (note / "results").mkdir()
    (note / "results" / "raw.jsonl").write_text("{}\n", encoding="utf-8")

    assert git_state(note).dirty is False


def test_real_git_still_sees_a_change_outside_the_field_note_folder(tmp_path):
    note = _real_repo(tmp_path)
    (tmp_path / "code.py").write_text("VALUE = 2\n", encoding="utf-8")

    assert git_state(note).dirty is True


def test_a_pass_that_made_no_calls_does_not_stretch_the_window(tmp_path):
    last = _records()[1].model_copy(update={"recorded_utc": "2026-09-18T19:40:09+00:00"})

    metadata = _metadata(
        tmp_path,
        records=[last],
        started="2026-09-18T19:50:00+00:00",
        ended="2026-09-18T19:50:56+00:00",
    )

    assert metadata.ended_utc == "2026-09-18T19:40:09+00:00"
    assert metadata.passes[-1].ended_utc == "2026-09-18T19:50:56+00:00"
