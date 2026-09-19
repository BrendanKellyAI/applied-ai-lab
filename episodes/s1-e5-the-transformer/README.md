# S1 E5: The transformer

The code behind the timings and the model size shown in S1 E5, The transformer. The part of `timing.py` below the marker comment matches the slide line for line.

## What it shows

Two claims in the episode rest on general knowledge. This code measures both, on GPT-2 small, instead of quoting them.

1. **Reading is fast and writing is slow.** The model reads a prompt in one pass, all input tokens together. It writes its answer one token at a time, and each new token needs its own pass through every layer. Slide: "Parallel to train, one token at a time to run".
2. **GPT-2 small's size.** 12 layers, 12 heads, 768-number vectors, a 50,257-token vocabulary, a 1,024-token context, about 124 million parameters. Slide: "GPT-2 small, by the numbers".

**Both claims held.** Writing cost 22.1 times as much per token as reading, and every size on the slide matches the loaded model exactly.

**These are one laptop CPU's timings.** Absolute numbers will differ on other machines, and they bear no direct relation to a provider's servers, which run on very different hardware with batching, many chips and optimised code. The direction of the gap is the point, and the size of the gap is this machine's. It is also part of why providers usually price output tokens higher than input tokens.

## Setup

| | |
|---|---|
| Model | GPT-2 small, `gpt2` on Hugging Face (now served as `openai-community/gpt2`), the same model and revision as S1 E4 |
| Revision | `607a30d783dfa663caf39e06633721c8d4cfcd7e`, pinned so the weights can never change under the results |
| Run | 19 September 2026 (UTC), on the CPU in float32, eval mode, `torch.no_grad()`. The run took 59 minutes |
| CPU | Intel Core i7-8565U @ 1.80GHz, 4 physical cores, 8 logical processors |
| Threads | 4, fixed with `torch.set_num_threads`, one per physical core |
| OS | Windows 11 (Windows-11-10.0.26200-SP0) |
| Power | **On battery**, at the start and at the end of the run. A laptop on battery may hold its CPU below its mains speed, which this run does not separate out |
| Attention code | PyTorch's default, `sdpa`, since this run times the model rather than reading its attention weights |
| Libraries | torch 2.14.0, transformers 5.17.0, tokenizers 0.23.2, Python 3.13.7 |

### Configuration, read from the loaded model

| | Measured | Slide |
|---|---|---|
| Layers (`n_layer`) | 12 | 12 |
| Heads (`n_head`) | 12 | 12 |
| Vector size (`n_embd`) | 768 | 768 |
| Vocabulary (`vocab_size`) | 50,257 | 50,257 |
| Context (`n_positions`) | 1,024 | 1,024 |
| Parameters, `sum(p.numel())` | **124,439,808** | about 124 million |

The parameter count is exact. The model's output layer shares its weights with the token embedding, and PyTorch's `parameters()` lists shared weights once, so they are counted once. The tests work the same figure out again from the five configuration numbers alone.

### How the timings were taken, fixed before any run

- **Reading:** one forward pass over a 512-token prompt, producing the next-token scores. Time per input token is the total time divided by 512. Only the last position's scores are computed (`logits_to_keep=1`), because that is all a next-token prediction needs and it is what generation itself does when it reads its prompt. Computing scores at all 512 positions would have added work that no reader of a prompt needs, and would have made reading look slower than it is. That variant was not timed.
- **Writing:** from an 8-token prompt, exactly 512 new tokens with greedy decoding (`do_sample=False`, `min_new_tokens=max_new_tokens=512`, so the end token cannot stop it early), with the key and value cache on, which is the default. Time per output token is the generation time divided by 512. The 8-token prompt is read inside that time.
- **Every condition:** two untimed warm-up runs, then 5 timed runs with `time.perf_counter`. The figure reported is the median, with the minimum and maximum beside it.
- **Sweeps:** reading prompts of 64, 128, 256, 512 and 896 tokens, and writing 64, 128, 256, 512 and 896 tokens from the same 8-token prompt. Prompt plus output never exceeds the 1,024-token context, and the script refuses a condition that would.
- **The headline is the 512-token point of each sweep**, not a separate run, so the headline and the sweeps can never disagree.

### The prompts

Cut from *Pride and Prejudice* (Project Gutenberg 1342), one of the six filler books S1 E7 uses, in the same form: the same pinned file, checked against the same SHA-256, with the Project Gutenberg header and footer removed and the front matter skipped. The prompts are cut by token, not by character, so every run sees exactly the same tokens. Each shorter prompt is the start of every longer one. The 8-token writing prompt is "Mr. Darcy stood near them in". The results record the SHA-256 of the 896 token ids, so a reader can confirm they used the same ones.

## Results

### Headline, at 512 tokens each way

| | Median | Minimum | Maximum |
|---|---|---|---|
| Reading, per input token | **2.95 ms** | 2.92 ms | 3.14 ms |
| Writing, per output token | **65.20 ms** | 64.11 ms | 66.50 ms |
| **Writing over reading** | **22.1 times** | 20.4 times | 22.8 times |

The ratio's medians are the medians above divided. Its range runs from the fastest writing over the slowest reading to the slowest writing over the fastest reading, so it is the widest gap the five runs allow. Reading a 512-token prompt took 1.51 s in total; writing 512 tokens took 33.38 s.

The slide listing prints one cold run of each, without warm-ups: **2.4 ms** and **65.6 ms** per token when this was run. Quote the table above, not the slide's printout. The first, cool run of reading was faster than every later one, which fits a CPU that slows a little once it has been working for a while, but this run cannot say so for certain.

### Sweep: reading

| Prompt tokens | Total, median (min to max) | Per token, median (min to max) |
|---|---|---|
| 64 | 0.216 s (0.193 to 0.219) | 3.38 ms (3.02 to 3.43) |
| 128 | 0.365 s (0.334 to 0.367) | 2.85 ms (2.61 to 2.87) |
| 256 | 0.757 s (0.683 to 0.767) | 2.96 ms (2.67 to 3.00) |
| 512 | 1.509 s (1.496 to 1.610) | 2.95 ms (2.92 to 3.14) |
| 896 | 2.581 s (2.510 to 2.667) | 2.88 ms (2.80 to 2.98) |

### Sweep: writing

| Output tokens | Total, median (min to max) | Per token, median (min to max) |
|---|---|---|
| 64 | 3.98 s (3.76 to 4.21) | 62.11 ms (58.67 to 65.85) |
| 128 | 7.65 s (7.61 to 8.05) | 59.76 ms (59.42 to 62.86) |
| 256 | 15.81 s (15.62 to 16.07) | 61.76 ms (61.00 to 62.75) |
| 512 | 33.38 s (32.82 to 34.05) | 65.20 ms (64.11 to 66.50) |
| 896 | 62.09 s (61.97 to 62.20) | 69.30 ms (69.16 to 69.42) |

Fitted through the five medians, total time grows by **2.87 ms per extra token read** and by **70.09 ms per extra token written**, a slope 24 times steeper. Writing's cost per token is not quite constant: it rises from about 60 ms to about 69 ms as the output grows. That is what more earlier work to look back over would predict, but this run did not test the cause.

### Secondary: writing 512 tokens with the cache off

Same prompt, same 512 tokens, `use_cache=False`. **Median 394.5 s** (337.4 to 406.2 s) in total, **770.5 ms per token**, against 33.4 s with the cache on: **11.8 times as long** (9.9 to 12.4 times across the runs). It is about 260 times as long as reading a 512-token prompt once.

This shows why a model keeps its earlier work within one call. With the cache off, every new token makes the model read the whole text so far again, so the work grows with each token written, instead of one token's worth per step. It is **not** the prompt caching that providers offer across separate calls, which is a different mechanism. The five runs vary more than any other condition here, from 337 s for the first run to between 385 s and 406 s for the other four, so treat the 11.8 as somewhere between 10 and 12 times, not a precise figure.

## What the results say about each claim

**Claim 1, reading is fast and writing is slow: it held, and clearly.** Per token, writing cost 22.1 times as much as reading on this CPU, the five runs never came closer than 20.4 times, and the sweeps show the same gap at every length, from 18 times at 64 tokens to 24 times at 896. What the numbers do and do not show:

- "Fast" means cheap per token, not free. Reading still takes longer the more there is to read: about 2.9 ms per token, in proportion to length. A 896-token prompt took 2.6 s.
- The timings show the gap, not its cause. That reading treats its tokens together, and writing needs a pass per token, is the standard explanation and is consistent with these numbers, but nothing here isolates it.
- Part of writing's cost may be per-step overhead in the Hugging Face `generate` loop rather than the model itself. This run did not separate the two.
- Only the run side of the slide is measured. "Parallel to train" is not tested here.

**Claim 2, GPT-2 small by the numbers: it held exactly.** Every figure on the slide equals the value the loaded model reports, and the parameter count is 124,439,808, which rounds to the slide's 124 million.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/). **No API key**: GPT-2 runs on your own machine.

The code needs PyTorch and Hugging Face Transformers, which the rest of the lab does not. They are the optional extra `e4`, named for the episode that introduced it, which serves this episode too:

```bash
uv sync --extra e4
uv run --extra e4 python episodes/s1-e5-the-transformer/timing.py
```

No new model download: this reuses the GPT-2 small files from S1 E4. If S1 E7's filler book is not already in `.cache/gutenberg`, the first run fetches it once, about 0.7 MB, from the Project Gutenberg mirror and checks its SHA-256.

The script prints the slide's two lines first, then runs every condition, printing each one's median per token with its range, and writes everything to `results/timing.json`. **A full run takes about an hour, most of it the cache-off condition.** For steadier numbers, plug the laptop in and close other programs first. Expect different absolute figures on any other machine, and somewhat different ones on this one.

## Redraw the charts, no model needed

```bash
uv run python episodes/s1-e5-the-transformer/chart.py
```

The charts read only `results/timing.json`, which is committed, so they need neither the model nor a network.

- `charts/per-token`: milliseconds per token for reading and for writing at 512 tokens, as medians with the minimum and maximum as whiskers. The acid green bar is the slower of the two. If they are within 10% of each other, nothing is highlighted and the chart says so. Here writing is far slower, so its bar is green.
- `charts/sweep`: total time against the number of tokens, one line for reading and one for writing. The acid green line is the one with the steeper slope, taken from the medians. If the two slopes are within 10% of each other, nothing is highlighted and the chart says so. Here the writing line is far steeper, so it is green.

Each chart is written at slide size (1080 by 1350, PNG and SVG) and article size (1920 by 1080, PNG).
