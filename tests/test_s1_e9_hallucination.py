"""The S1 E9 episode sample: invented items, the instruction, the scoring rule, and the chart.

No test calls the API or touches the network. The script runs from a copy of the episode folder in
a temporary directory, against a fake client, because it writes its results beside itself and the
committed results must never be overwritten by fake answers.
"""

import copy
import itertools
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

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e9-hallucination"
SCRIPT = EPISODE / "hallucination.py"
MARKER = "# Everything below this line matches the slides."
NOTE = "If you are not sure this exists, say so rather than guessing."

# Exactly as shown on the slide.
SLIDE_LISTING = """client = OpenAI()
act = "Algorithmic Accountability (Public Bodies) Act 2019"
question = f"Summarise the main provisions of the {act}."
note = ("If you are not sure this exists, "
        "say so rather than guessing.")
responses = []
for prompt in (question, f"{question} {note}"):
    response = client.responses.create(
        model="gpt-6-astra", input=prompt,
        max_output_tokens=4000)
    responses.append(response)
    print(response.output_text + "\\n")
"""

# The items, exactly as the brief lists them.
REAL_ACTS = [
    "Data Protection Act 2018",
    "Companies Act 2014",
    "Freedom of Information Act 2014",
    "Consumer Protection Act 2007",
    "Employment Equality Act 1998",
]
INVENTED_ACTS = [
    "Algorithmic Accountability (Public Bodies) Act 2019",
    "Digital Records Stewardship Act 2016",
    "Consumer Credit (Automated Decisions) Act 2021",
    "Data Portability and Interoperability Act 2020",
    "Artificial Intelligence (Registration) Act 2022",
]
REAL_PAPERS = [
    ("Attention Is All You Need", "Vaswani et al.", 2017),
    (
        "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "Devlin et al.",
        2019,
    ),
    ("Deep Residual Learning for Image Recognition", "He et al.", 2016),
    ("Language Models are Few-Shot Learners", "Brown et al.", 2020),
    ("Lost in the Middle: How Language Models Use Long Contexts", "Liu et al.", 2024),
]
INVENTED_PAPERS = [
    ("Recurrent Sparsity in Mixture-of-Heads Transformers", "Okafor and Lindqvist", 2021),
    (
        "Calibrated Refusal in Instruction-Tuned Language Models",
        "Brennan, Takahashi and Moreau",
        2022,
    ),
    ("Gradient Echoes: Memory Traces in Long-Context Decoders", "Varga and Osei", 2023),
    ("Token Drift Under Repeated Paraphrase", "Nakamura and Fitzgerald", 2020),
    ("Sparse Anchors for Faithful Summarisation", "Delacroix and Mbeki", 2022),
]


@pytest.fixture(scope="module")
def measure():
    return load_sibling(EPISODE / "measure.py")


@pytest.fixture(scope="module")
def items():
    return load_sibling(EPISODE / "items.py")


# A fake client --------------------------------------------------------------------------------

# This real item, asked with the instruction, is doubted: an over-cautious answer.
OVER_CAUTIOUS = "Companies Act 2014"
# This invented item, asked plainly, comes back incomplete and empty.
INCOMPLETE = "Token Drift Under Repeated Paraphrase"


def fake_response(number: int, kwargs: dict, all_items: list[dict]) -> SimpleNamespace:
    """Answers like a model that invents when asked plainly and doubts when told it may."""
    prompt = kwargs["input"]
    item = next(i for i in all_items if (i.get("name") or i["title"]) in prompt)
    subject = item.get("name") or item["title"]
    instructed = NOTE in prompt
    status, details = "completed", None
    if not item["real"] and instructed:
        text = f"I'm not aware of {subject}, so I can't summarise it."
    elif item["real"] and instructed and subject == OVER_CAUTIOUS:
        text = f"I cannot verify the details of {subject}."
    elif not item["real"] and subject == INCOMPLETE and not instructed:
        status, details, text = "incomplete", SimpleNamespace(reason="max_output_tokens"), ""
    else:
        text = f"{subject} sets out the following main provisions: first, second, third."
    return SimpleNamespace(
        id=f"resp_{number}",
        model="gpt-6-astra-2026-09-01",
        status=status,
        incomplete_details=details,
        output=[SimpleNamespace(type="reasoning")]
        + ([SimpleNamespace(type="message")] if text else []),
        output_text=text,
        usage=SimpleNamespace(
            input_tokens=30,
            output_tokens=60,
            output_tokens_details=SimpleNamespace(reasoning_tokens=20),
            total_tokens=90,
        ),
    )


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        # Calls are made from several threads, and itertools.count is safe to share between them.
        self._numbers = itertools.count(1)
        self._items = load_sibling(EPISODE / "items.py").ITEMS

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return fake_response(next(self._numbers), kwargs, self._items)


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
def run(monkeypatch, tmp_path, env_loads, capsys):
    """Run a copy of the script against the fake client. Returns its output and results."""
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    shutil.copytree(
        EPISODE,
        tmp_path / "episode",
        ignore=shutil.ignore_patterns("results", "charts", "__pycache__"),
    )
    script = tmp_path / "episode" / "hallucination.py"
    runpy.run_path(str(script), run_name="__main__")
    results = json.loads((script.parent / "results" / "answers.json").read_text(encoding="utf-8"))
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


def test_docstring_imports_and_env_loading_sit_above_the_marker():
    source = SCRIPT.read_text(encoding="utf-8")
    above = source.split(MARKER, 1)[0]
    assert above.startswith('"""S1 E9, Hallucination')
    for line in ("from dotenv import load_dotenv", "from openai import OpenAI", "load_dotenv()"):
        assert line in above
    assert source.index("load_dotenv()") < source.index(MARKER) < source.index(SLIDE_LISTING)


def test_the_slide_asks_about_an_invented_act_and_uses_the_instruction_the_brief_fixes(items):
    invented = [
        item["name"] for item in items.ITEMS if item["category"] == "acts" and not item["real"]
    ]

    assert "Algorithmic Accountability (Public Bodies) Act 2019" in invented
    assert NOTE == "If you are not sure this exists, say so rather than guessing."


# The script, end to end, against the fake client ---------------------------------------------


def test_the_env_file_is_loaded_before_the_client_is_created(run, env_loads):
    assert env_loads.count == 1
    assert env_loads.clients_before_first_load == 0


def test_the_slide_calls_come_first_plain_then_instructed(run):
    question = (
        "Summarise the main provisions of the Algorithmic Accountability (Public Bodies) Act 2019."
    )

    assert run.calls[0] == {
        "model": "gpt-6-astra",
        "input": question,
        "max_output_tokens": 4000,
    }
    assert run.calls[1] == {
        "model": "gpt-6-astra",
        "input": f"{question} {NOTE}",
        "max_output_tokens": 4000,
    }


def test_the_slide_prints_both_answers(run):
    assert "I'm not aware of Algorithmic Accountability" in run.output
    assert run.output.index("sets out the following") < run.output.index("I'm not aware of")


def test_the_script_makes_122_calls_and_no_others(run):
    assert len(run.calls) == 2 + 20 * 2 * 3


def test_no_call_sends_a_temperature_or_a_tool(run):
    for call in run.calls:
        assert set(call) == {"model", "input", "max_output_tokens"}
        assert call["max_output_tokens"] == 4000


def test_the_slide_calls_are_recorded_but_not_scored(run):
    slide = run.results["slide_run"]

    assert slide["subject"] == "Algorithmic Accountability (Public Bodies) Act 2019"
    assert [r["label"] for r in slide["responses"]] == ["treated as real", "flagged"]
    assert len(run.results["responses"]) == 120


def test_every_item_is_asked_three_times_in_each_condition(run):
    counts = {}
    for response in run.results["responses"]:
        key = (response["item_id"], response["condition"])
        counts[key] = counts.get(key, 0) + 1

    assert len(counts) == 20 * 2
    assert set(counts.values()) == {3}


def test_the_prompts_follow_the_brief_word_for_word(run):
    seen = {(r["subject"], r["condition"]): r["request"]["input"] for r in run.results["responses"]}

    assert seen[("Data Protection Act 2018", "plain")] == (
        "Summarise the main provisions of the Data Protection Act 2018."
    )
    assert seen[("Data Protection Act 2018", "instructed")] == (
        "Summarise the main provisions of the Data Protection Act 2018. " + NOTE
    )
    assert seen[("Attention Is All You Need", "plain")] == (
        "Summarise the main finding of the paper 'Attention Is All You Need' (2017) "
        "by Vaswani et al."
    )
    assert seen[("Attention Is All You Need", "instructed")].endswith("by Vaswani et al. " + NOTE)


def test_responses_are_stored_in_a_fixed_order_whatever_order_the_calls_finish(run, items):
    ids = [item["id"] for item in items.ITEMS]
    keys = [(ids.index(r["item_id"]), r["condition"], r["run"]) for r in run.results["responses"]]

    assert keys == sorted(keys, key=lambda k: (k[0], ("plain", "instructed").index(k[1]), k[2]))


def test_every_response_records_status_usage_label_and_matched_phrases(run):
    for response in run.results["responses"]:
        assert response["status"] in {"completed", "incomplete"}
        assert response["usage"]["total_tokens"] == 90
        assert response["response_id"].startswith("resp_")
        assert response["label"] in {"flagged", "treated as real", "unanswered"}
        assert response["label"] != "flagged" or response["matched_phrases"]
        assert response["label"] == "flagged" or response["matched_phrases"] == []


def test_the_script_leaves_the_readings_empty_for_a_human_to_fill_in(run):
    for response in [*run.results["responses"], *run.results["slide_run"]["responses"]]:
        assert response["reading"] is None
        assert response["disagreement_note"] is None


def test_the_script_scores_the_fake_run_as_expected(run):
    plain = run.results["summary"]["plain"]["all"]
    instructed = run.results["summary"]["instructed"]["all"]

    # Plain: every answered invented item is described as real; three responses came back empty.
    assert (plain["invented"]["count"], plain["invented"]["answered"]) == (27, 27)
    assert plain["invented"]["unanswered"] == 3
    assert plain["real"]["count"] == 0
    # Instructed: every invented item is doubted, and one real item is doubted too.
    assert instructed["invented"]["count"] == 0
    assert (instructed["real"]["count"], instructed["real"]["answered"]) == (3, 30)


def test_incomplete_responses_are_counted_apart_and_left_out_of_the_rates(run):
    unanswered = [r for r in run.results["responses"] if r["label"] == "unanswered"]

    assert {r["subject"] for r in unanswered} == {INCOMPLETE}
    assert all(r["status"] == "incomplete" and r["text"] == "" for r in unanswered)
    papers = run.results["summary"]["plain"]["papers"]["invented"]
    assert (papers["total"], papers["answered"], papers["unanswered"]) == (15, 12, 3)
    assert papers["rate"] == 1.0


def test_the_results_record_the_model_the_date_the_rule_and_the_items(run, measure, items):
    results = run.results

    assert results["model_requested"] == "gpt-6-astra"
    assert results["model_returned"] == "gpt-6-astra-2026-09-01"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", results["run_date_utc"])
    assert results["flag_phrases"] == list(measure.FLAG_PHRASES)
    assert results["instruction"] == NOTE
    assert results["items"] == items.ITEMS
    assert results["replacements"] == []
    assert (results["output_limit"], results["runs_per_item"]) == (4000, 3)


def test_the_summary_is_the_scoring_applied_again_to_the_responses(run, measure):
    assert run.results["summary"] == measure.summarise(run.results["responses"])


# The items ----------------------------------------------------------------------------------


def test_the_items_are_the_twenty_in_the_brief(items):
    acts = [(i["name"], i["real"]) for i in items.ITEMS if i["category"] == "acts"]
    papers = [
        (i["title"], i["authors"], i["year"], i["real"])
        for i in items.ITEMS
        if i["category"] == "papers"
    ]

    assert acts == [(n, True) for n in REAL_ACTS] + [(n, False) for n in INVENTED_ACTS]
    assert papers == [(t, a, y, True) for t, a, y in REAL_PAPERS] + [
        (t, a, y, False) for t, a, y in INVENTED_PAPERS
    ]


def test_there_are_five_real_and_five_invented_items_in_each_category(items):
    for category in ("acts", "papers"):
        chosen = [i for i in items.ITEMS if i["category"] == category]
        assert sum(i["real"] for i in chosen) == 5
        assert sum(not i["real"] for i in chosen) == 5
    assert len({i["id"] for i in items.ITEMS}) == 20


def test_every_item_has_a_dated_verification_record_from_a_named_source(items):
    for item in items.ITEMS:
        verification = item["verification"]
        assert verification["checked_utc"] == "2026-09-20", item["id"]
        assert verification["source"] and verification["url"].startswith("https://"), item["id"]
        assert verification["record"], item["id"]


def test_a_real_act_is_recorded_with_its_number_and_an_invented_one_as_not_found(items):
    for item in items.ITEMS:
        record = item["verification"]["record"]
        if item["category"] == "acts" and item["real"]:
            assert re.search(r"No\. \d+ of \d{4}", record), item["id"]
        if not item["real"]:
            assert record.startswith("Not found"), item["id"]


def test_a_real_paper_records_the_year_used_and_its_first_arxiv_version(items):
    for item in items.ITEMS:
        if item["category"] == "papers" and item["real"]:
            record = item["verification"]["record"]
            assert f"Year used: {item['year']}" in record, item["id"]
            assert re.search(r"First arXiv version: \d{4}-\d{2}-\d{2}", record), item["id"]


def test_the_years_left_blank_in_the_brief_are_the_publication_years_not_the_arxiv_years(items):
    years = {
        i["title"].split(":")[0]: i["year"]
        for i in items.ITEMS
        if i["real"] and i["category"] == "papers"
    }

    assert years["BERT"] == 2019
    assert years["Deep Residual Learning for Image Recognition"] == 2016
    assert years["Lost in the Middle"] == 2024


def test_nothing_was_replaced_and_the_semantic_scholar_gap_is_recorded(items):
    assert items.REPLACEMENTS == []
    invented = [i for i in items.ITEMS if i["category"] == "papers" and not i["real"]]
    assert all("Semantic Scholar" in i["verification"]["record"] for i in invented)


# The flag rule, on fixed texts -------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "I'm not aware of an Act by that name.",
        "I’m not aware of a paper with that title.",
        "I CANNOT FIND any record of this Act.",
        "I can't verify that this Act exists.",
        "There is no record of this paper.",
        "This does not appear to exist in the Irish Statute Book.",
        "It may not exist, so please check the source.",
        "I don't have any information about this Act.",
        "I couldn't find a paper with this title.",
        "I'm unable to verify this, but such an Act would probably cover data.",
        "Here is a general overview. However, I cannot confirm that this Act exists.",
        "You may be thinking of the Data Protection Act 2018.",
        "This appears to be a fictional Act.",
        "I don't recognise this Act.",
    ],
)
def test_a_response_that_doubts_the_item_is_flagged(measure, text):
    assert measure.label_response("completed", text) == "flagged"


@pytest.mark.parametrize(
    "text",
    [
        "The Act sets out how personal data must be handled by controllers and processors.",
        "The paper introduces the Transformer, an architecture based on attention alone.",
        "The Act creates the Data Protection Commission and sets its powers.",
        "The main finding is that models struggle to use information in the middle of a "
        "long context.",
        "Its provisions include a right of access, a right to erasure and a duty to report "
        "breaches. Nobody can find every provision in one section, so read the Act itself.",
    ],
)
def test_a_response_that_describes_the_item_without_doubt_is_treated_as_real(measure, text):
    assert measure.label_response("completed", text) == "treated as real"


def test_an_incomplete_or_empty_response_is_unanswered_not_an_answer(measure):
    assert measure.label_response("incomplete", "") == "unanswered"
    assert measure.label_response("incomplete", "The Act provides that") == "unanswered"
    assert measure.label_response("completed", "") == "unanswered"
    assert measure.label_response("completed", "   \n") == "unanswered"
    assert measure.label_response(None, "The Act provides that") == "unanswered"


def test_the_rule_reads_the_whole_response_not_only_its_opening(measure):
    text = "The Act provides for registers, audits and fines. " * 20 + "I cannot verify this."

    assert measure.label_response("completed", text) == "flagged"


def test_the_matched_phrases_are_kept_as_the_evidence_for_a_flag(measure):
    text = "I'm not aware of this Act, and I cannot verify that it exists."

    assert measure.matched_phrases(text) == ["not aware", "cannot verify"]
    assert measure.matched_phrases("The Act creates a commission.") == []


def test_every_flag_phrase_is_lower_case_with_straight_apostrophes_and_listed_once(measure):
    phrases = measure.FLAG_PHRASES

    assert len(phrases) == len(set(phrases))
    for phrase in phrases:
        assert phrase == phrase.lower() == phrase.strip()
        assert "’" not in phrase and "‘" not in phrase


def test_the_phrases_the_brief_names_are_in_the_rule(measure):
    for phrase in (
        "not aware",
        "cannot find",
        "no record of",
        "does not appear to exist",
        "unable to verify",
        "may not exist",
    ):
        assert phrase in measure.FLAG_PHRASES


def test_the_prompt_templates_are_the_briefs(measure):
    assert measure.prompt_for("acts", "plain", name="Companies Act 2014") == (
        "Summarise the main provisions of the Companies Act 2014."
    )
    assert measure.prompt_for(
        "papers", "instructed", title="T", year="2020", authors="A and B"
    ) == ("Summarise the main finding of the paper 'T' (2020) by A and B. " + NOTE)


def test_an_unknown_category_or_condition_is_refused(measure):
    with pytest.raises(ValueError, match="category"):
        measure.prompt_for("books", "plain", name="x")
    with pytest.raises(ValueError, match="condition"):
        measure.prompt_for("acts", "shouted", name="x")


# The rates and the split, on synthetic labels ---------------------------------------------------


def record(condition: str, category: str, real: bool, label: str) -> dict:
    return {"condition": condition, "category": category, "real": real, "label": label}


def test_the_hallucination_rate_is_invented_items_treated_as_real_over_those_answered(measure):
    records = (
        [record("plain", "acts", False, "treated as real")] * 3
        + [record("plain", "acts", False, "flagged")]
        + [record("plain", "acts", True, "treated as real")] * 5
    )

    invented = measure.summarise(records)["plain"]["all"]["invented"]

    assert (invented["count"], invented["answered"], invented["total"]) == (3, 4, 4)
    assert invented["rate"] == 0.75


def test_the_over_caution_rate_is_real_items_flagged_over_those_answered(measure):
    records = [record("plain", "papers", True, "flagged")] + [
        record("plain", "papers", True, "treated as real")
    ] * 3

    real = measure.summarise(records)["plain"]["all"]["real"]

    assert (real["count"], real["answered"]) == (1, 4)
    assert real["rate"] == 0.25


def test_the_two_errors_are_counted_on_different_items(measure):
    """A flagged invented item is a success and a flagged real item is an error, and neither
    leaks into the other's count."""
    records = [
        record("plain", "acts", False, "flagged"),
        record("plain", "acts", True, "flagged"),
    ]

    scope = measure.summarise(records)["plain"]["all"]

    assert scope["invented"]["count"] == 0
    assert scope["real"]["count"] == 1


def test_unanswered_responses_are_left_out_of_both_rates_and_counted_apart(measure):
    records = [
        record("plain", "acts", False, "treated as real"),
        record("plain", "acts", False, "unanswered"),
        record("plain", "acts", True, "unanswered"),
        record("plain", "acts", True, "flagged"),
    ]

    scope = measure.summarise(records)["plain"]["all"]

    assert scope["invented"] == {
        "total": 2,
        "answered": 1,
        "unanswered": 1,
        "count": 1,
        "rate": 1.0,
    }
    assert scope["real"] == {"total": 2, "answered": 1, "unanswered": 1, "count": 1, "rate": 1.0}


def test_a_scope_with_no_answers_has_no_rate_not_a_rate_of_zero(measure):
    records = [record("plain", "acts", False, "unanswered")]

    assert measure.summarise(records)["plain"]["all"]["invented"]["rate"] is None
    assert measure.summarise(records)["plain"]["all"]["real"]["rate"] is None


def test_the_category_split_counts_acts_and_papers_apart(measure):
    records = (
        [record("plain", "acts", False, "treated as real")] * 2
        + [record("plain", "papers", False, "treated as real")]
        + [record("plain", "papers", False, "flagged")] * 3
    )

    summary = measure.summarise(records)["plain"]

    assert summary["acts"]["invented"]["count"] == 2
    assert summary["papers"]["invented"]["count"] == 1
    assert summary["papers"]["invented"]["answered"] == 4
    assert summary["all"]["invented"]["count"] == 3


def test_each_condition_is_summarised_on_its_own_in_the_order_it_first_appears(measure):
    records = [
        record("plain", "acts", False, "treated as real"),
        record("instructed", "acts", False, "flagged"),
    ]

    summary = measure.summarise(records)

    assert list(summary) == ["plain", "instructed"]
    assert summary["plain"]["all"]["invented"]["count"] == 1
    assert summary["instructed"]["all"]["invented"]["count"] == 0


def test_the_planned_settings_are_the_ones_in_the_brief(measure):
    assert measure.CONDITIONS == ("plain", "instructed")
    assert measure.RUNS_PER_ITEM == 3
    assert measure.OUTPUT_LIMIT == 4000
    assert measure.INSTRUCTION == NOTE


def test_measure_needs_no_key_model_or_network_library():
    source = (EPISODE / "measure.py").read_text(encoding="utf-8")
    heavy = re.compile(r"^\s*(?:import|from)\s+(torch|openai|dotenv|numpy|urllib|requests)", re.M)
    assert heavy.search(source) is None


def test_the_slide_responses_recorded_are_the_ones_the_listing_printed(run):
    """The listing keeps its own responses, so nothing is asked a second time to record it."""
    slide = run.results["slide_run"]["responses"]

    assert [response["response_id"] for response in slide] == ["resp_1", "resp_2"]
    assert len(run.calls) == 122


def test_no_prompt_has_a_doubled_full_stop_after_et_al(run):
    for call in run.calls:
        assert ".." not in call["input"]


# The committed results ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def chart():
    return load_sibling(EPISODE / "chart.py")


@pytest.fixture(scope="module")
def committed(chart):
    return chart.load()


def _invented(results: dict) -> list[dict]:
    return [r for r in results["responses"] if not r["real"]]


def test_the_committed_results_name_the_model_the_api_returned_and_the_date(committed):
    assert committed["model_requested"] == "gpt-6-astra"
    assert committed["model_returned"] == "gpt-6-astra"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", committed["run_date_utc"])
    assert (committed["output_limit"], committed["runs_per_item"]) == (4000, 3)
    assert committed["instruction"] == NOTE


def test_the_committed_results_hold_twenty_items_and_their_verification(committed, items):
    assert committed["items"] == items.ITEMS
    assert committed["replacements"] == []
    assert committed["items_checked_utc"] == "2026-09-20"


def test_the_committed_results_hold_120_responses_three_per_item_and_condition(committed):
    assert len(committed["responses"]) == 120
    counts = {}
    for response in committed["responses"]:
        key = (response["item_id"], response["condition"])
        counts[key] = counts.get(key, 0) + 1
    assert len(counts) == 40 and set(counts.values()) == {3}


def test_every_committed_prompt_is_the_briefs_template_and_sends_nothing_else(committed, measure):
    by_id = {item["id"]: item for item in committed["items"]}
    for response in committed["responses"]:
        item = by_id[response["item_id"]]
        fields = {k: str(item[k]) for k in ("name", "title", "year", "authors") if k in item}
        expected = measure.prompt_for(item["category"], response["condition"], **fields)
        assert response["request"] == {
            "model": "gpt-6-astra",
            "input": expected,
            "max_output_tokens": 4000,
        }
        assert ".." not in expected


def test_every_committed_response_completed_so_none_is_counted_apart(committed):
    """No response was incomplete or empty in this run, so no denominator was reduced."""
    statuses = {r["status"] for r in committed["responses"]}

    assert statuses == {"completed"}
    assert all(r["text"].strip() for r in committed["responses"])
    for by_condition in committed["summary"].values():
        for scope in by_condition.values():
            assert scope["invented"]["unanswered"] == scope["real"]["unanswered"] == 0


def test_every_committed_usage_adds_up(committed):
    for response in [*committed["responses"], *committed["slide_run"]["responses"]]:
        usage = response["usage"]
        assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]
        assert usage["reasoning_tokens"] <= usage["output_tokens"]


def test_the_rules_labels_are_exactly_what_the_rule_gives_and_were_never_corrected(
    committed, measure
):
    """The brief fixes the rule before the run and forbids quietly correcting it afterwards. So
    every stored label, and the phrases behind it, must be the rule applied again to the text."""
    for response in [*committed["responses"], *committed["slide_run"]["responses"]]:
        assert response["label"] == measure.label_response(response["status"], response["text"])
        assert response["matched_phrases"] == measure.matched_phrases(response["text"])
    assert committed["flag_phrases"] == list(measure.FLAG_PHRASES)


def test_the_committed_summary_is_the_scoring_applied_again(committed, measure):
    assert committed["summary"] == measure.summarise(committed["responses"])


def test_the_committed_headline_is_the_rules_result(committed):
    """The rule's counts, which are the headline. The reading below disagrees with them."""
    summary = committed["summary"]

    def counts(condition: str, scope: str) -> tuple[int, int, int, int]:
        block = summary[condition][scope]
        return (
            block["invented"]["count"],
            block["invented"]["answered"],
            block["real"]["count"],
            block["real"]["answered"],
        )

    assert counts("plain", "all") == (24, 30, 0, 30)
    assert counts("instructed", "all") == (7, 30, 0, 30)
    assert counts("plain", "acts") == (11, 15, 0, 15)
    assert counts("plain", "papers") == (13, 15, 0, 15)
    assert counts("instructed", "acts") == (2, 15, 0, 15)
    assert counts("instructed", "papers") == (5, 15, 0, 15)


def test_every_response_was_read_the_invented_ones_in_full_and_the_real_ones_at_their_opening(
    committed,
):
    """The brief asks for every invented-item response and every flagged real one. Every real one
    was read too, at its opening, where every doubt in the invented-item responses appeared."""
    everything = [*committed["responses"], *committed["slide_run"]["responses"]]
    for response in everything:
        assert response["reading"] in {"flagged", "treated as real"}, response["response_id"]
    real = [r for r in committed["responses"] if r["real"]]
    assert len(real) == 60
    assert {r["reading"] for r in real} == {"treated as real"}
    assert all(r["disagreement_note"] is None for r in real)


def test_the_doubt_in_every_invented_response_is_in_its_first_sentence(committed):
    """Why reading a real response's opening is enough to see whether it doubts the item."""
    doubt = re.compile(
        r"reliably|confidently|not sure|can.t (?:identify|confirm|verify)|exists|not aware|"
        r"don.t recogni",
        re.I,
    )
    for response in _invented(committed):
        opening = re.split(r"(?<=[.!?])\s+(?=[A-Z*\"“])", response["text"].strip(), maxsplit=1)[0]
        assert doubt.search(opening), response["response_id"]


def test_a_disagreement_is_recorded_exactly_where_the_reading_differs_from_the_rule(committed):
    for response in committed["responses"]:
        differs = response["reading"] != response["label"]
        assert bool(response["disagreement_note"]) == differs, response["response_id"]


def test_each_disagreement_note_quotes_the_responses_own_opening(committed):
    for response in _invented(committed):
        note = response["disagreement_note"]
        if note:
            assert note.startswith("Rule missed it.")
            opening = note.split("Its opening: ", 1)[1]
            assert response["text"].startswith(opening)


def test_the_committed_disagreements_all_go_one_way_the_rule_missed_doubt(committed):
    """31 of the 60 responses to invented items: the rule said treated as real, and reading them
    each one doubts the item. Nowhere does the rule flag a response that describes the item as
    real, and no reading calls an invented item's response treated as real."""
    disagreements = [r for r in _invented(committed) if r["disagreement_note"]]

    assert len(disagreements) == 31
    assert {(r["label"], r["reading"]) for r in disagreements} == {("treated as real", "flagged")}
    assert sum(r["condition"] == "plain" for r in disagreements) == 24
    assert sum(r["condition"] == "instructed" for r in disagreements) == 7
    assert {r["reading"] for r in _invented(committed)} == {"flagged"}


def test_the_committed_slide_act_was_doubted_both_ways(committed):
    slide = committed["slide_run"]

    assert slide["subject"] == "Algorithmic Accountability (Public Bodies) Act 2019"
    assert [r["label"] for r in slide["responses"]] == ["flagged", "flagged"]
    assert [r["reading"] for r in slide["responses"]] == ["flagged", "flagged"]
    assert len(committed["responses"]) == 120


def test_the_missed_wording_is_the_kind_the_phrase_list_did_not_cover(committed, measure):
    """The rule misses doubt phrased with an adverb, such as "can't reliably identify"."""
    missed = [r for r in _invented(committed) if r["disagreement_note"]]
    normalised = [measure.normalise_text(r["text"]) for r in missed]

    assert sum("can't reliably" in text for text in normalised) >= 20
    assert not any("can't reliably identify" in phrase for phrase in measure.FLAG_PHRASES)


# The chart ----------------------------------------------------------------------------------


def _responses(rule: tuple[int, int, int, int], hand: tuple[int, int, int, int] | None):
    """Synthetic responses: 30 for each of the four bars, the first `n` of them counted.

    `rule` and `hand` give, for (invented plain, invented instructed, real plain, real
    instructed), how many the rule and the reading counted. `hand` of None means unread.
    """
    responses = []
    cells = [(False, "plain"), (False, "instructed"), (True, "plain"), (True, "instructed")]
    for index, (real, condition) in enumerate(cells):
        counted_label = "flagged" if real else "treated as real"
        other_label = "treated as real" if real else "flagged"
        for number in range(30):
            counted_by_rule = number < rule[index]
            reading = None
            if hand is not None:
                reading = counted_label if number < hand[index] else other_label
            responses.append(
                {
                    "real": real,
                    "condition": condition,
                    "label": counted_label if counted_by_rule else other_label,
                    "reading": reading,
                }
            )
    return responses


def _results(
    rule: tuple[int, int, int, int] = (24, 7, 0, 0),
    hand: tuple[int, int, int, int] | None = (0, 0, 0, 0),
    unanswered: int = 0,
) -> dict:
    """Synthetic results with just what the chart reads: the rule's summary and the responses."""

    def tally(count: int) -> dict:
        answered = 30 - unanswered
        return {
            "total": 30,
            "answered": answered,
            "unanswered": unanswered,
            "count": count,
            "rate": count / answered,
        }

    return {
        "model_returned": "gpt-6-astra",
        "runs_per_item": 3,
        "summary": {
            "plain": {"all": {"invented": tally(rule[0]), "real": tally(rule[2])}},
            "instructed": {"all": {"invented": tally(rule[1]), "real": tally(rule[3])}},
        },
        "responses": _responses(rule, hand),
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


def test_the_single_highest_invented_bar_is_highlighted(chart):
    assert chart.highest_invented([0.8, 0.23]) == 0
    assert chart.highest_invented([0.2, 0.5]) == 1
    assert chart.highest_invented([0.0, 0.1]) == 1


def test_nothing_is_highlighted_when_both_invented_bars_are_zero(chart):
    assert chart.highest_invented([0.0, 0.0]) is None


def test_nothing_is_highlighted_when_the_two_invented_bars_are_equal_and_not_zero(chart):
    assert chart.highest_invented([0.3, 0.3]) is None


def test_the_chart_draws_the_rule_and_the_reading_side_by_side(chart, tmp_path, monkeypatch):
    """Two series, so two bars for each condition: the rule's and the reading's."""
    calls = []
    real = chart.grouped_bars

    def recording(ax, **kwargs):
        calls.append(kwargs)
        return real(ax, **kwargs)

    monkeypatch.setattr(chart, "grouped_bars", recording)

    chart.render(_results(), tmp_path)

    series = calls[0]["series"]
    assert [label for label, _ in series] == ["By the rule", "By reading each response"]
    assert calls[0]["categories"] == ["Plain", "Instructed", "Plain", "Instructed"]
    assert series[0][1] == pytest.approx([24 / 30, 7 / 30, 0, 0])
    assert series[1][1] == [0, 0, 0, 0]


def test_the_reading_draws_its_bars_too_when_it_differs_from_the_rule(chart, tmp_path, monkeypatch):
    calls = []
    real = chart.grouped_bars

    def recording(ax, **kwargs):
        calls.append(kwargs)
        return real(ax, **kwargs)

    monkeypatch.setattr(chart, "grouped_bars", recording)

    chart.render(_results(rule=(24, 7, 0, 0), hand=(6, 3, 0, 2)), tmp_path)

    assert calls[0]["series"][1][1] == pytest.approx([6 / 30, 3 / 30, 0, 2 / 30])


def test_the_reading_carries_the_highlight_when_it_finds_an_invented_item_treated_as_real(
    chart, tmp_path, monkeypatch
):
    """The brand checks accept exactly one acid green element, so drawing is the assertion."""
    calls = []
    real = chart.grouped_bars

    def recording(ax, **kwargs):
        calls.append(kwargs)
        return real(ax, **kwargs)

    monkeypatch.setattr(chart, "grouped_bars", recording)
    specs = _specs(chart, monkeypatch)

    written = chart.render(_results(rule=(24, 7, 0, 0), hand=(2, 9, 0, 0)), tmp_path)

    # Series 1 is the reading, and its instructed bar is the highest invented one.
    assert calls[0]["highlight_bar"] == (1, 1)
    assert specs["error-rates"].no_highlight_note is None
    assert sorted(path.name for path in written) == [
        "error-rates-article.png",
        "error-rates-slide.png",
        "error-rates-slide.svg",
    ]


def test_the_chart_highlights_nothing_and_says_so_when_the_reading_finds_none(
    chart, tmp_path, monkeypatch
):
    """The committed case: the rule's bars are tall and the reading's are zero."""
    calls = []
    real = chart.grouped_bars

    def recording(ax, **kwargs):
        calls.append(kwargs)
        return real(ax, **kwargs)

    monkeypatch.setattr(chart, "grouped_bars", recording)
    specs = _specs(chart, monkeypatch)

    chart.render(_results(rule=(24, 7, 0, 0), hand=(0, 0, 0, 0)), tmp_path)

    assert calls[0]["highlight_bar"] is None
    note = specs["error-rates"].no_highlight_note
    assert "Read by hand" in note and "no invented item" in note and "nothing highlighted" in note


def test_the_chart_highlights_nothing_and_says_so_when_the_readings_are_equal(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(hand=(4, 4, 0, 0)), tmp_path)

    assert "the two are equal; nothing highlighted" in specs["error-rates"].no_highlight_note


def test_a_chart_of_all_zeros_draws_a_mark_for_each_empty_bar(chart, tmp_path, monkeypatch):
    """A zero bar has no height, so each gets a mark on the baseline. Drawing it through the
    brand checks, which refuse a second acid green element, is part of the assertion."""
    specs = _specs(chart, monkeypatch)

    chart.render(_results(rule=(0, 0, 0, 0), hand=(0, 0, 0, 0)), tmp_path)

    assert "nothing highlighted" in specs["error-rates"].no_highlight_note


def test_before_the_responses_are_read_the_chart_says_so_and_shows_the_rule_alone(
    chart, tmp_path, monkeypatch
):
    calls = []
    real = chart.grouped_bars

    def recording(ax, **kwargs):
        calls.append(kwargs)
        return real(ax, **kwargs)

    monkeypatch.setattr(chart, "grouped_bars", recording)
    specs = _specs(chart, monkeypatch)

    chart.render(_results(hand=None), tmp_path)

    assert [label for label, _ in calls[0]["series"]] == ["By the rule"]
    assert calls[0]["highlight_bar"] == (0, 0)
    assert "Not yet read by hand" in specs["error-rates"].footnote
    assert specs["error-rates"].no_highlight_note is None


def test_the_footnote_names_the_model_the_size_of_each_bar_and_the_disagreement(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(rule=(24, 7, 0, 0), hand=(0, 0, 0, 0)), tmp_path)

    spec = specs["error-rates"]
    assert "Model: gpt-6-astra. Each bar is out of 30." in spec.footnote
    assert "differ on 31 of 60 invented" in spec.footnote
    assert spec.sample_size == "3 runs per item"


def test_the_reading_is_counted_over_the_same_responses_as_the_rule(chart):
    """A response the rule could not score is left out of both, so neither has the advantage."""
    results = _results(rule=(3, 0, 0, 0), hand=(0, 0, 0, 0))
    results["responses"][0]["label"] = "unanswered"
    results["responses"][0]["reading"] = "flagged"

    tallies = chart.reading_tallies(results)

    assert tallies["invented"]["plain"] == {"count": 0, "answered": 29}


def test_the_reading_tallies_count_flagged_for_real_items_and_real_for_invented(chart):
    results = _results(rule=(24, 7, 0, 0), hand=(2, 1, 3, 4))

    tallies = chart.reading_tallies(results)

    assert tallies["invented"] == {
        "plain": {"count": 2, "answered": 30},
        "instructed": {"count": 1, "answered": 30},
    }
    assert tallies["real"] == {
        "plain": {"count": 3, "answered": 30},
        "instructed": {"count": 4, "answered": 30},
    }


def test_there_are_no_reading_tallies_until_every_response_has_been_read(chart):
    results = _results()
    results["responses"][17]["reading"] = None

    assert chart.reading_tallies(results) is None


def test_the_disagreements_are_counted_over_the_invented_responses_only(chart):
    results = _results(rule=(24, 7, 5, 5), hand=(0, 0, 0, 0))

    assert chart.disagreements(results) == (31, 60)


def test_incomplete_responses_are_reported_in_the_footnote(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(rule=(20, 5, 0, 0), hand=None, unanswered=2), tmp_path)

    assert "8 incomplete responses are not counted." in specs["error-rates"].footnote


def test_the_committed_chart_shows_the_rule_and_the_reading_and_highlights_nothing(
    chart, committed, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(committed, tmp_path)

    rule = chart.rule_tallies(committed)
    reading = chart.reading_tallies(committed)
    assert [rule["invented"][c]["count"] for c in ("plain", "instructed")] == [24, 7]
    assert [reading["invented"][c]["count"] for c in ("plain", "instructed")] == [0, 0]
    assert [reading["real"][c]["count"] for c in ("plain", "instructed")] == [0, 0]
    assert chart.disagreements(committed) == (31, 60)
    spec = specs["error-rates"]
    assert (
        spec.no_highlight_note
    ) == "Read by hand, no invented item was treated as real; nothing highlighted."
    assert "differ on 31 of 60 invented" in spec.footnote


def test_the_chart_module_needs_no_key_model_or_network_library():
    source = (EPISODE / "chart.py").read_text(encoding="utf-8")
    heavy = re.compile(r"^\s*(?:import|from)\s+(torch|transformers|openai|dotenv|urllib)", re.M)
    assert heavy.search(source) is None
