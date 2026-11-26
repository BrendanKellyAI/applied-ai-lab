# S4 E8: Field note: can fine-tuning teach facts?

E5 to E7 tuned behaviour: a routing rule, a format, a house style. A common hope is that tuning a
model on your documents makes it know them, so you can drop retrieval. E8 tuned a small model on
1,724 question and answer pairs written from Halvard's library, then asked it Season 2's 520 test
questions without showing it the documents. Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: tuning taught almost no facts and took away the model's ability to say "I don't
know".** The tuned model was right on 26 of 400 answerable questions (the untuned model 11,
Season 2's retrieval system 354). It declined none of the 120 questions the library cannot
answer, where the untuned model declined 78, and gave a confident wrong answer to 494 of all 520
questions. All four claims held. Tuning changes how a model answers; it does not reliably put
your documents into it.

## The design

- **The questions:** `halvard-v2` test, 520 items, Season 2's frozen set: 400 answerable (40
  asked by staff about staff-only documents) and 120 the library cannot answer. Dev, 100 items,
  was judged as a check.
- **The training pairs:** `gemini-3.1-flash-lite` wrote 4 pairs from each of the library's 436
  current public passages. 1,724 were kept: 6 near duplicates of a dev or test question and 14
  repeated questions were removed (`pairs/pairs-log.json`). Staff-only, superseded and deleted
  documents were left out on purpose.
- **Arms:**

  | Arm | Model | Given |
  |---|---|---|
  | `e8-base-closed` | Qwen3-0.6B, untuned | the question only |
  | `e8-tuned-closed` | Qwen3-0.6B, tuned on the 1,724 pairs | the question only |
  | `e8-reference` | Season 2's reference system: retrieval and `gpt-6-luna` | its own run, no new calls |

  Both Qwen arms were told to say they could not find the answer if they did not know it.
- **Tuning:** LoRA rank 16, 3 epochs, the season's defaults, on a free Colab T4: 15 minutes of
  training (458,964 Qwen tokens, final training loss 1.52, peak 9.9 GB).
- **The judge:** Season 2's, `gemini-3.6-flash`, shown no passages. "Right" is the judge's
  `correct`, for every arm.

## Results (test, 520 questions)

| Arm | Right, of 400 answerable | Declined, of 120 unanswerable | Confident wrong answers, of 520 | Declined an answerable question |
|---|---|---|---|---|
| `e8-base-closed` | 11 (2% to 5%) | 78 (56% to 73%) | 165 (28% to 36%) | 267 of 400 |
| `e8-tuned-closed` | 26 (4% to 9%) | **0** (0% to 3%) | **494** (92% to 97%) | 0 of 400 |
| `e8-reference` | **354** (85% to 91%) | **107** (82% to 94%) | **11** (1% to 4%) | 48 of 400 |

Intervals are Wilson 95%. On dev (Qwen arms only): right 0 and 1 of 70; declined 17 and 0 of 30.

**The tuned model never declined.** Every one of its 520 replies is a short, confident answer in
the style of its training pairs. Its training targets always answered, so it learned to always
answer. The untuned model, told the same thing, said "I could not find it" two times in three.

**What it got right** was mostly what is shared across many passages: 16 of its 26 right answers
are `shared` questions (facts repeated across the library), 6 are paraphrases. It got none of the
single-policy, identifier or two-part questions right. It could not answer the 40 staff
questions by design: those documents were left out.

**What it says when the library has no answer** (invented examples, `DELETED-000` and `-001`,
about documents that were withdrawn): the tuned model gives a plausible instruction in Halvard's
voice ("contact Halvard Home customer support to check whether it is suitable for your model");
the untuned model says it could not find it.

## The claims

**C1 held: tuning teaches some facts.** 26 against 11 right; 19 and 4 items each way (exact
McNemar p 0.003). Some, and very few.

**C2 held: a tuned model does not replace retrieval.** 26 against 354; 3 and 331 items each way
(p below 0.0001).

**C3 held: tuning on answers teaches the model to answer everything.** 0 against 78 correct
declines; 78 items lost, none gained (p below 0.0001).

**C4 held: the tuned model states more wrong answers with confidence than retrieval does.** 494
against 11; 483 and 0 items each way (p below 0.0001).

## What it means

Tuning on your documents is the wrong tool for knowing them. It taught a small model the voice of
Halvard's answers far better than their content, and the training data, which only ever
answered, removed the habit that made the untuned model safe: declining. A model that knows
nothing and says so is safer than one that knows a little and answers everything.

For facts, retrieve (Season 2): the documents stay current, can carry permissions, and the
answer can cite them. If a tuned model is ever used for facts, its training data needs examples
of declining as well as answering.

**Decision rule (proposed):** "To give a model your facts, retrieve them. Tune for behaviour, and
if you tune on answers, include the questions it should decline."

**Ask your team:** "If our model did not know the answer, would it say so, and have we tested
that?"

## What this does not show

- **One way of tuning.** Rank 16, 3 epochs, 4 pairs a passage, one seed. Much more data, more
  passes or a larger adapter might teach more facts; the season's defaults were kept so E8
  compares with E5 to E7.
- **A 0.6 billion parameter model.** A larger model may hold more of what it is shown.
- **Pairs written by a model.** A mistaken pair teaches a mistaken fact.
- **The judge is a model,** checked against a person in Season 2 E3 with passages, not closed
  book.
- **No pairs that decline.** The training data had no unanswerable questions; adding some might
  restore declining (not tested).
- **The tuned model inside retrieval** (the plan's optional arm) was not run.

## Cost

Costs are ratios only. The pairs and both judge runs together stayed well within the approved
budget; the judge's test run was about five times its dev run. The two Colab jobs used the free
T4: 15 minutes of training and about 3 minutes of answers each.

Tokens, estimated before the calls and counted by the provider after (no cached input was
reported):

| Step | Model | Calls made | Input, estimated | Input, actual | Output, expected | Output, actual |
|---|---|---|---|---|---|---|
| Pairs | `gemini-3.1-flash-lite` | 436 | 215,116 | 219,880 | 122,080 | 113,279 |
| Judge, dev | `gemini-3.6-flash` | 199 of 200 (1 from the cache) | 67,266 | 72,756 | 12,000 | 9,945 |
| Judge, test | `gemini-3.6-flash` | 1,038 of 1,040 (2 from the cache) | 349,716 | 379,860 | 62,400 | 51,869 |

GPU time: 15 minutes of training (458,964 Qwen tokens) and about 5 minutes of predictions across
the two jobs.

## Run it

```bash
uv run lab adapt facts-analyse episodes/s4-e8-can-fine-tuning-teach-facts/config.yaml
uv run python episodes/s4-e8-can-fine-tuning-teach-facts/claims.py
uv run python episodes/s4-e8-can-fine-tuning-teach-facts/charts.py
```

Charts, in `results/charts/`: right, correct declines and confident wrong answers on test, each
as a slide (PNG and SVG) and an article image.

The judge verdicts are committed in `results/`; `facts-run` re-judges and costs money. The jobs:
`results/e8-tuned-closed/job.json` and `results/e8-base-closed/job.json`, each run once.
