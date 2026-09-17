"""Deterministic scoring and confidence intervals (specification section 5.7)."""

import pytest

from lab.scoring import (
    contains_match,
    exact_match,
    normalise,
    numeric_match,
    wilson_interval,
)


class TestNormalise:
    def test_lowercases_and_strips(self):
        assert normalise("  Yes  ") == "yes"

    def test_collapses_inner_whitespace(self):
        assert normalise("8352\n\n  is\tthe code") == "8352 is the code"

    def test_removes_surrounding_punctuation_and_quotes(self):
        assert normalise('"8352."') == "8352"
        assert normalise("**8352**") == "8352"

    def test_keeps_inner_punctuation(self):
        assert normalise("K-417") == "k-417"

    def test_empty_stays_empty(self):
        assert normalise("   ") == ""


class TestExactMatch:
    def test_matches_ignoring_case_and_surrounding_space(self):
        assert exact_match(" 8352 ", "8352")

    def test_rejects_extra_words(self):
        assert not exact_match("the code is 8352", "8352")


class TestContainsMatch:
    """E7 scoring: correct if the normalised response contains the exact inserted value."""

    def test_finds_the_value_inside_a_sentence(self):
        assert contains_match("The maintenance code is 8352.", "8352")

    def test_rejects_a_different_value(self):
        assert not contains_match("The maintenance code is 1234.", "8352")

    def test_rejects_a_value_embedded_in_a_longer_number(self):
        assert not contains_match("the code is 83521", "8352")

    def test_accepts_a_value_next_to_punctuation(self):
        assert contains_match("Answer: (8352).", "8352")

    def test_empty_response_is_not_a_match(self):
        assert not contains_match("", "8352")

    def test_empty_value_is_never_a_match(self):
        assert not contains_match("anything", "")


class TestNumericMatch:
    def test_matches_within_tolerance(self):
        assert numeric_match("3.14159", 3.1416, tolerance=0.001)

    def test_rejects_outside_tolerance(self):
        assert not numeric_match("3.0", 3.1416, tolerance=0.001)

    def test_reads_a_number_from_a_sentence(self):
        assert numeric_match("The answer is 42.", 42, tolerance=0)

    def test_no_number_is_not_a_match(self):
        assert not numeric_match("no idea", 42, tolerance=0)


class TestWilsonInterval:
    def test_all_correct_has_an_upper_bound_of_one(self):
        point, low, high = wilson_interval(6, 6)
        assert point == 1.0
        assert high == pytest.approx(1.0)
        assert low < 1.0

    def test_none_correct_has_a_lower_bound_of_zero(self):
        point, low, high = wilson_interval(0, 6)
        assert point == 0.0
        assert low == pytest.approx(0.0)
        assert high > 0.0

    def test_matches_a_published_value(self):
        # 6 of 10 successes, Wilson 95%: 0.3127 to 0.8318, checked by hand.
        _, low, high = wilson_interval(6, 10)
        assert low == pytest.approx(0.3126, abs=0.001)
        assert high == pytest.approx(0.8318, abs=0.001)

    def test_interval_narrows_as_the_sample_grows(self):
        _, small_low, small_high = wilson_interval(5, 10)
        _, large_low, large_high = wilson_interval(50, 100)
        assert (large_high - large_low) < (small_high - small_low)

    def test_no_trials_gives_the_whole_range(self):
        point, low, high = wilson_interval(0, 0)
        assert (point, low, high) == (0.0, 0.0, 1.0)

    def test_more_correct_than_trials_is_refused(self):
        with pytest.raises(ValueError):
            wilson_interval(7, 6)
