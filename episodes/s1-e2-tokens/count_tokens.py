"""S1 E2, Tokens: the same sentence costs a different number of tokens in each language.

Run from the repository root:

    uv run python episodes/s1-e2-tokens/count_tokens.py

Needs no API key and makes no API call. It counts tokens on your own machine with o200k_base,
OpenAI's current tokeniser. The first run downloads the tokeniser once.
"""

import sys

# Lets a Windows console print Amharic. Everything below this line matches the slides.
sys.stdout.reconfigure(encoding="utf-8")

import tiktoken

encoding = tiktoken.get_encoding("o200k_base")

sentences = {
    "English": "My name is Brendan.",
    "French": "Je m'appelle Brendan.",
    "Amharic": "ስሜ ብሬንዳን ነው።",
}

for language, sentence in sentences.items():
    tokens = encoding.encode(sentence)
    print(f"{language}: {len(tokens)} tokens  {sentence}")
