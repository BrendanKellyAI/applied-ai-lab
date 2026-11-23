# S4 E6 pre-registration: how much data does tuning need?

Written before any E6 job is launched and not edited after; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held, Failed or Not tested. The
pass marks are in `claims.yaml`.

## The question

E5 tuned Qwen3-0.6B on all 1,600 labelled Task A messages and matched the best prompt (592
against 587 of 600). Labelled data is the expensive part of tuning. How few examples are enough,
and where does adding more stop helping?

## Setup

- **Data:** Task A, frozen. Test 600 to report; dev 200 is scored but chooses nothing.
- **Training sets, nested:** the first 50, 200 and 800 of the same seeded shuffle of train
  (`subset_seed` 20261122) that E5 used, so each set is the start of the next and of E5's 1,600.
  Safety items in each: 7, 22, 88, and 166 in the 1,600.
- **Everything else as E5's `e5-tuned-short`:** `Qwen/Qwen3-0.6B` at commit `c1899de`, the short
  instruction, LoRA rank 16, 3 epochs, learning rate 2e-4, batch 8 with 2 accumulation steps,
  seed 1, greedy decoding. One run per size. Epochs are fixed, so smaller sets also get fewer
  training steps (about 12, 39 and 150, against 300 for 1,600); that is part of what a smaller
  dataset means in practice, and is reported.
- **Points on the curve:**

  | Arm | Examples | Source |
  |---|---|---|
  | `e6-tuned-0` | 0 (untuned, definitions prompt) | E5's `e5-untuned-0-6b` |
  | `e6-tuned-50` | 50 | this episode |
  | `e6-tuned-200` | 200 | this episode |
  | `e6-tuned-800` | 800 | this episode |
  | `e6-tuned-1600` | 1,600 | E5's `e5-tuned-short` |
  | `e6-reference` | prompted, not tuned | E5's `e5-reference`: `gpt-6-luna` with E2's definitions prompt |

- **Where it runs:** three jobs on a free Colab T4, each in a fresh runtime with its own notebook
  copy (`JOB_DIR` set), recorded in `results/<arm>/job.json`. Estimated from E5's speed: about
  7, 10 and 20 minutes, about 40 minutes in all. No money is spent.
- **Statistics:** Wilson 95% intervals; exact McNemar on the same items, one test per claim,
  uncorrected. The analysis also reports every arm against `e6-reference`, Holm corrected.

## Measures

- **Primary:** fully right, out of 600, at each size: the learning curve.
- **Reported:** JSON validity, safety recall (of 65) and false alarms (of 535), fully right by
  hard-case kind, training steps, loss and minutes at each size.

## Definitions used by the claims

- **Matches the prompt:** the arm is not worse than `e6-reference` on fully right with an exact
  McNemar p below 0.05. (Equal, better, or worse by too little to tell.)
- **The smallest matching size:** the smallest of 50, 200, 800 and 1,600 that matches the prompt.

## Claims (on test)

**C1. Fifty examples are not enough.**

- *Pass mark:* `e6-tuned-50` is worse than `e6-reference` on fully right with an exact McNemar
  p below 0.05.

**C2. A few hundred examples are enough.**

- *Pass mark:* the smallest matching size is 800 or fewer.

**C3. Beyond 800, more data adds nothing measurable.**

- *Pass mark:* `e6-tuned-800` and `e6-tuned-1600` do not differ on fully right (exact McNemar p
  of 0.05 or more).

**C4. The smallest matching size still catches incidents.**

- *Pass mark:* its safety recall is at least 95% (point estimate). Not tested if no size
  matches.

## The scoreboard

No E6 arm is a new rung: the sizes are points on E5's rung. The scoreboard is unchanged unless a
size clears the strict bar above `e2-definitions` (96.3% to 98.7%), which is then reported and
joins as E5's would have.

## What E6 cannot show

- **One draw of each subset and one seed.** A different 50 could score quite differently; with
  50 examples, which ones matters most. The curve is one path, not a band.
- **Fixed epochs.** Small sets get few steps; more epochs on 50 examples might do better, and is
  not tried.
- **The generator caveat from E5 applies more strongly here:** train and test share one
  generator's templates, so few examples may go further than they would on real messages.
- The readiness checklist this starts (`season4/finetune-readiness.md`) gives Halvard's numbers
  as one worked case, not a rule for other tasks.
