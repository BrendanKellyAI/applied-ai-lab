# S3 E12 deck handover: Season 3 recap: the strategy card

For the content agent. No experiment: a recap deck built from the strategy card, the case and
the three field notes. Read the other Season 3 handovers first.

## Sources of truth

- `season3/strategy-card.md`: every decision rule and "Ask your team" question, the final
  scorecard, the first pick and its stop criteria, and what the field notes changed.
- `season3/case/results/scorecard.json`, `sensitivity.json`; charts
  `season3/case/results/charts/scorecard-final-slide.svg`, `sensitivity-slide.svg`, and the
  reveal steps `scorecard-e1-slide.svg` to `scorecard-e11-slide.svg`.
- The field note READMEs: `field-notes/s3-e3-leaderboard/README.md`,
  `field-notes/s3-e7-data-or-model/README.md`, `field-notes/s3-e9-model-change/README.md`.
- `season3/halvard-one-page.md`.

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E12 |
| Title | Season 3 recap: the strategy card |
| Hub slug | `season-3-recap` (proposed; confirm) |
| Deck file | `bk-s3-e12-season-3-recap-v1.pdf` |
| Hub format | `recap` |

## The argument

The season answered one question for one invented firm: of everything Halvard Home could use
AI for, what goes first, and how would it know it worked? It answered it with a rule fixed in
advance, one column per episode, and three experiments on the firm's own questions. The
strategy card is what a reader keeps: eleven rules, eleven questions, and one worked case.

1. **The card.** One rule and one "Ask your team" question per episode (E1 to E11).
2. **The case, first column to first pick.** Eight candidates; two redirected at G2 (refund
   approval is a rule over records, parts demand is a forecast); the CEO's website assistant
   third, because it would answer customers on warranty, refunds and safety with nobody
   checking (error tolerance 1 of 5); the library consistency check (C6) first at 4.20 of 5,
   reply drafts for agents (C2) second at 4.15. Fragile: C6 holds in 9 of 15 other weightings,
   and C2 wins the rest. Both point to the same order: clean the library, then help the agents.
3. **What the field notes changed.**
   - E3: the board's order did not predict Halvard's; the cheapest model tied the leaders.
   - E7: data work beat the bigger model, 461 against 303 of 520.
   - E9: a model update left the total flat and changed 18 answers.
   Together: spend on your own data and your own test set, not on the top of a leaderboard.

## Case recap slide

The final scorecard: `scorecard-final-slide.svg` (from `lab strategy case`), with the first
pick's total highlighted. Optionally a strip of the seven reveal steps as small multiples
(`scorecard-e1` to `scorecard-e11`), showing the card filling in one column at a time.

## Evidence

| Figure | What it measures | Out of | Source |
|---|---|---|---|
| 4.20 and 4.15 | Weighted totals of C6 and C2 | 5 | `case/results/scorecard.json` |
| 9 of 15 | Alternative weightings in which C6 stays first | 15 | `case/results/sensitivity.json` |
| 1 | C1's error tolerance score (anchor: a regulatory error reaches customers and nobody catches it) | 5 | `case/scores.yaml` |
| 354 and 107 | The measured system behind C1 and C2: right answers, correct declines | 400 and 120 | `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` |
| 457 to 465 | E3: items handled right by the five indistinguishable top models (board 18 to 42) | 520 | `field-notes/s3-e3-leaderboard/README.md` |
| 461 against 303 | E7: small model on the final system against large model on the naive one | 520 | `field-notes/s3-e7-data-or-model/README.md` |
| 18 | E9: answers that changed when the total did not | 520 | `field-notes/s3-e9-model-change/README.md` |

Mark which case scores are measured and which are assumptions: only C1 and C2 have measured
accuracy.

## Slide ideas

1. The CEO's sentence from E0: "We need an AI assistant on the website by spring." Ask the
   reader where they think it ended up.
2. Reveal: third, and why, in one line of the rule's own words.
3. The scorecard filling in, column by column (small multiples of the reveal steps).
4. The final scorecard with C6 highlighted; then the sensitivity chart: fragile, and why that is
   a finding.
5. Three field notes as three single-number slides (465 to 457 tie; 461 against 303; 18
   changed answers), each with its one-line lesson.
6. The strategy card itself: eleven rules on one slide, readable as a printout.
7. The three tools: scorecard template, one-page template, the card.
8. Where the series goes next (below), then the series map as the last slide.

## For leaders

**Ask your team:** "Which three of these eleven questions could we not answer today?"

## Decision rule (proposed)

**"Fix the rule before you score, start with the use case the rule picks, and write down when
you would stop."**

## Next

Season 4. Hand-offs from this season: money (costs, total cost of ownership, self-hosting
break-even) to S6; preparing data to S7; building your own evaluations to S8; teams and the
operating model to S9; rollout and adoption to S12; policy and controls to S15.

## Careful with

- **Halvard Home is invented**, and every score except C1's and C2's accuracy rests on stated
  assumptions. The method is the lesson, not Halvard's answer.
- **The pick is fragile**; do not present C6 as obvious.
- **Field notes cover one task, one system, one date** (October 2026).
- No legal claims beyond consumer protection, product safety and data protection law. Prices
  are never shown: ratios only.

## From practice

_Brendan to add one anonymised line from his own practice._
