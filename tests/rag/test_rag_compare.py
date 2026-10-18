"""Tests for the paired comparison helpers, with expected values worked out by hand."""

import math
from pathlib import Path

import pytest

from lab.providers.base import GenerationResult
from lab.rag import compare
from lab.rag.judge import Verdict
from lab.rag.log import ItemLog, ModelCall
from lab.raw_log import RawLogWriter, RunRecord

EN_DASH = chr(0x2013)


def call(text="An answer [P1].", out=10, inp=100, finish="stop") -> ModelCall:
    return ModelCall(
        text=text,
        model_returned="m",
        input_tokens=inp,
        output_tokens=out,
        reasoning_tokens=None,
        finish_reason=finish,
    )


def verdict(declined=False, correct=True, faithful=True) -> Verdict:
    return Verdict(declined=declined, correct=correct, faithful=faithful, reason="r")


def make_log(
    item_id="i1",
    *,
    answerable=True,
    answer="default",
    verdict_=None,
    chunks=3,
) -> ItemLog:
    return ItemLog(
        item_id=item_id,
        type="t",
        asker="a",
        answerable=answerable,
        condition="c",
        config_id="cfg",
        queries=(),
        searched=(),
        removed=(),
        ranked=(),
        prompt_chunks=tuple(f"c{n}" for n in range(chunks)),
        spans=(),
        evidence_rank=None,
        distractor_above=False,
        leaks=(),
        answer=call() if answer == "default" else answer,
        verdict=verdict_,
    )


class TestHandled:
    def test_no_verdict_is_not_handled(self):
        assert compare.handled(make_log(verdict_=None)) is False

    def test_answerable_needs_correct_and_faithful(self):
        assert compare.handled(make_log(verdict_=verdict())) is True
        assert compare.handled(make_log(verdict_=verdict(correct=False))) is False
        assert compare.handled(make_log(verdict_=verdict(faithful=False))) is False

    def test_unanswerable_needs_decline(self):
        log = make_log(answerable=False, verdict_=verdict(declined=True, correct=False))
        assert compare.handled(log) is True
        assert compare.handled(make_log(answerable=False, verdict_=verdict())) is False

    def test_answered_right(self):
        assert compare.answered_right(make_log(verdict_=verdict())) is True
        assert compare.answered_right(make_log(verdict_=None)) is False
        unanswerable = make_log(answerable=False, verdict_=verdict())
        assert compare.answered_right(unanswerable) is False

    def test_hits_and_proportion(self):
        logs = [
            make_log("a", verdict_=verdict()),
            make_log("b", verdict_=verdict(correct=False)),
            make_log("c", verdict_=verdict()),
            make_log("d", verdict_=None),
        ]
        assert compare.hits(logs) == {"a": True, "b": False, "c": True, "d": False}
        p = compare.proportion(logs)
        assert (p.count, p.total, p.rate) == (2, 4, 0.5)
        assert compare.proportion(logs, compare.answered_right).count == 2


class TestMcnemar:
    def test_no_discordant_pairs(self):
        assert compare.exact_mcnemar(0, 0) == 1.0

    def test_zero_versus_five(self):
        assert compare.exact_mcnemar(0, 5) == pytest.approx(0.0625)

    def test_symmetric(self):
        assert compare.exact_mcnemar(5, 0) == compare.exact_mcnemar(0, 5)
        assert compare.exact_mcnemar(1, 4) == compare.exact_mcnemar(4, 1)

    def test_one_versus_four(self):
        # 2 * (C(5,0) + C(5,1)) / 2**5 = 12 / 32
        assert compare.exact_mcnemar(1, 4) == pytest.approx(0.375)

    def test_even_split_is_capped_at_one(self):
        # 2 * (1 + 6 + 15 + 20) / 64 = 84 / 64, capped
        assert compare.exact_mcnemar(3, 3) == 1.0


class TestPaired:
    def test_counts_shared_items_only(self):
        a = {"1": True, "2": True, "3": False, "4": True, "only_a": True}
        b = {"1": True, "2": False, "3": True, "4": False, "only_b": True}
        result = compare.paired(a, b)
        assert result["only_a"] == 2
        assert result["only_b"] == 1
        assert result["p_value"] == pytest.approx(compare.exact_mcnemar(2, 1))
        assert result["p_value"] == 1.0


class TestHolm:
    def test_known_example(self):
        raw = {"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005}
        adjusted = compare.holm(raw)
        assert adjusted["d"] == pytest.approx(0.02)
        assert adjusted["a"] == pytest.approx(0.03)
        assert adjusted["c"] == pytest.approx(0.06)
        assert adjusted["b"] == pytest.approx(0.06)

    def test_monotone_and_capped(self):
        adjusted = compare.holm({"x": 0.4, "y": 0.9})
        assert adjusted == {"x": pytest.approx(0.8), "y": 0.9}
        assert compare.holm({"x": 0.9, "y": 0.8, "z": 0.7})["x"] == 1.0

    def test_empty(self):
        assert compare.holm({}) == {}


def pair_table():
    return {
        ("A", "B"): {"p_holm": 0.5},
        ("A", "C"): {"p_holm": 0.001},
        ("B", "C"): {"p_holm": 0.001},
    }


class TestAllPairs:
    def test_keys_and_holm(self):
        items = ["1", "2", "3", "4", "5", "6"]
        per_model = {
            "A": dict.fromkeys(items, True),
            "B": dict.fromkeys(items, True),
            "C": dict.fromkeys(items, False),
        }
        out = compare.all_pairs(per_model)
        assert set(out) == {("A", "B"), ("A", "C"), ("B", "C")}
        assert out[("A", "B")]["p_value"] == 1.0
        assert out[("A", "B")]["p_holm"] == 1.0
        # 0 versus 6: p = 2 / 64 = 0.03125; the smaller of three p-values is scaled by 3.
        assert out[("A", "C")]["p_value"] == pytest.approx(0.03125)
        assert out[("A", "C")]["p_holm"] == pytest.approx(0.09375)
        assert out[("B", "C")]["p_holm"] == pytest.approx(0.09375)
        assert out[("A", "C")]["only_a"] == 6


class TestDistinguishable:
    def test_either_key_order(self):
        pairs = pair_table()
        assert compare.distinguishable(pairs, "A", "C") is True
        assert compare.distinguishable(pairs, "C", "A") is True
        assert compare.distinguishable(pairs, "A", "B") is False

    def test_alpha(self):
        assert compare.distinguishable(pair_table(), "A", "B", alpha=0.6) is True

    def test_missing_pair_raises(self):
        with pytest.raises(KeyError, match="no comparison"):
            compare.distinguishable(pair_table(), "A", "Z")


class TestTiers:
    def test_best_and_second_tied_third_separated(self):
        totals = {"C": 10, "A": 50, "B": 48}
        assert compare.tiers(totals, pair_table()) == [["A", "B"], ["C"]]

    def test_all_separated(self):
        pairs = {
            ("A", "B"): {"p_holm": 0.01},
            ("A", "C"): {"p_holm": 0.01},
            ("B", "C"): {"p_holm": 0.01},
        }
        assert compare.tiers({"A": 3, "B": 2, "C": 1}, pairs) == [["A"], ["B"], ["C"]]

    def test_equal_totals_break_by_name(self):
        pairs = {("A", "B"): {"p_holm": 0.9}}
        assert compare.tiers({"B": 5, "A": 5}, pairs) == [["A", "B"]]


class TestKendall:
    def test_perfect_agreement(self):
        assert compare.kendall_tau_b([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)

    def test_perfect_reversal(self):
        assert compare.kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)

    def test_tie_in_y(self):
        # Pairs: (0,1) tie in y; (0,2) and (1,2) concordant. C=2, D=0, Ty=1.
        expected = 2 / math.sqrt(2 * 3)
        assert compare.kendall_tau_b([1, 2, 3], [1, 1, 2]) == pytest.approx(expected)

    def test_tie_in_x(self):
        expected = 2 / math.sqrt(3 * 2)
        assert compare.kendall_tau_b([1, 1, 2], [1, 2, 3]) == pytest.approx(expected)

    def test_joint_tie_is_ignored(self):
        assert compare.kendall_tau_b([1, 1, 2], [1, 1, 3]) == pytest.approx(1.0)

    def test_mixed_concordant_and_discordant(self):
        # (0,1) concordant, (0,2) discordant, (1,2) discordant: (1 - 2) / sqrt(3 * 3)
        assert compare.kendall_tau_b([1, 2, 3], [2, 3, 1]) == pytest.approx(-1 / 3)

    def test_constant_sequence_gives_zero(self):
        assert compare.kendall_tau_b([1, 1, 1], [1, 2, 3]) == 0.0

    def test_bad_lengths(self):
        with pytest.raises(ValueError):
            compare.kendall_tau_b([1, 2], [1])
        with pytest.raises(ValueError):
            compare.kendall_tau_b([1], [1])


class TestBootstrapTau:
    @pytest.fixture
    def data(self):
        items = [f"i{n}" for n in range(10)]
        per_model = {
            "a": dict.fromkeys(items, True),
            "b": {i: n < 6 for n, i in enumerate(items)},
            "c": {i: n < 2 for n, i in enumerate(items)},
        }
        return {"a": 3.0, "b": 2.0, "c": 1.0}, per_model

    def test_deterministic_and_ordered(self, data):
        board, per_model = data
        first = compare.bootstrap_tau(board, per_model, resamples=200, seed=7)
        second = compare.bootstrap_tau(board, per_model, resamples=200, seed=7)
        assert first == second
        assert first["tau_b"] == 1.0
        assert first["low"] <= first["tau_b"] <= first["high"]

    def test_point_matches_kendall_on_totals(self, data):
        _, per_model = data
        shuffled = {"a": 1.0, "b": 3.0, "c": 2.0}
        out = compare.bootstrap_tau(shuffled, per_model, resamples=50)
        expected = compare.kendall_tau_b([1.0, 3.0, 2.0], [10, 6, 2])
        assert out["tau_b"] == pytest.approx(round(expected, 4))
        assert out["low"] <= out["tau_b"] <= out["high"]


def test_flips():
    before = {"1": True, "2": True, "3": False, "4": False, "5": True, "gone": True}
    after = {"1": False, "2": True, "3": True, "4": True, "5": False, "new": True}
    assert compare.flips(before, after) == {
        "right_to_wrong": 2,
        "wrong_to_right": 2,
        "flipped": 4,
        "net": 0,
    }
    assert compare.flips({"1": False}, {"1": True})["net"] == 1


class TestCited:
    def test_single_markers(self):
        assert compare.cited("See [P1] and [P3].", 5) == [1, 3]

    def test_comma_list_is_a_range_of_two(self):
        assert compare.cited("Shown in [P2, P3].", 5) == [2, 3]

    def test_hyphen_range(self):
        assert compare.cited("Shown in [P2-P4].", 5) == [2, 3, 4]

    def test_en_dash_range(self):
        assert compare.cited(f"Shown in [P2{EN_DASH}P4].", 5) == [2, 3, 4]

    def test_out_of_range_ignored(self):
        assert compare.cited("[P0] [P9] [P2]", 3) == [2]

    def test_duplicates_and_none(self):
        assert compare.cited("[P1] again [P1]", 3) == [1]
        assert compare.cited("no markers here", 3) == []


class TestNotFound:
    @pytest.mark.parametrize(
        "text",
        [
            "I could not find that in the passages.",
            "I couldn't find the answer.",
            "I cannot locate any mention.",
            "I was unable to find it.",
            "The passages do not contain this.",
            "The documents do not mention it.",
            "That is not mentioned.",
            "There is no information about it.",
            "The text does not specify the date.",
        ],
    )
    def test_recognised(self, text):
        assert compare.NOT_FOUND.search(text)

    def test_normal_answer_not_matched(self):
        assert not compare.NOT_FOUND.search("The refund window is 30 days [P1].")


class TestFormatMeasures:
    def test_citing_and_declines(self):
        logs = [
            make_log("a", answer=call("Yes [P1]."), verdict_=verdict()),
            make_log("b", answer=call("Yes, no marker."), verdict_=verdict()),
            make_log("c", answer=call("Cites out of range [P9]."), verdict_=verdict()),
            make_log(
                "d",
                answerable=False,
                answer=call("I could not find this."),
                verdict_=verdict(declined=True),
            ),
            make_log(
                "e",
                answerable=False,
                answer=call("Sorry, no."),
                verdict_=verdict(declined=True),
            ),
            make_log("f", answer=None, verdict_=verdict()),
            make_log("g", answer=call("Yes [P1]."), verdict_=None),
        ]
        out = compare.format_measures(logs)
        assert (out["citing"]["count"], out["citing"]["total"]) == (1, 3)
        recognised = out["declines_recognised"]
        assert (recognised["count"], recognised["total"]) == (1, 2)

    def test_empty(self):
        out = compare.format_measures([])
        assert out["citing"]["total"] == 0
        assert out["citing"]["rate"] == 0.0


class TestCitationValidity:
    def test_share_of_valid_citations(self):
        logs = [
            make_log("a", answer=call("[P1] and [P2]."), verdict_=verdict()),
            make_log("b", answer=call("[P3]."), verdict_=verdict()),
            # Skipped: declined, unanswerable, no answer, no verdict.
            make_log("c", answer=call("[P1]."), verdict_=verdict(declined=True)),
            make_log("d", answerable=False, answer=call("[P1]."), verdict_=verdict()),
            make_log("e", answer=None, verdict_=verdict()),
            make_log("f", answer=call("[P1]."), verdict_=None),
        ]
        out = compare.citation_validity(logs, lambda g, n: n != 2)
        assert (out["count"], out["total"]) == (2, 3)
        assert out["rate"] == pytest.approx(2 / 3)

    def test_no_citations(self):
        out = compare.citation_validity([], lambda g, n: True)
        assert out["total"] == 0


def _result(latency: float) -> GenerationResult:
    return GenerationResult(
        request_hash="h",
        provider="p",
        model_requested="m",
        model_returned="m",
        text="t",
        input_tokens=1,
        output_tokens=1,
        reasoning_tokens=None,
        cached_input_tokens=None,
        time_to_first_answer_token_ms=None,
        total_latency_ms=latency,
        finish_reason="stop",
        timestamp_utc="2026-10-18T00:00:00+00:00",
    )


def _record(call_id: str, result: GenerationResult | None, error: str | None = None) -> RunRecord:
    return RunRecord(
        call_id=call_id,
        request_hash="h",
        model_label="m",
        mode="answer",
        cell={},
        source="api",
        attempts=1,
        result=result,
        error=error,
    )


def write_raw(path: Path) -> None:
    with RawLogWriter(path) as writer:
        writer.append(_record("c1", _result(100.0)))
        writer.append(_record("c2", _result(300.0)))
        writer.append(_record("c3", None, error="boom"))


class TestBehaviour:
    @pytest.fixture
    def logs(self):
        return [
            make_log("a", answer=call("ok", out=10, inp=100)),
            make_log("b", answer=call("ok", out=30, inp=200)),
            make_log("c", answer=call("  ", out=20, inp=300, finish="refusal")),
            make_log("d", answer=None),
            make_log("e", answer=call("ok", out=40, inp=400, finish="safety")),
        ]

    def test_counts_and_medians(self, logs):
        assert compare.behaviour(logs) == {
            "median_output_tokens": 25,
            "median_input_tokens": 250,
            "errors": 1,
            "empty_answers": 1,
            "refusals": 2,
        }

    def test_no_answers(self):
        out = compare.behaviour([make_log("a", answer=None)])
        assert out["median_output_tokens"] is None
        assert out["median_input_tokens"] is None
        assert out["errors"] == 1

    def test_missing_raw_file_has_no_latency(self, logs, tmp_path):
        assert "median_latency_ms" not in compare.behaviour(logs, tmp_path / "none.jsonl")

    def test_latency_from_raw_log(self, logs, tmp_path):
        raw = tmp_path / "raw.jsonl"
        write_raw(raw)
        assert compare.behaviour(logs, raw)["median_latency_ms"] == 200.0

    def test_raw_log_without_successes(self, logs, tmp_path):
        raw = tmp_path / "empty.jsonl"
        raw.write_text("", encoding="utf-8")
        assert compare.behaviour(logs, raw)["median_latency_ms"] is None


class TestCost:
    def test_answer_cost(self):
        logs = [
            make_log("a", answer=call(out=500, inp=1000)),
            make_log("b", answer=call(out=1000, inp=2000)),
            make_log("c", answer=None),
        ]
        # (3000 * 3 + 1500 * 15) / 1e6 = 31500 / 1e6
        assert compare.answer_cost(logs, 3.0, 15.0) == pytest.approx(0.0315)

    def test_ratios(self):
        out = compare.ratios({"a": 10.0, "b": 20.0, "c": 5.0}, {"a": 5, "b": 5, "c": 0})
        assert out == {"a": 1.0, "b": 2.0}

    def test_ratios_round_to_two_places(self):
        assert compare.ratios({"a": 1.0, "b": 1.0}, {"a": 3, "b": 2}) == {"a": 1.0, "b": 1.5}
        assert compare.ratios({"a": 1.0, "b": 2.0}, {"a": 3, "b": 1}) == {"a": 1.0, "b": 6.0}
