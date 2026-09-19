"""The S1 E5 episode sample: reading against writing on GPT-2, its measurements, and its charts.

No test loads GPT-2, imports torch, times anything, or touches the network. The arithmetic is
checked on synthetic numbers, and the charts on the committed results and on synthetic timings.
"""

import re
from pathlib import Path

import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e5-the-transformer"
E4_SCRIPT = Path(__file__).parents[1] / "episodes" / "s1-e4-attention" / "attention.py"
SCRIPT = EPISODE / "timing.py"
MARKER = "# Everything below this line matches the slides."
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"

# Exactly as shown on the slide.
SLIDE_LISTING = """tokenizer = AutoTokenizer.from_pretrained(
    "gpt2", revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(
    "gpt2", revision=REVISION).eval()
long, short = prompt(tokenizer, 512), prompt(tokenizer, 8)
with torch.no_grad():
    start = time.perf_counter()
    model(**long, logits_to_keep=1)
    read = time.perf_counter() - start
    start = time.perf_counter()
    model.generate(**short, do_sample=False,
        min_new_tokens=512, max_new_tokens=512)
    write = time.perf_counter() - start
print(f"reading: {read / 512 * 1000:.1f} ms per token")
print(f"writing: {write / 512 * 1000:.1f} ms per token")
"""


@pytest.fixture(scope="module")
def measure():
    return load_sibling(EPISODE / "measure.py")


@pytest.fixture(scope="module")
def chart():
    return load_sibling(EPISODE / "chart.py")


@pytest.fixture(scope="module")
def committed(chart):
    return chart.load()


# The slide listing ---------------------------------------------------------------------------


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


def test_the_listing_reads_and_writes_the_headline_lengths(measure):
    """The slide's literals are the episode's headline lengths, so slide and results agree."""
    headline = measure.HEADLINE_TOKENS
    assert f"prompt(tokenizer, {headline})" in SLIDE_LISTING
    assert f"prompt(tokenizer, {measure.WRITING_PROMPT_TOKENS})" in SLIDE_LISTING
    assert f"min_new_tokens={headline}, max_new_tokens={headline}" in SLIDE_LISTING


def test_imports_the_revision_and_the_prompt_helper_sit_above_the_marker():
    above = SCRIPT.read_text(encoding="utf-8").split(MARKER, 1)[0]
    assert "import torch" in above
    assert "from transformers import AutoModelForCausalLM, AutoTokenizer" in above
    assert f'REVISION = "{REVISION}"' in above
    assert "def prompt(" in above
    assert "torch.set_num_threads(THREADS)" in above


def test_the_revision_is_the_one_s1_e4_uses():
    assert f'REVISION = "{REVISION}"' in E4_SCRIPT.read_text(encoding="utf-8")


def test_the_episode_needs_no_new_extra():
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r"^e4 = \[", pyproject, re.MULTILINE)
    assert "e5" not in pyproject


# Measurements on synthetic numbers -----------------------------------------------------------


def test_a_per_token_time_is_the_total_over_the_tokens_in_milliseconds(measure):
    assert measure.per_token_ms(1.024, 512) == pytest.approx(2.0)
    assert measure.per_token_ms(30.0, 512) == pytest.approx(58.59375)


def test_a_per_token_time_needs_a_token(measure):
    with pytest.raises(ValueError, match="at least one token"):
        measure.per_token_ms(1.0, 0)


def test_the_median_of_an_odd_set_is_the_middle_value(measure):
    result = measure.spread([9.0, 1.0, 5.0, 3.0, 7.0])
    assert result == {"median": 5.0, "min": 1.0, "max": 9.0}


def test_the_median_of_an_even_set_is_the_mean_of_the_middle_two(measure):
    assert measure.spread([1.0, 2.0, 4.0, 10.0])["median"] == pytest.approx(3.0)


def test_a_spread_does_not_reorder_its_input(measure):
    values = [3.0, 1.0, 2.0]
    measure.spread(values)
    assert values == [3.0, 1.0, 2.0]


def test_no_timings_cannot_be_summarised(measure):
    with pytest.raises(ValueError, match="no timings"):
        measure.spread([])


def test_a_summary_gives_total_and_per_token_as_median_min_and_max(measure):
    result = measure.summarise([1.0, 2.0, 4.0], 500)
    assert result["total_s"] == {"median": 2.0, "min": 1.0, "max": 4.0}
    assert result["per_token_ms"] == {"median": 4.0, "min": 2.0, "max": 8.0}


def test_the_ratio_is_writing_over_reading(measure):
    assert measure.ratio(60.0, 2.5) == pytest.approx(24.0)


def test_a_ratio_needs_a_positive_denominator(measure):
    with pytest.raises(ValueError, match="positive denominator"):
        measure.ratio(1.0, 0.0)


def test_the_context_guard_allows_a_prompt_and_output_that_exactly_fill_the_context(measure):
    measure.check_context(8, 1016, 1024)
    measure.check_context(1024, 0, 1024)


def test_the_context_guard_refuses_one_token_too_many(measure):
    with pytest.raises(ValueError, match="1025.*over the 1024-token context"):
        measure.check_context(8, 1017, 1024)


def test_the_context_guard_refuses_an_empty_prompt(measure):
    with pytest.raises(ValueError, match="at least 1 token"):
        measure.check_context(0, 10, 1024)


def test_every_planned_condition_fits_gpt2s_context(measure):
    for tokens in measure.SWEEP_TOKENS:
        measure.check_context(tokens, 0)
        measure.check_context(measure.WRITING_PROMPT_TOKENS, tokens)


def test_the_headline_is_one_of_the_sweep_points(measure):
    assert measure.HEADLINE_TOKENS in measure.SWEEP_TOKENS
    assert (measure.WARMUPS, measure.REPEATS) == (2, 5)


def test_a_prompt_is_the_first_tokens_of_the_text(measure):
    ids = list(range(100, 200))
    assert measure.cut_to_length(ids, 8) == list(range(100, 108))
    assert measure.cut_to_length(ids, 8) == measure.cut_to_length(ids, 8)


def test_a_shorter_prompt_is_a_prefix_of_a_longer_one(measure):
    ids = list(range(1000))
    assert measure.cut_to_length(ids, 512)[:64] == measure.cut_to_length(ids, 64)


def test_a_prompt_cannot_be_longer_than_the_text(measure):
    with pytest.raises(ValueError, match="only 5"):
        measure.cut_to_length([1, 2, 3, 4, 5], 6)


def test_a_condition_is_warmed_up_untimed_then_timed_the_stated_number_of_times(measure):
    calls = []
    ticks = iter(range(0, 100, 2))

    def run():
        calls.append(len(calls))
        return "output"

    def clock():
        return float(next(ticks))

    seconds, result = measure.timed(run, warmups=2, repeats=5, clock=clock)

    assert len(calls) == 7
    assert seconds == [2.0] * 5
    assert result == "output"
    # The clock is read only around the five timed runs, never around a warm-up.
    assert next(ticks) == 20


def test_two_figures_within_ten_percent_count_as_the_same(measure):
    assert measure.same_within(100.0, 110.0)
    assert measure.same_within(110.0, 100.0)
    assert not measure.same_within(100.0, 110.5)


def test_the_slope_of_a_straight_line_is_recovered(measure):
    assert measure.slope([64, 128, 256], [0.2 * x + 1 for x in (64, 128, 256)]) == pytest.approx(
        0.2
    )


def test_a_slope_needs_two_different_points(measure):
    with pytest.raises(ValueError):
        measure.slope([1], [1])
    with pytest.raises(ValueError, match="different x"):
        measure.slope([2, 2], [1, 3])


# The committed results ----------------------------------------------------------------------


def _gpt2_small_parameters(config: dict) -> int:
    """GPT-2's parameter count worked out from its shape alone: an independent check on the sum
    taken from the loaded model."""
    d, layers = config["n_embd"], config["n_layer"]
    embeddings = (config["vocab_size"] + config["n_positions"]) * d
    norm = 2 * d
    attention = d * 3 * d + 3 * d + d * d + d
    feed_forward = d * 4 * d + 4 * d + 4 * d * d + d
    return embeddings + layers * (norm + attention + norm + feed_forward) + norm


def test_the_committed_results_name_the_model_revision_and_libraries(committed):
    assert committed["model"] == "gpt2"
    assert committed["revision"] == REVISION
    assert (committed["device"], committed["dtype"]) == ("cpu", "float32")
    assert {"python", "torch", "transformers", "tokenizers"} <= set(committed["libraries"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", committed["run_date_utc"])


def test_the_committed_configuration_is_gpt2_small_read_from_the_model(committed):
    config = committed["configuration"]
    assert (config["n_layer"], config["n_head"], config["n_embd"]) == (12, 12, 768)
    assert (config["vocab_size"], config["n_positions"]) == (50257, 1024)


def test_the_committed_parameter_count_is_exact(committed):
    config = committed["configuration"]
    assert isinstance(config["parameters"], int)
    assert config["parameters"] == _gpt2_small_parameters(config)


def test_the_committed_machine_record_is_complete(committed):
    machine = committed["machine"]
    for field in ("cpu", "physical_cores", "logical_cores", "threads_used", "os", "power_source"):
        assert machine[field] is not None, field
    assert machine["threads_used"] >= 1


def test_the_committed_method_matches_the_measurements_fixed_in_advance(committed, measure):
    method = committed["method"]
    assert method["timer"] == "time.perf_counter"
    assert (method["warmups"], method["repeats"]) == (measure.WARMUPS, measure.REPEATS)
    assert method["headline_tokens"] == measure.HEADLINE_TOKENS
    assert method["sweep_tokens"] == list(measure.SWEEP_TOKENS)
    assert method["writing_prompt_tokens"] == measure.WRITING_PROMPT_TOKENS


def test_every_committed_condition_has_five_timed_runs_after_two_warm_ups(committed):
    assert committed["conditions"]
    for condition in committed["conditions"]:
        assert len(condition["seconds"]) == 5, condition["name"]
        assert condition["warmups"] == 2, condition["name"]
        assert all(seconds > 0 for seconds in condition["seconds"]), condition["name"]


def test_the_committed_conditions_are_both_sweeps_and_the_no_cache_run(committed, measure):
    names = [condition["name"] for condition in committed["conditions"]]
    expected = [f"reading-{n}" for n in measure.SWEEP_TOKENS]
    expected += [f"writing-{n}" for n in measure.SWEEP_TOKENS]
    expected += [f"writing-no-cache-{measure.HEADLINE_TOKENS}"]
    assert names == expected


def test_only_the_no_cache_condition_turns_the_cache_off(committed):
    off = [c["name"] for c in committed["conditions"] if not c["kv_cache"]]
    assert off == ["writing-no-cache-512"]


def test_every_committed_condition_stayed_within_the_context(committed):
    limit = committed["configuration"]["n_positions"]
    for condition in committed["conditions"]:
        assert condition["prompt_tokens"] + condition["new_tokens"] <= limit, condition["name"]


def test_reading_takes_a_prompt_and_writing_takes_the_short_prompt(committed):
    for condition in committed["conditions"]:
        if condition["kind"] == "reading":
            assert (condition["prompt_tokens"], condition["new_tokens"]) == (
                condition["tokens"],
                0,
            )
        else:
            assert (condition["prompt_tokens"], condition["new_tokens"]) == (
                8,
                condition["tokens"],
            )


def test_every_committed_summary_agrees_with_its_raw_timings(committed, measure):
    for condition in committed["conditions"]:
        expected = measure.summarise(condition["seconds"], condition["tokens"])
        for measure_name, figures in expected.items():
            assert condition["summary"][measure_name] == pytest.approx(figures), condition["name"]


def test_the_committed_prompts_come_from_the_pinned_public_domain_book(committed):
    prompt = committed["prompt"]
    assert (prompt["book"], prompt["gutenberg_id"]) == ("Pride and Prejudice", 1342)
    assert len(prompt["book_sha256"]) == 64
    assert prompt["longest_prompt_tokens"] == max(committed["method"]["sweep_tokens"])
    assert len(prompt["longest_prompt_ids_sha256"]) == 64


def test_the_filler_book_is_pinned_by_the_same_checksum_s1_e7_uses(committed):
    config = (
        Path(__file__).parents[1] / "field-notes" / "s1-e7-lost-in-the-middle" / "config.yaml"
    ).read_text(encoding="utf-8")
    assert committed["prompt"]["book_sha256"] in config


# The charts ---------------------------------------------------------------------------------


def _condition(kind: str, tokens: int, ms_per_token: float, kv_cache: bool = True) -> dict:
    seconds = ms_per_token * tokens / 1000
    return {
        "name": f"{kind}-{tokens}",
        "kind": kind,
        "kv_cache": kv_cache,
        "tokens": tokens,
        "seconds": [seconds * factor for factor in (0.98, 0.99, 1.0, 1.01, 1.02)],
    }


def _results(
    reading_ms: float,
    writing_ms: float,
    reading_headline_ms: float | None = None,
    writing_headline_ms: float | None = None,
) -> dict:
    """Synthetic timings with a steady cost per token. The 512-token point is both the headline
    and a sweep point, so a headline override lets one rule see a gap the other does not."""
    sweep = (64, 128, 256, 512, 896)
    headline = {"reading": reading_headline_ms, "writing": writing_headline_ms}

    def cost(kind: str, steady: float, tokens: int) -> float:
        override = headline[kind]
        return override if tokens == 512 and override is not None else steady

    return {
        "machine": {"cpu": "Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz", "threads_used": 4},
        "method": {"headline_tokens": 512, "sweep_tokens": list(sweep)},
        "conditions": [
            *(
                _condition("reading", tokens, cost("reading", reading_ms, tokens))
                for tokens in sweep
            ),
            *(
                _condition("writing", tokens, cost("writing", writing_ms, tokens))
                for tokens in sweep
            ),
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


def test_the_slower_bar_is_highlighted(chart):
    assert chart.slower_bar(2.0, 60.0) == 1
    assert chart.slower_bar(60.0, 2.0) == 0


def test_no_bar_is_highlighted_within_ten_percent(chart):
    assert chart.slower_bar(60.0, 64.0) is None
    assert chart.slower_bar(64.0, 60.0) is None
    assert chart.slower_bar(50.0, 50.0) is None
    # Exactly 10% apart still counts as the same; a hair more does not.
    assert chart.slower_bar(50.0, 55.0) is None
    assert chart.slower_bar(50.0, 55.1) == 1


def test_the_steeper_line_is_highlighted(chart):
    assert chart.steeper_line(0.003, 0.07) == 1
    assert chart.steeper_line(0.07, 0.003) == 0


def test_no_line_is_highlighted_when_the_slopes_are_within_ten_percent(chart):
    assert chart.steeper_line(0.030, 0.032) is None
    assert chart.steeper_line(0.032, 0.030) is None
    assert chart.steeper_line(0.030, 0.030) is None
    assert chart.steeper_line(0.030, 0.0331) == 1


def test_the_slopes_are_read_from_the_median_total_times(chart):
    reading, writing = chart.slopes(_results(2.0, 60.0))
    assert reading == pytest.approx(0.002)
    assert writing == pytest.approx(0.060)


def test_the_headline_is_read_from_the_raw_timings(chart):
    figures = chart.headline(_results(2.0, 60.0))
    assert figures["reading"]["median"] == pytest.approx(2.0)
    assert figures["writing"]["median"] == pytest.approx(60.0)
    assert figures["writing"]["min"] == pytest.approx(58.8)
    assert figures["writing"]["max"] == pytest.approx(61.2)


def test_a_missing_condition_is_named_in_the_error(chart):
    results = _results(2.0, 60.0)
    with pytest.raises(ValueError, match="writing condition of 512 tokens with kv_cache=False"):
        chart.condition(results, "writing", 512, kv_cache=False)


def test_a_cpu_name_loses_its_trademark_marks(chart):
    assert chart.short_cpu("Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz") == (
        "Intel Core i7-8565U @ 1.80GHz"
    )
    assert chart.short_cpu(None) == "an unnamed CPU"


def test_both_rules_highlight_when_writing_is_far_slower(chart, tmp_path, monkeypatch):
    """The brand checks accept exactly one acid green element on each chart."""
    specs = _specs(chart, monkeypatch)

    chart.render(_results(2.0, 60.0), tmp_path)

    assert specs["per-token"].no_highlight_note is None
    assert specs["sweep"].no_highlight_note is None


def test_both_rules_highlight_reading_when_reading_is_the_slower_one(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(60.0, 2.0), tmp_path)

    assert specs["per-token"].no_highlight_note is None
    assert specs["sweep"].no_highlight_note is None
    assert chart.slower_bar(60.0, 2.0) == 0


def test_nothing_is_highlighted_when_reading_and_writing_are_within_ten_percent(
    chart, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(50.0, 52.0), tmp_path)

    assert "nothing highlighted" in specs["per-token"].no_highlight_note
    assert "nothing highlighted" in specs["sweep"].no_highlight_note


def test_the_bars_can_be_the_same_while_the_slopes_differ(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(2.0, 6.0, writing_headline_ms=2.05), tmp_path)

    assert "nothing highlighted" in specs["per-token"].no_highlight_note
    assert specs["sweep"].no_highlight_note is None


def test_the_slopes_can_be_the_same_while_the_bars_differ(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(2.0, 2.0, writing_headline_ms=2.4), tmp_path)

    assert specs["per-token"].no_highlight_note is None
    assert "nothing highlighted" in specs["sweep"].no_highlight_note


def test_the_footnotes_name_the_model_cpu_threads_and_sample(chart, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    chart.render(_results(2.0, 60.0), tmp_path)

    for name in ("per-token", "sweep"):
        spec = specs[name]
        assert "GPT-2 small" in spec.footnote
        assert "Intel Core i7-8565U @ 1.80GHz" in spec.footnote
        assert "4 threads" in spec.footnote
        assert spec.sample_size == "median of 5 runs"
    assert "30.0 times as long per token as reading" in specs["per-token"].footnote


def test_the_committed_charts_render_from_the_committed_results_alone(chart, committed, tmp_path):
    written = chart.render(committed, tmp_path)

    assert sorted(path.name for path in written) == [
        "per-token-article.png",
        "per-token-slide.png",
        "per-token-slide.svg",
        "sweep-article.png",
        "sweep-slide.png",
        "sweep-slide.svg",
    ]


def test_the_chart_and_measure_modules_import_no_model_or_network_library():
    heavy = re.compile(r"^\s*(?:import|from)\s+(torch|transformers|urllib|requests|socket)", re.M)
    for name in ("chart.py", "measure.py"):
        source = (EPISODE / name).read_text(encoding="utf-8")
        assert heavy.search(source) is None, name
