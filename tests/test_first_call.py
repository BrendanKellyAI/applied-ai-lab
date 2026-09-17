"""The S1 E1 episode sample, run against a fake client. No network calls are made."""

import runpy
from pathlib import Path
from types import SimpleNamespace

import dotenv
import openai
import pytest

SCRIPT = Path(__file__).parents[1] / "episodes" / "s1-e1-one-token-at-a-time" / "first_call.py"

SLIDE_ONE = """from openai import OpenAI

# Reads OPENAI_API_KEY from the environment
client = OpenAI()

first = client.responses.create(
    model="gpt-6-astra",
    input="My name is Brendan.",
)
print(first.output_text)
print("Input tokens:", first.usage.input_tokens)
print("Output tokens:", first.usage.output_tokens)
"""

SLIDE_TWO = """second = client.responses.create(
    model="gpt-6-astra",
    input="What is my name?",
)
print(second.output_text)
"""


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        replies = ["Nice to meet you, Brendan.", "I don't know your name.", "Your name is Brendan."]
        reply = replies[len(self.calls) - 1]
        return SimpleNamespace(
            output_text=reply,
            usage=SimpleNamespace(
                input_tokens=10 * len(self.calls),
                output_tokens=8 + len(self.calls),
                # The first call reasons a little; the others do not, to check 0 is printed.
                output_tokens_details=SimpleNamespace(
                    reasoning_tokens=5 if len(self.calls) == 1 else 0
                ),
            ),
        )


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


@pytest.fixture
def calls(monkeypatch, capsys, env_loads):
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    runpy.run_path(str(SCRIPT), run_name="__main__")
    return FakeOpenAI.instances[0].responses.calls


@pytest.mark.parametrize("listing", [SLIDE_ONE, SLIDE_TWO])
def test_script_contains_slide_code_exactly(listing):
    assert listing in SCRIPT.read_text(encoding="utf-8")


def test_first_and_second_calls_send_no_history(calls):
    assert len(calls) == 3
    assert calls[0] == {"model": "gpt-6-astra", "input": "My name is Brendan."}
    assert calls[1] == {"model": "gpt-6-astra", "input": "What is my name?"}


def test_third_call_sends_history_explicitly(calls):
    assert calls[2] == {
        "model": "gpt-6-astra",
        "input": [
            {"role": "user", "content": "My name is Brendan."},
            {"role": "assistant", "content": "Nice to meet you, Brendan."},
            {"role": "user", "content": "What is my name?"},
        ],
    }
    assert all("previous_response_id" not in call for call in calls)


def test_prints_a_heading_before_each_part(calls, capsys):
    output = capsys.readouterr().out

    headings = [
        "Part 1: first call",
        "Part 2: second call, no history",
        "Part 3: third call, with history",
    ]
    positions = [output.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_every_part_labels_its_token_counts_including_zero(calls, capsys):
    output = capsys.readouterr().out
    parts = output.split("=== Part ")[1:]

    expected = [
        ("Input tokens: 10", "Output tokens: 9", "Reasoning tokens (included in output): 5"),
        ("Input tokens: 20", "Output tokens: 10", "Reasoning tokens (included in output): 0"),
        ("Input tokens: 30", "Output tokens: 11", "Reasoning tokens (included in output): 0"),
    ]
    assert len(parts) == 3
    for part, lines in zip(parts, expected, strict=True):
        for line in lines:
            assert line in part


def test_loads_env_file_before_creating_the_client(calls, env_loads):
    assert env_loads.count == 1
    assert env_loads.clients_before_first_load == 0


def test_env_loading_sits_above_the_slide_code():
    source = SCRIPT.read_text(encoding="utf-8")

    assert source.index("load_dotenv()") < source.index("=== Part 1: first call ===")
    assert source.index("load_dotenv()") < source.index(SLIDE_ONE)
