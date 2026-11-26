# S4 E9 deck handover: Distillation: a big model teaches a small one

For the content agent. Has an experiment: a large model labels Halvard's training messages, and
a small model tuned on those labels is compared with the large model and with the small model
tuned on the true labels (Task A, triage).

## Sources of truth

- `episodes/s4-e9-distillation-a-big-model-teaches-a-small-one/README.md` and
  `PREREGISTRATION.md` (which quotes the provider's terms).
- `results/analysis-task-a-test.json`, `analysis-task-a-dev.json`, `analysis-task-a-train.json`
  (the teacher's labels scored), `results/claims-test.json`.
- Chart: `results/charts/s4-e9-distillation-a-big-model-teaches-a-small-one-fully_right-test-slide.svg`.
- The teacher's labels: `results/e9-teacher/predictions-train.jsonl`.
- The job: `results/e9-student-teacher-labels/job.json`.
- `season4/scoreboard.json`, `season4/reference_history.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E9 |
| Title | Distillation: a big model teaches a small one |
| Hub slug | `distillation-a-big-model-teaches-a-small-one` (proposed; confirm) |
| Deck file | `bk-s4-e9-distillation-a-big-model-teaches-a-small-one-v1.pdf` |
| Hub format | `experiment` |

## The argument

Tuning needs labelled data, and labelling is the expensive part (E6). Halvard had labels; most
teams do not. Could the large model they already pay for do the labelling?

`gpt-6-luna`, with the best prompt from E2, labelled 1,600 messages and got 98% right. A 0.6
billion parameter model tuned on those labels scored 589 of 600: as good as its teacher (587)
and as good as the same model tuned on the real labels (592). It reads an eighth of the input
the teacher needs on every message.

The catch is in the terms: OpenAI's allow this for an in-house classifier, not for a model that
writes text or is shared.

## Scoreboard slide

Task A ladder. Chart: `...-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 | The baseline |
| E2 + written definitions | 587 (96.3% to 98.7%) | Joined: the reference |
| E3 + 8 similar examples | 593 | No: overlaps the reference |
| E4 + JSON mode | 594 | No |
| E5 Qwen3-0.6B tuned on 1,600 true labels | 592 | No |
| **E9 Qwen3-0.6B tuned on the teacher's labels** | **589 (96.7% to 99.0%)** | **No: overlaps the reference** |

What E9 adds: the same small model reaches the top of the ladder without anyone labelling data
by hand.

## Setup before results

**The task** (Task A, as E1 to E5): read a customer message, return the product, the fault, the
route and whether it is a safety issue, as one line of JSON. "Fully right" means all
four fields right.

**The terms, quoted for the slide** (OpenAI Services Agreement, effective 1 January 2026): output
may be used to develop models "primarily intended to categorize, classify, or organize data
(e.g., embeddings or classifiers), if these models are not distributed or made commercially
available to third parties".

| Arm | Model | Trained on, or told |
|---|---|---|
| Teacher | `gpt-6-luna` | E2's definitions prompt (about 950 tokens) |
| Untuned student | Qwen3-0.6B | the same definitions prompt |
| Student, teacher's labels | Qwen3-0.6B, tuned | the teacher's labels for 1,600 training messages; told one line (about 120 tokens with the message) |
| Student, true labels | Qwen3-0.6B, tuned | the true labels for the same 1,600 (E5) |

The two tuned students differ only in where their training labels came from.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 1,572 of 1,600 (98.3%) | The teacher's labels fully right on the training messages | `claims-test.json`, C1 |
| 587, 24, 589, 592 of 600 | Fully right on test: teacher, untuned, teacher-label student, true-label student | `analysis-task-a-test.json`, `arms.*.fully_right` |
| 12 and 10; p 0.83 | Student against teacher, items each way | `claims-test.json`, C3 |
| 3 and 6; p 0.51 | Teacher-label student against true-label student, items each way | same, C4 |
| 65 of 65 | Safety recall: the teacher and both tuned students (untuned 58) | `analysis-task-a-test.json`, `safety_recall` |
| 947 against 122 | Mean input tokens a message, teacher against student | same, `tokens.mean_input_tokens` |
| 199, 12, 199, 198 of 200 | Dev, same order | `analysis-task-a-dev.json` |
| 28 minutes | Training the student, free Colab T4 | `results/e9-student-teacher-labels/job.json` |

## Cost

Ratios only. Labelling the 1,600 training messages was the only spend, well within the approved
budget; dev and test came from the cache. The student trained for 28 minutes on the free T4.
Token counts, estimated against actual, are in the README.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **The expensive part of tuning is the labels.** E6's curve: 800 labelled messages to match
   the prompt.
2. **What if the big model labels them?** Teacher and student, as a diagram.
3. **Read the terms first.** The quoted exception: classifiers, kept in-house.
4. **The teacher's homework.** 98% of its 1,600 labels right; 28 wrong, and the student learned
   from those too.
5. **Prediction.** "The student learns from a teacher that is 98% right. Does it score above or
   below its teacher?" Reader picks.
6. **Reveal.** 589 against 587: the same. Bar chart.
7. **Not a photocopy.** 12 messages the student got right that its teacher got wrong.
8. **Against real labels.** 589 against 592: no measurable cost.
9. **The prize.** 122 input tokens a message against 947.
10. **Scoreboard:** at the top of the ladder, and still not joined; the reference's interval
    overlaps.
11. **Series map** (last slide), E9 marked.

## For leaders

**Ask your team:** "Do we need to label data by hand, or could the model we already pay for label
it, and do its terms let us?"

## Decision rule (proposed)

**"If a big model does the task well and its terms allow it, let it label the training data,
check a sample by hand, and tune the small model on the rest."**

## Next

E10, Field note: what does tuning break?: everyday requests, the reply writer's habits leaking
into other questions, and declines, before and after tuning.

## Careful with

- **The terms are Season 4's reading, not legal advice.** Quote them; do not paraphrase them as
  a permission.
- **Classification only.** Do not imply a reply writer could be distilled the same way.
- **"True labels" are the data generator's,** checked by a second model, not by people at scale.
- **One teacher, one prompt, one run.** A weaker teacher would pass on more mistakes.
- **"Matches" means no measurable difference** on 600 messages, not identical.
- **No break-even in money:** hosting is Season 6.

## From practice

_Brendan to add one anonymised line from his own practice._
