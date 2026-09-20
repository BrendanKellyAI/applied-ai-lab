"""The S1 E8 episode sample: GPT-2's probabilities, repeated API answers, and their charts.

No test calls the API, loads GPT-2, or touches the network. The API script runs from a copy of
the episode folder in a temporary directory, against a fake client, because it writes its results
beside itself and the committed results must never be overwritten by fake answers. The maths
behind Part A lives in measure.py and is checked on small synthetic logits.
"""

import copy
import json
import math
import re
import runpy
import shutil
from pathlib import Path
from types import SimpleNamespace

import dotenv
import openai
import pytest

from lab.experiments import load_sibling
from tests.fakes import http_response

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e8-sampling"
E5_TIMING = Path(__file__).parents[1] / "episodes" / "s1-e5-the-transformer" / "timing.py"
SCRIPT = EPISODE / "sampling.py"
MARKER = "# Everything below this line matches the slides."
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
COFFEE = "Suggest a name for a coffee shop in Dublin. Reply with the name only."
CAPITAL = "What is the capital of Ireland? Reply with one word."

# Exactly as shown on the slide.
SLIDE_LISTING = """client = OpenAI()
prompt = ("Suggest a name for a coffee shop in Dublin. "
          "Reply with the name only.")
responses = [
    client.responses.create(
        model="gpt-6-astra", input=prompt,
        max_output_tokens=4000)
    for _ in range(20)
]
counts = Counter(r.output_text.strip() for r in responses)
for answer, count in counts.most_common():
    print(f"{count:2d}  {answer}")
"""


@pytest.fixture(scope="module")
def measure():
    return load_sibling(EPISODE / "measure.py")


# A fake client --------------------------------------------------------------------------------

COFFEE_NAMES = [
    "Bean There",
    "Bean There.",
    " bean there ",
    "The Liffey Roast",
    "Grand Canal Coffee",
    "Grand Canal Coffee",
    "Bean There",
]
CAPITAL_ANSWERS = ["Dublin", "Dublin.", "dublin", "Dublin\n"]
# Every seventh coffee call comes back incomplete and empty, as a reasoning model can.
INCOMPLETE_EVERY = 7


def fake_response(index: int, kwargs: dict, mode: str) -> SimpleNamespace:
    """The `index`th call of the run, 1-based. `mode` says what a temperature setting does."""
    status, details = "completed", None
    if kwargs["input"] == CAPITAL:
        text = CAPITAL_ANSWERS[index % len(CAPITAL_ANSWERS)]
    elif "temperature" in kwargs:
        text = "Bean There"
    else:
        text = COFFEE_NAMES[(index - 1) % len(COFFEE_NAMES)]
        if index % INCOMPLETE_EVERY == 0:
            status, details, text = "incomplete", SimpleNamespace(reason="max_output_tokens"), ""
    echoed = None
    if "temperature" in kwargs:
        echoed = kwargs["temperature"] if mode == "accept" else 1.0
    items = [SimpleNamespace(type="reasoning")] + (
        [SimpleNamespace(type="message")] if text else []
    )
    return SimpleNamespace(
        id=f"resp_{index}",
        model="gpt-6-astra-2026-09-01",
        status=status,
        incomplete_details=details,
        temperature=echoed,
        output=items,
        output_text=text,
        usage=SimpleNamespace(
            input_tokens=20,
            output_tokens=30,
            output_tokens_details=SimpleNamespace(reasoning_tokens=12),
            total_tokens=50,
        ),
    )


class FakeResponses:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        if "temperature" in kwargs and self.mode == "reject":
            body = {
                "message": "Unsupported parameter: 'temperature' is not supported with this model.",
                "type": "invalid_request_error",
                "param": "temperature",
                "code": "unsupported_parameter",
            }
            raise openai.BadRequestError(body["message"], response=http_response(400), body=body)
        return fake_response(len(self.calls), kwargs, self.mode)


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []
    mode = "accept"

    def __init__(self) -> None:
        self.responses = FakeResponses(FakeOpenAI.mode)
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


def _run_script(monkeypatch, tmp_path, capsys, mode: str) -> SimpleNamespace:
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(FakeOpenAI, "mode", mode)
    shutil.copytree(
        EPISODE,
        tmp_path / "episode",
        ignore=shutil.ignore_patterns("results", "charts", "__pycache__"),
    )
    script = tmp_path / "episode" / "sampling.py"
    runpy.run_path(str(script), run_name="__main__")
    results = json.loads((script.parent / "results" / "api.json").read_text(encoding="utf-8"))
    return SimpleNamespace(
        output=capsys.readouterr().out,
        results=results,
        calls=FakeOpenAI.instances[0].responses.calls,
    )


@pytest.fixture
def accepted(monkeypatch, tmp_path, env_loads, capsys):
    return _run_script(monkeypatch, tmp_path, capsys, "accept")


@pytest.fixture
def rejected(monkeypatch, tmp_path, env_loads, capsys):
    return _run_script(monkeypatch, tmp_path, capsys, "reject")


@pytest.fixture
def ignored(monkeypatch, tmp_path, env_loads, capsys):
    return _run_script(monkeypatch, tmp_path, capsys, "ignore")


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


def test_docstring_imports_and_env_loading_sit_above_the_marker():
    source = SCRIPT.read_text(encoding="utf-8")
    above = source.split(MARKER, 1)[0]
    assert above.startswith('"""S1 E8, Sampling')
    for line in (
        "from collections import Counter",
        "from dotenv import load_dotenv",
        "from openai import OpenAI",
        "load_dotenv()",
    ):
        assert line in above
    assert source.index("load_dotenv()") < source.index(MARKER) < source.index(SLIDE_LISTING)


def test_the_env_file_is_loaded_before_the_client_is_created(accepted, env_loads):
    assert env_loads.count == 1
    assert env_loads.clients_before_first_load == 0


# The script, end to end, against the fake client ---------------------------------------------


def test_the_slide_calls_come_first_and_use_the_model_defaults(accepted):
    assert len(accepted.calls[:20]) == 20
    for call in accepted.calls[:20]:
        assert call == {"model": "gpt-6-astra", "input": COFFEE, "max_output_tokens": 4000}


def test_the_slide_prints_each_distinct_answer_with_its_count_most_common_first(accepted):
    lines = accepted.output.split("\n")
    # Grand Canal Coffee came back 6 times, and the three spellings of Bean There 3 times each.
    assert lines[0] == " 6  Grand Canal Coffee"
    assert lines[1:5] == [
        " 3  Bean There",
        " 3  Bean There.",
        " 3  bean there",
        " 3  The Liffey Roast",
    ]
    # The slide counts raw text, so the two incomplete, empty responses show as an empty answer.
    assert lines[5] == " 2  "


def test_the_script_makes_sixty_one_calls_when_temperature_is_accepted(accepted):
    assert len(accepted.calls) == 20 + 20 + 1 + 20


def test_the_capital_prompt_is_sent_twenty_times_at_the_defaults(accepted):
    capital = accepted.calls[20:40]
    assert all(
        call == {"model": "gpt-6-astra", "input": CAPITAL, "max_output_tokens": 4000}
        for call in capital
    )


def test_one_probe_call_sends_temperature_zero(accepted):
    probe = accepted.calls[40]
    assert probe == {
        "model": "gpt-6-astra",
        "input": CAPITAL,
        "max_output_tokens": 4000,
        "temperature": 0,
    }


def test_the_temperature_zero_run_sends_the_coffee_prompt_twenty_times(accepted):
    zero = accepted.calls[41:]
    assert len(zero) == 20
    assert all(call["temperature"] == 0 and call["input"] == COFFEE for call in zero)


def test_an_accepted_temperature_is_recorded_as_accepted_and_applied(accepted):
    probe = accepted.results["probe"]

    assert probe["outcome"] == "accepted and applied"
    assert probe["response"]["temperature_echoed"] == 0
    assert "Temperature 0: accepted and applied" in accepted.output


def test_a_temperature_that_is_accepted_but_not_applied_is_recorded_as_such(ignored):
    assert ignored.results["probe"]["outcome"] == "accepted but not applied"
    assert ignored.results["probe"]["response"]["temperature_echoed"] == 1.0
    # Accepted, so the run goes ahead: the record then shows whether it changed anything.
    assert len(ignored.calls) == 61


def test_a_rejected_temperature_records_the_exact_error_and_skips_the_run(rejected):
    probe = rejected.results["probe"]

    assert probe["outcome"] == "rejected"
    error = probe["error"]
    assert (error["status_code"], error["type"], error["param"]) == (
        400,
        "invalid_request_error",
        "temperature",
    )
    assert error["code"] == "unsupported_parameter"
    # The SDK's own message wraps the API's, so the API's wording is checked as a part.
    assert "Unsupported parameter: 'temperature' is not supported" in error["message"]
    assert len(rejected.calls) == 20 + 20 + 1
    assert [c["name"] for c in rejected.results["conditions"]] == [
        "coffee-default",
        "capital-default",
    ]
    assert "Claim 3 cannot be tested on this model" in rejected.output


def test_every_response_is_recorded_with_its_status_and_usage(accepted):
    for condition in accepted.results["conditions"]:
        assert len(condition["runs"]) == 20
        for run in condition["runs"]:
            assert run["status"] in {"completed", "incomplete"}
            assert run["usage"] == {
                "input_tokens": 20,
                "output_tokens": 30,
                "reasoning_tokens": 12,
                "total_tokens": 50,
            }
            assert run["response_id"].startswith("resp_")
            assert "text" in run and "request" in run


def test_incomplete_responses_are_counted_apart_from_answers(accepted):
    coffee = accepted.results["conditions"][0]

    assert coffee["name"] == "coffee-default"
    assert (coffee["answered"], coffee["unanswered"]) == (18, 2)
    assert coffee["unanswered_statuses"] == ["incomplete", "incomplete"]
    # Three answers, not four: the empty responses are not an answer.
    assert coffee["distinct"] == [
        ["bean there", 9],
        ["grand canal coffee", 6],
        ["the liffey roast", 3],
    ]
    assert coffee["distinct_count"] == 3


def test_answers_that_differ_only_in_case_spacing_or_final_punctuation_are_one_answer(accepted):
    capital = accepted.results["conditions"][1]

    assert capital["name"] == "capital-default"
    assert capital["distinct"] == [["dublin", 20]]
    assert capital["distinct_count"] == 1
    raw = {run["text"] for run in capital["runs"]}
    assert raw == {"Dublin", "Dublin.", "dublin", "Dublin\n"}


def test_the_results_record_the_model_returned_the_date_and_the_settings(accepted):
    results = accepted.results

    assert results["model_requested"] == "gpt-6-astra"
    assert results["model_returned"] == "gpt-6-astra-2026-09-01"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", results["run_date_utc"])
    assert results["output_limit"] == 4000
    assert results["runs_per_condition"] == 20
    assert "fold the case" in results["normalisation"]


# The maths of Part A, on synthetic logits ------------------------------------------------------


def logits_for(probabilities: list[float]) -> list[float]:
    """Logits whose softmax at temperature 1 is exactly these probabilities."""
    return [math.log(p) for p in probabilities]


def test_temperature_one_returns_the_original_distribution(measure):
    original = [0.5, 0.3, 0.15, 0.05]

    result = measure.softmax(logits_for(original), 1.0)

    assert result == pytest.approx(original)


def test_a_low_temperature_raises_the_top_probability_and_a_high_one_lowers_it(measure):
    logits = logits_for([0.5, 0.3, 0.15, 0.05])

    cold = measure.softmax(logits, 0.3)[0]
    normal = measure.softmax(logits, 1.0)[0]
    hot = measure.softmax(logits, 1.8)[0]

    assert cold > normal > hot
    assert cold > 0.8


def test_a_low_temperature_lowers_the_least_likely_and_a_high_one_raises_it(measure):
    logits = logits_for([0.5, 0.3, 0.15, 0.05])

    assert measure.softmax(logits, 0.3)[-1] < 0.05 < measure.softmax(logits, 1.8)[-1]


@pytest.mark.parametrize("temperature", [0.3, 1.0, 1.8, 50.0])
def test_probabilities_add_up_to_one_at_any_temperature(measure, temperature):
    assert sum(measure.softmax([2.0, -1.0, 0.5, 7.5], temperature)) == pytest.approx(1.0)


def test_the_ranking_of_tokens_does_not_change_with_temperature(measure):
    logits = [2.0, -1.0, 0.5, 7.5, 3.0]

    orders = {tuple(measure.ranked(measure.softmax(logits, t))) for t in (0.3, 1.0, 1.8)}

    assert orders == {(3, 4, 0, 2, 1)}


def test_a_very_low_temperature_does_not_overflow(measure):
    result = measure.softmax([1000.0, 999.0, 0.0], 0.01)

    assert result[0] == pytest.approx(1.0)
    assert all(math.isfinite(p) for p in result)


def test_a_temperature_of_zero_or_less_is_refused(measure):
    for bad in (0, -1.0):
        with pytest.raises(ValueError, match="above 0"):
            measure.softmax([1.0, 2.0], bad)


def test_the_softmax_of_no_logits_is_refused(measure):
    with pytest.raises(ValueError, match="no logits"):
        measure.softmax([], 1.0)


def test_top_k_lists_the_most_likely_tokens_first_and_breaks_ties_by_index(measure):
    assert measure.top_k([0.1, 0.4, 0.4, 0.1], 3) == [(1, 0.4), (2, 0.4), (0, 0.1)]


def test_top_p_returns_the_smallest_set_reaching_p(measure):
    probabilities = [0.1, 0.5, 0.3, 0.1]

    assert measure.top_p_set(probabilities, 0.6) == [1, 2]
    assert measure.top_p_set(probabilities, 0.85) == [1, 2, 0]
    assert measure.top_p_set(probabilities, 1.0) == [1, 2, 0, 3]


def test_top_p_keeps_a_set_that_reaches_p_exactly(measure):
    assert measure.top_p_set([0.5, 0.3, 0.2], 0.5) == [0]
    assert measure.top_p_set([0.5, 0.3, 0.2], 0.8) == [0, 1]


def test_top_p_always_keeps_at_least_the_top_token(measure):
    assert measure.top_p_set([0.05, 0.9, 0.05], 0.01) == [1]


@pytest.mark.parametrize("p", [0.1, 0.35, 0.6, 0.9, 0.999])
def test_the_top_p_set_is_minimal(measure, p):
    probabilities = measure.softmax([3.0, 1.0, 0.5, 2.0, -1.0, 0.0], 1.0)

    kept = measure.top_p_set(probabilities, p)
    mass = sum(probabilities[i] for i in kept)

    assert mass >= p - 1e-9
    assert mass - probabilities[kept[-1]] < p


@pytest.mark.parametrize("p", [0, -0.1, 1.5])
def test_top_p_outside_zero_to_one_is_refused(measure, p):
    with pytest.raises(ValueError, match="p must be"):
        measure.top_p_set([0.5, 0.5], p)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Dublin", "dublin"),
        ("  Dublin  ", "dublin"),
        ("Dublin.", "dublin"),
        ("Dublin!!", "dublin"),
        ("Dublin?!.", "dublin"),
        ("Dublin .", "dublin"),
        ("\nDublin.\n", "dublin"),
        ("DUBLIN", "dublin"),
        ("Bean & Bloom", "bean & bloom"),
        ("Costa, Dublin", "costa, dublin"),
        ("Bean  There", "bean  there"),
        ("Straße", "strasse"),
        ("The Bean.", "the bean"),
        ("...", ""),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalisation_strips_whitespace_folds_case_and_drops_final_punctuation(
    measure, raw, expected
):
    assert measure.normalise_answer(raw) == expected


def test_normalisation_touches_only_the_end_of_an_answer(measure):
    """A quotation mark at the start is not removed, so it is a difference between answers."""
    assert measure.normalise_answer("“Bean & Bloom”") == "“bean & bloom"
    assert measure.normalise_answer("“Bean & Bloom”") != measure.normalise_answer("Bean & Bloom")


def test_distinct_answers_are_counted_after_normalising_most_common_first(measure):
    answers = ["Dublin", "dublin.", "Cork", "DUBLIN ", "Cork!", "Galway"]

    assert measure.distinct_counts(answers) == [("dublin", 3), ("cork", 2), ("galway", 1)]


def test_distinct_answers_with_equal_counts_keep_the_order_they_first_appeared(measure):
    assert measure.distinct_counts(["b", "a", "b", "a", "c"]) == [("b", 2), ("a", 2), ("c", 1)]


def test_no_answers_give_no_distinct_answers(measure):
    assert measure.distinct_counts([]) == []


def test_a_response_is_an_answer_only_if_completed_with_visible_text(measure):
    assert measure.is_answer("completed", "Dublin")
    assert not measure.is_answer("completed", "   ")
    assert not measure.is_answer("completed", "")
    assert not measure.is_answer("incomplete", "Dub")
    assert not measure.is_answer(None, "Dublin")


def test_the_probe_outcome_says_what_happened_to_the_temperature(measure):
    assert measure.classify_probe(False, None, 0) == "rejected"
    assert measure.classify_probe(True, 0, 0) == "accepted and applied"
    assert measure.classify_probe(True, 0.0, 0) == "accepted and applied"
    assert measure.classify_probe(True, 1.0, 0) == "accepted but not applied"
    assert measure.classify_probe(True, None, 0) == "accepted, no temperature echoed"


def test_the_planned_settings_are_the_ones_in_the_brief(measure):
    assert measure.TEMPERATURES == (0.3, 1.0, 1.8)
    assert tuple(range(20)) == measure.SEEDS
    assert (measure.NEW_TOKENS, measure.TOP_K, measure.TOP_P, measure.API_RUNS) == (10, 10, 0.6, 20)
    assert measure.PROMPTS == {
        "capital": "The capital of Ireland is",
        "colour": "My favourite colour is",
    }


# Part A's script, read as text: it cannot be imported without the model ------------------------


def test_local_uses_the_same_model_revision_as_s1_e5():
    local = (EPISODE / "local.py").read_text(encoding="utf-8")

    assert f'REVISION = "{REVISION}"' in local
    assert f'REVISION = "{REVISION}"' in E5_TIMING.read_text(encoding="utf-8")


def test_local_switches_off_the_libraries_own_top_k_and_top_p_when_sampling():
    local = (EPISODE / "local.py").read_text(encoding="utf-8")

    assert "top_k=0" in local and "top_p=1.0" in local
    assert "do_sample=True" in local and "torch.manual_seed(seed)" in local


def test_the_episode_needs_no_new_extra():
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r"^e4 = \[", pyproject, re.MULTILINE)
    assert "e8" not in pyproject


def test_measure_needs_no_model_or_network_library():
    source = (EPISODE / "measure.py").read_text(encoding="utf-8")
    heavy = re.compile(r"^\s*(?:import|from)\s+(torch|transformers|openai|numpy|urllib)", re.M)
    assert heavy.search(source) is None


# The committed results ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def chart():
    return load_sibling(EPISODE / "chart.py")


@pytest.fixture(scope="module")
def local(chart):
    return chart.load(chart.LOCAL)


@pytest.fixture(scope="module")
def api(chart):
    return chart.load(chart.API)


def _top(local: dict, prompt: str, temperature: str) -> list[dict]:
    return local["prompts"][prompt]["distributions"][temperature]["top"]


def test_the_committed_local_results_name_the_model_revision_and_libraries(local):
    assert local["model"] == "gpt2"
    assert local["revision"] == REVISION
    assert (local["device"], local["dtype"]) == ("cpu", "float32")
    assert {"python", "torch", "transformers", "tokenizers"} <= set(local["libraries"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", local["run_date_utc"])


def test_the_committed_local_results_cover_both_prompts_at_all_three_temperatures(local, measure):
    assert local["temperatures"] == list(measure.TEMPERATURES)
    for name, prompt in measure.PROMPTS.items():
        record = local["prompts"][name]
        assert record["prompt"] == prompt
        assert record["vocabulary_size"] == 50257
        assert set(record["distributions"]) == {"0.3", "1.0", "1.8"}


def test_every_committed_top_ten_is_ranked_and_adds_up(local):
    for name in ("capital", "colour"):
        for distribution in local["prompts"][name]["distributions"].values():
            top = distribution["top"]
            assert [entry["rank"] for entry in top] == list(range(1, 11))
            probabilities = [entry["probability"] for entry in top]
            assert probabilities == sorted(probabilities, reverse=True)
            assert 0 < sum(probabilities) <= 1
            assert distribution["top_mass"] == pytest.approx(sum(probabilities))


def test_temperature_never_reorders_the_committed_tokens(local):
    for name in ("capital", "colour"):
        orders = {
            tuple(entry["token_id"] for entry in _top(local, name, t))
            for t in ("0.3", "1.0", "1.8")
        }
        assert len(orders) == 1


def test_a_lower_temperature_gives_the_top_token_more_of_the_probability(local):
    for name in ("capital", "colour"):
        cold, normal, hot = (_top(local, name, t)[0]["probability"] for t in ("0.3", "1.0", "1.8"))
        assert cold > normal > hot


def test_the_committed_temperatures_are_the_same_logits_reshaped(local):
    """Dividing logits by a temperature turns every ratio of probabilities into that ratio to the
    power 1/T, whatever the total. So the ratios in the committed 0.3 and 1.8 lists must follow
    from the 1.0 list. This checks all three were worked out from one set of logits."""
    for name in ("capital", "colour"):
        normal = _top(local, name, "1.0")
        for temperature in ("0.3", "1.8"):
            reshaped = _top(local, name, temperature)
            for base, other in zip(normal[1:], reshaped[1:], strict=True):
                ratio = base["probability"] / normal[0]["probability"]
                expected = ratio ** (1 / float(temperature))
                assert other["probability"] / reshaped[0]["probability"] == pytest.approx(expected)


def test_gpt2_small_does_not_put_dublin_first_and_the_results_say_where_it_is(local):
    """The finding for the capital prompt: the most likely next token is " the", not " Dublin"."""
    top = _top(local, "capital", "1.0")
    dublin = local["prompts"]["capital"]["dublin"]

    assert top[0]["text"] == " the"
    assert dublin["single_token"] is True
    assert dublin["rank"] == 3
    assert top[2]["text"] == " Dublin" and top[2]["token_id"] == dublin["token_id"]
    assert top[2]["probability"] == pytest.approx(dublin["probability"])


def test_the_top_p_set_is_the_smallest_reaching_p_and_matches_the_library(local):
    top_p = local["top_p"]
    kept = top_p["kept"]

    assert top_p["top_p"] == 0.6 and top_p["temperature"] == 1.0
    assert top_p["matches_transformers"] is True
    cumulative = [entry["cumulative"] for entry in kept]
    assert cumulative == sorted(cumulative)
    assert cumulative[-1] >= 0.6 > cumulative[-2]
    assert top_p["kept_mass"] == pytest.approx(cumulative[-1])
    # It is the colour prompt's distribution at 1.0, so it starts with the same ten tokens.
    top_ten = [entry["token_id"] for entry in _top(local, "colour", "1.0")]
    assert [entry["token_id"] for entry in kept[:10]] == top_ten


def test_the_committed_samples_record_their_seeds_and_settings(local, measure):
    sampling = local["sampling"]

    assert sampling["prompt"] == measure.PROMPTS["colour"]
    assert sampling["seeds"] == list(range(20))
    assert "top_k=0" in sampling["settings"] and "top_p=1.0" in sampling["settings"]
    for temperature, block in sampling["by_temperature"].items():
        assert [sample["seed"] for sample in block["samples"]] == list(range(20)), temperature
        assert all(len(sample["token_ids"]) == 10 for sample in block["samples"]), temperature
        assert block["distinct"] == len({sample["text"] for sample in block["samples"]})
    assert len(sampling["greedy"]["token_ids"]) == 10


def test_greedy_starts_with_the_most_likely_token(local):
    first = _top(local, "colour", "1.0")[0]["token_id"]

    assert local["sampling"]["greedy"]["token_ids"][0] == first


def test_every_committed_sample_was_distinct_at_every_temperature(local):
    """Even at 0.3, ten tokens of open-ended text branch too often for two samples to match."""
    distinct = {t: block["distinct"] for t, block in local["sampling"]["by_temperature"].items()}

    assert distinct == {"0.3": 20, "1.0": 20, "1.8": 20}


def test_the_committed_api_results_name_the_model_the_api_returned(api):
    assert api["model_requested"] == "gpt-6-astra"
    assert api["model_returned"] == "gpt-6-astra"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", api["run_date_utc"])
    assert (api["output_limit"], api["runs_per_condition"]) == (4000, 20)


def test_the_committed_probe_shows_the_model_rejects_a_temperature(api):
    probe = api["probe"]

    assert probe["outcome"] == "rejected"
    assert probe["request"]["temperature"] == 0
    assert probe["error"]["status_code"] == 400
    assert probe["error"]["type"] == "invalid_request_error"
    assert probe["error"]["param"] == "temperature"
    wording = "Unsupported parameter: 'temperature' is not supported with this model."
    assert wording in probe["error"]["message"]


def test_a_rejected_temperature_means_no_temperature_zero_run(api):
    assert [c["name"] for c in api["conditions"]] == ["coffee-default", "capital-default"]


def test_every_committed_condition_is_twenty_identical_calls_at_the_defaults(api):
    for condition in api["conditions"]:
        assert len(condition["runs"]) == 20
        assert condition["temperature_requested"] is None
        assert len({json.dumps(run["request"], sort_keys=True) for run in condition["runs"]}) == 1
        for run in condition["runs"]:
            assert "temperature" not in run["request"]
            assert run["request"]["max_output_tokens"] == 4000
            assert run["model_returned"] == "gpt-6-astra"


def test_every_committed_response_records_status_and_usage(api):
    for condition in api["conditions"]:
        for run in condition["runs"]:
            assert run["status"] == "completed"
            usage = run["usage"]
            assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]
            assert usage["reasoning_tokens"] <= usage["output_tokens"]


def test_the_api_reports_the_default_temperature_it_used_on_every_response(api):
    """The response says temperature 1.0, though this model refuses to be sent one."""
    echoed = {run["temperature_echoed"] for c in api["conditions"] for run in c["runs"]}

    assert echoed == {1.0}


def test_every_committed_count_is_the_normalisation_applied_again(api, measure):
    for condition in api["conditions"]:
        answers = [
            run["text"]
            for run in condition["runs"]
            if measure.is_answer(run["status"], run["text"])
        ]
        expected = [[answer, count] for answer, count in measure.distinct_counts(answers)]
        assert condition["distinct"] == expected
        assert condition["distinct_count"] == len(expected)
        assert condition["answered"] == len(answers)
        assert condition["answered"] + condition["unanswered"] == 20
        assert sum(count for _, count in condition["distinct"]) == condition["answered"]


def test_the_committed_answers(api):
    """The figures the README reports."""
    by_name = {c["name"]: c for c in api["conditions"]}

    assert by_name["capital-default"]["distinct"] == [["dublin", 20]]
    assert by_name["coffee-default"]["distinct"] == [
        ["the liffey grind", 17],
        ["liffey & latte", 3],
    ]
    assert by_name["coffee-default"]["unanswered"] == by_name["capital-default"]["unanswered"] == 0


# The charts ---------------------------------------------------------------------------------


def _entry(text: str, probability: float, token_id: int) -> dict:
    return {"text": text, "probability": probability, "token_id": token_id}


def _local(first: str = " the") -> dict:
    """Synthetic GPT-2 results: ten tokens per prompt and temperature, with a Dublin entry."""
    words = [first, " a", " Dublin", " now", " in", " not", " Ireland", " also", " home", " it"]

    def top(scale: float) -> dict:
        return {
            "top": [
                _entry(word, scale * (0.10 - 0.008 * rank), rank + 1)
                for rank, word in enumerate(words)
            ]
        }

    distributions = {"0.3": top(4.0), "1.0": top(1.0), "1.8": top(0.2)}
    return {
        "temperatures": [0.3, 1.0, 1.8],
        "prompts": {
            "capital": {
                "prompt": "The capital of Ireland is",
                "distributions": copy.deepcopy(distributions),
                "dublin": {"rank": 3, "probability": 0.0524},
            },
            "colour": {
                "prompt": "My favourite colour is",
                "distributions": copy.deepcopy(distributions),
            },
        },
    }


def _api(counts: list[int], *, rejected: bool = True, unanswered: int = 0) -> dict:
    names = ["capital-default", "coffee-default", "coffee-temperature-0"][: len(counts)]
    return {
        "model_returned": "gpt-6-astra",
        "runs_per_condition": 20,
        "probe": {"outcome": "rejected" if rejected else "accepted and applied"},
        "conditions": [
            {
                "name": name,
                "distinct_count": count,
                "answered": 20 - (unanswered if index == 0 else 0),
                "unanswered": unanswered if index == 0 else 0,
            }
            for index, (name, count) in enumerate(zip(names, counts, strict=True))
        ],
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


def test_the_most_likely_token_is_highlighted_whichever_it_is(chart):
    entries = [_entry(" a", 0.05, 1), _entry(" Dublin", 0.09, 2), _entry(" the", 0.04, 3)]

    assert chart.most_likely_token(entries) == 1
    assert chart.most_likely_token(list(reversed(entries))) == 1
    assert chart.most_likely_token([_entry(" Dublin", 0.2, 1), _entry(" the", 0.1, 2)]) == 0


def test_a_token_label_shows_the_space_before_the_word(chart):
    assert chart.token_label(_entry(" Dublin", 0.05, 1)) == '" Dublin"'


def test_the_condition_with_the_most_distinct_answers_is_highlighted(chart):
    assert chart.most_distinct([1, 2]) == 1
    assert chart.most_distinct([5, 1, 2]) == 0
    assert chart.most_distinct([1, 3, 2]) == 1


def test_nothing_is_highlighted_when_all_conditions_are_equal(chart):
    assert chart.most_distinct([1, 1]) is None
    assert chart.most_distinct([4, 4, 4]) is None


def test_nothing_is_highlighted_when_the_most_is_shared(chart):
    assert chart.most_distinct([3, 3, 1]) is None


def test_conditions_are_drawn_in_a_fixed_order_and_a_missing_one_is_left_out(chart):
    api = _api([5, 6, 7])
    api["conditions"].reverse()

    assert [c["name"] for c in chart.api_conditions(api)] == [
        "capital-default",
        "coffee-default",
        "coffee-temperature-0",
    ]
    assert len(chart.api_conditions(_api([5, 6]))) == 2


def test_the_committed_charts_render_from_the_committed_results_alone(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    written = chart.render(out_dir=tmp_path)

    assert sorted(path.name for path in written) == [
        f"{name}-{kind}"
        for name in ("distinct-answers", "next-token", "temperature")
        for kind in ("article.png", "slide.png", "slide.svg")
    ]
    assert specs["distinct-answers"].no_highlight_note is None


def test_the_next_token_chart_says_where_dublin_ranks(chart, local, api, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(local, api, tmp_path)

    footnote = specs["next-token"].footnote
    assert 'Prompt: "The capital of Ireland is"' in footnote
    assert '" Dublin" ranks 3, with 5.2%.' in footnote
    assert specs["next-token"].sample_size == "exact, one forward pass"


def test_the_next_token_and_temperature_charts_draw_with_one_highlight_each(
    chart, tmp_path, monkeypatch
):
    """The brand checks refuse a chart with more than one acid green element, so drawing is the
    assertion."""
    specs = _specs(chart, monkeypatch)

    chart.render(_local(), _api([1, 2]), tmp_path)

    assert specs["next-token"].no_highlight_note is None
    assert specs["temperature"].no_highlight_note is None


def test_the_temperature_chart_refuses_top_tokens_that_differ_between_temperatures(chart):
    local = _local()
    local["prompts"]["colour"]["distributions"]["1.8"]["top"][0]["token_id"] = 999

    with pytest.raises(ValueError, match="cannot share bars"):
        chart.draw_temperature(local)


def test_the_answers_chart_highlights_and_says_nothing_when_conditions_differ(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_local(), _api([1, 2]), tmp_path)

    assert specs["distinct-answers"].no_highlight_note is None


@pytest.mark.parametrize("counts", [[1, 1], [3, 3, 3], [4, 4, 2]])
def test_the_answers_chart_highlights_nothing_and_says_so_when_the_most_is_shared(
    chart, tmp_path, monkeypatch, counts
):
    specs = _specs(chart, monkeypatch)

    chart.render(_local(), _api(counts), tmp_path)

    assert "nothing highlighted" in specs["distinct-answers"].no_highlight_note


def test_the_answers_footnote_names_the_model_the_runs_and_a_rejected_temperature(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_local(), _api([1, 2], unanswered=0), tmp_path)

    spec = specs["distinct-answers"]
    assert "Model: gpt-6-astra" in spec.footnote
    assert "Temperature 0 was rejected" in spec.footnote
    assert spec.sample_size == "20 calls per condition"
    assert "incomplete" not in spec.footnote


def test_the_answers_footnote_counts_incomplete_responses_and_drops_the_rejection_when_run(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_local(), _api([1, 5, 2], rejected=False, unanswered=3), tmp_path)

    footnote = specs["distinct-answers"].footnote
    assert "3 incomplete responses are not counted." in footnote
    assert "rejected" not in footnote


def test_the_chart_module_needs_no_key_model_or_network_library():
    source = (EPISODE / "chart.py").read_text(encoding="utf-8")
    heavy = re.compile(r"^\s*(?:import|from)\s+(torch|transformers|openai|dotenv|urllib)", re.M)
    assert heavy.search(source) is None
