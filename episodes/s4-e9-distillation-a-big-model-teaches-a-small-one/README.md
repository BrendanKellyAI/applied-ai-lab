# S4 E9: Distillation: a big model teaches a small one

E5 tuned a small model on 1,600 messages labelled by Halvard's own rules, and it matched the best
prompt. Most teams do not have labelled data: labelling is the expensive part (E6). Distillation
takes the labels from a large model instead. If the large model, given the best prompt, labels
the training messages, does a small model tuned on those labels do as well? Claims and pass
marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: yes. A 0.6 billion parameter model tuned on the large model's labels scored 589 of
600, against 587 for the large model itself and 592 for the same small model tuned on the true
labels.** None of the differences is measurable. The student reads an eighth of the teacher's
input on every message. All four claims held. It does not join the scoreboard: its interval
overlaps the reference's.

## The design

- **Data:** Task A triage, frozen. Train 1,600 for the teacher to label; dev 200; test 600.
- **Teacher:** `gpt-6-luna`, reasoning off, with E2's definitions prompt (the Task A reference).
  It labelled the 1,600 training messages without seeing the true labels.
- **Terms:** OpenAI's Services Agreement allows output to train a model "primarily intended to
  categorize, classify, or organize data" that is not distributed. Task A is classification and
  the student is never shared; Task B, a reply writer, was not distilled. This is Season 4's
  reading of the terms, not legal advice (details in the pre-registration).
- **Arms (test, 600):**

  | Arm | Model | Source |
  |---|---|---|
  | `e9-teacher` | `gpt-6-luna`, definitions prompt | E2's answers, from the cache |
  | `e9-student-untuned` | Qwen3-0.6B, untuned, definitions prompt | E5's untuned arm |
  | `e9-student-teacher-labels` | Qwen3-0.6B tuned on the teacher's 1,600 labels | this episode |
  | `e9-student-true-labels` | Qwen3-0.6B tuned on the true labels | E5's `e5-tuned-short` |

- **Tuning:** the student job copied E5's in every setting; only the targets differ. A free Colab
  T4: 28 minutes of training (740,160 Qwen tokens), then under 4 minutes of predictions.

## Results (test, 600 messages)

| Arm | Fully right | Safety recall | False safety alarms, of 535 | Valid output | Input tokens a message |
|---|---|---|---|---|---|
| `e9-teacher` | 587 (96.3% to 98.7%) | 65 of 65 | 3 | 600 | 947 |
| `e9-student-untuned` | 24 (2.7% to 5.9%) | 58 of 65 | 452 | 560 | 961 |
| **`e9-student-teacher-labels`** | **589 (96.7% to 99.0%)** | 65 of 65 | 2 | 594 | **122** |
| `e9-student-true-labels` | 592 (97.4% to 99.3%) | 65 of 65 | 1 | 596 | 122 |

On dev: 199, 12, 199 and 198 of 200.

**The teacher's labels:** 1,572 of the 1,600 training messages fully right (98.3%), every one a
valid label. The student was trained on all 1,600, the 28 mistakes included.

**The student did not just copy its teacher.** It got 12 test messages right that the teacher
got wrong, and 10 the other way. Learning from 1,600 examples smoothed out some of the teacher's
one-off mistakes; on the hard cases it did as well or better everywhere but two-request messages
(58 of 62 against the teacher's 60).

## The claims

**C1 held: the teacher's labels are mostly right.** 1,572 of 1,600, 98.3% (the mark was 95%).

**C2 held: distillation teaches the task.** 589 against the untuned student's 24; 565 items
gained, none lost (exact McNemar p below 0.0001).

**C3 held: the student matches its teacher.** 589 against 587; 12 and 10 items each way (p 0.83).

**C4 held: teacher labels cost nothing measurable against true labels.** 589 against 592; 3 and
6 items each way (p 0.51).

## The scoreboard

`e9-student-teacher-labels` does not join Task A's reference. Its interval (96.7% to 99.0%)
overlaps `e2-definitions` (96.3% to 98.7%); the strict bar is to sit clear above it.

## What it means

If a large model already does your classification task well with a good prompt, you can use it
to label your training data, and a small tuned model will match it at a fraction of the input on
every call. The labels Halvard did not have to write cost about one large-model call per training
message, once.

Two conditions: the large model must be good at the task first (check its labels against a
sample you label yourself), and its provider's terms must allow it. The terms here allow it for a
classifier you keep in-house, not for a model that writes text.

**Decision rule (proposed):** "If a big model does the task well and its terms allow it, let it
label the training data, check a sample by hand, and tune the small model on the rest."

**Ask your team:** "Do we need to label data by hand, or could the model we already pay for label
it, and do its terms let us?"

## What this does not show

- **One teacher, one prompt, one run.** A weaker teacher would make more mistakes for the
  student to learn.
- **"True labels" are the generator's labels,** checked by a second model, not by people at
  scale.
- **Classification only.** Distilling a reply writer was not tested, and the terms would not
  allow it.
- **No money break-even.** The student runs on a GPU, which Season 6 prices; input tokens a
  message stand in.

## Cost

Costs are ratios only. Labelling the 1,600 training messages was the episode's only spend, well
within the approved budget; dev and test made no new call (the teacher's answers were E2's, from
the cache). The student job used the free T4.

Tokens, estimated before the calls and counted by the provider after:

| Step | Model | Calls made | Input, estimated | Input, actual | Output, expected | Output, actual |
|---|---|---|---|---|---|---|
| Teacher labels, train | `gpt-6-luna` | 1,600 | 1,501,408 | 1,517,408 | 72,000 | 43,513 |
| Teacher, dev and test | `gpt-6-luna` | 0 (800 from the cache) | | | | |

The provider reported no cached input on the labelling run, though the prompt's 900-token
definitions are a fixed prefix; the estimate's expected figure assumed none either. GPU time:
28 minutes of training (740,160 Qwen tokens) and under 4 minutes of predictions.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e9-distillation-a-big-model-teaches-a-small-one/config.yaml
uv run python episodes/s4-e9-distillation-a-big-model-teaches-a-small-one/claims.py
```

The teacher's train labels: `results/e9-teacher/predictions-train.jsonl`. The job:
`results/e9-student-teacher-labels/job.json`, run once. The student's adapter is on a private
Drive and is not committed or shared, as the terms require.
