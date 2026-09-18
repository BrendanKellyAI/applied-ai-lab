"""Deterministic scoring and confidence intervals (specification section 5.7)."""

import pytest

from lab.scoring import (
    contains_match,
    exact_match,
    integer_match,
    normalise,
    numeric_match,
    paired_difference_interval,
    parse_answer,
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


class TestParseAnswer:
    def test_reads_the_answer_line(self):
        assert parse_answer("Working it out.\nANSWER: 42") == "42"

    def test_is_not_case_sensitive(self):
        assert parse_answer("answer: 42") == "42"

    def test_ignores_markdown_around_the_value(self):
        assert parse_answer("**ANSWER: 42**") == "42"

    def test_the_last_answer_line_wins(self):
        response = "I will reply as ANSWER: <value>\nANSWER: 42"
        assert parse_answer(response) == "42"

    def test_keeps_a_comma_separated_list_intact(self):
        assert parse_answer("ANSWER: audit, balancing, flushing") == "audit, balancing, flushing"

    def test_no_answer_line_gives_none(self):
        assert parse_answer("The answer is probably 42.") is None

    def test_the_prompt_instruction_echoed_back_is_not_an_answer(self):
        # The instruction itself contains "ANSWER: <value>", so a model that only repeats it
        # must not be recorded as having answered.
        echoed = "Give your final answer on the last line in the form ANSWER: <value>"
        assert parse_answer(echoed) is None

    def test_an_answer_after_the_echoed_instruction_is_still_read(self):
        response = "I will use the form ANSWER: <value>.\nANSWER: 42"
        assert parse_answer(response) == "42"

    def test_an_empty_answer_line_gives_none(self):
        assert parse_answer("ANSWER:   ") is None


class TestIntegerMatch:
    def test_exact_value_matches(self):
        assert integer_match("42", 42)

    def test_thousands_separators_are_allowed(self):
        assert integer_match("1,024", 1024)

    def test_a_different_value_does_not_match(self):
        assert not integer_match("43", 42)

    def test_a_value_with_units_does_not_match(self):
        assert not integer_match("42 units", 42)

    def test_a_decimal_does_not_match(self):
        assert not integer_match("42.0", 42)

    def test_a_negative_value_matches(self):
        assert integer_match("-7", -7)


class TestPairedDifferenceInterval:
    def test_difference_is_the_discordant_pairs_over_the_total(self):
        change, _, _ = paired_difference_interval(10, 8, 2, 10)
        assert change == pytest.approx((8 - 2) / 30)

    def test_equal_discordant_counts_give_no_change_and_span_zero(self):
        change, low, high = paired_difference_interval(5, 4, 4, 7)
        assert change == pytest.approx(0.0)
        assert low < 0 < high

    def test_a_clear_one_sided_effect_excludes_zero(self):
        _, low, high = paired_difference_interval(5, 20, 0, 5)
        assert low > 0
        assert high <= 1.0

    def test_swapping_the_conditions_negates_the_interval(self):
        change, low, high = paired_difference_interval(7, 9, 3, 11)
        other_change, other_low, other_high = paired_difference_interval(7, 3, 9, 11)
        assert other_change == pytest.approx(-change)
        assert other_low == pytest.approx(-high)
        assert other_high == pytest.approx(-low)

    def test_the_interval_contains_the_difference(self):
        change, low, high = paired_difference_interval(4, 6, 1, 9)
        assert low <= change <= high

    def test_it_is_narrower_than_the_unpaired_interval_when_answers_agree(self):
        # 20 items, the same 3 point gain, but every disagreement is one sided: strongly paired.
        _, paired_low, paired_high = paired_difference_interval(14, 3, 0, 3)
        _, first_low, first_high = wilson_interval(17, 20)
        _, second_low, second_high = wilson_interval(14, 20)
        unpaired = (first_high - first_low) + (second_high - second_low)
        assert (paired_high - paired_low) < unpaired

    def test_an_empty_margin_falls_back_to_no_correlation(self):
        # Nobody answered correctly in either condition, so phi cannot be estimated.
        change, low, high = paired_difference_interval(0, 0, 0, 12)
        assert change == pytest.approx(0.0)
        assert low <= 0 <= high

    def test_no_pairs_gives_the_whole_range(self):
        assert paired_difference_interval(0, 0, 0, 0) == (0.0, -1.0, 1.0)

    def test_negative_counts_are_refused(self):
        with pytest.raises(ValueError):
            paired_difference_interval(1, -1, 0, 0)
