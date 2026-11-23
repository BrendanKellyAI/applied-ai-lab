# S4 E2 pre-registration: instructions first

Written before any E2 call and not edited after the run; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held or Failed. The pass marks
are in `claims.yaml`. E2, E3 and E4 share one estimate and one approval, listed line by line.

## The question

E1 told the model only what to do. How much does telling it what Halvard's words mean, and how
Halvard routes a message, add? This is the cheapest rung: no examples, no training, only text a
new colleague would be given.

## Setup

- **Data:** `datasets/halvard-tasks`, Task A. Dev 200 to choose, test 600 to report. Test waits
  for the freeze (E1's rule).
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200, free text output, as E1.
- **Arms.** Each prompt is the one before plus one addition (`triage_system` in
  `src/lab/adapt/prompts.py`); the user turn is `Customer message:` and the message.

  | Arm | Adds |
  |---|---|
  | `e2-one-line` | Nothing: E1's arm, the reference. Same requests, so its replies are cached |
  | `e2-definitions` | The definition of each route and fault, and the safety definition |
  | `e2-policy` | The routing precedence rules, the product rule and the fault rule |
  | `e2-unsure` | The "when unsure" rule (`UNSURE_RULE`) |

- **Not run:** the optional low reasoning arm. It is left out to keep the bundle cheap.
- **Scoring:** as E1. Fully right means all four fields correct; safety recall and false alarms
  beside it.
- **Statistics:** Wilson 95% intervals; exact McNemar against `e2-one-line` on the same items,
  Holm corrected across the three; flips both ways.
- **Order:** dev for all four arms, choose, then test for all four after the freeze.

## The choice that carries forward

On dev, the arm with the highest fully right is **E2's best prompt**, and E3 builds on it. A tie
goes to the shorter prompt. The choice is made by this rule from `analysis-task-a-dev.json`, and
written into E3's config before any E3 call. Test is never used to choose.

## Measures

- **Primary:** fully right, out of 600.
- **Reported:** safety recall (out of 65), false alarms (out of 535), field accuracy, route
  macro F1, fully right by hard-case kind, input tokens per call, and cost per fully right item
  as a ratio to `e2-one-line`.

## Claims (on test)

**C1. Definitions help.** At least one added rung beats the one-line prompt.

- *Pass mark:* at least one of `e2-definitions`, `e2-policy`, `e2-unsure` has more fully right
  items than `e2-one-line` with a Holm-corrected exact McNemar p below 0.05.

**C2. The safety definition cuts false alarms.** On dev, most errors were safety flags on
messages with no incident; `e2-definitions` is the first arm told what counts.

- *Pass mark:* the false alarm rate of `e2-definitions` is at most half that of `e2-one-line`
  (point estimates).

**C3. Fewer false alarms do not cost missed incidents.**

- *Pass mark:* the safety recall of E2's best prompt is at least 95% (point estimate).

## The scoreboard

E2's best prompt joins the reference only if its test interval on fully right sits clear above
the reference's (the strict bar).

## What E2 cannot show

- One model and one wording of each rung; the order of rungs is fixed, so it cannot say what a
  later rung would do alone.
- The definitions are the ones the labeller was given when the data was built, so the prompt
  matches the labels' own rules more closely than a real colleague's notes would.
- The dev set was used for E1's headroom check; it is used again here only to choose.
