# S4 E2 deck handover: Instructions first

For the content agent. Has an experiment: three instruction rungs on Task A, each the one before
plus one addition.

## Sources of truth

- `episodes/s4-e2-instructions-first/README.md` and `PREREGISTRATION.md` (with Amendment 1).
- `results/analysis-task-a-test.json` and `analysis-task-a-dev.json`; `results/claims-test.json`.
- Chart: `results/charts/s4-e2-instructions-first-fully_right-test-slide.svg`.
- The prompts: `triage_system` and `UNSURE_RULE` in `src/lab/adapt/prompts.py`; the text they
  quote is in `datasets/halvard-tasks/routes.yaml`.
- `season4/scoreboard.json`, `season4/reference.yaml`, `season4/reference_history.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E2 |
| Title | Instructions first |
| Hub slug | `instructions-first` (proposed; confirm) |
| Deck file | `bk-s4-e2-instructions-first-v1.pdf` |
| Hub format | `explainer` |

## The argument

The cheapest change to a model's behaviour is the one a new colleague would get on their first
day: write down what the words mean and how the work is routed. No examples, no training.

E1's model knew enough and lacked Halvard's rules. Given the definitions, it went from 521 to 587
of 600 fully right, and harmless messages flagged as incidents fell from 68 to 3, with every
real incident still caught. Each further rung (the routing policy, then a "when unsure" rule)
added a little more. Most of the gap E1 found was a page of text away.

## Scoreboard slide

Task A ladder. Chart: `s4-e2-instructions-first-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 (84% to 89%) | The baseline |
| **E2 + definitions** | **587 (96% to 99%)** | **Joined: clear above the baseline** |

What this episode adds: the first rung that clears the bar. The definitions prompt becomes the
Task A reference, and the arm Season 4's tuning is later measured against.

## Setup before results

Same model (`gpt-6-luna`, reasoning off), same 600 messages, free text output. Each arm is the
one before plus one addition. Quote each addition on its own slide before any score:

| Arm | Adds | Input tokens per call |
|---|---|---|
| One-line (E1) | Nothing | 308 |
| + definitions | What each of the 8 routes means, the 12 faults, and what counts as a safety incident | 947 |
| + policy | Which route wins when a message fits two, and the product and fault rules | 1,113 |
| + when unsure | A rule for doubtful cases | 1,193 |

**The safety definition**, the line that does most of the work:

> true if the message describes, or may describe, a real incident or hazard involving fire,
> smoke, burning, sparks, scorching, electric shock or injury, even if the customer plays it
> down. false if a safety word is used harmlessly (a hob that is "hot" as it should be, a dryer
> "on fire" as praise) or only as a question about safe use with no incident.

**One route definition**, for example `how_to_use`:

> The customer asks how to set up, use, clean or understand an appliance, including what an error
> code means, and describes no other fault and asks for no repair, return or visit.

**The routing policy** (the first rule that applies wins), in full:

> - A message that asks for a formal complaint or escalation is a complaint. Anger, threats or
>   lost faith alone do not make a complaint.
> - A message about an order not yet delivered is delivery.
> - A message that asks for money back or to send the appliance back is return_refund.
> - A fault with a request for repair or replacement is warranty_claim.
> - Otherwise use the route that matches the main request.

**The "when unsure" rule**, in full:

> When unsure: set safety to true if the message could describe fire, smoke, burning, sparks,
> scorching, an electric shock or an injury, even if the customer plays it down; set product to
> null unless one Halvard product is clearly what the request is about; set fault to null unless
> the customer describes a fault; and choose the route by the precedence rules, not by the
> customer's tone.

**Worked example** (`A-test-00410`, invented): "Is it normal for the stainless steel body to get
very hot to the touch while it is boiling?" The one-line prompt flags it as a safety incident.
All three rungs mark it `safety: false`, `how_to_use`, Brio kettle, no fault: fully right.

**How the best prompt was chosen:** on the 200 dev messages, before any test call. Dev: one-line
170, definitions 199, policy 197, unsure 197. Definitions led, so it is E2's best prompt.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 521, 587, 590, 596 of 600 | Fully right: one-line, definitions, policy, unsure | `analysis-task-a-test.json`, `arms.*.fully_right` |
| 68, 3, 1, 1 of 535 | Harmless messages flagged as incidents, same order | same, `safety_false_alarms` |
| 65 of 65, every arm | Safety incidents flagged | same, `safety_recall` |
| 73 and 7 | Items definitions fixed and broke against one-line | same, `comparisons.e2-definitions` |
| Below 0.0001 | Holm-corrected exact McNemar p, each rung against one-line | same, `comparisons.*.p_holm` |
| 6 to 40 of 40 | Questions about safe use, fully right, one-line to definitions | same, `fully_right_by_kind.safe_use_question` |
| 600 of 600 | Routes right with the "when unsure" rule | same, `e2-unsure.field_accuracy.route` |
| 199 of 200 | Definitions on dev, which chose it | `analysis-task-a-dev.json` |

## Cost

Ratios to the one-line prompt, answer calls only.

| Arm | Prompt length | Billed per item | Billed per fully right item |
|---|---|---|---|
| + definitions | 3.1 times | 2.44 times | 2.16 times |
| + policy | 3.6 times | 2.81 times | 2.48 times |
| + when unsure | 3.9 times | 0.78 times | 0.68 times |

**Explain caching before showing the third row.** The provider charges much less for the part of
a prompt it has seen recently. The "when unsure" prompt had about 90% of its input billed at the
cached rate in this run; the others had none. Prompt length is the fair comparison; billed cost
is one run's outcome.

**The cost of wrong answers** (extrapolation from invented figures): on Halvard's invented 45,000
contacts a month, the one-line prompt's false alarm rate would send the safety team of 6 several
thousand harmless messages a month; the definitions prompt's rate, about 250. Two and a half
times the prompt cost buys back most of a safety team's month.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Refresher: E1's floor.** One line and a pointer: 521 of 600, 68 false alarms.
2. **A new colleague's first day.** What you would hand them: definitions, routing rules, what
   to do when unsure. That is the experiment.
3. **The ladder of prompts.** A stacked diagram, each block one addition, with its token count.
4. **The kettle message, arm by arm.** One-line: safety true. With definitions: safety false.
   Show the sentence of the definition that changed the answer.
5. **Prediction.** "How many of the 68 false alarms do the definitions remove?" Reader picks.
6. **Reveal.** 68 to 3, as two grids of 535 squares.
7. **And the incidents?** 65 of 65 caught in every arm. The fix did not trade one error for the
   other.
8. **The full ladder.** 521, 587, 590, 596 with intervals, as a bar chart.
9. **Flips, not totals.** Definitions fixed 73 items and broke 7: a two-way arrow diagram.
10. **Why the highest bar is not the winner.** The choice was made on dev, before test; on test
    the three intervals overlap.
11. **Refresher: caching,** then the cost table.
12. **Scoreboard:** definitions joins.
13. **Series map** (last slide), E2 marked.

## For leaders

**Ask your team:** "Have we written down for the model what we would tell a new member of staff?"

## Decision rule (proposed)

**"Write down the definitions a new colleague would need, and give them to the model. Measure
before adding anything else."**

## Next

E3, How many examples?: can worked examples do what the definitions did, and what does each one
cost on every call?

## Careful with

- **The definitions are the labeller's own rules,** used to build and check the labels. A real
  team's notes would match its labels less closely, so expect a smaller gain in practice.
- **`e2-unsure` scored highest on test (596) and is not the winner.** Say why: choices are made on
  dev, and test cannot separate the three.
- **The order of rungs is fixed.** E2 cannot say what the policy or the "when unsure" rule would
  do without the definitions.
- **Cost ratios depend on caching,** so do not present the 0.78 as "longer prompts are cheaper".
- **One model, one wording.** Every figure covers these Halvard tasks and this model only.

## From practice

_Brendan to add one anonymised line from his own practice._
