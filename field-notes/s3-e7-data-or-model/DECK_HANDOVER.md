# S3 E7 deck handover: Better data or a bigger model? (field note)

For the content agent. Has an experiment: a short field-note deck in the Season 2 field note
format. Act 3, "Decide what to own".

## Sources of truth

`field-notes/s3-e7-data-or-model/README.md`, `results/analysis.json`, `PREREGISTRATION.md`,
charts in `results/charts/` (`grid-slide.svg`, `leaks-slide.svg`). Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E7 |
| Title | Field note: better data or a bigger model? |
| Hub slug | `better-data-or-a-bigger-model` (proposed; confirm) |
| Hub format | `field_note` |
| Folder | `field-notes/s3-e7-data-or-model` |
| Deck file | `bk-s3-e7-better-data-or-a-bigger-model-v1.pdf` |

The title rule was fixed before the run (see the README): data work alone gave 63% of the
system's gain, above the half the rule needed, so the title stays. On the slide, define "better
data" as section structure and document metadata (access and version labels).

## The argument

A bigger model without retrieval knows nothing about Halvard Home, so the fair contest is: spend
on your own system, or spend on a bigger model, on the same 520 questions. Three versions of the
Season 2 system (naive, data fixes, final) crossed with a small and a large model from the same
provider. The small model on the final system handled 461 of 520 right; the large model on the
naive system, 303. Data work alone moved the small model from 295 to 399. On the final system
the large model, at 20 times the price per token, added 1 item.

## Case recap slide

None: field notes carry no scorecard column. Optionally, one line linking to E6: this is the
evidence behind the durable advantage column (your data and its structure are what a competitor
with the same model does not have).

## Evidence

| Figure | What it measures | Out of | Source |
|---|---|---|---|
| 303 | Items handled right, large model on the naive system (P0) | 520 | `results/analysis.json`, `cells.p0-large.handled` |
| 461 | Items handled right, small model on the final system (P2) | 520 | `cells.p2-small.handled` |
| 295 to 399 | Small model, naive system to data fixes (P1) | 520 | `cells.p0-small`, `cells.p1-small` |
| 242, 319, 354 | Right answers, small model on P0, P1, P2 | 400 answerable | `cells.*.answer` |
| 53, 80, 107 | Correct declines, small model on P0, P1, P2 | 120 unanswerable | `cells.*.not_found` |
| 51 to 0 | Public questions with a staff-only passage in the prompt, P0 to P1, both models | 480 public | `cells.*.leaks` |
| +8, +20, +1 | Large model's gain over small, P0, P1, P2 | 520 | `claims` D3 |
| 21x and 30x | Large model's cost per item handled right on P0 and P2, against the cheapest cell | ratio | `cost_per_item_handled_ratio` |
| 20x | Large model's price per token against the small one's (published prices, 18 October 2026) | ratio | `PREREGISTRATION.md` |

## Slide ideas

1. Open with the question as a bet: you have budget for one thing, a bigger model or work on
   your documents. Which wins? Ask the reader to predict.
2. Step one question through all three pipelines with the small model: the same warranty
   question gets a wrong passage on P0, the right section on P1, the right section cited on P2.
   (Pick an item from `results/p0-small/log.jsonl` that is wrong on P0 and right on P1.)
3. Reveal the prediction on the next slide: the 2 by 3 grid (`grid-slide.svg`), with P2 small
   highlighted.
4. A slope or arrow diagram: 295 to 399 (data) to 461 (retrieval and prompt), against 295 to 303
   (bigger model on P0).
5. Leaks as a separate, structural point (`leaks-slide.svg`): a bigger model cannot remove a
   staff-only passage it has already been given.
6. Price: 20 times the price per token for 1 more item on the final system.
7. For leaders slide, decision rule slide, next slide, then the series map.

Keep statistics light: one line that the paired test separates P2 small from P0 large, and that
P2 small and P2 large cannot be told apart.

## For leaders

**Ask your team:** "Before we pay for a bigger model, what would the same money do to our
documents and retrieval?"

## Decision rule (from the result)

**"Fix your documents and retrieval before you buy a bigger model: on our test, structure and
metadata gave more than the bigger model did, at a twentieth of the price per token."**

## Next

S3 E8, Build, buy, or managed: own the layer that sets you apart, rent the rest, and keep the
model swappable.

## Careful with

- One task, one provider's two sizes, one point in time (18 October 2026). Do not say "bigger
  models do not help" in general; on P1 the large model added 20 items.
- The large model ran with low reasoning, the small with none.
- Leaks being equal across models is by construction, not a finding.
- "Better data" here is structure and metadata, not cleaning contradictions (S2 E14) and not new
  data; how to prepare data belongs to S7.
- Prices are never shown: ratios only.

## From practice

_Brendan to add one anonymised line from his own practice._
