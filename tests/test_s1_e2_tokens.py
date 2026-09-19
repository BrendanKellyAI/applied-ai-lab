"""The S1 E2 episode sample: token counts per language, and its chart.

The counts are pinned. If a tokeniser update ever changes them, this test fails, so the slides
and the article can be updated to match rather than quietly disagreeing with the code.
"""

import os
import subprocess
import sys
from pathlib import Path

from lab.experiments import load_sibling

EPISODE = Path("episodes/s1-e2-tokens")
SCRIPT = EPISODE / "count_tokens.py"

# Exactly as shown on the slide.
SLIDE_LISTING = """import tiktoken

encoding = tiktoken.get_encoding("o200k_base")

sentences = {
    "English": "My name is Brendan, welcome to my course everyone.",
    "French": "Je m'appelle Brendan, bienvenue à tous dans mon cours.",
    "Amharic": "ስሜ ብሬንዳን ነው፤ ሁላችሁም ወደ ትምህርቴ እንኳን ደህና መጣችሁ።",
}

for language, sentence in sentences.items():
    tokens = encoding.encode(sentence)
    print(f"{language}: {len(tokens)} tokens  {sentence}")
"""

EXPECTED = {"English": 11, "French": 12, "Amharic": 76}


def _chart():
    return load_sibling(EPISODE / "chart.py")


def test_the_script_matches_the_slide_listing():
    assert SLIDE_LISTING in SCRIPT.read_text(encoding="utf-8")


def test_the_script_prints_the_counts_on_the_slide():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    output = completed.stdout.decode("utf-8")

    for language, count in EXPECTED.items():
        assert f"{language}: {count} tokens  {_chart().SENTENCES[language]}" in output


def test_the_chart_counts_match_the_script():
    assert _chart().token_counts() == EXPECTED


def test_the_chart_and_the_script_count_the_same_sentences():
    script = SCRIPT.read_text(encoding="utf-8")
    for sentence in _chart().SENTENCES.values():
        assert sentence in script


def test_the_highlight_is_the_language_that_costs_the_most():
    assert _chart().most_tokens(EXPECTED) == "Amharic"


def test_the_chart_renders_with_one_highlight(tmp_path):
    written = _chart().render(tmp_path)

    assert sorted(path.name for path in written) == [
        "tokens-by-language-article.png",
        "tokens-by-language-slide.png",
        "tokens-by-language-slide.svg",
    ]
