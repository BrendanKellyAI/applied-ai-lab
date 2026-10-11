import pytest

from lab.cache import ResponseCache, shared_cache_root
from lab.providers.base import request_hash
from lab.providers.mock import MockProvider


def test_miss_then_hit_after_put(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call().request
    result = MockProvider().generate(request)

    assert cache.get(request) is None
    cache.put(request, result)

    assert cache.get(request) == result


def test_stores_one_file_per_result_under_provider_and_prefix(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call().request
    cache.put(request, MockProvider().generate(request))
    digest = request_hash(request)

    assert (tmp_path / "mock" / digest[:2] / f"{digest}.json").is_file()


def test_hit_ignores_stream_and_metadata(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call().request
    cache.put(request, MockProvider().generate(request))
    relabelled = request.model_copy(update={"stream": False, "metadata": {"cell": "x"}})

    assert cache.get(relabelled) is not None


def test_failed_results_are_not_cached(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call().request
    failed = MockProvider().generate(request).model_copy(update={"error": "boom"})

    with pytest.raises(ValueError, match="not cached"):
        cache.put(request, failed)
    assert cache.get(request) is None


def test_rejects_result_for_a_different_request(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call(item=1).request
    other_result = MockProvider().generate(make_call(item=2).request)

    with pytest.raises(ValueError, match="does not match"):
        cache.put(request, other_result)


def test_unreadable_entry_is_treated_as_a_miss(tmp_path, make_call):
    cache = ResponseCache(tmp_path)
    request = make_call().request
    cache.put(request, MockProvider().generate(request))
    cache.path_for(request).write_text("{ not json", encoding="utf-8")

    assert cache.get(request) is None


def test_shared_cache_root_is_the_main_checkout(tmp_path, monkeypatch):
    # From a worktree, git reports the main checkout's .git as the common directory.
    main = tmp_path / "main"
    (main / ".git").mkdir(parents=True)
    monkeypatch.setattr(
        "lab.cache._git_common_dir", lambda start: main / ".git"
    )

    assert shared_cache_root(tmp_path / "worktree") == main / ".cache"


def test_shared_cache_root_falls_back_outside_git(tmp_path, monkeypatch):
    monkeypatch.setattr("lab.cache._git_common_dir", lambda start: None)

    assert shared_cache_root(tmp_path) == tmp_path / ".cache"


def test_git_common_dir_of_this_repository_exists():
    from pathlib import Path

    from lab.cache import _git_common_dir

    found = _git_common_dir(Path.cwd())
    assert found is not None and found.name == ".git"
