# S4 E10: Field note: what does tuning break?

E5 and E7 tuned the same small model for one narrow task each, and both did that task well. A
tuned model is usually deployed where other requests reach it too. E10 asked both tuned models,
and the untuned model, three sets of questions outside their tasks: Season 1's reasoning items,
100 ordinary requests, and Season 2's unanswerable questions with the reference system's
passages. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: all three claims failed, because only one of the two tuned models broke.** The reply
writer (E7) carried its job into everything: it answered 41 of 100 ordinary requests as a Halvard
customer reply, a soup recipe included, and declined fewer unanswerable questions than the
untuned model (52 against 65). The triage model (E5) did neither: no bleed, and slightly more
declines (78). Neither lost general ability on the check as scored; both scored higher than the
untuned model, for reasons that are mostly about answer format (below). What tuning breaks
depends on what it taught: a format that only fits one job stayed in that job; a voice that fits
any request went everywhere.

## The design

- **Models:** Qwen3-0.6B at commit `c1899de`, thinking off, greedy, up to 400 new tokens.

  | Arm | What it is |
  |---|---|
  | `e10-base` | untuned |
  | `e10-tuned-triage` | E5's triage adapter (`e5-tuned-short`), hash checked |
  | `e10-tuned-replies` | E7's reply adapter (`e7-tuned-short-b4`), hash checked |

- **General ability:** Season 1 E10's 120 items (30 each of extraction, arithmetic, state
  tracking and constraint puzzles), no system prompt, scored by Season 1's code: the final
  `ANSWER:` line, compared exactly.
- **Format bleed:** 100 ordinary requests written for E10 (80 everyday, 20 that mention
  appliances), no system prompt. A reply bleeds if it is a triage object or opens or signs off
  as Halvard's house reply. Scored by code.
- **Declines:** the 120 unanswerable `halvard-v2` test questions, each with exactly the prompt
  Season 2's reference system sent (checked by hash), judged by Season 2's judge,
  `gemini-3.6-flash`.
- **Jobs:** three eval-only Colab jobs on a free T4, notebook v3 (Amendment 1: the first
  `e10-base` attempt ran out of memory on the long decline prompts, before any prediction was
  saved).

## Results

| Arm | General, right of 120 | Bleed, of 100 | Declines, of 120 |
|---|---|---|---|
| `e10-base` | 41 (26% to 43%) | 0 (0% to 4%) | 65 (45% to 63%) |
| `e10-tuned-triage` | 56 (38% to 56%) | 0 (0% to 4%) | 78 (56% to 73%) |
| `e10-tuned-replies` | 56 (38% to 56%) | **41** (32% to 51%) | **52** (35% to 52%) |

Intervals are Wilson 95%.

**The reply writer answers everything as a customer reply.** 41 of the 100 ordinary requests
(33 of 80 everyday, 8 of 20 about appliances) came back opening "Thank you for getting in touch."
Asked for a vegetable soup recipe, it replied that it could not find the recipe "in our database"
and had passed the question to a colleague. It was tuned on 600 replies and nothing else, so a
reply is what it gives. The triage model never answered with a triage object: a line of JSON
with a route does not fit a soup recipe, and it gave the recipe.

**The reply writer declines less, even with the passages in front of it.** 52 against 65; it
declined 11 the untuned model answered and answered 24 the untuned model declined. Asked what
engineers may spend on parts without permission (`RESTRICT-PUBLIC-005`), it answered with the
price of a routine service from the nearest passage, in house style. The triage model declined more often than the untuned
model (78; 26 and 13 items each way).

**General ability rose, and the check mostly measures format.** Both tuned models scored 56
against 41, with 18 and 3 items each way for each. The whole gain is arithmetic (11, 26 and 29
of 30); extraction was 30, 30 and 27; state tracking and constraint puzzles were 0 for every
model. The untuned model often worked the sum correctly and wrote the result as `\boxed{77}`
instead of the `ANSWER:` line Season 1's scorer reads (17 of its 19 arithmetic misses end in a
boxed number), and it ran into the 400 token limit on 58 of its 79 misses. Both tuned models
learned to finish briefly with an answer line. On the two families every model fails, the check
cannot show a loss.

## The claims

**C1 failed: tuning on one task costs general ability.** Both tuned models were right on more
items, not fewer: 56 against 41, 18 and 3 items each way (exact McNemar p 0.0015, in the
opposite direction to the claim).

**C2 failed: a tuned format bleeds into ordinary requests.** The reply writer bled: 41 against
0 (p below 0.0001). The triage model did not: 0 against 0. The claim needed both.

**C3 failed: tuning weakens declines even with retrieval.** The reply writer declined fewer:
52 against 65, 11 and 24 items each way (p 0.041). The triage model declined more: 78 against 65
(p 0.053). The claim needed both.

## What it means

A tuned model takes its training habits to requests that were never in its training data, but
only habits that can travel. The reply writer learned a voice and an opening, which fit any
request, so it used them on soup and on questions its passages could not answer. The triage
model learned a format that fits nothing but a support message, and left ordinary requests
alone.

So the question before deploying a tuned model is not "did it lose ability?" in general but
"where else will it be used, and what did we teach it that would make sense there?" A model that
only ever sees its own task needs only its own test. One that shares a channel with other
requests needs E10's checks, run on its own traffic, after every retrain.

**Decision rule (proposed):** "Before a tuned model sees requests outside its task, test it on
them: ordinary requests and the questions it should decline. Rerun those tests after every
retrain."

**Ask your team:** "What else will this tuned model be asked, and have we tested it on that?"

## What this does not show

- **One small model.** A 0.6 billion parameter model starts at zero on Season 1's state tracking
  and puzzles, so there was nothing there to lose; a larger model could lose ability this check
  would see.
- **The general check rewards the answer line.** Season 1's scorer reads `ANSWER:` exactly, as
  pre-registered. The gain is mostly format and brevity, not better reasoning.
- **One adapter per task, one seed.** Tuning longer or on more varied data changes how much
  bleeds.
- **No system prompt** on the general and bleed sets. A deployment that always sends its task
  instruction would see different behaviour.
- **Code-scored bleed** catches only the two tuned formats; terser or more formal replies are
  not counted.
- **The judge is a model,** checked against a person in Season 2 E3.

## Cost

Costs are ratios only. The judge run was the only spend, below the approved budget, and its
actual cost matched its estimate closely. The three Colab jobs used the free T4: about 14, 13
and 31 minutes of answers (base, triage, replies); the reply writer is slowest because its
replies are long. The failed first attempt used a few minutes.

Tokens, estimated before the calls and counted by the provider after (no cached input was
reported):

| Step | Model | Calls made | Input, estimated | Input, actual | Output, expected | Output, actual |
|---|---|---|---|---|---|---|
| Judge, declines | `gemini-3.6-flash` | 360 of 360 | 1,068,600 | 1,122,153 | 21,600 | 18,613 |

## Run it

```bash
uv run lab adapt regression-analyse episodes/s4-e10-what-does-tuning-break/config.yaml
uv run python episodes/s4-e10-what-does-tuning-break/claims.py
uv run python episodes/s4-e10-what-does-tuning-break/charts.py
```

Charts, in `results/charts/`: general, bleed and declines, each as a slide (PNG and SVG) and an
article image. The judge verdicts are in `results/raw/`; `regression-run` re-judges and costs
money. The jobs: `results/<arm>/job.json`, each recorded once (`e10-base` on its second attempt).
