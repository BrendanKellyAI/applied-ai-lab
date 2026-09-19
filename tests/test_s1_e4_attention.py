"""The S1 E4 episode sample: attention from "it", its measurements, and its charts.

No test loads GPT-2, imports torch, or touches the network. The measurements are checked on small
synthetic attention arrays, and the charts on the committed results and on synthetic data.
"""

from pathlib import Path

import numpy as np
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s1-e4-attention"
SCRIPT = EPISODE / "attention.py"
MARKER = "# Everything below this line matches the slides."
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"

# Exactly as shown on the slide.
SLIDE_LISTING = """tokenizer = AutoTokenizer.from_pretrained(
    "gpt2", revision=REVISION)
model = AutoModel.from_pretrained(
    "gpt2", revision=REVISION, attn_implementation="eager")
sentence = ("The trophy did not fit in the suitcase "
            "because it was too big.")
inputs = tokenizer(sentence, return_tensors="pt")
with torch.no_grad():
    out = model(**inputs, output_attentions=True)
weights = torch.stack(out.attentions).mean(dim=(0, 2))[0]
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
it = tokens.index("Ġit")
pairs = zip(weights[it, :it].tolist(), tokens)
for weight, token in sorted(pairs, reverse=True):
    print(f"{weight:.3f}  {token.lstrip('Ġ')}")
"""

G = "Ġ"


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


def test_imports_and_the_pinned_revision_sit_above_the_marker():
    above = SCRIPT.read_text(encoding="utf-8").split(MARKER, 1)[0]
    assert "import torch" in above
    assert "from transformers import AutoModel, AutoTokenizer" in above
    assert f'REVISION = "{REVISION}"' in above


def test_the_slide_sentence_is_the_big_sentence_the_script_measures():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"big": "The trophy did not fit in the suitcase because it was too big.",' in source
    assert '"small": "The trophy did not fit in the suitcase because it was too small.",' in source


# Measurements on synthetic attention ---------------------------------------------------------


def test_a_word_split_across_tokens_is_one_word(measure):
    tokens = ["The", f"{G}tro", "phy", f"{G}did", f"{G}it"]
    assert measure.word_spans(tokens, 4) == [("The", [0]), ("trophy", [1, 2]), ("did", [3])]


def test_a_word_weight_is_the_sum_over_its_tokens(measure):
    tokens = ["The", f"{G}tro", "phy", f"{G}did", f"{G}it"]
    row = np.array([0.5, 0.1, 0.15, 0.05, 0.2])
    result = measure.word_weights(row, measure.word_spans(tokens, 4), 4)
    trophy = next(word for word in result["words"] if word["word"] == "trophy")
    assert trophy["raw"] == pytest.approx(0.25)


def test_the_raw_set_with_the_token_itself_sums_to_one(measure):
    tokens = ["The", f"{G}tro", "phy", f"{G}did", f"{G}it"]
    row = np.array([0.5, 0.1, 0.15, 0.05, 0.2])
    result = measure.word_weights(row, measure.word_spans(tokens, 4), 4)
    total = sum(word["raw"] for word in result["words"]) + result["self_weight"]
    assert total == pytest.approx(1.0)


def test_the_first_token_is_reported_alone_and_left_out_of_the_renormalised_set(measure):
    tokens = ["The", f"{G}tro", "phy", f"{G}did", f"{G}it"]
    row = np.array([0.5, 0.1, 0.15, 0.05, 0.2])
    result = measure.word_weights(row, measure.word_spans(tokens, 4), 4)
    words = {word["word"]: word for word in result["words"]}
    assert result["first_token_share"] == pytest.approx(0.5)
    assert words["The"]["renormalised"] is None
    # The other earlier words, 0.25 and 0.05, rescaled to sum to 1.
    assert words["trophy"]["renormalised"] == pytest.approx(0.25 / 0.30)
    assert words["did"]["renormalised"] == pytest.approx(0.05 / 0.30)


def test_a_first_word_split_across_tokens_keeps_its_later_tokens(measure):
    tokens = ["Tro", "phy", f"{G}did", f"{G}it"]
    row = np.array([0.6, 0.1, 0.1, 0.2])
    result = measure.word_weights(row, measure.word_spans(tokens, 3), 3)
    first = result["words"][0]
    assert first["word"] == "Trophy"
    assert first["renormalised"] == pytest.approx(0.5)


def test_the_average_runs_over_every_layer_and_head(measure):
    attentions = np.zeros((2, 3, 4, 4))
    attentions[0, 0, 3, 1] = 1.0
    attentions[1, 2, 3, 2] = 1.0
    row = measure.averaged_row(attentions, 3)
    assert row[1] == pytest.approx(1 / 6)
    assert row[2] == pytest.approx(1 / 6)


def test_trophy_minus_suitcase_per_layer_and_per_head(measure):
    attentions = np.zeros((2, 2, 4, 4))
    attentions[:, :, 3, 1] = [[0.4, 0.2], [0.1, 0.1]]
    attentions[:, :, 3, 2] = [[0.1, 0.1], [0.3, 0.1]]
    result = measure.trophy_minus_suitcase(attentions, 3, [1], [2])
    assert np.allclose(result["per_head"], [[0.3, 0.1], [-0.2, 0.0]])
    assert result["per_layer"] == pytest.approx([0.2, -0.1])


def test_head_shifts_are_counted_each_way_with_unchanged_heads_apart(measure):
    big = np.array([[0.3, 0.1], [0.0, 0.2]])
    small = np.array([[0.1, 0.1], [0.1, 0.2]])
    result = measure.head_shifts(big, small)
    assert result["heads"] == 4
    assert (result["towards_suitcase"], result["towards_trophy"], result["unchanged"]) == (1, 1, 2)


def test_the_most_responsive_head_is_labelled_as_chosen_after_looking(measure):
    result = measure.head_shifts(np.array([[0.3, 0.1]]), np.array([[0.1, 0.15]]))
    most = result["most_responsive_head"]
    assert most["label"] == "the most responsive head, chosen after looking"
    assert (most["layer"], most["head"]) == (0, 0)


def test_no_head_is_named_when_none_moves(measure):
    identical = np.array([[0.3, 0.1]])
    assert measure.head_shifts(identical, identical)["most_responsive_head"] is None


# The committed results ----------------------------------------------------------------------


def test_the_committed_results_name_the_model_and_revision(committed):
    assert committed["model"] == "gpt2"
    assert committed["revision"] == REVISION
    assert {"torch", "transformers", "tokenizers", "numpy"} <= set(committed["libraries"])


def test_every_committed_weight_set_sums_to_one(committed):
    for sentence in committed["sentences"].values():
        raw = sum(word["raw"] for word in sentence["words"]) + sentence["self_weight"]
        renormalised = sum(
            word["renormalised"] for word in sentence["words"] if word["renormalised"] is not None
        )
        assert raw == pytest.approx(1.0, abs=1e-6)
        assert renormalised == pytest.approx(1.0, abs=1e-6)


def test_every_word_records_its_token_split(committed):
    for sentence in committed["sentences"].values():
        for word in sentence["words"]:
            assert len(word["token_split"]) == len(word["tokens"]) >= 1


def test_every_head_is_counted_once(committed):
    shifts = committed["head_shifts"]
    total = shifts["towards_suitcase"] + shifts["towards_trophy"] + shifts["unchanged"]
    assert total == shifts["heads"] == 144


def test_attention_up_to_it_is_identical_in_both_sentences(committed):
    """GPT-2 reads left to right, so "it" cannot see "big" or "small". This pins that the
    measurement shows it: not a tolerance, an exact zero."""
    assert committed["max_difference_up_to_it"] == 0.0


# The charts ---------------------------------------------------------------------------------


def _words(values: list[float]) -> list[dict]:
    return [{"word": f"w{index}", "renormalised": value} for index, value in enumerate(values)]


def test_the_word_that_changes_most_is_highlighted(chart):
    assert chart.most_changed_word(_words([0.5, 0.3, 0.2]), _words([0.3, 0.3, 0.4])) in (0, 2)
    assert chart.most_changed_word(_words([0.6, 0.4]), _words([0.3, 0.7])) == 0


def test_no_word_is_highlighted_when_none_changes(chart):
    same = _words([0.5, 0.5])
    assert chart.most_changed_word(same, same) is None


def test_the_widest_layer_is_highlighted(chart):
    assert chart.widest_layer([0.0, 0.1, 0.0], [0.0, -0.1, 0.02]) == 1


def test_no_layer_is_highlighted_when_the_lines_stay_within_the_threshold(chart):
    assert chart.widest_layer([0.0, 0.1], [0.005, 0.095]) is None


def _specs(chart, monkeypatch) -> dict:
    """Records the spec of every chart drawn, while still drawing it through the brand checks."""
    specs = {}
    real = chart.export_chart

    def recording(draw, out_dir, spec, *args, **kwargs):
        specs[spec.name] = spec
        return real(draw, out_dir, spec, *args, **kwargs)

    monkeypatch.setattr(chart, "export_chart", recording)
    return specs


def test_the_committed_charts_highlight_nothing_and_say_so(chart, committed, tmp_path, monkeypatch):
    specs = _specs(chart, monkeypatch)

    written = chart.render(committed, tmp_path)

    assert "nothing highlighted" in specs["word-attention"].no_highlight_note
    assert "nothing highlighted" in specs["layer-shift"].no_highlight_note
    assert sorted(path.name for path in written) == [
        "layer-shift-article.png",
        "layer-shift-slide.png",
        "layer-shift-slide.svg",
        "word-attention-article.png",
        "word-attention-slide.png",
        "word-attention-slide.svg",
    ]


def test_both_rules_highlight_when_the_sentences_differ(chart, committed, tmp_path, monkeypatch):
    """Synthetic results where the weight moves to "suitcase": both charts must highlight, and
    the brand checks must accept exactly one acid green element on each."""
    import copy

    synthetic = copy.deepcopy(committed)
    small = synthetic["sentences"]["small"]
    words = [word for word in small["words"] if word["renormalised"] is not None]
    words[0]["renormalised"] -= 0.1
    words[-1]["renormalised"] += 0.1
    small["trophy_minus_suitcase"]["per_layer"][5] -= 0.05
    specs = _specs(chart, monkeypatch)

    chart.render(synthetic, tmp_path)

    assert specs["word-attention"].no_highlight_note is None
    assert specs["layer-shift"].no_highlight_note is None


def test_the_word_chart_footnote_names_the_model_averaging_and_first_token(
    chart, committed, tmp_path, monkeypatch
):
    specs = _specs(chart, monkeypatch)

    chart.render(committed, tmp_path)

    footnote = specs["word-attention"].footnote
    assert "GPT-2 small" in footnote
    assert "all 12 layers and 12 heads" in footnote
    share = committed["sentences"]["big"]["first_token_share"]
    assert f"{share:.1%}" in footnote
