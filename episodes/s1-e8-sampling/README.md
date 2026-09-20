# S1 E8: Sampling

The code behind the probabilities and repeated answers shown in S1 E8, Sampling. The part of `sampling.py` below the marker comment matches the slide line for line.

## What it shows

A language model does not pick a word. It gives every possible next token a probability, and then a sampling rule picks one. The episode's probability slides are illustrative, and three of its claims rest on general knowledge. This code measures them, in two parts, and reports what happened:

1. **Real next-token probabilities, and how temperature reshapes them.** Measured exactly on GPT-2 small, from its own scores (Part A).
2. **The same prompt gives different answers, more so when many answers are valid.** Measured on GPT-2 small by sampling, and on `gpt-6-astra` through the Responses API (Parts A and B).
3. **Turning randomness down does not guarantee identical output.** Tested only if the API model accepts a temperature setting (Part B).

**Claim 1 held for the shape of the effect, but not for the example: GPT-2 small does not put " Dublin" first. Claim 2 held in direction, weakly, on the API model. Claim 3 could not be tested, because the model rejects a temperature setting.**

## Part A: GPT-2 small, no key

Run on 20 September 2026 on the CPU in float32, with GPT-2 small at the revision S1 E4 and S1 E5 use (`607a30d783dfa663caf39e06633721c8d4cfcd7e`). torch 2.14.0, transformers 5.17.0, tokenizers 0.23.2, Python 3.13.7.

### How the probabilities are worked out

One forward pass gives the model's raw scores, its **logits**, one for each of its 50,257 tokens. The probability of each token is the softmax of those scores. Temperature divides the scores before the softmax: below 1 it widens the gaps between tokens, above 1 it narrows them. Every distribution here, at every temperature, is worked out exactly from the same logits in double precision over the whole vocabulary. Nothing is estimated by sampling.

### "The capital of Ireland is": the top 10 at temperature 1.0

| Rank | Next token | Probability |
|---|---|---|
| 1 | ` the` | 9.61% |
| 2 | ` a` | 5.93% |
| 3 | ` Dublin` | 5.23% |
| 4 | ` now` | 5.06% |
| 5 | ` in` | 2.88% |
| 6 | ` not` | 2.87% |
| 7 | ` Ireland` | 2.79% |
| 8 | ` also` | 2.30% |
| 9 | ` home` | 2.21% |
| 10 | ` located` | 1.40% |

**GPT-2 small does not put " Dublin" first.** It puts " the", and " Dublin" is third, at 5.2%. That is a finding about a small 2019 model, not an error: it is a next-word predictor, not a question-answering system, and for "The capital of Ireland is" a very large share of ordinary text continues with "the" or "a". The ten tokens together hold only 40.3% of the probability. The distribution is flat, not the sharply peaked one an illustration might draw: even the top token has under a tenth of it.

(The leading space is part of each token: GPT-2 writes a word with the space before it as one token.)

### "My favourite colour is": the top 10 at temperature 1.0

| Rank | Next token | Probability |
|---|---|---|
| 1 | ` the` | 10.55% |
| 2 | ` blue` | 5.14% |
| 3 | ` black` | 3.68% |
| 4 | ` red` | 3.64% |
| 5 | ` a` | 3.28% |
| 6 | ` pink` | 3.12% |
| 7 | ` white` | 2.91% |
| 8 | ` green` | 2.45% |
| 9 | ` orange` | 2.21% |
| 10 | ` purple` | 1.94% |

The top 10 hold 38.9%. Again " the" comes first, and the first colour, " blue", is second.

### Temperature reshapes the odds

The same colour prompt, from the same logits, at three temperatures:

| Token | 0.3 | 1.0 | 1.8 |
|---|---|---|---|
| ` the` | 81.89% | 10.55% | 0.75% |
| ` blue` | 7.45% | 5.14% | 0.51% |
| ` black` | 2.45% | 3.68% | 0.42% |
| ` red` | 2.37% | 3.64% | 0.42% |
| ` a` | 1.67% | 3.28% | 0.39% |
| ` pink` | 1.41% | 3.12% | 0.38% |
| ` white` | 1.12% | 2.91% | 0.37% |
| ` green` | 0.63% | 2.45% | 0.34% |
| ` orange` | 0.45% | 2.21% | 0.32% |
| ` purple` | 0.29% | 1.94% | 0.29% |
| **Top 10 together** | **99.73%** | **38.9%** | **4.19%** |

At 0.3 the top token takes 82% and the ten together take nearly everything. At 1.8 the ten tokens share 4% and the curve is almost flat: any of tens of thousands of tokens is nearly as likely as any other. The ranking never changes, only the gaps. For the capital prompt the top token goes from 9.6% to 65.5% at 0.3 and 0.85% at 1.8, and " Dublin" from 5.2% to 8.6% and 0.60%.

**Low temperature makes the likeliest token win more, not the right one.** " Dublin" gains a little at 0.3, but " the" gains far more.

### Top-p 0.6

Top-p keeps the smallest group of the likeliest tokens whose probabilities add up to at least 0.6, and samples only from those. At temperature 1.0, for the colour prompt, that is **63 tokens**, holding 60.1% of the probability. The 63, most likely first:

> ` the`, ` blue`, ` black`, ` red`, ` a`, ` pink`, ` white`, ` green`, ` orange`, ` purple`, ` yellow`, ` grey`, ` that`, ` my`, ` '`, ` actually`, ` dark`, ` probably`, ` Black`, ` not`, ` also`, ` brown`, ` lime`, ` gold`, ` definitely`, ` silver`, ` Red`, ` this`, ` usually`, ` one`, ` bright`, ` navy`, ` an`, ` always`, `:`, ` peach`, ` "`, `,`, ` Blue`, ` in`, ` of`, ` to`, ` violet`, ` Green`, ` called`, ` from`, ` pale`, ` really`, ` tur`, ` now`, ` lav`, ` Pink`, ` often`, ` so`, ` her`, ` just`, ` very`, ` blonde`, ` your`, ` White`, ` when`, ` raspberry`, ` something`

Because the distribution is flat, a 0.6 cut still leaves 63 tokens, including " tur" and " lav", the starts of words. The set matches the one the `transformers` library's own top-p filter keeps, which the script checks.

### Sampling: 20 continuations at each temperature

From "My favourite colour is", 10 new tokens, sampled 20 times at each temperature with seeds 0 to 19 (recorded with each sample), pure temperature sampling with the library's default top-k and top-p switched off. One greedy run beside them.

| Temperature | Distinct continuations, of 20 | Started with " the" | Different first tokens |
|---|---|---|---|
| 0.3 | **20** | 15 | 5 |
| 1.0 | **20** | 1 | 20 |
| 1.8 | **20** | 0 | 19 |

Samples from seed 0, 1 and 2:

| Temperature | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| 0.3 | ` a bright blue with a very nice light blue tint` | ` the blue of the Moon. The blue of the` | ` pink, which is the most beautiful colour I've` |
| 1.0 | ` a bright blue with a spot of Gold "tree` | ` Dark Psychedelic Yellow, which I love.` | ` purple, which is healthier and safer. It's` |
| 1.8 | ` Jama button pilot originatedave Girls... is "tree` | ` upset wash foam grippers ones UNDER 40 Really inconsist` | ` Madrido Powderanto Pebble angry blu holesian 411` |

The greedy run, which always takes the top token, was ` the blue of the sun. It is the colour`.

**Every sample was different at every temperature, even 0.3.** At 0.3 the first token is often the same (15 of 20 began " the", close to the 82% expected), but ten tokens of open-ended text branch at each step, and the branches multiply. A low temperature makes samples more alike, not the same. At 1.8 the text turns to word salad.

## Part B: `gpt-6-astra` through the Responses API

Run on 20 September 2026, with the same model and call as S1 E1. The API returned the model name `gpt-6-astra`. Every response carries its status, and none was incomplete: every response was `completed` with visible text. The output limit was 4,000 tokens, generous because a reasoning model spends part of the limit thinking before it writes, as S1 E6 showed.

### Does the model accept a temperature?

The current documentation is silent on it: the reasoning guide and the model's page both say nothing about temperature for `gpt-6-astra`. So one probe call was made with `temperature=0`, and this is exactly what happened:

| | |
|---|---|
| Outcome | **rejected** |
| HTTP status | 400 |
| Error type | `invalid_request_error` |
| Error param | `temperature` |
| Error code | none (`null`) |
| Error message | `Unsupported parameter: 'temperature' is not supported with this model.` |

The model does not accept a temperature, so the temperature 0 run was skipped. Every response reports `temperature: 1.0`, so the API says it sampled at 1 throughout.

### Twenty identical calls, at the model's defaults

| Prompt | Distinct answers, of 20 | The answers |
|---|---|---|
| One answer: "What is the capital of Ireland? Reply with one word." | **1** | Dublin (20) |
| Many answers: "Suggest a name for a coffee shop in Dublin. Reply with the name only." | **2** | The Liffey Grind (17), Liffey & Latte (3) |

Answers are counted after three steps, fixed before any run: strip the whitespace at both ends, fold the case, remove any punctuation at the end. Only the end: a quotation mark at the start would be left alone. The raw text is kept as well, and here the raw and normalised counts are the same. A response counts as an answer only if its status is `completed` and it has visible text; any other is counted apart, and there were none.

What the slide's script printed:

```
17  The Liffey Grind
 3  Liffey & Latte
```

The coffee responses each used 16 to 24 reasoning tokens. The capital responses used none in 15 of the 20 calls and up to 10 in the other 5.

## What the results say about each claim

**Claim 1, real probabilities and temperature: held for the shape, not for the example.** Temperature does what the slides say. Low temperature concentrates the probability on the top token (82% at 0.3, from 10.6%), high temperature flattens it (0.75% at 1.8), and the ranking never changes. But GPT-2 small does not put " Dublin" first for "The capital of Ireland is": it puts " the", and " Dublin" is third at 5.2%. The illustration of a confident top choice does not match this model, whose distribution is flat. "Greedy picks the top" is true, and here the top is " the".

**Claim 2, the same prompt gives different answers, more so when many are valid: held in direction, weakly.** On the API model the one-answer prompt gave 1 distinct answer in 20 and the many-answer prompt 2, so the direction is right. But the size of the effect is small: 17 of 20 coffee shop names were identical, and a reader who expects twenty different names will not see them. That is one prompt, 20 calls, one model on one day, so it says little about how often a given prompt varies. On GPT-2, sampling gave 20 different continuations of 20 at every temperature, so there the claim holds strongly, but that is ten tokens of open-ended text, a much wider space than a one-line answer.

**Claim 3, lowering randomness does not guarantee identical output: could not be tested on this model.** It rejects a temperature setting outright, so there is no lower setting to send. That the API refuses is itself the finding: on this model the sampling setting is not the reader's to turn. The GPT-2 samples do not speak to the claim, which is about an API model at temperature 0 returning different answers on identical calls, not about a sampler at 0.3. One greedy GPT-2 run was made, so nothing here shows whether greedy output repeats.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**Part A, GPT-2 small: no key.** It needs PyTorch and Hugging Face Transformers, the optional extra `e4`, named for the episode that introduced it and used by S1 E5 too:

```bash
uv sync --extra e4
uv run --extra e4 python episodes/s1-e8-sampling/local.py
```

No new download: this reuses the GPT-2 small files from S1 E4 and S1 E5. It takes under a minute, prints the top 10 for both prompts, the top-p set and the sample counts, and writes everything to `results/local.json`. The samples reproduce on the same library versions, because each has a fixed seed: a second run wrote a byte-identical results file.

**Part B, the API model: needs a key.** Add your OpenAI API key to `.env` in the repository root, the same file the rest of the lab uses (copy `.env.example` to `.env` first if it does not exist), then:

```bash
uv sync
uv run python episodes/s1-e8-sampling/sampling.py
```

It prints the slide's output, the result of the temperature probe, and a line per condition, and writes every request, response text, status and usage figure to `results/api.json`, with the model name the API returned and the date. Running it again replaces that file. Responses vary between runs, so your counts will differ from the table above.

## Redraw the charts, no key or model needed

```bash
uv run python episodes/s1-e8-sampling/chart.py
```

The charts read only `results/local.json` and `results/api.json`, which are committed.

- `charts/next-token`: GPT-2's top 10 next tokens for "The capital of Ireland is" at temperature 1.0. The acid green bar is the single most likely token, here " the". The footnote says where " Dublin" ranks.
- `charts/temperature`: the four likeliest tokens for "My favourite colour is" at 0.3, 1.0 and 1.8. The acid green bar is the top token at 0.3.
- `charts/distinct-answers`: distinct answers out of 20 for each API condition run. The acid green bar is the condition with the most. If they are all equal, or the most is shared, nothing is highlighted and the chart says so. Here the coffee shop prompt has the most, and the footnote records that temperature 0 was rejected and so has no bar.

## Cost

Part A costs nothing. Part B made 41 short calls: 40 answers, using 800 input and 793 output tokens between them, and the one rejected probe, which returned an error before generating anything. The exact cost depends on current OpenAI pricing. The script makes new calls every time it runs.
