# S4 E3 pre-registration: how many examples?

Written before any E3 call and not edited after the run; any later change goes in a dated
amendment at the end. Pass marks are in `claims.yaml`. Bundled with E2 and E4 for one estimate
and one approval.

## The question

Worked examples are paid for on every call. How many does Task A need before the score stops
rising, and does it matter which examples, or their order?

## Setup

- **Data:** Task A. Examples come from train only; dev 200 to choose, test 600 to report.
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200, free text output.
- **Base prompt:** E2's best prompt, chosen on dev by E2's rule. Until then `config.yaml` does
  not exist; `ceiling.yaml` and `ceiling.dev.yaml` use the longest prompt for the estimate and
  are never run. The real configs differ from the ceiling only in `instructions`.
- **Examples** go in the system prompt after the instructions, each as the message and its
  label as JSON (`triage_examples`). Random examples are drawn once from train with seed 0 and
  are nested: the 2 are the first 2 of the 8, and the 8 the first 8 of the 32.

  | Arm | Examples |
  |---|---|
  | `e3-n0` | None: E2's best prompt, the reference (cached from E2) |
  | `e3-random-2` | 2 random |
  | `e3-random-8` | 8 random |
  | `e3-similar-8` | The 8 train messages nearest each item (`text-embedding-3-small`, cosine), nearest last |
  | `e3-random-8-shuffled` | The same 8 random, in another order (shuffle seed 1) |
  | `e3-random-32` | 32 random |

- **Statistics:** Wilson intervals; exact McNemar against `e3-n0`, Holm corrected across the
  five; flips both ways.

## The choice that carries forward

On dev, the arm with the highest fully right is **E3's best arm**, and E4 uses its prompt and
examples. A tie goes to the arm with fewer examples, then to random over similar (no embedding
step), then to the unshuffled order. `e3-random-8-shuffled` is not a candidate: it tests order,
not count.

## Measures

- **Primary:** fully right, out of 600.
- **Reported, side by side:** input tokens per call, and cost per fully right item as a ratio to
  `e3-n0`. Safety recall and false alarms, field accuracy, fully right by kind.

## Claims (on test)

**C1. Examples help.**

- *Pass mark:* at least one example arm (not the shuffled one) has more fully right items than
  `e3-n0` with a Holm-corrected exact McNemar p below 0.05.

**C2. Returns shrink.** The gain from 8 to 32 random examples is smaller than from 0 to 8.

- *Pass mark:* fully right of `e3-random-32` minus `e3-random-8` is less than `e3-random-8`
  minus `e3-n0` (point estimates, counts).

**C3. Similar examples beat random ones.**

- *Pass mark:* `e3-similar-8` has more fully right items than `e3-random-8` (point estimate).
  The exact McNemar p between them is reported beside it.

**C4. Order alone moves answers.**

- *Pass mark:* `e3-random-8-shuffled` and `e3-random-8` differ on fully right for at least 2% of
  items (flips both ways added, at least 12 of 600).

## What E3 cannot show

- One draw of random examples; another draw could score differently, and only the order (not
  the draw) is varied.
- Similar examples are found by an embedding of the message alone, the existing Season 2 code.
- The base prompt was chosen on dev; the examples were not tuned on anything.
