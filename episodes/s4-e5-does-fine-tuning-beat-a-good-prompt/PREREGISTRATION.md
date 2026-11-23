# S4 E5 pre-registration: does fine-tuning beat a good prompt?

Written before any E5 job is launched and not edited after; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held or Failed. The pass marks
are in `claims.yaml`. A field note: one question, one tuning run per arm.

## The question

E2 to E4 reached 587 to 594 of 600 on Task A by prompting `gpt-6-luna`. Does a small open model,
tuned on Halvard's labelled messages, match that with a fraction of the prompt? And how much of
its score is the tuning, rather than the model?

No provider API offers tuning this season can use (`season4/PLAN.md`, section 1a), so the tuned
model is `Qwen3-0.6B` with an adapter (LoRA: a small set of extra weights trained on top of the
frozen model), trained on a free Colab GPU. Training costs no money, but it is not cached like a
response, so every job is recorded and none is relaunched without approval.

## Setup

- **Data:** `datasets/halvard-tasks`, Task A, frozen. Train 1,600 items (all of it), dev 200 to
  choose, test 600 to report. The tuned models see train only.
- **Base model:** `Qwen/Qwen3-0.6B` at commit `c1899de289a04d12100db370d81485cdf75e47ca`
  (Apache 2.0), thinking off, greedy decoding, output limit 160 tokens.
- **Adapter settings,** the defaults in `src/lab/adapt/tune_config.py`, fixed here: rank 16,
  alpha 32, dropout 0.05, on every attention and feed-forward projection; 3 epochs, learning rate
  2e-4 with cosine decay and 3% warm-up, batch 8 with 2 accumulation steps, seed 1. One run per
  arm.
- **Arms:**

  | Arm | Model | Prompt | Where |
  |---|---|---|---|
  | `e5-reference` | `gpt-6-luna`, reasoning off | E2's definitions prompt (the Task A reference) | API, same requests as E2, so cached |
  | `e5-untuned-0-6b` | Qwen3-0.6B, untuned | E2's definitions prompt | Colab, no training |
  | `e5-tuned-short` | Qwen3-0.6B, tuned | `Triage this Halvard Home customer message as JSON.` | Colab |
  | `e5-tuned-one-line` | Qwen3-0.6B, tuned | E1's one-line prompt, which lists the four fields and their allowed values | Colab |

  Each tuned arm is trained and run with the same prompt; the training target is the label as
  JSON (`label_json`). No examples in any arm.
- **Not run:** the optional larger prompted model (off by default at Gate 1), and a second seed.
- **Scoring:** as E1 to E4, by code. The same parser reads every arm.
- **Statistics:** Wilson 95% intervals; exact McNemar on the same items, one test per claim,
  uncorrected (each claim asks a different question). The analysis also reports every arm
  against `e5-reference`, Holm corrected across the three.

## Order

1. **Pilot: the base model.** `e5-untuned-0-6b` runs on dev and test. Its **dev** JSON validity
   decides the base, by the rule fixed at Gate 1: **if at least 180 of 200 dev replies are valid,
   Qwen3-0.6B stays; otherwise every Qwen arm moves to `Qwen/Qwen3-1.7B` at commit
   `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`,** under new arm names (`-1-7b`), by a dated
   amendment before any tuning launch. Its test predictions are not analysed until step 4.
2. **Tuning:** `e5-tuned-short` and `e5-tuned-one-line`, each in a fresh Colab runtime.
3. **Choice, on dev:** the tuned arm with the higher fully right is **E5's tuned arm**; a tie goes
   to `e5-tuned-short` (the shorter prompt). It carries forward to E6 and E10.
4. **Test:** analyse all four arms, then the claims.

## Measures

- **Primary:** fully right, out of 600.
- **Reported:** JSON validity, safety recall (of 65) and false alarms (of 535), field accuracy,
  fully right by hard-case kind, input tokens per call (counted with the same tokeniser for every
  arm, `o200k_base`, so prompt lengths compare), output tokens, training loss and minutes, GPU
  type, and inference minutes.
- **Cost:** the reference's API cost per item, and for the Qwen arms GPU minutes for training and
  per 1,000 items. Training costs no money on free Colab, so a money break-even needs a hosting
  price, which is Season 6's subject; E5 reports the GPU minutes it would be built from.

## Claims (on test)

**C1. Tuning teaches the task.** The tuning, not the model, does the work.

- *Pass mark:* E5's tuned arm has more fully right items than `e5-untuned-0-6b`, with an exact
  McNemar p below 0.05.

**C2. A tuned small model matches the best prompt.** It is not distinguishable from the
reference.

- *Pass mark:* E5's tuned arm and `e5-reference` do **not** differ on fully right, exact McNemar
  p of 0.05 or more. If they differ, the claim fails and the direction is reported.

**C3. With a fraction of the prompt.**

- *Pass mark:* E5's tuned arm's mean input tokens per call is at most a fifth of
  `e5-reference`'s.

**C4. Without missing incidents.**

- *Pass mark:* E5's tuned arm's safety recall is at least 95% (point estimate).

**C5. Once tuned, the field list adds nothing.**

- *Pass mark:* `e5-tuned-short` and `e5-tuned-one-line` do not differ on fully right (exact
  McNemar p of 0.05 or more).

## The scoreboard

E5's tuned arm joins the Task A reference only if its test interval on fully right sits clear
above `e2-definitions`'s (96.3% to 98.7%), which needs about 597 of 600. A tie in quality at a
fraction of the prompt is reported as such, not as joining.

## What E5 cannot show

- **Train and test come from the same generator.** The messages were written by one model from
  the same templates, so a tuned model may learn the generator's habits as well as Halvard's
  rules. Real messages would test it harder. The prompted arms never see train, so the
  comparison favours tuning.
- **Two models, not one.** The prompted reference is `gpt-6-luna`; the tuned model is
  Qwen3-0.6B. The untuned Qwen arm is what separates the tuning from the model.
- One seed and default settings: another seed could move a few items.
- The definitions in the reference prompt are the labeller's own rules (E2).
- Free Colab GPUs vary; minutes are reported with the GPU type and are not a benchmark.

## Amendment 1, 23 November 2026: the one-line tuned arm is not run

Written after the pilot and the `e5-tuned-short` job, and before any test analysis.

- **The pilot rule was met:** 192 of 200 dev replies from untuned Qwen3-0.6B were valid JSON
  (the bar was 180), so Qwen3-0.6B stays.
- **`e5-tuned-one-line` is not run.** Training `e5-tuned-short` took 28 minutes on the free T4
  (about three times the estimate) with a peak of 13.0 of 15 GB of GPU memory. The one-line arm
  has about 2.3 times the tokens per example, so it would take about 65 minutes and might not fit
  in memory. Brendan chose to drop it. Its launch was recorded and then closed as cancelled
  before any training.
- **Consequences:** C5 is not tested and is reported as such. `e5-tuned-short` is E5's tuned arm
  (the only candidate). The configs no longer list the one-line arm. C1 to C4, the pass marks
  and the scoreboard rule are unchanged.
- **An unapproved second run of the pilot** happened at 22:07 UTC, from a notebook edit that
  Colab did not save. It cost nothing, was not used, and reproduced every recorded answer (200
  of 200 dev, 600 of 600 test). See `results/e5-untuned-0-6b/rerun-unapproved.md`.
