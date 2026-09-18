from lab.providers.mock import MockProvider
from lab.raw_log import RawLogWriter, RunRecord, latest_successful, load_records


def _record(call, *, error: str | None = None) -> RunRecord:
    result = None if error else MockProvider().generate(call.request)
    return RunRecord.for_call(call, source="api", attempts=1, result=result, error=error)


def test_missing_file_loads_as_empty(tmp_path):
    assert load_records(tmp_path / "raw.jsonl") == []


def test_append_then_load_round_trips(tmp_path, make_call):
    path = tmp_path / "results" / "raw.jsonl"
    records = [_record(make_call(item=1)), _record(make_call(item=2), error="boom")]

    with RawLogWriter(path) as writer:
        for record in records:
            writer.append(record)

    assert load_records(path) == records


def test_truncated_last_line_is_skipped_and_next_append_starts_cleanly(tmp_path, make_call):
    path = tmp_path / "raw.jsonl"
    first = _record(make_call(item=1))
    with RawLogWriter(path) as writer:
        writer.append(first)
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"call_id": "half-writ')

    second = _record(make_call(item=2))
    with RawLogWriter(path) as writer:
        writer.append(second)

    assert load_records(path) == [first, second]


def test_latest_successful_ignores_failures_and_keeps_last_success(tmp_path, make_call):
    call = make_call(item=1)
    failed = _record(call, error="boom")
    succeeded = _record(call)
    other_failed = _record(make_call(item=2), error="boom")

    latest = latest_successful([failed, succeeded, other_failed])

    assert latest == {call.call_id: succeeded}


def test_an_answer_to_a_question_no_longer_asked_is_not_returned(make_call):
    """A prompt changed, and the attempt at the new prompt failed: the old answer is stale."""
    old = _record(make_call(item=1, prompt="the old question"))
    new_attempt = _record(make_call(item=1, prompt="the new question"), error="boom")
    assert old.call_id == new_attempt.call_id
    assert old.request_hash != new_attempt.request_hash

    assert latest_successful([old, new_attempt]) == {}


def test_a_failed_retry_of_the_same_request_keeps_the_earlier_answer(make_call):
    call = make_call(item=1)
    answered = _record(call)

    assert latest_successful([answered, _record(call, error="boom")]) == {call.call_id: answered}
