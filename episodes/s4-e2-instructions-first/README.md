# S4 E2: Instructions first

E1 told the model only what to do. How much does telling it what Halvard's words mean, and how
Halvard routes a message, add? This is the cheapest rung: no examples, no training, only text a
new colleague would be given. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: written definitions take Task A from 521 to 587 of 600 and cut false safety alarms
from 68 to 3, with no incident missed.** Every rung beats the one-line prompt by a wide margin.
`e2-definitions` joins the reference.

## The design

- **Data:** Task A, dev 200 to choose, test 600 to report. Frozen before any test call.
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200, free text output, as E1.
- **Arms.** Each prompt is the one before plus one addition (`triage_system` in
  `src/lab/adapt/prompts.py`):

  | Arm | Adds |
  |---|---|
  | `e2-one-line` | Nothing: E1's arm, the reference. Same requests, so its replies are cached |
  | `e2-definitions` | The definition of each route and fault, and the safety definition |
  | `e2-policy` | The routing precedence rules, the product rule and the fault rule |
  | `e2-unsure` | The "when unsure" rule |

- **Statistics:** Wilson 95% intervals; exact McNemar against `e2-one-line` on the same items,
  Holm corrected across the three.
- **The choice:** on dev, the highest fully right is E2's best prompt; a tie goes to the shorter
  prompt. Dev: one-line 170, definitions **199**, policy 197, unsure 197 of 200.

## Results (test, 600 items)

| Arm | Fully right | False alarms (535) | Safety recall (65) | Input tokens per call |
|---|---|---|---|---|
| `e2-one-line` (reference) | 521 (84% to 89%) | 68 | 65 | 308 |
| **`e2-definitions`** | **587 (96% to 99%)** | **3** | 65 | 947 |
| `e2-policy` | 590 (97% to 99%) | 1 | 65 | 1,113 |
| `e2-unsure` | 596 (98% to 100%) | 1 | 65 | 1,193 |

Item by item against the one-line prompt:

| Arm | Wrong to right | Right to wrong | Holm-corrected p |
|---|---|---|---|
| `e2-definitions` | 73 | 7 | below 0.0001 |
| `e2-policy` | 76 | 7 | below 0.0001 |
| `e2-unsure` | 77 | 2 | below 0.0001 |

The definitions fixed the hard case E1 failed worst: `safe_use_question` went from 6 to 40 of
40. Each later rung added a little more: with the "when unsure" rule, every route was right on
all 600 items.

**`e2-unsure` scored highest on test, and is not E2's best prompt.** The choice was made on dev,
where definitions led by two items; test is never used to choose. The three rungs' test
intervals overlap, so test cannot separate them either.

## The claims

**C1 held: definitions help.** All three rungs beat the one-line prompt, each with a
Holm-corrected p below 0.0001.

**C2 held: the safety definition cuts false alarms.** 3 of 535 (0.6%) against 68 of 535 (12.7%):
less than a twentieth of the rate, against a pass mark of half.

**C3 held: fewer false alarms do not cost missed incidents.** E2's best prompt caught all 65.

## The scoreboard

`e2-definitions` joins the Task A reference: its interval (96% to 99%) sits clear above the
one-line prompt's (84% to 89%). See `season4/reference_history.yaml`. It is also the arm E5
tunes against, the best prompted arm on dev across E2 to E4 (E4 Amendment 1).

## What this does not show

- One model and one wording of each rung. The order of rungs is fixed, so E2 cannot say what a
  later rung would do alone.
- **The definitions are the labeller's own.** They are the rules the labels were built and
  checked with, so the prompt matches the labels more closely than a real colleague's notes
  would.
- The dev set was used for E1's headroom check, and again here only to choose.

## Charts

`results/charts/`: **`fully_right`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

Costs are ratios to `e2-one-line`, answer calls only.

| Arm | Input tokens per call | Cost per item | Cost per fully right item |
|---|---|---|---|
| `e2-definitions` | 3.1 times | 2.44 times | 2.16 times |
| `e2-policy` | 3.6 times | 2.81 times | 2.48 times |
| `e2-unsure` | 3.9 times | 0.78 times | 0.68 times |

**The cost ratios depend on the provider's prompt caching,** not only on prompt length. The
system prompt is the same on every call, and a cached prompt is billed at a much lower rate.
Only `e2-unsure` got cache hits in this run (about 90% of its input tokens), so it is billed
below the one-line prompt; the others got none. Caching depends on prompt length, run order and
timing, so input tokens per call is the fair comparison of length, and billed cost is one run's
outcome.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e2-instructions-first/config.yaml
uv run python episodes/s4-e2-instructions-first/claims.py test
```

To call the model again (replies are cached): `uv run lab adapt run
episodes/s4-e2-instructions-first/config.yaml`. The dev run is `config.dev.yaml`.
