# S3 E3 deck handover: Does the leaderboard predict your task? (field note)

For the content agent. Has an experiment: a short field-note deck in the Season 2 field note
format. Act 1, "Choose the work"; publishes in week one.

## Sources of truth

`field-notes/s3-e3-leaderboard/README.md`, `results/2026-10/analysis.json`,
`leaderboard.yaml`, `PREREGISTRATION.md`, `results/2026-10/judge-agreement/report.json`. Charts
in `results/2026-10/charts/`: `order-slide.svg`, `handled-slide.svg`, `cost-slide.svg`. Branch
`s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E3 |
| Title | Field note: does the leaderboard predict your task? |
| Hub slug | `does-the-leaderboard-predict-your-task` (proposed; confirm) |
| Hub format | `field_note` |
| Folder | `field-notes/s3-e3-leaderboard` |
| Deck file | `bk-s3-e3-does-the-leaderboard-predict-your-task-v1.pdf` |

## The argument

A public leaderboard ranks models on general tests. Halvard's work is narrower: answer a
customer's question from the right passages and cite them. Eight models from three providers,
spread from 18 to 42 points on the board, each ran Halvard's 520 test questions through the
same system. Five of them, from the bottom of the board to the top, handled 457 to 465 right and
cannot be told apart. The cheapest tied the board's leaders. The board is a shortlist, not a
verdict on your task.

## Case recap slide

None: field notes carry no scorecard column. Optionally one line back to E2: task fit is about
your task, and this is how you measure it.

## Evidence

| Figure | What it measures | Out of | Source |
|---|---|---|---|
| 18 to 42 | Board scores of the eight models, at the settings named | index points | `leaderboard.yaml` |
| 457 to 465 | Items handled right by the five models in the top tier | 520 | `analysis.json`, `models.*.handled` |
| 461 and 462 | `gpt-6-luna` (board 18) against `gpt-6.1-sol` (board 42) | 520 | same |
| 434 to 444 | The second tier: `claude-haiku-5-5` and the two Gemini models | 520 | same |
| 0.22 | Kendall's tau-b between the two orders; 95% interval minus 0.07 to 0.47 | 8 models | `kendall_tau_b` |
| 21x and 84x | Cost per item handled right of `gpt-6.1-sol` and `claude-opus-5-5`, against `gpt-6-luna` | ratio | `cost_per_item_handled_ratio` |
| 15 points up, 27 items down | `gemini-3.8-flash` against `gpt-6-luna` | 520 | `claims` B4 |
| 97, 96, 99 | Items on which the two judges agreed on declines, correctness and faithfulness | 100 | `judge-agreement/report.json` |
| 318 against 28 | Median output tokens, `claude-opus-5-5` against `gpt-6-luna` | tokens | `models.*.median_output_tokens` |

## Slide ideas

1. Open with a leaderboard screenshot replaced by a plain table of the eight scores (numbers
   only, no screenshot): "Which would you pick?" Ask the reader to predict the winner on
   Halvard's questions.
2. Step one question through two models before any statistics: the same warranty question, its
   passages, `gpt-6-luna`'s short cited answer and `claude-opus-5-5`'s long one, both right.
3. Reveal on the next slide: the slope chart (`order-slide.svg`), board order left, Halvard order
   right, with the cheapest model's line highlighted.
4. Ties are real: the five-model top tier as a bracket over the intervals (`handled-slide.svg`).
   One line of explanation of "cannot be told apart".
5. Price per item handled right (`cost-slide.svg`): 1x to 84x for the same tier.
6. What totals hide: answer length and citations (318 against 28 median tokens).
7. "Why not trust the board?" The board tests general reasoning at its own settings; this task
   is reading and citing. Your test set measures your task (pointer to S8 for building one).
8. For leaders, decision rule, next, then the series map.

## For leaders

**Ask your team:** "Which model would win on our own questions, and have we tested it?"

## Decision rule (from the result)

**"Use a leaderboard to shortlist models, then choose on a test set of your own questions: on
ours, the cheapest model tied the board's leaders at a fraction of the cost."**

## Next

S3 E4, The cost of being wrong: price the error before you choose the use case.

## Careful with

- **One task.** Do not say "leaderboards are wrong". The claim is that this board's order did
  not predict this task's order.
- **Two judges.** The two Gemini models were judged by `claude-sonnet-5-5`, which on a shared
  sample marked 2 in 100 fewer items right. Their lower tier is partly, not wholly, explained by
  that; show this caveat on the slide that shows them.
- **Lowest reasoning settings only**; the board's highest rows were not run.
- **Supporting context, not a result of this note:** S2 E12 found a larger embedding model gave
  17 fewer right answers out of 400.
- **Prices are never shown**: ratios only. Building your own evaluation belongs to S8.

## From practice

_Brendan to add one anonymised line from his own practice._
