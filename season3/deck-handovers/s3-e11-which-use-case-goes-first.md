# S3 E11 deck handover: Which use case goes first?

For the content agent. No experiment: a teaching deck that adds the last criterion, time to evidence, then the weighted totals, the first pick, the sensitivity check and the stop criteria. It is the end of the season's case.

## Sources of truth

- `season3/case/rule.yaml` (the weights, the Time to evidence anchors, the sensitivity weightings and the list of stop criteria).
- `season3/case/scores.yaml` (every score with its evidence or assumption, and the `stop_criteria` block for the first pick).
- `season3/case/results/scorecard-e11.json` (the scorecard through E11, with totals and ranks) and `season3/case/results/scorecard.json`.
- `season3/case/results/sensitivity.json` (the pick under each of the 15 alternative weightings).
- `season3/case/PREREGISTRATION.md` (what was fixed before scoring; the "fragile if under 12 of 15" mark; Amendment 1).
- Charts in `season3/case/results/charts/`: `scorecard-e11-slide.svg`, `scorecard-final-slide.svg`, `sensitivity-slide.svg`.
- `season3/case/halvard-home.md` (the CEO's ask).
- `season3/halvard-one-page.md` (section 7, the first move, which this episode completes).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E11 |
| Title | Which use case goes first? |
| Hub slug | `which-use-case-goes-first` (proposed; confirm) |
| Deck file | `bk-s3-e11-which-use-case-goes-first-v1.pdf` |
| Hub format | `decision_framework` |

## The argument

Choose the first use case by a rule fixed before any score was written, then check how much the choice depends on the weights, and write down what would stop the pilot before it starts.

1. **Time to evidence is the last criterion.** A first use case must prove itself quickly: can a pilot show the outcome moving within a quarter? Anchors in `rule.yaml`: 1 means no result within a year, 3 means within two quarters, 5 means within a quarter or testable on past data now.
2. **The totals.** Weights fixed in advance (value 0.25, task fit 0.15, error tolerance 0.20, data readiness 0.15, durable advantage 0.10, time to evidence 0.15) give a total on the same 1 to 5 scale as a score, for the six candidates that passed both gates. C5 and C8 failed Gate 2 (a language model is not the right tool) and have no total.
3. **The first pick is C6, the library consistency check, at 4.20 of 5.** C2, reply drafts for agents, is second at 4.15 of 5.
4. **The pick is fragile.** It stays first in 9 of 15 alternative weightings. C2 is first in the other 6. The rule fixed in advance (`PREREGISTRATION.md`) calls a pick fragile if it holds in fewer than 12 of 15 (80%). This is a finding, not a failure: the top two are close, and the choice between them depends on what the board values most.
5. **Stop criteria, written before the pilot.** Success metric, threshold, time box, stop condition and reviewer. The stop condition names C2 as the fallback, because the pick is fragile.
6. **Where the CEO's headline ended up.** "We need an AI assistant on the website by spring" is C1. It scores 3.70 of 5 and ranks third.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e11-slide.svg` (from `lab strategy reveal --through E11`). Then `scorecard-final-slide.svg` (the final heat table) and `sensitivity-slide.svg` (the pick under each of the 15 alternative weightings).

New column this episode adds: **Time to evidence** (a score, 1 to 5), and **Weighted total and rank**.

| Rank | Candidate | Total (of 5) | Time to evidence (of 5) | Error tolerance (of 5) |
|---|---|---|---|---|
| 1 | C6 Library consistency check | 4.20 | 5 | 5 |
| 2 | C2 Reply drafts for agents | 4.15 | 5 | 3 |
| 3 | C1 Website assistant | 3.70 | 3 | 1 |
| 4 | C3 Warranty claim triage | 3.35 | 5 | 3 |
| 5 | C4 Safety signal screening | 3.20 | 2 | 3 |
| 6 | C7 Call and chat summaries | 3.00 | 5 | 3 |
| not ranked | C5 Automatic refund approval | none | not scored (failed Gate 2) | not scored |
| not ranked | C8 Spare parts demand forecast | none | not scored (failed Gate 2) | not scored |

Earlier columns carry forward from `scorecard-e11.json`. C5 and C8 stay on the portfolio with their redirects (rules over the order records; a forecasting model or a planning product) but cannot go first.

Measured versus assumed: only C1 and C2 have measured accuracy (the Season 2 final system). **Every other score, and every Time to evidence score, is an assumption** with a one-line reason in `scores.yaml`, except C6's time to evidence, which cites the known contradictions already found in Season 2 E14. The weights and the 15 alternatives are case design choices fixed in advance, not measurements.

### Sensitivity: which weightings keep C6 and which flip it

From `sensitivity.json` (15 alternative weightings; each is rescaled to sum to 1).

**C6 stays first (9 of 15):**

| Weighting | C6 total | Nearest rival |
|---|---|---|
| Equal weights | 4.33 | C2 4.17 |
| Value halved | 4.37 | C2 4.17 |
| Task fit halved | 4.22 | C2 4.08 |
| Data readiness halved | 4.22 | C2 4.08 |
| Time to evidence halved | 4.14 | C2 4.08 |
| Error tolerance doubled | 4.33 | C2 3.96 |
| Durable advantage doubled | 4.27 | C2 4.05 |
| Time to evidence doubled | 4.30 | C2 4.26 |
| Regulator weighting (error tolerance 0.40) | 4.45 | C2 3.95 |

**C2 goes first (6 of 15):**

| Weighting | C2 total | C6 total |
|---|---|---|
| Error tolerance halved | 4.28 | 4.11 |
| Durable advantage halved | 4.21 | 4.16 |
| Value doubled | 4.12 | 3.96 (C1 also 3.96) |
| Task fit doubled | 4.26 | 4.17 |
| Data readiness doubled | 4.26 | 4.17 |
| CEO weighting (value 0.40, time to evidence 0.20) | 4.20 | 4.00 (C1 also 4.00) |

Totals are rounded to two decimals from `sensitivity.json`. The regulator weighting keeps C6; the CEO weighting moves the pick to C2, and C2 wins the weightings that count value, task fit and data readiness more, or error tolerance and durable advantage less. In no weighting is C1 first: at best it ties with C6 for second.

## Stop criteria for the first pick

From the `stop_criteria` block of `scores.yaml` (written 18 October 2026, before the fictional pilot starts):

| Part | Halvard's C6 pilot |
|---|---|
| Success metric | Contradictions found between support articles and current policies, confirmed by the content team, and the share of the 300 articles checked that are consistent |
| Threshold | Finds every contradiction already known from Season 2 E14 (the Mira robot vacuum, the Fenwick cooker hood and the Vale fridge freezer), and at least half of its flags are confirmed by an editor |
| Time box | Six weeks from the first run over the library |
| Stop condition | Stop if it misses any known contradiction after one round of changes to its instructions, or if fewer than 1 in 4 flags are confirmed; then move to C2, reply drafts for agents |
| Reviewer | Content team lead, reporting to the head of customer operations |

This completes section 7 of the one-page strategy: the first move is C6, with this stop condition and C2 as the fallback.

## Where the CEO's headline ended up

The CEO's ask is C1, the website assistant. It ranks third, 3.70 of 5, in the rule's own terms:

- **Error tolerance 1 of 5.** A wrong answer is a regulatory error that reaches customers with nobody catching it, and C1 is proposed at automate where the autonomy table allows assist only. The measured Season 2 system answered 46 of 400 answerable questions wrongly and answered 13 of 120 unanswerable questions anyway.
- **Time to evidence 3 of 5.** Showing fewer agent contacts with no repeat contact needs live customer traffic and a launch review: about two quarters, an assumption.
- **Value 5 and task fit 5 are not enough.** C1 has the highest value score (5, an assumption: about 9,000 questions a month and the CEO's own ask), but its error tolerance of 1 costs it against C2, which is the same measured system with an agent reading every draft first.

C1 is not rejected. It sits in "Later" in Halvard's page: only once it can run with review, after reply drafts for agents.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 4.20 of 5 | C6's weighted total (six criteria, weights fixed in advance) | `season3/case/results/scorecard-e11.json` | Computed from scores |
| 4.15 of 5 | C2's weighted total | same | Computed from scores |
| 3.70, 3.35, 3.20, 3.00 of 5 | Totals for C1, C3, C4 and C7 | same | Computed from scores |
| 9 of 15 | Alternative weightings in which C6 stays first; C2 is first in the other 6 | `season3/case/results/sensitivity.json` | Computed |
| 12 of 15 | The pre-registered mark (80%) below which the pick is called fragile | `season3/case/PREREGISTRATION.md` | Case design |
| 46 of 400 | Answerable questions the Season 2 final system answered wrongly | `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` | Measured |
| 13 of 120 | Unanswerable questions the same system answered anyway | same | Measured |
| 3 of 5 | Failures with the right passage in the prompt that came from an article and a policy that disagree (the Mira robot vacuum, Fenwick cooker hood, Vale fridge freezer) | `episodes/s2-e14-tracing/README.md` | Measured |
| 1 in 4 | Share of flags confirmed below which the pilot stops | `season3/case/scores.yaml` | Case design |

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **One last question.** "Time to evidence": a pilot that cannot show the outcome moving in a quarter loses momentum. One sentence and the three anchors as a short ladder.
2. **One candidate, scored by hand.** Step C6 all the way through, one criterion at a time, with the weights shown: value 3, task fit 4, error tolerance 5, data readiness 4, durable advantage 5, time to evidence 5. Show the multiplication and the total, 4.20 of 5, before any other candidate.
3. **Prediction.** "The CEO's website assistant scored highest on value. Where did it finish of the six scored?" Reader picks a rank.
4. **Reveal.** Third, 3.70 of 5. Show `scorecard-e11-slide.svg`.
5. **Why third.** Two cells highlighted in the C1 row: error tolerance 1 (a regulatory error reaches customers and nobody catches it), time to evidence 3. A short sentence each, in the rule's own terms.
6. **The final table.** `scorecard-final-slide.svg`: ranks 1 to 6, with C5 and C8 shown as redirected, not ranked.
7. **Prediction.** "If the weights change, does the first pick change?" Reader picks: never, sometimes or often.
8. **Reveal.** `sensitivity-slide.svg`: C6 first in 9 of 15 weightings, C2 in the other 6. Two named weightings shown large: the CEO weighting (C2) and the regulator weighting (C6).
9. **Fragile is a finding.** One slide on the pre-registered mark (12 of 15) and the sentence: the top two are close, and the choice depends on what the board values most.
10. **Both lead to the same place.** C6 cleans the library; C2 reads from the library. The two picks are in order, not in competition.
11. **Write the stop first.** A five-row form filled in for the C6 pilot: success metric, threshold, time box, stop condition, reviewer.
12. **Prediction.** "What happens if the checker misses a known contradiction after one round of changes?" Reader picks: continue, tune, or stop.
13. **Reveal.** Stop, and move to C2. The fallback was written before the pilot started.
14. **Section 7, filled.** The one-page strategy's first move, now complete: C6, why it goes first, what the next quarter holds. Link back to E10.
15. **Series map** (last slide), Season 3 highlighted, E11 marked.

## For leaders

**Ask your team:** "What result would make us stop this pilot, and have we written it down?"

## Decision rule (proposed)

**"Start with the use case that scores best under rules fixed in advance, and write the stop condition before the pilot starts."**

## Next

E12, Season 3 recap: the strategy card. Every rule and question from the season on one card, and the case from first column to first pick.

## Careful with

- **The pick is fragile, and the deck must say so.** C6 holds in 9 of 15 alternative weightings, below the pre-registered mark of 12 of 15. Say it as a finding, not a failure. Do not present C6 as "the answer".
- **Every score except C1's and C2's accuracy is an assumption.** The two measured figures are the Season 2 final system's results (354 of 400 right, 46 of 400 wrong, 13 of 120 unanswered questions answered anyway). The other totals rest on stated assumptions, and a different assumption could move the order.
- **Halvard Home is invented**, including its volumes (for example about 9,000 contacts a month). No legal claims beyond "consumer protection, product safety and data protection law".
- **The weights were fixed before scoring, but they are a judgement.** Do not say they are objective. Do not say the CEO was wrong: the CEO weighting picks C2, and C1 is placed in "Later", not dropped.
- **The stop criteria are for a fictional pilot.** No pilot was run; do not report a result.
- **Time to evidence for C6 is the only one with a cited source** (the known contradictions from Season 2 E14); the others are assumptions.
- **Boundaries.** Rollout and adoption belong to S12; policy and controls to S15; people and operating model to S9; costs to S6. This deck chooses and sets the stop; it does not plan the pilot's delivery.

## From practice

_Brendan to add one anonymised line from his own practice._
