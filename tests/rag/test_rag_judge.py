import pytest

from lab.rag.chunk import WholeChunker, chunk_library
from lab.rag.judge import JudgeParseError, judge_prompt, parse_verdict, retry_prompt


def _item(library, item_id):
    return next(i for i in library.test + library.dev if i.id == item_id)


def test_prompt_holds_everything_the_judge_needs(library):
    chunks = chunk_library(library.documents, WholeChunker())
    item = _item(library, "IDENT-000")
    text = judge_prompt(item, chunks[:2], "The drain pump is blocked.")

    assert "Question: What does error E-2194 mean?" in text
    assert "Can the question be answered from the documents: yes" in text
    assert "Reference answer: The drain pump is blocked." in text
    assert "[P1] Error E-2194 on the Tessa dishwasher" in text
    assert text.endswith("System's answer:\nThe drain pump is blocked.")


def test_prompt_never_shows_the_evidence_labels(library):
    item = _item(library, "IDENT-000")
    text = judge_prompt(item, (), "answer")

    assert "drain pump is blocked." in text  # the reference answer
    assert "A000" not in text and "start" not in text


def test_unanswerable_item_says_so(library):
    text = judge_prompt(_item(library, "ABSENT-000"), (), "I could not find that.")

    assert "Can the question be answered from the documents: no" in text
    assert "Passages given to the system:\n(none)" in text


def test_followup_shows_the_conversation(library):
    text = judge_prompt(_item(library, "FOLLOW-000"), (), "36 months.")

    assert "Conversation so far:\nUser: How long is the Brio kettle warranty?" in text


def test_parses_a_plain_json_verdict():
    verdict = parse_verdict(
        '{"declined": false, "correct": true, "faithful": true, "reason": "Matches."}'
    )

    assert (verdict.declined, verdict.correct, verdict.faithful) == (False, True, True)


def test_parses_a_verdict_inside_a_code_fence():
    text = '```json\n{"declined": true, "correct": true, "faithful": true, "reason": "r"}\n```'

    assert parse_verdict(text).declined is True


@pytest.mark.parametrize(
    "text",
    [
        "I think it is correct.",
        '{"declined": false, "correct": "yes", "faithful": true, "reason": "r"}',
        '{"declined": false, "correct": true, "reason": "r"}',
        '{"declined": false, "correct": true, "faithful": true, "reason": "r"',
    ],
)
def test_unreadable_verdicts_raise(text):
    with pytest.raises(JudgeParseError):
        parse_verdict(text)


def test_retry_prompt_names_the_error():
    text = retry_prompt("original", "missing field faithful")

    assert text.startswith("original\n\n")
    assert "missing field faithful" in text
