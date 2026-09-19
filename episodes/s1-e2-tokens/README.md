# S1 E2: Tokens

The code behind the token counts shown in [S1 E2, Tokens](https://brendankellyai.github.io/episodes/s1-e2-tokens/). `count_tokens.py` matches the slide line for line.

It follows on from [S1 E1, One token at a time](https://brendankellyai.github.io/episodes/s1-e1-one-token-at-a-time/), where the first call to a model said "My name is Brendan." Here the same sentence is counted in three languages.

## What it shows

A model does not read letters or words. It reads **tokens**: pieces of text from a fixed vocabulary its tokeniser learned. You pay per token, and a model's context window is measured in tokens, so the same sentence can cost more, and fill more of the window, in one language than another.

| Language | Sentence | Tokens |
|---|---|---|
| English | My name is Brendan. | 5 |
| French | Je m'appelle Brendan. | 5 |
| Amharic | ስሜ ብሬንዳን ነው። | 22 |

Counted with `o200k_base`, OpenAI's current tokeniser. In S1 E7, GPT-5.6 Terra's billed input matched `o200k_base` to within the few tokens of question around each document.

**The same meaning costs over four times as many tokens in Amharic.**

### Why

- **The vocabulary favours some languages.** A tokeniser learns its pieces from the text it was trained on, and far more English and French is written online than Amharic. Common English words, such as " name" and " Brendan", became single tokens. Amharic words did not.
- **Amharic falls back to fragments.** Amharic is written in Ge'ez script. Each character takes three bytes, where most English letters take one, and a word the tokeniser has not learned gets split into small fragments of those bytes. The Amharic sentence is 12 characters but 32 bytes, and becomes 22 tokens.

### It depends on whose tokeniser you ask

Every model maker uses its own tokeniser. The same three sentences, counted on 19 September 2026:

| Tokeniser | English | French | Amharic | Amharic against English |
|---|---|---|---|---|
| OpenAI `o200k_base` (current) | 5 | 5 | 22 | 4.4 times |
| OpenAI `cl100k_base` (GPT-4 era) | 5 | 6 | 30 | 6 times |
| Claude Sonnet 5 | 8 | 12 | 17 | 2.1 times |
| Gemini 3.6 Flash | 6 | 7 | 8 | 1.3 times |

The OpenAI counts come from `tiktoken`, on your own machine. The Claude and Gemini counts come from each provider's free token counting endpoint. Those endpoints count a whole message, so a fixed allowance for message formatting is included: a one-letter message counts as 7 tokens for Claude and 2 for Gemini. The Claude row above has 6 subtracted from each count, to show the sentence alone; the Gemini row is as reported.

The newer OpenAI tokeniser narrows the gap, and Gemini's tokeniser handles Amharic almost as efficiently as English. Which model you choose changes what the same text costs.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/). **No API key**: tokens are counted on your own machine and no model is called.

```bash
uv sync
uv run python episodes/s1-e2-tokens/count_tokens.py
```

The first run downloads the `o200k_base` tokeniser once.

Unlike a model's reply, a token count never varies: the same text and tokeniser always give the same number.

## The chart

`charts/tokens-by-language` is the slide chart, drawn from the same tokeniser so it always matches the script. The acid green bar is the language whose sentence costs the most tokens. To redraw it:

```bash
uv run python episodes/s1-e2-tokens/chart.py
```

The chart font, Inter Tight, has no Amharic characters, so they are drawn from a fallback font: Ebrima, which ships with Windows. On macOS or Linux, install [Noto Sans Ethiopic](https://fonts.google.com/noto/specimen/Noto+Sans+Ethiopic) first, or the Amharic label shows as empty boxes.
