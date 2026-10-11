import pytest

from lab.rag.chunk import WholeChunker, chunk_library
from lab.rag.corpus import Turn
from lab.rag.prompt import PromptConfig, build_prompt, instruction, order_passages, render


@pytest.fixture
def chunks(library):
    return chunk_library(library.documents, WholeChunker())


def test_passages_are_numbered_with_their_titles(chunks):
    text = build_prompt("What does error E-2194 mean?", (), chunks[:2])

    assert "[P1] Error E-2194 on the Tessa dishwasher\n" in text
    assert "[P2] Error E-1294 on the Tessa dishwasher\n" in text
    assert text.endswith("Question: What does error E-2194 mean?")


def test_history_appears_before_the_question(chunks):
    history = (
        Turn(role="user", content="How long is the kettle warranty?"),
        Turn(role="assistant", content="24 months."),
    )
    text = build_prompt("And the dishwasher?", history, chunks[:1])

    assert (
        "Conversation so far:\nUser: How long is the kettle warranty?\nAssistant: 24 months."
        in text
    )
    assert text.index("Conversation so far") < text.index("Question:")


def test_no_history_section_without_history(chunks):
    assert "Conversation so far" not in build_prompt("q", (), chunks[:1])


def test_order_rank_reverse_and_ends():
    ranked = ["1", "2", "3", "4", "5"]

    assert order_passages(ranked, "rank") == ["1", "2", "3", "4", "5"]
    assert order_passages(ranked, "reverse") == ["5", "4", "3", "2", "1"]
    # Best first and last, weakest in the middle.
    assert order_passages(ranked, "ends") == ["1", "3", "5", "4", "2"]


def test_render_takes_the_top_k_in_order(chunks):
    built = render("q", (), list(chunks), PromptConfig(k=3, order="reverse"))

    assert built.chunk_ids == tuple(c.chunk_id for c in reversed(chunks[:3]))
    assert built.system == instruction("plain")


def test_plain_instruction_is_the_naive_baseline():
    assert instruction("plain") == "Answer the question using the passages below."


def test_unknown_instruction_is_refused():
    with pytest.raises(ValueError):
        PromptConfig(instruction="clever")
