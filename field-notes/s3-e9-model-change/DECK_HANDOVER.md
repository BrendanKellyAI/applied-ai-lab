# S3 E9 deck handover: Does it survive a model change? (field note)

For the content agent. Has an experiment: a short field-note deck in the Season 2 field note
format. Act 3, "Decide what to own".

## Sources of truth

`field-notes/s3-e9-model-change/README.md`, `results/2026-10/analysis.json`,
`PREREGISTRATION.md`. Charts in `results/2026-10/charts/`: `churn-slide.svg`,
`citing-slide.svg`. Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E9 |
| Title | Field note: does it survive a model change? |
| Hub slug | `does-it-survive-a-model-change` (proposed; confirm) |
| Hub format | `field_note` |
| Folder | `field-notes/s3-e9-model-change` |
| Deck file | `bk-s3-e9-does-it-survive-a-model-change-v1.pdf` |

## The argument

Your provider updates the model, or you switch provider to save money. The system around the
model stays the same. Does it still work? Measured on the 520 questions, the total says yes: the
update left it exactly where it was. Item by item, 18 answers changed between right and wrong.
Switching to another provider's cheapest tier changed 25 answers for a net loss of 5, and made
answers four times as long. The format held; the content and behaviour shifted under a steady
total.

## Case recap slide

None: field notes carry no scorecard column. Optionally one line back to E8: "keep the model
swappable" means being able to measure a swap like this in a day.

## Evidence

| Figure | What it measures | Out of | Source |
|---|---|---|---|
| 461 and 461 | Items handled right before and after the version update | 520 | `analysis.json`, `measures.*.handled` |
| 18 (9 each way) | Items that flipped with the version update | 520 | `changes.version.handled` |
| 456, 25 flipped | The switch to `claude-haiku-5-5`: handled right, items flipped (15 lost, 10 gained) | 520 | `changes.provider.handled` |
| 436, 41 flipped | The switch to `gemini-3.5-flash-lite` (33 lost, 8 gained) | 520 | `changes.provider-google.handled` |
| 365 of 365, 363 of 363 | Non-decline answers with a parseable citation, baseline and Anthropic | answers | `measures.*.citing` |
| 28 against 126 | Median output tokens, baseline against Anthropic | tokens | `measures.*.median_output_tokens` |
| 91% against 71% | Citations holding the evidence, baseline (365 of 400) against Anthropic (375 of 525) | citations | `measures.*.citation_validity` |
| 2.1x, 1.8x, 3.4x | Cost per item handled right against the baseline | ratio | `cost_per_item_handled_ratio` |

## Slide ideas

1. Open with a notice: "Your provider has updated the model." Ask the reader: did our results
   change? Predict.
2. Reveal on the next slide: 461 before, 461 after. Then turn the page: 18 answers changed.
3. Step one flipped question through before any statistics: the same question, the same
   passages, right before and wrong after (pick an item from `results/2026-10/version/log.jsonl`
   that is right in one arm and wrong in the other).
4. The churn chart (`churn-slide.svg`): change in the total against items that flipped, for all
   three swaps.
5. Three kinds of break as a three-column grid: content (flips), format (held: citations and
   "not found" wording), behaviour (length, citations, cost).
6. The behaviour slide: 28 against 126 median tokens; more citations, fewer holding evidence.
7. What to do: rerun your own test set before accepting any model change, and read the flipped
   items.
8. For leaders, decision rule, next, then the series map.

## For leaders

**Ask your team:** "If our provider changed the model tomorrow, how would we know which answers
changed?"

## Decision rule (from the result)

**"Treat a model change as a release: rerun your own test set and compare answers question by
question, because a steady total can hide changed answers."**

## Next

S3 E10, The one-page AI strategy: put it all in front of the board on one page.

## Careful with

- **The reranker was held fixed.** Real swaps often change it too.
- **The Google arm had a different judge**, which marked 2 in 100 fewer items right on a shared
  sample; part of its gap may be the judge. It had no pre-registered claim.
- **The version arm is read backwards** (older model as "before").
- **No arm failed outright**: no errors, refusals or broken formats. The point is quiet change,
  not breakage.
- Managed versus direct access was not tested (decided before the run). Costs belong to S6.
- Prices are never shown: ratios only.

## From practice

_Brendan to add one anonymised line from his own practice._
