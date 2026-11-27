# Season 4: Adapting models

Changing how a model behaves, not what it knows: instructions, examples, structured output,
fine-tuning and distillation, and when each is worth it. Everything is invented: Halvard Home is
a fictional UK appliance maker, and so are its customers, products and rules.

The season was planned in `PLAN.md` and approved at Gate 1 on 22 November 2026. This page is the
season guide: what was built, where it is, and where each episode stands.

## The two tasks

Both come from the use cases Season 3 scored, and from nothing more.

| Task | What the model does | Data | Primary measure |
|---|---|---|---|
| **A, triage** | Reads a customer message and returns its route, a safety flag, the product and the fault, as JSON | `datasets/halvard-tasks/task-a/`: train 1,600, dev 200, test 600 (65 safety items) | Fully right: all four fields correct |
| **B, house style replies** | Writes the reply to a customer from a correct answer, in Halvard's house style | `datasets/halvard-tasks/task-b/`: train 600, dev 100, test 300 (34 not found) | Passes every code check of the style guide and keeps the facts (judged) |

The test sets were frozen on 23 November 2026; `datasets/halvard-tasks/MANIFEST.json` holds
their hashes and a test fails if they change. The rules the labels follow are written down:
`routes.yaml` (8 routes, 10 products, 12 faults) and `style-guide.md` (13 rules, 9 checked by
code).

## Models

The cheapest model that does the job, in every role (`PLAN.md`, section 2):

| Role | Model |
|---|---|
| Prompted answers | `gpt-6-luna`, reasoning off |
| Tuning, every tuning episode | `Qwen/Qwen3-0.6B` (Apache 2.0) at commit `c1899de`, adapter (LoRA) tuning on a free Google Colab T4 |
| Data generation, E8's training pairs | `gemini-3.1-flash-lite` |
| Label checker | `claude-haiku-5-5` |
| Judge, Task B and E8 | `gemini-3.6-flash` |

No provider API offered tuning Season 4 could use (`PLAN.md`, section 1a), so every tuned model
is a small open model on Colab. Training costs no money, but it is not cached like a response:
every job is recorded in its episode's `results/<arm>/job.json`, launched only after approval,
and never rerun silently.

## Episodes

| Act | Ep | Title | Status |
|---|---|---|---|
| | E0 | Season intro | Handover written |
| Ask better | [E1](../episodes/s4-e1-baseline/) | Prompt, retrieve, or tune: what each one changes | Done |
| | [E2](../episodes/s4-e2-instructions-first/) | Instructions first | Done |
| | [E3](../episodes/s4-e3-how-many-examples/) | How many examples? | Done |
| | [E4](../episodes/s4-e4-making-output-a-contract/) | Making output a contract | Done |
| Tune | [E5](../episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/) | Field note: does fine-tuning beat a good prompt? | Done |
| | [E6](../episodes/s4-e6-how-much-data-does-tuning-need/) | How much data does tuning need? | Done |
| | [E7](../episodes/s4-e7-teaching-a-house-style/) | Teaching a house style | Done |
| Know the limits | [E8](../episodes/s4-e8-can-fine-tuning-teach-facts/) | Field note: can fine-tuning teach facts? | Done |
| | [E9](../episodes/s4-e9-distillation-a-big-model-teaches-a-small-one/) | Distillation: a big model teaches a small one | Done |
| | [E10](../episodes/s4-e10-what-does-tuning-break/) | Field note: what does tuning break? | Done |
| Choose | [E11](../episodes/s4-e11-where-your-tuned-model-runs/) | Where your tuned model runs | Done |
| | E12 | Prompt, retrieve, or tune? | Next |
| | E13 | Season 4 recap: the adaptation card | Last |

Each finished episode has a `README.md` with its results and claims, its `PREREGISTRATION.md`
(written before any call, changed only by dated amendments), a `claims.py` that applies the pass
marks, and a `DECK_HANDOVER.md`. The E0 and E1 handovers are in `deck-handovers/`.

## The scoreboard

`scoreboard.json`, built by `scoreboard.py` from each episode's test analysis. A candidate,
chosen on dev by its episode's pre-registered rule, joins a task's reference only if its Wilson
interval on test sits clear above the reference's. The current references are in
`reference.yaml`; every decision is in `reference_history.yaml`.

| Task | Rung | Score | Joined? |
|---|---|---|---|
| A | E1 one-line prompt | 521 of 600 | The baseline |
| A | E2 + written definitions | 587 of 600 | Joined: the reference |
| A | E3 + 8 similar examples | 593 of 600 | No: overlaps the reference |
| A | E4 + JSON mode | 594 of 600 | No |
| A | E5 Qwen3-0.6B tuned on 1,600 | 592 of 600 | No |
| A | E9 Qwen3-0.6B tuned on the teacher's labels | 589 of 600 | No |
| B | E1 one-line prompt | 0 of 300 | The baseline |
| B | E7 Qwen3-0.6B tuned on 600 replies | 293 of 300 | Joined: the reference |

## Tools

- **`finetune-readiness.md`:** the checklist to run before commissioning a tuning project,
  with Halvard's numbers as a worked case. Started in E6; completed in E10.
- **`decision-card.md`:** the decision path from "what is the gap?" to the cheapest fix that
  clears the bar. Written in E12.
- **`lab adapt score`:** score your own Task A predictions against the test set, with no API
  calls: `uv run lab adapt score predictions.jsonl --split test`.

## Running it

```bash
uv run lab adapt run <episode>/config.yaml --estimate     # count tokens and cost, no call
uv run lab adapt run <episode>/config.yaml                # prompted arms, within the budget
uv run lab adapt analyse <episode>/config.yaml            # score and chart, no call
uv run lab adapt tune <episode>/tune-<arm>.yaml           # prepare a tuning job's files
uv run python <episode>/claims.py                         # apply the pre-registered claims
uv run python season4/scoreboard.py                       # rebuild the scoreboard
```

Paid runs stop unless the episode has a budget in `prices.local.yaml` that covers the ceiling
cost (every call at its output limit). Tuning runs in `colab/lora_job.ipynb`, one copy per job
with its folder set; `lab adapt status` records the result.

E8 and E10 add their own commands: `lab adapt pairs`, `facts-run` and `facts-analyse` (E8), and
`regression-run` and `regression-analyse` (E10).

## Costs

Costs appear only as ratios in episode READMEs. Every paid run so far stayed within its approved
budget; tuning has cost nothing but free Colab GPU time, about 2.5 hours in all by E7.
