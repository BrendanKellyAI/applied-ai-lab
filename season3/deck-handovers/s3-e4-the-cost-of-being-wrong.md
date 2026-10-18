# S3 E4 deck handover: The cost of being wrong

For the content agent. No experiment: a teaching deck that adds the Error tolerance score, backed by the Season 2 measurements of how the support system fails.

## Sources of truth

- `season3/case/rule.yaml` (Error tolerance anchors and the error cost and "caught by" definitions).
- `season3/case/candidates.yaml` (each candidate's error cost, who catches it, and what a wrong output causes).
- `season3/case/scores.yaml` and `season3/case/results/scorecard-e4.json`; chart `season3/case/results/charts/scorecard-e4-slide.svg`.
- `season2/scoreboard.json` (leaks and answers by stage).
- `episodes/s2-e8-filters/README.md` (the filter that stopped the leaks).
- `episodes/s2-e10-grounding-and-citations/README.md` (declining when the answer is not there).
- `episodes/s2-e14-tracing/README.md` (the 46 wrong answers traced).
- `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` (the final system's figures).
- `episodes/s1-e9-hallucination/README.md` (S1 E9).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E4 |
| Title | The cost of being wrong |
| Hub slug | `the-cost-of-being-wrong` (proposed; confirm) |
| Deck file | `bk-s3-e4-the-cost-of-being-wrong-v1.pdf` |
| Hub format | `explainer` |

## The argument

Every AI output is sometimes wrong. The decision is not "is it accurate?" but **"what does a wrong answer cost, and who catches it?"** Price that before building, including errors that touch regulation.

Two measured facts from Season 2 make the point:

1. **A leak is a design error, not a model error.** The naive system put a staff-only passage into 51 of 480 public prompts. A better model would not have fixed it. The fix was a filter on each document's metadata, applied before ranking (S2 E8).
2. **A good system is still wrong some of the time.** The final system answered 46 of 400 answerable questions wrongly, and answered 13 of 120 unanswerable questions anyway instead of declining.

Apply it to candidate 1, the website assistant: a wrong warranty or safety answer goes straight to a customer, with no person in between. For Halvard the worst errors touch product safety and consumer protection law, so they are design constraints, not risks to accept.

The episode's new column is **Error tolerance at the chosen autonomy**, 1 to 5. A regulatory error that nobody catches scores 1. A cheap error that a person sees before it reaches anyone scores 5. (Autonomy itself is introduced in E5; this episode scores each candidate at the autonomy it was proposed at and shows error cost and who catches it.)

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e4-slide.svg` (from `lab strategy reveal --through E4`).

New column this episode adds: **Error tolerance at the chosen autonomy**, with each candidate's error cost and who catches a wrong output.

| Candidate | Error cost | Caught by | Error tolerance |
|---|---|---|---|
| C1 Website assistant | regulatory | nobody | **1** |
| C2 Reply drafts for agents | regulatory | reviewer | 3 |
| C3 Warranty claim triage | high | downstream | 3 |
| C4 Safety signal screening | regulatory | downstream | 3 |
| C5 Automatic refund approval | regulatory | nobody | not scored (failed G2) |
| C6 Library consistency check | low | reviewer | 5 |
| C7 Call and chat summaries | high | downstream | 3 |
| C8 Spare parts demand forecast | high | reviewer | not scored (failed G2) |

Earlier columns carry forward: C5 and C8 failed G2 in E2 and are not scored on the criteria.

Measured versus assumed: C1's score of 1 cites the **measured** Season 2 figures (46 of 400 answerable questions answered wrongly and 13 of 120 unanswerable questions answered anyway, with no person between answer and customer). C2's 3 also uses the measured 46 of 400 as the load the reviewer must catch. Every other Error tolerance score is an **assumption**, with a one-line reason in `scores.yaml`.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 51 of 480 | Public-asker prompts that held a staff-only passage, in the Season 2 naive system | `season2/scoreboard.json` (episode `s2-e2-first-rag-system`, `leaks`) | Measured |
| 64 to 0 of 480 | Public-asker prompts with a staff-only passage, before and after the metadata filter (S2 E8), measured on the system as it stood at E8 | `season2/scoreboard.json`; `episodes/s2-e8-filters/README.md` | Measured |
| 0 of 480 | Public prompts with a staff-only passage in the final system | `season2/scoreboard.json` | Measured |
| 46 of 400 | Answerable questions the final system answered wrongly | `episodes/s2-e14-tracing/README.md` (354 of 400 right, `season2/scoreboard.json`) | Measured |
| 13 of 120 | Unanswerable questions the final system answered anyway (it declined 107 of 120) | `season2/scoreboard.json`; `episodes/s2-e10-grounding-and-citations/README.md` | Measured |
| 9 of those 13 | Answered anyway because the topic is covered but the detail is not in the library (the other 4 ask about restricted documents) | `episodes/s2-e14-tracing/README.md` (claim T3) | Measured |
| About 1 in 9 | The wrong drafts an agent would have to catch, if they used the final system's drafts (46 of 400) | `season3/case/scores.yaml` (C2) | Derived from the measured figure |
| About 40 a month, of 45,000 contacts | Contacts that may describe a fire, smoke or shock incident | `season3/case/halvard-home.md` | Invented |

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **One wrong answer.** Step one example all the way through, with no statistics: a customer asks the website assistant about the warranty on the Mira robot vacuum. The support article and the warranty policy disagree (a two-year warranty from purchase against 40 months from delivery, S2 E14). Walk the answer from the screen to what the customer does next, to the complaint.
2. **Two questions to price an error.** What does it cost? Who catches it? Show them as two stacked boxes. Add the three error costs: low, high, regulatory.
3. **Prediction.** "In Season 2's naive system, how many of 480 public prompts held a staff-only passage?" Reader picks a number.
4. **Reveal.** 51 of 480, as a filled-in grid of 480 squares with 51 highlighted. Then one line: the fix was not a better model but a filter on each document's access label, before ranking (S2 E8), which took the leak from 64 to 0 of 480 at that stage.
5. **A leak is a design choice.** A short diagram of the pipeline with the filter stage highlighted.
6. **Prediction.** "The final system answers 400 answerable questions. How many does it get wrong?" Reader picks.
7. **Reveal.** 46 of 400, and 13 of 120 unanswerable questions answered instead of declined. Show as two paired bars, "right" and "wrong or answered anyway".
8. **Where the 13 come from.** 9 of 13 are details the library does not have, on topics it covers. A small sorted list.
9. **Put it on candidate 1.** A split slide: the same 46 wrong answers, with no person between answer and customer, against a person who reads each draft. Do not give the verdict yet; leave the contrast to E5.
10. **Error tolerance anchors.** The 1, 3 and 5 anchors on a ladder.
11. **The third column.** Reveal `scorecard-e4-slide.svg`, with C1's 1 highlighted and C6's 5.
12. **Regulatory errors are constraints.** One slide: for product safety, consumer protection and data protection law, design so a wrong output cannot reach the customer unreviewed.
13. **Series map** (last slide), Season 3 highlighted, E4 marked.

## For leaders

**Ask your team:** "When this is wrong, who finds out first, us or the customer?"

## Decision rule (proposed)

**"Price the error before the use case: decide who catches a wrong answer and what it costs when they miss. Treat a regulatory error as a design constraint, not a risk to accept."**

## Next

E5, Assist, automate, or act: the same measured system appears as two candidates, and the difference between them is only how much autonomy it gets.

## Careful with

- **The 51 and the 64 are different measurements.** 51 of 480 is the naive system at S2 E2; 64 of 480 is the system after later changes, just before the S2 E8 filter. Say which.
- **The filter fixed leaks; it did not fix wrong answers.** Do not credit it with the 46.
- **The 46 and 13 describe the Season 2 final system on 520 test questions.** They are not a forecast for any other library or model.
- **Only C1 and C2 have measured figures.** Every other Error tolerance score is an assumption; label it.
- **No legal claims.** Describe exposure only as "consumer protection, product safety and data protection law". Nothing here is legal advice.
- **Halvard Home is invented.** Its contact volumes and incident counts are invented.
- **Boundaries.** Policy and controls are S15; people and operating model are S9. Do not draft policy on the slides.

## From practice

_Brendan to add one anonymised line from his own practice._
