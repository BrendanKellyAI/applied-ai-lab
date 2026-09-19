# S1 E4: Attention

The code behind the attention weights shown in [S1 E4, Attention](https://brendankellyai.github.io/episodes/s1-e4-attention/). The part of `attention.py` below the marker comment matches the slide line for line.

## What it shows

Inside a transformer, every token looks back over the tokens before it and decides how much of each to take into account. That share is its **attention**, and each token's attention over the tokens it can see adds up to 1. Slide 5 illustrates the classic example:

> In "The trophy did not fit in the suitcase because it was too big.", the token "it" attends more to "trophy" than to "suitcase". Change "big" to "small", and the weight should shift towards "suitcase".

This code measures that with a real model, GPT-2 small, instead of drawing it.

**The claim did not hold, on either half, and the second half cannot hold for this kind of model.**

## Setup

| | |
|---|---|
| Model | GPT-2 small, `gpt2` on Hugging Face (now served as `openai-community/gpt2`), 12 layers of 12 attention heads |
| Revision | `607a30d783dfa663caf39e06633721c8d4cfcd7e`, pinned so the weights can never change under the results |
| Run | 19 September 2026, on the CPU in float32. Run twice: the second results file was identical to the first |
| Libraries | torch 2.14.0, transformers 5.17.0, tokenizers 0.23.2, numpy 2.5.3, Python 3.13.7 |

### Token splits

GPT-2 can split a word into several tokens, so a word's weight is the sum over all of its tokens. Here, every word is a single token, and " it" is one token (number 340):

| Word | GPT-2 tokens |
|---|---|
| The | `The` |
| trophy, did, not, fit, in, the, suitcase, because | one token each, with a leading space: `Ġtrophy`, `Ġdid`, and so on |
| it | `Ġit` |

(`Ġ` is how GPT-2 writes the space in front of a word.)

### How attention is measured, fixed before the results

- **Primary:** the attention "it" pays to each earlier word, averaged over all 12 layers and all 12 heads.
- **The first token.** The first token of a sequence often takes a large share of attention whatever it says, a so-called attention sink. Its share is reported on its own. Word weights are reported raw, and renormalised over the other earlier words with the first token left out. The chart uses the renormalised figures.
- **Per layer:** raw attention to "trophy" minus attention to "suitcase", averaged over the 12 heads in each layer.
- **Per head:** how many of the 144 heads move towards "suitcase" when "big" becomes "small", and how many move the other way.

Per layer and per head use raw attention, because a head that puts nearly everything on the first token leaves a tiny remainder, and renormalising it would inflate noise.

## Results

Attention from "it", averaged over all layers and heads:

| Word | Raw, "too big" | Raw, "too small" | Renormalised, "too big" | Renormalised, "too small" |
|---|---|---|---|---|
| The (first token) | 0.536 | 0.536 | left out | left out |
| trophy | 0.033 | 0.033 | 0.088 | 0.088 |
| did | 0.027 | 0.027 | 0.070 | 0.070 |
| not | 0.026 | 0.026 | 0.069 | 0.069 |
| fit | 0.038 | 0.038 | 0.101 | 0.101 |
| in | 0.028 | 0.028 | 0.074 | 0.074 |
| the | 0.029 | 0.029 | 0.075 | 0.075 |
| suitcase | 0.062 | 0.062 | 0.162 | 0.162 |
| because | 0.138 | 0.138 | 0.362 | 0.362 |
| it (itself) | 0.084 | 0.084 | left out | left out |

The raw column, including "it" itself, sums to 1; the renormalised column sums to 1 over the words it covers.

**The first token took 53.6% of the attention in both sentences.**

**Heads:** of 144 heads, **0 moved towards "suitcase", 0 moved towards "trophy", and all 144 were unchanged.** The largest difference anywhere in the attention up to "it", between the two sentences, is exactly 0.

**Per layer**, trophy minus suitcase, identical in both sentences: -0.036, -0.027, -0.078, -0.019, -0.005, +0.017, -0.010, -0.049, -0.054, -0.078, -0.005, +0.004. It is negative in 10 of the 12 layers: "it" attends more to "suitcase" than to "trophy" almost everywhere.

## What the results say about the claim

**The first half failed.** In the "too big" sentence, "it" attends to "suitcase" (0.162) nearly twice as much as to "trophy" (0.088), not more to "trophy". The strongest pull is on "because" (0.362), then "suitcase": the nearest words, not the one "it" refers to. GPT-2 small's attention from "it" tracks position more than meaning here.

**The second half cannot hold for GPT-2, and the measurement shows why.** GPT-2 reads left to right: each token can only look at the tokens before it. "big" and "small" come after "it". So when GPT-2 works out where to look from "it", it has not yet read the word that decides what "it" means. Everything up to "it" is the same in both sentences, so the attention from "it" is exactly the same too: every one of the 144 heads, to the last decimal place. That is a property of how the model is built, not a failure to understand.

This is a good example for the "Where it breaks" slide. A left-to-right model cannot resolve a reference using a word it has not read yet. It can only use that word later, from the tokens that come after it.

**What would test the claim properly** (not run here):

- Measure from a token that comes after "big" or "small", such as the final full stop, and ask whether it attends to "trophy" or "suitcase".
- Use a model that reads in both directions, such as BERT, where "it" can see "big" and "small". The well-known illustrations of this example come from models of that kind.

## Attention shows where a model looked, not why

An attention weight says how much of one token went into another at one step. It does not say that the model used that token to reach its answer, or that the answer depends on it. Many heads and layers combine, and later layers can undo or ignore what earlier ones attended to. Treat attention charts as a view of where the model looked, never as an explanation of what it concluded.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/). **No API key**: GPT-2 runs on your own machine.

The attention code needs PyTorch and Hugging Face Transformers, which the rest of the lab does not. They are an optional extra, so the base install stays light:

```bash
uv sync --extra e4
uv run --extra e4 python episodes/s1-e4-attention/attention.py
```

The first run downloads GPT-2 small, about 550 MB, once; after that it runs offline. On the CPU in float32, with the pinned revision, the results reproduce exactly. It prints the attention from "it" to each earlier token, highest first, then both sentences' figures, and writes everything to `results/attention.json`.

## Redraw the charts, no model needed

```bash
uv run python episodes/s1-e4-attention/chart.py
```

The charts read only `results/attention.json`, which is committed, so they need neither the model nor a network.

- `charts/word-attention`: attention from "it" to each earlier word, renormalised, one pair of bars per word for "too big" and "too small". The acid green bar is the word whose weight changes most between the sentences. In this run no word changes, so nothing is highlighted and the chart says so.
- `charts/layer-shift`: trophy minus suitcase, layer by layer, as one line per sentence. The acid green mark is the layer where the two sentences differ most, if they ever differ by more than 0.01. Here the lines lie exactly on top of each other, so nothing is highlighted and the chart says so.
