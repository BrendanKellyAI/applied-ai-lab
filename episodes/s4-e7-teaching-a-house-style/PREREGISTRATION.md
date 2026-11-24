# S4 E7 pre-registration: teaching a house style

Written before any E7 call or job and not edited after; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held, Failed or Not tested. The
pass marks are in `claims.yaml`.

## The question

E1 found that the cheapest model writes short, correct, polite replies and follows none of
Halvard's house rules: 0 of 300 passed every check, though 262 kept the facts. Task B is about
behaviour, not knowledge, which is what tuning is for. Does writing the style guide into the
prompt teach the house style? Do a few worked examples add to it? Can a small tuned model,
told only "Write the Halvard Home reply.", match the best prompt, and does it keep the facts
while it does?

## Setup

- **Data:** Task B, frozen. Test 300 to report (266 answerable, 34 not found); dev 100 to choose;
  train 600 to tune on and to draw examples from.
- **Arms:**

  | Arm | Model | Prompt |
  |---|---|---|
  | `e7-one-line` | `gpt-6-luna`, reasoning off | E1's one-line prompt, no style guide: exactly E1's `b-one-line` requests, so it comes from the cache |
  | `e7-style-guide` | the same | the one-line prompt plus the full style guide (`style-guide.md`) |
  | `e7-guide-4-examples` | the same | the style guide plus 4 worked examples from train, the same 4 for every item (random, seed 0) |
  | `e7-tuned-short` | `Qwen/Qwen3-0.6B` at commit `c1899de`, tuned | `Write the Halvard Home reply.`, then the question, answer and source |

- **The tuning job** (`tune-short.yaml`): all 600 train replies, the target replies written to
  the style guide. LoRA rank 16, 3 epochs, learning rate 2e-4, batch 8 with 2 accumulation
  steps, seed 1, greedy decoding: E5's settings, with `max_new_tokens` 320 because replies are
  longer than triage. About 318,000 training tokens (o200k stand-in), about 113 steps. One run,
  on a free Colab T4, recorded in `results/e7-tuned-short/job.json`.
- **The tuned model is the small model, the prompted arms the hosted one.** As in E5, that
  compares two practical choices, not one model with and without tuning. The untuned small model
  is not run here; E10 runs it.
- **Judges:** `gemini-3.6-flash`, minimal reasoning, as in E1: facts kept for every answerable
  item, and pairwise style. The style judge compares every arm with `e7-style-guide`, in both
  orders; a win needs the arm preferred both times. (Against the one-line arm, which follows no
  rule, every guided reply would win, and the comparison would show nothing.)
- **The judge check** (`judge-check/config.yaml`): `claude-haiku-5-5`, reasoning off, judges the
  first 50 test items again for every arm, facts and style, from the main run's replies. No new
  replies are made. Haiku is a seventh of Gemini's price, and Gemini's price doubles on
  1 January 2027; if it agrees, it is proposed as the judge from E8 on.
- **Statistics:** Wilson 95% intervals; exact McNemar on the same items, one test per claim,
  uncorrected. The analysis also reports every arm against `e7-style-guide`, Holm corrected.

## Order of work

1. The Colab job (free), after approval.
2. One paid run on dev, then one on test, all four arms and both judges, after approval.
3. The judge check, paid, after approval.

## Measures

- **Primary:** replies that pass every code check and keep the facts, out of 300 (E1's).
- **Reported for every arm:** each code check (opening, sign-off, length, no formatting, policy
  citation, banned phrases, the not found sentence, British spelling), facts kept, style wins,
  ties and losses against `e7-style-guide`, mean words, input tokens per call. One reply per arm
  side by side, for the deck.
- **Judge check:** agreement on facts verdicts, and on style outcomes (win, tie or loss).

## Definitions used by the claims

- **The best prompted arm:** of `e7-style-guide` and `e7-guide-4-examples`, the higher primary
  count on dev; a tie goes to `e7-style-guide`, the simpler.
- **Not worse:** not lower than the other arm with an exact McNemar p below 0.05.

## Claims (on test)

**C1. The style guide teaches the house style.**

- *Pass mark:* `e7-style-guide` beats `e7-one-line` on the primary, exact McNemar p below 0.05.

**C2. Examples add to the guide.**

- *Pass mark:* `e7-guide-4-examples` beats `e7-style-guide` on the primary, exact McNemar p
  below 0.05.

**C3. A tuned small model matches the best prompt on the house style.**

- *Pass mark:* `e7-tuned-short` is not worse than the best prompted arm on the primary.

**C4. Tuning keeps the facts.**

- *Pass mark:* `e7-tuned-short` is not worse than the best prompted arm on facts kept.

**C5. A cheaper judge agrees with the facts judge.**

- *Pass mark:* `claude-haiku-5-5` and `gemini-3.6-flash` give the same facts verdict on at least
  90% of the shared verdicts (the answerable items among the first 50 test items, every arm).

## The scoreboard

The Task B reference is E1's `b-one-line` (0 of 300). E7's candidate is chosen on dev: the
highest primary count of `e7-style-guide`, `e7-guide-4-examples` and `e7-tuned-short`, ties to
the first listed. It joins if its Wilson interval on test sits clear above the reference's
(0% to 1.3%).

## Estimate

From `lab adapt run --estimate`, prompt caching not counted (the one-line arm is entirely cached,
and the guide and examples are a fixed prefix, so the real cost is lower):

| Run | Expected | Ceiling (every call at its limit) |
|---|---|---|
| Dev, 100 items | $0.62 | $1.66 |
| Test, 300 items | $1.86 | $5.00 |
| Judge check, 50 items | $0.04 | $0.11 |
| **Total** | **$2.52** | **$6.77** |

Most of it is the Gemini style judge (2,400 calls). Proposed budget: $7.00. Wall-clock: about
25 minutes on Colab (training about 13, predictions about 10), then about 20 minutes of paid runs.

## What E7 cannot show

- **One draw of examples, one seed, one run** of the tuning job.
- **The targets are the generator's replies,** written to the guide by a model. Tuning learns
  that model's way of following the guide; the prompted arms learn it from the guide itself.
- **The facts judge is a model.** The judge check compares two models with each other, not with
  a person; agreement between them is not accuracy.
- **Two models.** The tuned arm is a different, much smaller model than the prompted arms.
- **Judged rules (5, 9, 11 to 13 of the guide) are only in the style judge,** not the primary.
