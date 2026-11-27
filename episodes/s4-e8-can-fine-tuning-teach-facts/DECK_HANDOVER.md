# S4 E8 deck handover: Field note: can fine-tuning teach facts?

For the content agent. A field note with an experiment: a small model tuned on question and
answer pairs from Halvard's library, asked Season 2's questions without the documents, against
the untuned model and Season 2's retrieval system.

## Sources of truth

- `episodes/s4-e8-can-fine-tuning-teach-facts/README.md` and `PREREGISTRATION.md`.
- `results/analysis-facts-test.json` (by question type, and per item), `analysis-facts-dev.json`,
  `results/claims-test.json`.
- Charts: `results/charts/s4-e8-can-fine-tuning-teach-facts-{right,declined_unanswerable,confident_wrong}-test-slide.svg`.
- The pairs: `pairs/pairs.jsonl`, `pairs/pairs-log.json`.
- The jobs: `results/e8-tuned-closed/job.json`, `results/e8-base-closed/job.json`.
- The reference: `field-notes/s2-e12-embedding-swap/results/baseline/` (Season 2's own run).
- The questions: `datasets/halvard/test.jsonl` (Season 2, frozen).

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E8 |
| Title | Field note: can fine-tuning teach facts? |
| Hub slug | `can-fine-tuning-teach-facts` (as on the hub) |
| Deck file | `bk-s4-e8-can-fine-tuning-teach-facts-v1.pdf` |
| Hub format | `field_note` |

## The argument

"Can't we just train the model on our documents?" is the question every team asks. E8 tried it
on the cheapest terms: a small model tuned on 1,724 questions and answers written from every
public Halvard document, then asked Season 2's 520 questions with no documents in front of it.

It learned the voice, not the facts: 26 of 400 right, against 11 untuned and 354 for retrieval.
And it lost something the untuned model had: saying "I don't know". It declined none of the 120
questions the library cannot answer and gave confident wrong answers to 494 of 520. Its training
answers always answered, so it does too.

## Scoreboard slide

None: E8 is a field note on Season 2's questions, not a rung on Season 4's Task A or B ladders.
The scoreboard does not change. If the deck wants a reference point, Season 2's reference
system is the bar here (354 of 400 right).

## Setup before results

**The training pairs.** `gemini-3.1-flash-lite` wrote 4 question and answer pairs from each of
the library's 436 current public passages, asked for varied wording and exact figures. 1,724 were
kept; 6 too close to a test or dev question and 14 repeats were removed. Staff-only documents
were left out on purpose (a tuned model has no permission filter), as were withdrawn and
superseded ones.

| Arm | Model | What it is given |
|---|---|---|
| Untuned | Qwen3-0.6B | the question only |
| Tuned | Qwen3-0.6B, tuned on the 1,724 pairs | the question only |
| Retrieval | Season 2's reference system, `gpt-6-luna` | the question and the passages it retrieved |

Both small models are told: "Answer the Halvard Home customer's question. If you do not know the
answer, say that you could not find it."

**Worked examples** (`datasets/halvard/test.jsonl`, invented):

`PARA-000`, answerable: "Which wireless frequency does my smart water boiler support?" (The
answer: 2.4 GHz.)

| Arm | What came back |
|---|---|
| Untuned | "I could not find it." |
| Tuned | "The Halvard Home smart water boiler connects using 2.4 GHz Wi-Fi." Right |
| Retrieval | "Your Brio kettle supports a 2.4 GHz Wi-Fi network, not 5 GHz." Right, with a citation |

`DELETED-000`, not answerable (the notice was withdrawn): "What should I do if I have a wall
bracket from batch 4867 for my Brio kettle?"

| Arm | What came back |
|---|---|
| Untuned | "I could not find it." Correct decline |
| Tuned | "If you still have a wall bracket fitted to your Brio kettle, contact Halvard Home customer support to check whether it is suitable for your model." Plausible, polite, made up |
| Retrieval | "I could not find information about a wall bracket from batch 4867 in the passages." Correct decline |

The first example is one of the tuned model's 26 successes; most questions went like the second.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 11, 26, 354 of 400 | Right on answerable questions: untuned, tuned, retrieval | `analysis-facts-test.json`, `arms.*.right` |
| 78, 0, 107 of 120 | Correct declines on unanswerable questions, same order | same, `declined_unanswerable` |
| 165, 494, 11 of 520 | Confident wrong answers, same order | same, `confident_wrong` |
| 267, 0, 48 of 400 | Declined an answerable question, same order | same, `declined_answerable` |
| 19 and 4; p 0.003 | Tuned against untuned, right, items each way | `claims-test.json`, C1 |
| 3 and 331 | Tuned against retrieval, right, items each way | same, C2 |
| 16 of 26 | The tuned model's right answers that are `shared` questions (facts repeated across the library) | `analysis-facts-test.json`, `e8-tuned-closed.by_type` |
| 1,724 of 1,744 | Training pairs kept | `pairs/pairs-log.json` |
| 0 and 1 of 70; 17 and 0 of 30 | Dev: right, then correct declines, untuned and tuned | `analysis-facts-dev.json` |

The declines chart has an empty bar for the tuned model: it is zero, not missing. Label it "0".

## Cost

Ratios only: the pairs and both judge runs stayed well within the approved budget, and the
judge's test run was about five times its dev run. The two Colab jobs ran on the free T4: 15
minutes of training, about 3 minutes of answers each. Token counts, estimated against actual,
are in the README.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **"Just train it on our documents."** The idea, stated as a team would say it.
2. **The experiment.** 436 passages, 1,724 practice questions, one small model; then 520 real
   questions with the documents taken away.
3. **The boiler question.** All three arms answer it; the tuned model gets it right.
4. **Prediction.** "Out of 400 answerable questions, how many does the tuned model get right?"
   Reader picks: about 300, about 150, under 50.
5. **Reveal.** 26. Against 354 for retrieval. Bar chart (`right`).
6. **The bracket question.** A withdrawn notice. Untuned and retrieval say "I could not find
   it"; the tuned model invents advice.
7. **Prediction.** "How often does the tuned model say it does not know, on 120 questions it
   cannot answer?"
8. **Reveal.** Never. Bar chart (`declined_unanswerable`).
9. **Why.** Every training answer answered. It learned to answer, not to know.
10. **What it did pick up.** Facts the library repeats (16 of its 26), not the one-off detail a
    customer asks about.
11. **The safer model knew nothing.** Untuned, it declined two times in three. Confident wrong
    answers: 165, 494, 11 (`confident_wrong`).
12. **Series map** (last slide), E8 marked.

## For leaders

**Ask your team:** "If our model did not know the answer, would it say so, and have we tested
that?"

## Decision rule (proposed)

**"To give a model your facts, retrieve them. Tune for behaviour, and if you tune on answers,
include the questions it should decline."**

## Next

E9, Distillation: a big model teaches a small one: a large model labels the training data, and
a small model tuned on its labels is compared with both.

## Careful with

- **One way of tuning.** Rank 16, 3 epochs, 4 pairs a passage, one seed. Do not say tuning can
  never teach facts; say it did not here, on the season's settings.
- **A 0.6 billion parameter model.** A larger model may hold more.
- **The pairs were written by a model,** and the judge is a model, checked against a person in
  Season 2 with passages, not closed book.
- **No pairs that decline.** Adding some might restore declining; it was not tested. Present it
  as the lesson, not as a result.
- **The retrieval system is a different, larger model.** The comparison is of two approaches as
  a team would build them, not of tuning alone.
- **Staff questions:** the tuned model could not answer them by design.

## From practice

_Brendan to add one anonymised line from his own practice._
