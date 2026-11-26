# S4 E9 deck handover: Distillation: a big model teaches a small one

For the content agent. Has an experiment: a large model labels Halvard's training messages, and
a small model tuned on those labels is compared with the large model and with the small model
tuned on the true labels (Task A, triage).

## Sources of truth

- `episodes/s4-e9-distillation-a-big-model-teaches-a-small-one/README.md` and
  `PREREGISTRATION.md` (which quotes the provider's terms).
- `results/analysis-task-a-test.json`, `analysis-task-a-dev.json`, `results/claims-test.json`.
- Charts: `results/charts/s4-e9-distillation-a-big-model-teaches-a-small-one-fully_right-test-slide.svg`.
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
| E2 + written definitions | 587 (96.3% to 98.7%) | The reference |
| **E9 small model tuned on the big model's labels** | **589 (96.7% to 99.0%)** | **No: overlaps the reference** |

## The key slide

| | Fully right, of 600 | Input tokens a message |
|---|---|---|
| Big model (teacher), best prompt | 587 | 947 |
| Small model, untuned | 24 | 961 |
| Small model tuned on the big model's labels | 589 | 122 |
| Small model tuned on the true labels | 592 | 122 |

## The claims

- **C1 held:** the teacher's labels were 98.3% right (mark: 95%).
- **C2 held:** the student learned the task, 589 against 24.
- **C3 held:** the student matches its teacher, 589 against 587 (p 0.83).
- **C4 held:** no measurable loss against true labels, 589 against 592 (p 0.51).

## Worth saying on a slide

- **The student is not a photocopy.** It got 12 messages right that its teacher got wrong (and
  10 the other way): learning from 1,600 examples smooths out one-off mistakes.
- **Read the terms first.** The exception covers classifiers kept in-house. Season 4 did not
  distil its reply writer for that reason.

## Decision rule and question

- **Rule (proposed):** "If a big model does the task well and its terms allow it, let it label
  the training data, check a sample by hand, and tune the small model on the rest."
- **Ask your team:** "Do we need to label data by hand, or could the model we already pay for
  label it, and do its terms let us?"

## What this does not show

- One teacher, one prompt, one run; a weaker teacher passes on more mistakes.
- The "true" labels are the data generator's, checked by a second model.
- Classification only.
- No break-even in money: hosting is Season 6.

## Cost

Ratios only. Labelling 1,600 messages was the only spend, well within the approved budget; dev
and test came from the cache. The student trained for 28 minutes on the free T4.
