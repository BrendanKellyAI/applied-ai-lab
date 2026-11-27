# S4 E3 deck handover: How many examples?

For the content agent. Has an experiment: worked examples added to the one-line prompt, by
number, by how they are chosen, and in a different order.

## Sources of truth

- `episodes/s4-e3-how-many-examples/README.md` and `PREREGISTRATION.md` (with Amendment 1).
- `results/analysis-task-a-test.json` and `analysis-task-a-dev.json`; `results/claims-test.json`
  (C3 and C4 compare arms item by item).
- Chart: `results/charts/s4-e3-how-many-examples-fully_right-test-slide.svg`.
- How examples are written into the prompt: `triage_examples` in `src/lab/adapt/prompts.py`;
  how they are chosen: `src/lab/adapt/examples.py`.
- `episodes/s4-e2-instructions-first/README.md` (the comparison with written definitions).
- `season4/scoreboard.json`, `season4/reference_history.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E3 |
| Title | How many examples? |
| Hub slug | `how-many-examples` (as on the hub) |
| Deck file | `bk-s4-e3-how-many-examples-v1.pdf` |
| Hub format | `explainer` |

## The argument

Showing a model worked examples (a message and its right answer) is the other cheap way to teach
it. But examples are paid for on every call, so the questions are how many, which ones, and does
their order matter.

Starting from E1's one-line prompt:

- **Which examples matters more than how many.** The 8 training messages most similar to each
  incoming message took it from 521 to 593 of 600, as well as E2's written definitions (587). 8
  random examples reached 562, and 32 random ones 583, at five times the prompt length.
- **Returns shrink.** 0 to 8 random examples gained 41 items; 8 to 32 gained 21.
- **Order alone moves single answers.** The same 8 examples in another order changed the result
  on 27 of 600 messages, though the total barely moved.

## Scoreboard slide

Task A ladder. Chart: `s4-e3-how-many-examples-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 (84% to 89%) | The baseline |
| E2 + definitions | 587 (96% to 99%) | Joined: the reference |
| **E3 one-line + 8 similar examples** | **593 (98% to 99%)** | **No: overlaps the reference** |

What this episode adds: a second way to reach the same level. It does not clear the bar, so the
reference stays the definitions prompt.

## Setup before results

Same model and messages as E2. **The base is E1's one-line prompt, not E2's best.** E2's
definitions got 199 of 200 on dev, leaving nothing for examples to add, so the base was changed
before any E3 call (Amendment 1). Each example is written into the prompt like this:

> Customer message:
> [a training message]
> JSON: {"route": "...", "safety": ..., "product": "...", "fault": ...}

| Arm | Examples | Input tokens per call |
|---|---|---|
| No examples (E1) | None | 308 |
| 2 random | The same 2 for every message | 668 |
| 8 random | The same 8; the 2 are its first 2 | 1,512 |
| 8 similar | For each message, the 8 training messages closest in meaning, nearest last | 1,345 |
| 8 random, shuffled | The same 8 random, in another order | 1,512 |
| 32 random | The same 32; the 8 are its first 8 | 4,654 |

"Closest in meaning" uses embeddings, numbers that place similar texts near each other (refresher
from S1 E3), with the Season 2 code. Random examples are drawn once from the training set with a
fixed seed. Examples never come from the test set.

**Worked example** (`A-test-00410`, invented): "Is it normal for the stainless steel body to get
very hot to the touch while it is boiling?"

| Arm | safety | Fully right? |
|---|---|---|
| No examples | true | No |
| 2 random | true | No |
| 8 random | true | No |
| 8 similar | false | **Yes** |
| 32 random | false | Yes |

**How the best arm was chosen:** on dev, before any test call. Dev: none 170, 2 random 179, 8
random 189, 8 similar 196, 32 random 192 of 200.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 521, 527, 562, 593, 583 of 600 | Fully right: none, 2, 8 random, 8 similar, 32 random | `analysis-task-a-test.json`, `arms.*.fully_right` |
| 561 of 600 | 8 random, shuffled | same, `e3-random-8-shuffled` |
| 68, 41, 20, 3, 12 of 535 | False alarms, same order as the first row | same, `safety_false_alarms` |
| 65 of 65, every arm | Safety incidents flagged | same, `safety_recall` |
| 31 and 25 | Items 2 random examples fixed and broke | same, `comparisons.e3-random-2` |
| 0.50 | Holm-corrected p for 2 random against none (not a difference) | same, `p_holm` |
| 41 and 21 | Gain from 0 to 8 random, and from 8 to 32 | `claims-test.json`, C2 |
| 32 and 1 | Items only similar, and only random, got right at 8 | `claims-test.json`, C3 |
| 27 of 600 (14 and 13) | Items that changed when only the order changed | `claims-test.json`, C4 |
| 6, 20, 29, 40, 31 of 40 | Questions about safe use, fully right, same order as the first row | `fully_right_by_kind.safe_use_question` |

## Cost

Ratios to no examples, answer calls only. The embedding step for similar examples is left out;
it costs a small fraction of an answer call.

| Arm | Prompt length | Billed per item | Billed per fully right item |
|---|---|---|---|
| 2 random | 2.2 times | 1.81 times | 1.79 times |
| 8 random | 4.9 times | 0.85 times | 0.79 times |
| 8 similar | 4.4 times | 3.33 times | 2.93 times |
| 32 random | 15.1 times | 1.57 times | 1.40 times |

**This is the episode to teach caching properly.** Fixed examples make every call's prompt the
same, so the provider bills most of it at its cached rate (about 93% of 8 random's input, 98% of
32 random's). Similar examples differ for every message, so nothing is cached: the shorter prompt
costs four times as much. The 2 random prompt is too short to be cached at all. The lesson: in
billing, a fixed long prompt can be cheaper than a short one that changes.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Refresher: tokens and cost.** Every token in the prompt is paid for on every call (S1 E2).
2. **What an example looks like.** One message and its JSON answer, as the model sees it.
3. **The arms as a picture.** Stacks of example cards: 2, 8, 32, and 8 picked for the message.
4. **The kettle message, arm by arm.** The table above, revealed one row at a time.
5. **Prediction.** "8 random examples or 8 similar ones: how far apart on 600 messages?" Reader
   picks.
6. **Reveal.** 562 against 593: 32 messages only similar got right, 1 only random.
7. **The curve.** 521, 527, 562, 583 against number of random examples, with the similar point
   above it. Show tokens on a second axis.
8. **Examples against definitions.** E2's 587 at 947 tokens beside 8 similar at 1,345 and 32
   random at 4,654.
9. **Prediction.** "Shuffle the same 8 examples. How many answers change?" Reader picks.
10. **Reveal.** 27 of 600, 14 one way and 13 the other, total unchanged.
11. **Caching changes the bill.** Prompt length against billed cost, with the explanation above.
12. **Scoreboard:** 593, not joined, and why overlapping intervals mean "not proven better".
13. **Series map** (last slide), E3 marked.

## For leaders

**Ask your team:** "How many examples are in our prompts, who chose them, and what does each one
cost us a month?"

## Decision rule (proposed)

**"Add examples until the score stops rising, then stop: every example is paid for on every
call. Choose them to match the message before you add more."**

## Next

E4, Making output a contract: when code reads the answer, should the provider enforce the format?

## Careful with

- **One random draw.** Another draw of random examples could score differently; only the order
  of this draw was varied.
- **The base changed before the run** (Amendment 1). Say so if the deck compares E3 with E2.
- **The examples-against-definitions comparison is context, not a pre-registered claim.**
- **Order changed 27 answers but not the total.** Do not say order makes the model worse; say it
  makes single answers less stable.
- **Similar examples need an embedding index of the training set,** a system to build and keep
  current, not only a longer prompt.
- **Cost ratios depend on caching and run order.**
- **One model.** Every figure covers these Halvard tasks and this model only.

## From practice

_Brendan to add one anonymised line from his own practice._
