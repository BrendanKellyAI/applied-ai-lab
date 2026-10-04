"""The S2 E6 field note: the slide listing, the builder and its checks, scoring, the claims, the
pilot, and the analysis end to end on hand-made records.

No test calls an API or reaches the network: a fake fetcher supplies book text.
"""

import csv
import json
import random
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from lab.config import load_config
from lab.experiments import load_sibling
from lab.pilot import select_calls
from lab.plan import PlannedCall, build_request, make_call_id
from lab.providers.base import GenerationResult, request_hash
from lab.raw_log import RunRecord

FIELD_NOTE = Path(__file__).parents[1] / "field-notes" / "s2-e6-distractors-and-two-facts"
MARKER = "# Everything below this line matches the slides."
END_OF_LISTING = "\n# Not on the slides."
LISTING = '''LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"


def look_alikes(target, count, rng):
    """Ids one edit from target, hardest first: for K-417, two
    digits swapped (K-147), a digit changed (K-447), the letter
    changed (X-417). Never a leading zero, so the format holds."""
    letter, d = target.split("-")
    kinds = [
        [f"{letter}-{d[:i]}{d[i + 1]}{d[i]}{d[i + 2 :]}" for i in range(2)],
        [f"{letter}-{d[:i]}{n}{d[i + 1 :]}" for i in range(3) for n in "0123456789"],
        [f"{other}-{d}" for other in LETTERS],
    ]
    found = []
    for kind in [0, 1, 2, 1] * count:
        pool = sorted({x for x in kinds[kind] if x != target and x[2] != "0"} - set(found))
        found += [rng.choice(pool)] if pool and len(found) < count else []
    return found'''

# Filler with numbers in it, so the builder has to steer around them.
SENTENCE = "The lamp burned low, and chapter 12 of the log said 1851 and 6B on the wall. "
FILLER = SENTENCE * 3000
SMALL_LENGTHS = (4000, 8000)


@pytest.fixture(scope="module")
def m():
    return SimpleNamespace(
        **{
            name: load_sibling(FIELD_NOTE / f"{name}.py")
            for name in ("lookalikes", "build_dataset", "scoring", "claims", "analyse")
        }
    )


@pytest.fixture(scope="module")
def config():
    return load_config(FIELD_NOTE / "config.yaml")


@pytest.fixture(scope="module")
def built(m, config, tmp_path_factory):
    """A dataset at small lengths from fake books, so the build checks run without a network."""
    builder = m.build_dataset
    body = f"*** START OF THE PROJECT GUTENBERG EBOOK 1 ***\n{FILLER}\n"
    body += "*** END OF THE PROJECT GUTENBERG EBOOK 1 ***\n"
    patch = pytest.MonkeyPatch()
    patch.setattr(builder.S1E7, "fetch_bytes", lambda url, timeout=0.0: body.encode("utf-8"))
    patch.setattr(builder.S1E7, "verify_checksum", lambda book, raw: None)
    folder = tmp_path_factory.mktemp("s2e6")
    try:
        dataset = builder.build_dataset(
            config, folder, lengths=SMALL_LENGTHS, cache_dir=folder / ".cache"
        )
        again = builder.build_dataset(
            config, folder, lengths=SMALL_LENGTHS, cache_dir=folder / ".cache", write=False
        )
    finally:
        patch.undo()
    return SimpleNamespace(dataset=dataset, again=again, folder=folder)


# The slide listing ---------------------------------------------------------------------------


def test_listing_matches_the_slide():
    source = (FIELD_NOTE / "lookalikes.py").read_text(encoding="utf-8")
    listing = source.split(MARKER, 1)[1].split(END_OF_LISTING, 1)[0].strip("\n")
    assert listing == LISTING
    body = listing.split("def look_alikes", 1)[1].splitlines()
    assert len(body) <= 16


def test_look_alikes_are_one_edit_hardest_first(m):
    rng = random.Random(0)
    for _ in range(200):
        target = f"{rng.choice(m.lookalikes.LETTERS)}-{rng.randint(100, 999)}"
        found = m.lookalikes.look_alikes(target, 4, rng)
        assert len(set(found)) == 4 and target not in found
        assert all(m.build_dataset.edit_distance(x, target) == 1 for x in found)
        assert all(x[2] != "0" for x in found)
        kinds = [m.scoring.edit_kind(x, target) for x in found]
        if _swappable(target):
            assert kinds == ["swap", "digit", "letter", "digit"]
        else:
            assert kinds == ["digit", "letter", "digit", "digit"]


def _swappable(target: str) -> bool:
    """Whether two neighbouring digits differ, and swapping them keeps a leading digit."""
    d = target[2:]
    return (d[0] != d[1] and d[1] != "0") or d[1] != d[2]


def test_look_alikes_without_a_swap_still_fill(m):
    found = m.lookalikes.look_alikes("K-111", 4, random.Random(1))
    assert len(set(found)) == 4
    assert all(m.build_dataset.edit_distance(x, "K-111") == 1 for x in found)


def test_look_alikes_come_from_the_seed(m):
    assert m.lookalikes.look_alikes("K-417", 4, random.Random(7)) == m.lookalikes.look_alikes(
        "K-417", 4, random.Random(7)
    )


# The build -----------------------------------------------------------------------------------


def test_build_makes_every_shape_length_and_item(built):
    dataset = built.dataset
    assert len(dataset.fact_sets) == 12
    assert len(dataset.documents) == 12 * 4 * len(SMALL_LENGTHS)


def test_rebuild_is_identical(m, config, built):
    first = m.build_dataset.manifest(built.dataset, config)
    second = m.build_dataset.manifest(built.again, config)
    assert first == second


def test_every_shape_shares_one_filler(m, built):
    """The paired design: removing the inserted sentences leaves the same text in every shape."""
    by_key = {}
    for document in built.dataset.documents:
        fact = built.dataset.fact_sets[document.item]
        text = document.text
        for insert in m.build_dataset.inserts(fact, document.shape):
            text = text.replace(insert.sentence, "")
        by_key.setdefault((document.item, document.context_length_tokens), set()).add(
            " ".join(text.split())
        )
    assert all(len(texts) == 1 for texts in by_key.values())


def test_values_avoid_the_book_text(built):
    for fact in built.dataset.fact_sets:
        assert fact.hangar != "6B" and "6B" not in fact.look_alike_hangars
        values = {fact.maintenance_code, fact.access_code, *fact.look_alike_codes}
        assert "1851" not in values
        assert "12" not in values


def test_lengths_and_positions_within_tolerance(m, config, built):
    found = m.build_dataset.deviations(built.dataset.documents)
    assert found["max_length_deviation_percent"] <= config.parameters["length_tolerance_percent"]
    limit = config.parameters["position_tolerance_points"]
    assert found["max_position_deviation_points"] <= limit


def test_placement_rules(built):
    for fact in built.dataset.fact_sets:
        assert 25 <= fact.target_position <= 75
        early, late = sorted((fact.bridge_position, fact.answer_position))
        assert 10 <= early <= 30 and 70 <= late <= 90
        assert (fact.bridge_position < fact.answer_position) == fact.bridge_first
        for fixed, spread in (
            ([fact.target_position], fact.distractor_positions),
            ([fact.bridge_position, fact.answer_position], fact.combined_positions),
        ):
            everything = [*fixed, *spread]
            gaps = [abs(a - b) for i, a in enumerate(everything) for b in everything[i + 1 :]]
            assert min(gaps) >= 10
            assert all(0 <= p <= 100 for p in spread)


def test_order_alternates_six_against_six(built):
    assert sum(fact.bridge_first for fact in built.dataset.fact_sets) == 6


def test_shape_four_uses_a_swap_and_a_changed_digit(m, built):
    for fact in built.dataset.fact_sets:
        kinds = [m.scoring.edit_kind(x, fact.identifier) for x in fact.look_alikes[:2]]
        assert kinds == (["swap", "digit"] if _swappable(fact.identifier) else ["digit", "letter"])


def test_a_two_edit_look_alike_fails_the_build(m, built):
    fact = built.dataset.fact_sets[0]
    bad = fact.__class__(**{**fact.__dict__, "look_alikes": ("Q-999", *fact.look_alikes[1:])})
    with pytest.raises(m.build_dataset.DatasetError, match="one edit"):
        m.build_dataset.check_fact_set(bad)


def test_a_repeated_value_fails_the_build(m, built):
    fact = built.dataset.fact_sets[0]
    codes = (fact.maintenance_code, *fact.look_alike_codes[1:])
    bad = fact.__class__(**{**fact.__dict__, "look_alike_codes": codes})
    with pytest.raises(m.build_dataset.DatasetError, match="repeats"):
        m.build_dataset.check_fact_set(bad)


def test_a_value_in_the_book_fails_the_build(m, config, built):
    builder = m.build_dataset
    fact = built.dataset.fact_sets[0]
    document = next(d for d in built.dataset.documents if d.item == 0 and d.shape == "single")
    filler = builder.Filler(f"Code {fact.maintenance_code} was here. " * 400, len)
    with pytest.raises(builder.DatasetError, match="book text"):
        builder.check_document(document, fact, filler, config.parameters)


def test_questions_never_contain_the_answer(m, built):
    builder = m.build_dataset
    for fact in built.dataset.fact_sets:
        for shape in builder.SHAPES:
            asked = builder.whole_tokens(builder.question(fact, shape))
            assert asked[builder.expected(fact, shape).lower()] == 0
            assert asked[fact.hangar.lower()] == 0


def test_documents_hold_each_sentence_once(m, built):
    for document in built.dataset.documents:
        fact = built.dataset.fact_sets[document.item]
        for insert in m.build_dataset.inserts(fact, document.shape):
            assert document.text.count(insert.sentence) == 1


def test_plan_has_one_call_per_model_and_document(m, config, built, monkeypatch):
    monkeypatch.setattr(m.build_dataset, "CONTEXT_LENGTH_OVERRIDE", SMALL_LENGTHS)
    calls = m.build_dataset.plan_calls(config, built.folder)
    assert len(calls) == 3 * len(built.dataset.documents)
    call = calls[0]
    assert call.request.system == m.build_dataset.SYSTEM_PROMPT
    assert call.request.prompt.startswith("<document>\n")
    assert "\n</document>\n\nQuestion: What is the " in call.request.prompt


# Pilot ---------------------------------------------------------------------------------------


def _grid_calls(config):
    calls = []
    for shape in config.parameters["shapes"]:
        for length in config.parameters["context_lengths_tokens"]:
            for item in range(12):
                cell = {"shape": shape, "context_length_tokens": length, "item": item}
                for model in config.models:
                    calls.append(
                        PlannedCall(
                            call_id=make_call_id(
                                model_label=model.display_label, mode="standard", cell=cell
                            ),
                            model_label=model.display_label,
                            mode="standard",
                            cell=cell,
                            request=build_request(model, "standard", prompt="p", system="s"),
                        )
                    )
    return calls


def test_pilot_is_fifteen_calls_reaching_128k_for_every_provider(config):
    calls = _grid_calls(config)
    assert len(calls) == 432
    pilot = select_calls(calls, config, pilot=True)
    assert len(pilot) == 15
    longest = {c.request.provider for c in pilot if c.cell["context_length_tokens"] == 128000}
    assert longest == {"openai", "anthropic", "google"}


# Scoring -------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fact(m):
    manifest = m.build_dataset.load_manifest(FIELD_NOTE)
    return m.build_dataset.fact_sets_from(manifest)[0]


def _classify(m, reply, shape, fact, finish="stop"):
    return m.scoring.classify(reply, finish, fact, shape, m.build_dataset)


def test_correct_reply(m, fact):
    verdict = _classify(m, f"{fact.maintenance_code}", "single", fact)
    assert verdict.correct and verdict.type == "correct"


def test_look_alike_code_is_a_distractor_value(m, fact):
    verdict = _classify(m, fact.look_alike_codes[0], "distractors", fact)
    assert (verdict.correct, verdict.type, verdict.matched) == (
        False,
        "distractor value",
        fact.look_alike_codes[0],
    )
    assert "(swap)" in verdict.matched_role


def test_hangar_is_intermediate_in_two_fact_shapes(m, fact):
    verdict = _classify(m, f"Hangar {fact.hangar}", "two-fact", fact)
    assert verdict.type == "intermediate"


def test_look_alike_hangar_is_a_distractor_value(m, fact):
    verdict = _classify(m, fact.look_alike_hangars[0], "two-fact-distractors", fact)
    assert verdict.type == "distractor value"
    unbridged = _classify(m, fact.look_alike_access_codes[3], "two-fact-distractors", fact)
    assert "no turbine" in unbridged.matched_role


def test_truncated_reply_is_wrong_and_flagged(m, fact):
    verdict = _classify(m, fact.maintenance_code, "single", fact, finish="length")
    assert (verdict.correct, verdict.type, verdict.truncated) == (False, "other", True)


def test_refusal_is_other(m, fact):
    assert _classify(m, "I don't know.", "two-fact", fact).type == "other"


def test_hedged_reply_is_correct_but_counted(m, fact):
    reply = f"{fact.maintenance_code} or {fact.look_alike_codes[1]}"
    verdict = _classify(m, reply, "distractors", fact)
    assert verdict.correct and verdict.also_names_distractor


def test_whole_token_rule(m, fact):
    assert not _classify(m, f"{fact.maintenance_code}1", "single", fact).correct


# Claims --------------------------------------------------------------------------------------

MODELS = ["A", "B", "C"]
LENGTHS = [16000, 64000, 128000]
SHAPES = ["single", "distractors", "two-fact", "two-fact-distractors"]


def _cells(m, correct: dict):
    """Cells where every model scores `correct[(shape, length)]` of 12, unless given per model."""
    counts = {}
    for shape in SHAPES:
        for length in LENGTHS:
            value = correct.get((shape, length), 12)
            for index, model in enumerate(MODELS):
                n = value[index] if isinstance(value, tuple) else value
                counts[(model, shape, length)] = m.claims.Count(n, 12)
    return m.claims.Cells(counts, MODELS)


def _marks(config):
    return config.parameters["pass_marks"]


def test_all_correct_holds_h0_and_fails_the_rest(m, config):
    claims = m.claims.evaluate(_cells(m, {}), LENGTHS, 0, _marks(config))
    assert [c.verdict for c in claims] == ["Held", "Failed", "Failed", "Failed", "Failed", "Failed"]


def test_h1_needs_four_calls_and_three_distractor_replies(m, config):
    # 4 of 36 lower is 11.1 points; 3 of 36 is 8.3.
    four = _cells(m, {("distractors", 128000): (11, 11, 10)})
    three = _cells(m, {("distractors", 128000): (11, 11, 11)})
    assert m.claims.evaluate(four, LENGTHS, 3, _marks(config))[1].verdict == "Held"
    assert m.claims.evaluate(four, LENGTHS, 2, _marks(config))[1].verdict == "Failed"
    assert m.claims.evaluate(three, LENGTHS, 9, _marks(config))[1].verdict == "Failed"


def test_h0_fails_when_one_model_misses_three(m, config):
    cells = _cells(m, {("single", 16000): (9, 12, 12)})
    assert m.claims.evaluate(cells, LENGTHS, 0, _marks(config))[0].verdict == "Failed"


def test_h3_needs_both_gaps(m, config):
    held = _cells(
        m,
        {
            ("distractors", 128000): 10,
            ("two-fact", 128000): 10,
            ("two-fact-distractors", 128000): (9, 9, 8),
        },
    )
    failed = _cells(
        m,
        {
            ("distractors", 128000): 10,
            ("two-fact", 128000): 9,
            ("two-fact-distractors", 128000): (9, 9, 8),
        },
    )
    assert m.claims.evaluate(held, LENGTHS, 0, _marks(config))[3].verdict == "Held"
    assert m.claims.evaluate(failed, LENGTHS, 0, _marks(config))[3].verdict == "Failed"


def test_h5_needs_non_overlapping_intervals(m, config):
    apart = _cells(m, {("two-fact-distractors", 128000): (12, 12, 3)})
    close = _cells(m, {("two-fact-distractors", 128000): (12, 12, 9)})
    assert m.claims.evaluate(apart, LENGTHS, 0, _marks(config))[5].verdict == "Held"
    assert m.claims.evaluate(close, LENGTHS, 0, _marks(config))[5].verdict == "Failed"


def test_partial_grid_is_not_evaluated(m, config):
    cells = m.claims.Cells({("A", "single", 16000): m.claims.Count(1, 1)}, MODELS)
    verdicts = {c.verdict for c in m.claims.evaluate(cells, LENGTHS, 0, _marks(config))}
    assert verdicts == {"Not evaluated"}


def test_preregistration_states_the_config_marks(config):
    text = " ".join((FIELD_NOTE / "PREREGISTRATION.md").read_text(encoding="utf-8").split())
    marks = _marks(config)
    assert f"each model at least {marks['h0_single_correct_per_model']} of 36" in text
    assert f"pooled at 128,000 at least {marks['h0_single_correct_pooled_128k']} of 36" in text
    assert f"at least {marks['h1_drop_points']} points below pooled Single" in text
    assert f"at least {marks['h1_distractor_replies']} wrong replies" in text
    assert f"Two-fact accuracy at 128,000 is at least {marks['h2_drop_points']}" in text
    assert f"at least {marks['h3_drop_points']} points below both" in text
    assert f"at least {marks['h4_drop_points']} points below pooled shape 4 at 16,000" in text


# Analysis end to end -------------------------------------------------------------------------


def _record(model, shape, length, item, text, finish="stop") -> RunRecord:
    cell = {"shape": shape, "context_length_tokens": length, "item": item}
    request = build_request(model, "standard", prompt="prompt", system="system")
    call = PlannedCall(
        call_id=make_call_id(model_label=model.display_label, mode="standard", cell=cell),
        model_label=model.display_label,
        mode="standard",
        cell=cell,
        request=request,
    )
    result = GenerationResult(
        request_hash=request_hash(request),
        provider=model.provider,
        model_requested=model.model,
        model_returned=model.model,
        text=text,
        input_tokens=length,
        output_tokens=4,
        reasoning_tokens=0 if model.provider != "google" else None,
        cached_input_tokens=0,
        time_to_first_answer_token_ms=10.0,
        total_latency_ms=20.0,
        finish_reason=finish,
        timestamp_utc="2026-10-05T10:00:00+00:00",
    )
    return RunRecord.for_call(call, source="api", attempts=1, result=result)


@pytest.fixture(scope="module")
def full_run(m, config):
    """Every call answered: Gemini takes look-alike codes on shape 4 at 128,000, Sonnet names
    the hangar on two two-fact items, and one Terra reply is cut short."""
    builder = m.build_dataset
    facts = builder.fact_sets_from(builder.load_manifest(FIELD_NOTE))
    records = []
    for model in config.models:
        for shape in builder.SHAPES:
            for length in LENGTHS:
                for item, fact in enumerate(facts):
                    text, finish = builder.expected(fact, shape), "stop"
                    gemini = model.label == "Gemini 3.6 Flash"
                    if gemini and shape == "two-fact-distractors" and length == 128000 and item < 9:
                        text = fact.look_alike_access_codes[0]
                    if model.label == "Claude Sonnet 5" and shape == "two-fact" and item < 2:
                        text = f"Hangar {fact.hangar}"
                    if model.label == "GPT-5.6 Terra" and shape == "single" and item == 0:
                        finish = "length" if length == 64000 else "stop"
                    records.append(_record(model, shape, length, item, text, finish))
    return records


def test_analysis_end_to_end(m, config, full_run, tmp_path):
    report = m.analyse.analyse(config, FIELD_NOTE, full_run, tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))

    assert summary["scored_calls"] == 432 and summary["grid_complete"]
    verdicts = {c["id"]: c["verdict"] for c in summary["claims"]}
    assert verdicts == {
        "H0": "Held",
        "H1": "Failed",
        "H2": "Failed",
        "H3": "Held",
        "H4": "Held",
        "H5": "Held",
    }
    assert summary["wrong_by_shape"]["two-fact-distractors"]["distractor value"] == 9
    assert summary["wrong_by_shape"]["two-fact"]["intermediate"] == 6
    assert summary["truncated"] == [
        {"model": "GPT-5.6 Terra", "shape": "single", "length": 64000, "item": 0}
    ]
    assert summary["chart_highlights"]["models-hardest"] == "Gemini 3.6 Flash"
    assert summary["chart_highlights"]["wrong-types"] == "two-fact-distractors"
    assert summary["chart_highlights"]["length-hardest"] == "Gemini 3.6 Flash"
    assert summary["tokens"]["GPT-5.6 Terra"]["reasoning_tokens"] == 0

    with (tmp_path / "wrong_answers.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 9 + 6 + 1
    assert {row["type"] for row in rows} == {"distractor value", "intermediate", "other"}

    charts = sorted(path.name for path in (tmp_path / "charts").iterdir())
    for name in ("shapes-128k", "length-hardest", "wrong-types", "models-hardest"):
        assert f"{name}-slide.png" in charts and f"{name}-slide.svg" in charts
        assert f"{name}-article.png" in charts
    assert "H5: Held" in report


def test_pilot_results_analyse_without_charts(m, config, full_run, tmp_path):
    pilot = [
        r for r in full_run if r.cell["item"] == 0 and r.cell["context_length_tokens"] == 16000
    ]
    report = m.analyse.analyse(config, FIELD_NOTE, pilot, tmp_path)
    assert "not complete" in report
    assert not (tmp_path / "charts").exists()


def test_too_long_errors_say_stop(m, config, full_run, tmp_path):
    model = config.models[1]
    failed = RunRecord(
        call_id="x" * 16,
        request_hash="h",
        model_label=model.display_label,
        mode="standard",
        cell={"shape": "single", "context_length_tokens": 128000, "item": 3},
        source="api",
        attempts=1,
        result=None,
        error="prompt is too long: 210000 tokens > 200000 maximum",
    )
    report = m.analyse.analyse(config, FIELD_NOTE, [*full_run[:5], failed], tmp_path)
    assert re.search(r"STOP: 1 prompt", report)


def test_manifest_matches_the_config(m, config):
    manifest = m.build_dataset.load_manifest(FIELD_NOTE)
    assert manifest["seed"] == config.seed
    assert [b["id"] for b in manifest["books"]] == [
        b["id"] for b in config.parameters["filler_books"]
    ]
    assert len(manifest["documents"]) == 144
    assert manifest["max_length_deviation_percent"] <= 5
    assert manifest["max_position_deviation_points"] <= 2
