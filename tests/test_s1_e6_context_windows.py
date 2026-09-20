"""The S1 E6 episode sample: two silent failures at the edge of the window, and its chart.

No network calls are made. The script runs from a copy of the episode folder in a temporary
directory, because it writes its results beside itself, and the committed results must never be
overwritten by the fake client's answers.
"""

import copy
import json
import re
import runpy
import shutil
from pathlib import Path
from types import SimpleNamespace

import dotenv
import openai
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e6-context-windows"
SCRIPT = EPISODE / "edge.py"
MARKER = "# Everything below this line matches the slides."
BUDGET = 2000

# Exactly as shown on the slide.
SLIDE_LISTING = """from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-6-astra",
    input="Explain how a context window works, "
          "in five paragraphs.",
    max_output_tokens=60,
)
print(response.output_text)
print("Status:", response.status)
print("Reason:", response.incomplete_details.reason)
"""

FRENCH_REPLY = "Commencez petit : une seule plante que vous aimez et que vous arrosez bien."
ENGLISH_REPLY = "Start small: one plant that you enjoy and that you water well."


@pytest.fixture(scope="module")
def trim():
    return load_sibling(EPISODE / "trim.py")


@pytest.fixture(scope="module")
def french():
    return load_sibling(EPISODE / "french.py")


@pytest.fixture(scope="module")
def conversation():
    return load_sibling(EPISODE / "conversation.py")


@pytest.fixture(scope="module")
def chart():
    return load_sibling(EPISODE / "chart.py")


# A fake client --------------------------------------------------------------------------------


def fake_response(index: int, kwargs: dict) -> SimpleNamespace:
    """Answers like the API might. A short limit cuts the answer off; the instruction, if it is
    still in the conversation, makes the reply French."""
    limit = kwargs["max_output_tokens"]
    if isinstance(kwargs["input"], str):
        if limit >= 1000:
            status, details, text, output_tokens, reasoning = (
                "completed",
                None,
                "Five paragraphs.",
                900,
                300,
            )
        elif limit == 16:
            status, details, text, output_tokens, reasoning = (
                "incomplete",
                SimpleNamespace(reason="max_output_tokens"),
                "",
                16,
                16,
            )
        else:
            status, details, text, output_tokens, reasoning = (
                "incomplete",
                SimpleNamespace(reason="max_output_tokens"),
                "A context window is",
                limit,
                limit - 5,
            )
    else:
        kept_instruction = any(message["role"] == "system" for message in kwargs["input"])
        status, details, output_tokens, reasoning = "completed", None, 40, 10
        text = FRENCH_REPLY if kept_instruction else ENGLISH_REPLY
    items = [SimpleNamespace(type="reasoning")]
    if text:
        items.append(SimpleNamespace(type="message"))
    return SimpleNamespace(
        id=f"resp_{index}",
        model="gpt-6-astra-2026-09-01",
        status=status,
        incomplete_details=details,
        output=items,
        output_text=text,
        usage=SimpleNamespace(
            input_tokens=100 + index,
            output_tokens=output_tokens,
            output_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
            total_tokens=100 + index + output_tokens,
        ),
    )


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return fake_response(len(self.calls), kwargs)


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self) -> None:
        self.responses = FakeResponses()
        FakeOpenAI.instances.append(self)


class EnvLoads:
    """Stands in for load_dotenv, so tests never read a real .env file."""

    def __init__(self) -> None:
        self.count = 0
        self.clients_before_first_load = None

    def __call__(self, *_args, **_kwargs) -> bool:
        if self.count == 0:
            self.clients_before_first_load = len(FakeOpenAI.instances)
        self.count += 1
        return False


@pytest.fixture
def env_loads(monkeypatch):
    loads = EnvLoads()
    monkeypatch.setattr(dotenv, "load_dotenv", loads)
    return loads


def _copy_episode(destination: Path) -> Path:
    shutil.copytree(
        EPISODE, destination, ignore=shutil.ignore_patterns("results", "charts", "__pycache__")
    )
    return destination / "edge.py"


@pytest.fixture
def run(monkeypatch, tmp_path, env_loads, capsys):
    """Run a copy of the script against the fake client. Returns its output and results."""
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    script = _copy_episode(tmp_path / "episode")
    runpy.run_path(str(script), run_name="__main__")
    results = json.loads((script.parent / "results" / "edge.json").read_text(encoding="utf-8"))
    return SimpleNamespace(
        output=capsys.readouterr().out,
        results=results,
        calls=FakeOpenAI.instances[0].responses.calls,
    )


# The slide listing --------------------------------------------------------------------------


def test_the_script_contains_the_slide_listing_exactly():
    assert SLIDE_LISTING in SCRIPT.read_text(encoding="utf-8")


def test_the_listing_follows_the_marker_directly():
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.split(MARKER, 1)[1].startswith("\n" + SLIDE_LISTING)


def test_the_listing_fits_a_slide():
    lines = SLIDE_LISTING.rstrip("\n").split("\n")
    assert len(lines) <= 16
    assert max(len(line) for line in lines) <= 64


def test_the_listing_uses_no_lab_helpers():
    assert "lab" not in SLIDE_LISTING


def test_env_loading_sits_above_the_marker_and_the_listing():
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.index("load_dotenv()") < source.index(MARKER) < source.index(SLIDE_LISTING)
    assert source.index("from dotenv import load_dotenv") < source.index("load_dotenv()")


def test_the_env_file_is_loaded_before_the_client_is_created(run, env_loads):
    assert env_loads.count == 1
    assert env_loads.clients_before_first_load == 0


# The script, end to end, against the fake client ---------------------------------------------


def test_the_slide_call_is_the_first_call_and_asks_for_60_tokens(run):
    assert run.calls[0] == {
        "model": "gpt-6-astra",
        "input": "Explain how a context window works, in five paragraphs.",
        "max_output_tokens": 60,
    }


def test_the_script_makes_thirteen_calls_and_no_others(run):
    limits = [call["max_output_tokens"] for call in run.calls[:3]]
    assert limits == [60, 16, 8000]
    assert len(run.calls) == 3 + 2 * 5


def test_the_slide_prints_the_text_then_the_status_and_reason(run):
    lines = run.output.split("\n")
    assert lines[:3] == ["A context window is", "Status: incomplete", "Reason: max_output_tokens"]


def test_each_cut_off_run_records_text_status_reason_and_usage(run):
    first, second, generous = run.results["cut_off"]["runs"]

    assert first["text"] == "A context window is"
    assert first["characters"] == len("A context window is")
    assert first["status"] == "incomplete"
    assert first["incomplete_details"] == {"reason": "max_output_tokens"}
    assert first["usage"] == {
        "input_tokens": 101,
        "output_tokens": 60,
        "reasoning_tokens": 55,
        "total_tokens": 161,
    }
    assert first["output_item_types"] == ["reasoning", "message"]
    assert first["request"]["max_output_tokens"] == 60
    # Hidden reasoning that uses the whole limit leaves nothing visible, and is recorded as such.
    assert second["text"] == "" and second["characters"] == 0
    assert second["usage"]["reasoning_tokens"] == second["usage"]["output_tokens"] == 16
    assert second["output_item_types"] == ["reasoning"]
    assert generous["status"] == "completed"
    assert generous["incomplete_details"] is None


def test_the_results_record_the_model_the_api_returned_and_the_run_date(run):
    assert run.results["model_requested"] == "gpt-6-astra"
    assert run.results["model_returned"] == "gpt-6-astra-2026-09-01"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", run.results["run_date_utc"])


def test_every_call_after_the_cut_off_runs_sends_a_trimmed_conversation(run, conversation):
    final = conversation.FINAL_QUESTION
    for call in run.calls[3:]:
        assert call["model"] == "gpt-6-astra"
        assert call["input"][-1] == {"role": "user", "content": final}
        assert call["max_output_tokens"] == run.results["truncated"]["reply_limit"]


def test_the_two_strategies_are_sent_alternately_five_times_each(run):
    sent = [
        "pinned" if any(m["role"] == "system" for m in call["input"]) else "naive"
        for call in run.calls[3:]
    ]
    assert sent == ["naive", "pinned"] * 5


def test_what_was_sent_fits_the_budget(run, trim):
    for call in run.calls[3:]:
        assert trim.total_tokens(call["input"]) <= BUDGET


def test_the_results_report_each_strategy(run):
    strategies = run.results["truncated"]["strategies"]

    assert strategies["naive"]["instruction_survived"] is False
    assert strategies["pinned"]["instruction_survived"] is True
    assert strategies["naive"]["french_replies"] == 0
    assert strategies["pinned"]["french_replies"] == 5
    for name, strategy in strategies.items():
        assert strategy["messages_kept"] == len(strategy["messages"]), name
        assert strategy["messages_kept"] + strategy["messages_dropped"] == 50, name
        assert strategy["tokens_kept"] <= BUDGET, name
        assert len(strategy["replies"]) == 5, name
        assert all(reply["status"] == "completed" for reply in strategy["replies"]), name


def test_every_reply_records_its_text_usage_and_french_verdict(run):
    for strategy in run.results["truncated"]["strategies"].values():
        for reply in strategy["replies"]:
            assert reply["text"]
            assert isinstance(reply["french"], bool)
            assert reply["usage"]["input_tokens"] > 0
            assert reply["response_id"].startswith("resp_")


def test_the_script_stops_when_the_conversation_would_not_be_trimmed(
    monkeypatch, tmp_path, env_loads
):
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    script = _copy_episode(tmp_path / "episode")
    shortened = script.parent / "conversation.py"
    shortened.write_text(
        shortened.read_text(encoding="utf-8") + "\nEARLIER_EXCHANGES = EARLIER_EXCHANGES[:2]\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="nothing would be trimmed"):
        runpy.run_path(str(script), run_name="__main__")

    assert not (script.parent / "results").exists()


# The trimming strategies, on synthetic conversations ------------------------------------------


def words(text: str) -> int:
    """A stand-in token counter: one token per word, so the tests can work the sums out."""
    return len(text.split())


def conversation_of(*sizes: int) -> list[dict]:
    """A system instruction, then user and assistant turns of the given sizes, then a question."""
    roles = ["system"] + ["user", "assistant"] * ((len(sizes) - 2) // 2 + 1)

    def text(index: int, size: int) -> str:
        # The first word is unique to the message, so no two messages are equal.
        return " ".join([f"m{index}", *["word"] * (size - 1)])

    turns = [
        {"role": roles[index], "content": text(index, size)}
        for index, size in enumerate(sizes[:-1])
    ]
    return [*turns, {"role": "user", "content": text(len(sizes) - 1, sizes[-1])}]


def test_naive_drops_the_instruction_first(trim):
    messages = conversation_of(2, 10, 10, 10, 10, 3)

    kept = trim.trim_naive(messages, 30, words)

    assert messages[0] not in kept
    # 45 tokens over a budget of 30: the instruction (2) and two 10-token turns have to go.
    assert kept == messages[3:]


def test_pinned_always_keeps_the_instruction(trim):
    messages = conversation_of(2, 10, 10, 10, 10, 3)

    kept = trim.trim_pinned(messages, 20, words)

    assert kept[0] == messages[0]


def test_pinned_drops_the_oldest_other_messages_first(trim):
    messages = conversation_of(2, 10, 10, 10, 10, 3)

    kept = trim.trim_pinned(messages, 25, words)

    # The instruction (2) and question (3) stay; the two oldest 10-token turns go, and the two
    # newest turns before the question fit in what remains.
    assert kept == [messages[0], messages[3], messages[4], messages[5]]


@pytest.mark.parametrize("budget", [15, 20, 25, 30, 35, 45])
def test_both_strategies_fit_the_budget(trim, budget):
    messages = conversation_of(2, 10, 10, 10, 10, 3)

    assert trim.total_tokens(trim.trim_naive(messages, budget, words), words) <= budget
    assert trim.total_tokens(trim.trim_pinned(messages, budget, words), words) <= budget


@pytest.mark.parametrize("strategy", ["trim_naive", "trim_pinned"])
def test_neither_strategy_drops_the_final_question(trim, strategy):
    messages = conversation_of(2, 10, 10, 10, 10, 3)

    for budget in (5, 10, 20, 30):
        kept = getattr(trim, strategy)(messages, budget, words)
        assert kept[-1] == messages[-1]


@pytest.mark.parametrize("strategy", ["trim_naive", "trim_pinned"])
def test_a_conversation_that_already_fits_is_returned_whole(trim, strategy):
    messages = conversation_of(2, 10, 10, 3)

    assert getattr(trim, strategy)(messages, 100, words) == messages


@pytest.mark.parametrize("strategy", ["trim_naive", "trim_pinned"])
def test_the_order_is_kept_and_the_input_is_not_changed(trim, strategy):
    messages = conversation_of(2, 10, 10, 10, 10, 3)
    before = copy.deepcopy(messages)

    kept = getattr(trim, strategy)(messages, 25, words)

    assert messages == before
    assert kept is not messages
    positions = [messages.index(message) for message in kept]
    assert positions == sorted(positions)


def test_a_budget_too_small_for_the_question_alone_is_refused(trim):
    messages = conversation_of(2, 10, 10, 8)

    with pytest.raises(ValueError, match="over the 5-token budget"):
        trim.trim_naive(messages, 5, words)


def test_pinned_refuses_a_budget_too_small_for_the_instruction_and_question(trim):
    messages = conversation_of(4, 10, 10, 3)

    with pytest.raises(ValueError, match="over the 6-token budget"):
        trim.trim_pinned(messages, 6, words)
    # The naive strategy has no such floor: it can drop the instruction to make room.
    assert trim.trim_naive(messages, 6, words) == messages[-1:]


@pytest.mark.parametrize("strategy", ["trim_naive", "trim_pinned"])
def test_an_empty_conversation_is_refused(trim, strategy):
    with pytest.raises(ValueError, match="at least a final message"):
        getattr(trim, strategy)([], 100, words)


def test_the_instruction_check_looks_for_the_system_message(trim):
    messages = conversation_of(2, 10, 10, 3)

    assert trim.has_instruction(messages)
    assert not trim.has_instruction(messages[1:])


# The committed conversation, with the real tokeniser ---------------------------------------------


def test_the_tokeniser_is_o200k_base_as_in_s1_e2(trim):
    assert trim.ENCODING == "o200k_base"
    assert trim.count_tokens("Reply only in French.") == 5


def test_the_committed_conversation_opens_with_the_instruction_and_ends_with_the_question(
    conversation,
):
    messages = conversation.messages()

    assert messages[0] == {"role": "system", "content": "Reply only in French."}
    assert messages[-1] == {"role": "user", "content": conversation.FINAL_QUESTION}
    assert [m["role"] for m in messages[1:-1]] == ["user", "assistant"] * 24


def test_the_committed_conversation_is_well_over_the_budget(trim, conversation):
    assert trim.total_tokens(conversation.messages()) > BUDGET + 300


def test_the_committed_conversation_is_in_english(french, conversation):
    """The earlier answers must not be French, or a French reply could be copying them."""
    for message in conversation.messages()[1:]:
        assert not french.is_french(message["content"]), message["content"][:40]


def test_on_the_committed_conversation_naive_loses_the_instruction_and_pinned_keeps_it(
    trim, conversation
):
    messages = conversation.messages()

    naive = trim.trim_naive(messages, BUDGET)
    pinned = trim.trim_pinned(messages, BUDGET)

    assert not trim.has_instruction(naive)
    assert trim.has_instruction(pinned)
    assert trim.total_tokens(naive) <= BUDGET and trim.total_tokens(pinned) <= BUDGET
    assert naive[-1] == pinned[-1] == messages[-1]
    # The two strategies throw away about the same amount, so the comparison is fair.
    assert abs(len(naive) - len(pinned)) <= 2


# The French rule ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Plantez ce que vous aimez manger, et arrosez-le régulièrement pour qu'il pousse bien.",
        "Le conseil le plus utile est de commencer petit, avec une seule plante.",
        "Il faut commencer par le sol : un bon compost est la base de tout.",
        "l'eau est dans le verre",
        "Voici un conseil : commencez petit. The garden will thank you, avec des fleurs et des "
        "légumes dans les pots.",
    ],
)
def test_french_replies_are_counted_as_french(french, text):
    assert french.is_french(text)


@pytest.mark.parametrize(
    "text",
    [
        "Start small, and grow only what you will actually eat.",
        "It's the soil that matters most, so add compost every year.",
        "",
        "   ",
        "12345 !!! ???",
        # Two French words are not enough, however English the rest is not.
        "The le la garden",
        # Three French words, but more English ones.
        "le la les the garden is not the point of this plan",
    ],
)
def test_other_replies_are_not_counted_as_french(french, text):
    assert not french.is_french(text)


def test_the_rule_needs_three_french_words_and_more_french_than_english(french):
    assert french.french_hits("le la les") == 3
    assert french.is_french("le la les")
    assert not french.is_french("le la")
    # Equal counts are not enough: French has to win.
    assert not french.is_french("le la les the is are")
    assert french.is_french("le la les une the is")


def test_an_apostrophe_splits_a_word_so_contractions_do_not_count_as_french(french):
    assert french.words("It's l'eau") == ["it", "s", "l", "eau"]
    assert french.french_hits("It's fine, don't worry, we'll see") == 0


def test_words_ordinary_in_both_languages_are_on_neither_list(french):
    for word in ("on", "plus", "son", "par", "a"):
        assert word not in french.FRENCH_WORDS
        assert word not in french.ENGLISH_WORDS


def test_the_rule_is_recorded_beside_the_replies_it_was_applied_to(run, french):
    assert run.results["truncated"]["french_rule"] == french.RULE


# The chart ----------------------------------------------------------------------------------


def _results(naive: int, pinned: int, runs: int = 5) -> dict:
    return {
        "model_returned": "gpt-6-astra-2026-09-01",
        "truncated": {
            "budget_tokens": BUDGET,
            "runs_per_strategy": runs,
            "strategies": {
                "naive": {"french_replies": naive},
                "pinned": {"french_replies": pinned},
            },
        },
    }


def _specs(chart, monkeypatch) -> dict:
    """Records the spec of every chart drawn, while still drawing it through the brand checks."""
    specs = {}
    real = chart.export_chart

    def recording(draw, out_dir, spec, *args, **kwargs):
        specs[spec.name] = spec
        return real(draw, out_dir, spec, *args, **kwargs)

    monkeypatch.setattr(chart, "export_chart", recording)
    return specs


def test_the_strategy_with_fewer_french_replies_is_highlighted(chart):
    assert chart.fewer_french([0, 5]) == 0
    assert chart.fewer_french([5, 0]) == 1
    assert chart.fewer_french([2, 3]) == 0


def test_nothing_is_highlighted_when_the_strategies_are_equal(chart):
    assert chart.fewer_french([5, 5]) is None
    assert chart.fewer_french([0, 0]) is None
    assert chart.fewer_french([3, 3]) is None


def test_the_chart_highlights_and_says_nothing_when_the_strategies_differ(
    chart, tmp_path, monkeypatch
):
    """The brand checks accept exactly one acid green element."""
    specs = _specs(chart, monkeypatch)

    written = chart.render(_results(0, 5), tmp_path)

    assert specs["french-replies"].no_highlight_note is None
    assert sorted(path.name for path in written) == [
        "french-replies-article.png",
        "french-replies-slide.png",
        "french-replies-slide.svg",
    ]


@pytest.mark.parametrize(("naive", "pinned"), [(0, 5), (2, 5), (5, 0), (5, 3)])
def test_exactly_one_element_is_highlighted_whether_or_not_the_bar_has_height(
    chart, tmp_path, monkeypatch, naive, pinned
):
    """A bar of height zero cannot carry the colour, so its label does. The brand checks refuse
    a chart with more than one acid green element, so drawing it at all is the assertion."""
    specs = _specs(chart, monkeypatch)

    chart.render(_results(naive, pinned), tmp_path)

    assert specs["french-replies"].no_highlight_note is None


@pytest.mark.parametrize("count", [0, 5])
def test_the_chart_highlights_nothing_and_says_so_when_the_strategies_are_equal(
    chart, tmp_path, monkeypatch, count
):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(count, count), tmp_path)

    assert "nothing highlighted" in specs["french-replies"].no_highlight_note


def test_the_footnote_names_the_model_budget_and_run_count(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(0, 5), tmp_path)

    spec = specs["french-replies"]
    assert "gpt-6-astra-2026-09-01" in spec.footnote
    assert "2,000 tokens" in spec.footnote
    assert spec.sample_size == "5 runs each"


def test_the_chart_module_needs_no_api_key_or_network_library():
    source = (EPISODE / "chart.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(?:import|from)\s+(openai|dotenv|requests|urllib)", source, re.M)


# The committed results ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed(chart):
    return chart.load()


def test_the_committed_results_name_the_model_the_api_returned_and_the_run_date(committed):
    assert committed["model_requested"] == "gpt-6-astra"
    assert committed["model_returned"] == "gpt-6-astra"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", committed["run_date_utc"])


def test_the_committed_cut_off_runs_are_the_three_limits_on_the_same_prompt(committed):
    runs = committed["cut_off"]["runs"]

    assert [run["request"]["max_output_tokens"] for run in runs] == [60, 16, 8000]
    assert {run["request"]["input"] for run in runs} == {committed["cut_off"]["prompt"]}
    assert {run["request"]["model"] for run in runs} == {"gpt-6-astra"}


def test_a_committed_cut_off_run_reports_incomplete_and_the_reason(committed):
    for run in committed["cut_off"]["runs"][:2]:
        assert run["status"] == "incomplete"
        assert run["incomplete_details"] == {"reason": "max_output_tokens"}


def test_the_committed_complete_run_reports_completed_with_no_reason(committed):
    generous = committed["cut_off"]["runs"][2]

    assert generous["status"] == "completed"
    assert generous["incomplete_details"] is None
    assert generous["output_item_types"] == ["reasoning", "message"]
    assert generous["characters"] == len(generous["text"]) > 1000


def test_hidden_reasoning_used_the_whole_limit_and_left_no_visible_text(committed):
    """The finding the README reports: at both small limits the answer is empty, and the only
    sign anything went wrong is the status field."""
    for run in committed["cut_off"]["runs"][:2]:
        limit = run["request"]["max_output_tokens"]
        assert run["text"] == "" and run["characters"] == 0
        assert run["output_item_types"] == ["reasoning"]
        assert run["usage"]["output_tokens"] == run["usage"]["reasoning_tokens"] == limit


def test_every_committed_usage_adds_up(committed):
    replies = [
        reply
        for strategy in committed["truncated"]["strategies"].values()
        for reply in strategy["replies"]
    ]
    for run in [*committed["cut_off"]["runs"], *replies]:
        usage = run["usage"]
        assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]
        assert usage["reasoning_tokens"] <= usage["output_tokens"]


def test_the_committed_conversation_size_matches_the_committed_text(committed, trim, conversation):
    truncated = committed["truncated"]
    messages = conversation.messages()

    assert truncated["conversation_messages"] == len(messages)
    assert (
        truncated["conversation_tokens"] == trim.total_tokens(messages) > truncated["budget_tokens"]
    )
    assert truncated["budget_tokens"] == BUDGET
    assert truncated["instruction"] == conversation.INSTRUCTION
    assert truncated["final_question"] == conversation.FINAL_QUESTION


def test_the_committed_trims_are_what_the_committed_strategies_produce(
    committed, trim, conversation
):
    messages = conversation.messages()
    strategies = committed["truncated"]["strategies"]

    assert strategies["naive"]["messages"] == trim.trim_naive(messages, BUDGET)
    assert strategies["pinned"]["messages"] == trim.trim_pinned(messages, BUDGET)


def test_the_committed_table_agrees_with_the_committed_messages(committed, trim):
    for name, strategy in committed["truncated"]["strategies"].items():
        assert strategy["messages_kept"] == len(strategy["messages"]), name
        assert strategy["messages_dropped"] == 50 - strategy["messages_kept"], name
        assert strategy["tokens_kept"] == trim.total_tokens(strategy["messages"]) <= BUDGET, name
        assert strategy["instruction_survived"] == trim.has_instruction(strategy["messages"]), name


def test_the_committed_replies_were_all_complete_answers_from_five_runs(committed):
    """A reply cut off by its limit would confuse Demonstration 2 with Demonstration 1."""
    assert committed["truncated"]["runs_per_strategy"] == 5
    for name, strategy in committed["truncated"]["strategies"].items():
        assert len(strategy["replies"]) == 5, name
        for reply in strategy["replies"]:
            assert reply["status"] == "completed" and reply["text"], name


def test_every_committed_french_verdict_is_the_rule_applied_again(committed, french):
    for strategy in committed["truncated"]["strategies"].values():
        for reply in strategy["replies"]:
            assert reply["french"] == french.is_french(reply["text"])
        assert strategy["french_replies"] == sum(r["french"] for r in strategy["replies"])


def test_the_committed_truncation_result(committed):
    """Naive lost the instruction and answered in English every time; pinned kept it and
    answered in French every time. These are the figures the README reports."""
    strategies = committed["truncated"]["strategies"]

    assert strategies["naive"]["instruction_survived"] is False
    assert strategies["pinned"]["instruction_survived"] is True
    assert strategies["naive"]["french_replies"] == 0
    assert strategies["pinned"]["french_replies"] == 5


def test_the_committed_chart_highlights_the_naive_bar(chart, committed, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    written = chart.render(committed, tmp_path)

    assert chart.fewer_french(chart.french_counts(committed)) == 0
    assert specs["french-replies"].no_highlight_note is None
    assert len(written) == 3
