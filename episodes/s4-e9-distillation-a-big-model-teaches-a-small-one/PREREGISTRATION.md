# S4 E9 pre-registration: distillation, a big model teaches a small one

Written before any E9 call or job and not edited after; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held, Failed or Not tested. The
pass marks are in `claims.yaml`.

## The question

E5 tuned a small model on 1,600 messages labelled by Halvard's own rules. Most teams do not have
that: labelling is the expensive part (E6). Distillation takes the labels from a large model
instead. If the large model, given the best prompt, labels the training messages, does a small
model tuned on those labels do as well as one tuned on the true labels, and as well as the
large model itself?

## The teacher, and whether its output may train another model

- **Teacher:** `gpt-6-luna`, reasoning off, with E2's definitions prompt: the Task A reference,
  587 of 600 on test. It is far larger than the 0.6 billion parameter student and is the
  cheapest model on file, so no pricier model and no exception is needed. (The plan's teacher
  exception assumed the student would be `gpt-6-luna`; since tuning moved to Qwen on Colab, the
  reference is the natural teacher.)
- **Terms, read 24 November 2026.** OpenAI's Services Agreement (updated 1 December 2025,
  effective 1 January 2026, https://openai.com/policies/services-agreement/) says a customer
  will not, "except for a Permitted Exception, use Output to develop artificial intelligence
  models that compete with OpenAI's products and services". A Permitted Exception includes
  using Output to "develop artificial intelligence models primarily intended to categorize,
  classify, or organize data (e.g., embeddings or classifiers), if these models are not
  distributed or made commercially available to third parties". Task A is classification, and
  the student's adapter stays on a private Drive and is never committed or shared, so E9 is
  within the exception. Season 4 states this as its reading of the terms, not legal advice.
- **Task B is not distilled.** A reply writer is not a classifier, so the exception would not
  cover it.

## Setup

- **Data:** Task A, frozen. Train 1,600 for the teacher to label; dev 200; test 600 to report.
- **Teacher labels** (`config.train.yaml`): the teacher answers every train message with the
  definitions prompt, ignoring the true labels. Its replies are scored against the true labels.
  A reply that is not a valid label is left out of the student's training set and counted.
- **The student job** (`tune-teacher-labels.yaml`, written once the labels exist, with
  `train_size` set to the number of valid labels): Qwen3-0.6B at commit `c1899de`, the short
  instruction, every setting as E5's `e5-tuned-short`. The only difference from E5 is where the
  targets come from. One run on a free Colab T4.
- **Arms (test, 600):**

  | Arm | Model | Source |
  |---|---|---|
  | `e9-teacher` | `gpt-6-luna`, definitions prompt | E2's requests, from the cache |
  | `e9-student-untuned` | Qwen3-0.6B, untuned, definitions prompt | E5's `e5-untuned-0-6b` |
  | `e9-student-teacher-labels` | Qwen3-0.6B tuned on the teacher's labels | this episode |
  | `e9-student-true-labels` | Qwen3-0.6B tuned on the true labels | E5's `e5-tuned-short` |

- **Statistics:** Wilson 95% intervals; exact McNemar on the same items, one test per claim,
  uncorrected. The analysis also reports every arm against `e9-teacher`, Holm corrected.

## Measures

- **Primary:** fully right, out of 600.
- **Teacher label quality:** the teacher's fully right on train, out of 1,600, and its field
  errors, against the true labels.
- **Reported:** safety recall and false alarms, JSON validity, fully right by hard-case kind,
  input tokens per call (teacher against student), training time.

## Claims

**C1. The teacher's labels are mostly right.**

- *Pass mark:* the teacher is fully right on at least 95% of the 1,600 train messages (point
  estimate).

**C2. Distillation teaches the task.**

- *Pass mark:* `e9-student-teacher-labels` is fully right on more test items than
  `e9-student-untuned`, exact McNemar p below 0.05.

**C3. The student matches its teacher.**

- *Pass mark:* `e9-student-teacher-labels` is not worse than `e9-teacher` on fully right (not
  lower with an exact McNemar p below 0.05).

**C4. Teacher labels cost nothing measurable against true labels.**

- *Pass mark:* `e9-student-teacher-labels` is not worse than `e9-student-true-labels` on fully
  right (not lower with an exact McNemar p below 0.05).

## The scoreboard

The candidate is `e9-student-teacher-labels`. It joins the Task A reference only if its interval
on test sits clear above `e2-definitions` (96.3% to 98.7%).

## Estimate

`lab adapt run --estimate` on `config.train.yaml`: 1,600 calls, $0.19 expected, $0.31 ceiling,
before caching (the 900-token prompt is a fixed prefix, so most input is billed at the cached
rate). Dev and test make no new call. Proposed budget: $0.50. Wall-clock: about 5 minutes of
labelling, then about 30 minutes on Colab (training about 28, as E5).

## What E9 cannot show

- **One teacher, one prompt, one run.** A stronger teacher would make fewer mistakes for the
  student to copy.
- **The teacher's mistakes and the student's.** If the student matches the teacher, it may have
  learned the teacher's errors; the per-item comparison with the true-label student shows how
  many.
- **The labels Halvard holds are the generator's.** "True labels" means the labels the data
  was built with, checked by a second model, not by people at scale.
- **No money break-even.** The student runs on a GPU whose price is Season 6's subject; E9
  reports input tokens per call instead.
