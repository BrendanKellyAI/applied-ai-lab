# S3 E5 deck handover: Assist, automate, or act

For the content agent. No experiment: a teaching deck that adds autonomy as a setting, built around the season's central contrast, backed by Season 2's measurements of the same system.

## Sources of truth

- `season3/case/rule.yaml` (the autonomy levels, error costs, "caught by" values and the autonomy table).
- `season3/case/candidates.yaml` (each candidate's design autonomy, error cost, who catches it, and whether a wrong output can be undone).
- `season3/case/scores.yaml` and `season3/case/results/scorecard-e5.json`; chart `season3/case/results/charts/scorecard-e5-slide.svg`.
- `season2/scoreboard.json`, `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` (the measured system behind C1 and C2).
- `episodes/s2-e10-grounding-and-citations/README.md` (declining and citing).
- `episodes/s2-e14-tracing/README.md` (where the remaining wrong answers come from).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E5 |
| Title | Assist, automate, or act |
| Hub slug | `assist-automate-or-act` (proposed; confirm) |
| Deck file | `bk-s3-e5-assist-automate-or-act-v1.pdf` |
| Hub format | `explainer` |

## The argument

Autonomy is a **setting**, not a score. It follows the cost of an error and who catches it (E4):

- **Assist:** a person reviews every output before it is used.
- **Automate:** outputs go out unreviewed, and a sample is checked.
- **Act:** the system changes a live system itself, such as a payment or an order.

The rule's table gives the highest autonomy allowed. A low-cost error may be automated. A high-cost error that someone downstream catches may be automated; one that nobody catches is assist only. A regulatory error is assist only, always. Act is allowed only where automate is allowed and a wrong output can be fully reversed.

**The season's central contrast.** Candidates 1 and 2 are the same measured system: the Season 2 final system answered 354 of 400 answerable questions right, declined 107 of 120 unanswerable questions, and put a staff passage into none of 480 public prompts. Only the autonomy differs.

- **C1, the website assistant, at automate.** The error cost is regulatory and nobody catches it, so the table allows assist only. C1 is above what the table allows, and it scores **1** on error tolerance.
- **C2, reply drafts for agents, at assist.** The same errors, but an agent reads every draft first. It is within the table and scores **3**.

Same system, same accuracy, different design, different risk.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e5-slide.svg` (from `lab strategy reveal --through E5`). The chart marks designs above the table's limit with an asterisk.

New column this episode adds: **Autonomy** (a setting, not a score): the autonomy each candidate was proposed at, and the highest the table allows.

| Candidate | Proposed at | Table allows | Above the limit? | Error tolerance |
|---|---|---|---|---|
| C1 Website assistant | automate | assist | **yes** | 1 |
| C2 Reply drafts for agents | assist | assist | no | 3 |
| C3 Warranty claim triage | automate | act | no | 3 |
| C4 Safety signal screening | assist | assist | no | 3 |
| C5 Automatic refund approval | act | assist | **yes** | not scored (failed G2) |
| C6 Library consistency check | assist | act | no | 5 |
| C7 Call and chat summaries | automate | act | no | 3 |
| C8 Spare parts demand forecast | assist | assist | no | not scored (failed G2) |

Earlier columns carry forward: C5 and C8 failed G2 in E2 and are not scored on the criteria. C5 is also above the table's limit, which is a second reason it cannot go as designed.

Measured versus assumed: C1 and C2 both rest on the **same measured** Season 2 results. The autonomy table and each candidate's error cost, who catches it and whether it can be undone are **case design choices** recorded in `candidates.yaml`, not measurements. Only C1 and C2 have measured accuracy; every other score is an assumption.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 354 of 400 | Answerable questions answered right by the Season 2 final system (so 46 were wrong) | `season2/scoreboard.json`; `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` | Measured |
| 107 of 120 | Unanswerable questions the final system correctly declined (so 13 were answered anyway) | same | Measured |
| 0 of 480 | Public prompts that held a staff-only passage | same | Measured |
| 83 to 107 of 120 | Correct declines before and after the grounded, citing instruction (S2 E10) | `episodes/s2-e10-grounding-and-citations/README.md` | Measured |
| 365 of 400 | Citations whose cited passage holds the evidence; 35 of 400 do not | same | Measured |
| 343 of 346 | Right answers that cite a passage with the evidence | same | Measured |
| 24 of 39 | Wrong answers lost at ranking where the right passage was below 20th place after search, so the reranker never saw it | `episodes/s2-e14-tracing/README.md` | Measured |
| 33 of 46 | Wrong answers that are follow-up questions (19) or identifier questions (14) | same | Measured |
| 3 of 5 | Failures with the right passage in the prompt that came from a support article and a policy that disagree | same | Measured |
| About 1 in 9 | Wrong drafts an agent must catch (46 of 400) | `season3/case/scores.yaml` (C2) | Derived from the measured figure |

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **Three words.** Assist, automate, act, each with one icon and one sentence.
2. **One question, three ways.** Step one example all the way through, no statistics yet: a customer asks about the warranty on the Ashby tumble dryer. Show the same draft answer handled three ways: an agent reads and edits it (assist); it goes out and someone checks a sample (automate); the system issues the warranty claim itself (act).
3. **The table.** A small grid of error cost against who catches it, filled with the highest autonomy allowed. Make "regulatory: assist always" visible.
4. **Prediction.** "Candidates 1 and 2 are the same system. Which has the worse error tolerance score?" Reader picks.
5. **Reveal.** C1 scores 1, C2 scores 3, side by side as two columns of the same measured numbers (354 of 400, 107 of 120, 0 of 480), with a person in one column and not in the other.
6. **What the 46 look like.** The remaining wrong answers are mostly follow-ups and identifiers, and some are an article and a policy that disagree (S2 E14). Show as a short sorted list: they are not rare, and not predictable.
7. **What "not found" buys.** S2 E10: declining rose from 83 to 107 of 120, and 365 of 400 citations hold the evidence. Citations let a reviewer check an answer quickly, which is what makes assist workable.
8. **Prediction.** "Which candidate does the table say is allowed to act?" Reader picks.
9. **Reveal.** C3, C6 and C7 are allowed up to act on error cost alone, but only those with reversible outputs. C5 designed at act is above the limit.
10. **The risk in assist.** An agent who stops reading the drafts. One slide: assist is only as good as the review; sampling and quality review are what keep it honest.
11. **The fourth column.** Reveal `scorecard-e5-slide.svg` with asterisks on C1 and C5.
12. **Series map** (last slide), Season 3 highlighted, E5 marked.

## For leaders

**Ask your team:** "What would have to be true before we let this run without review?"

## Decision rule (proposed)

**"Give AI the autonomy its error cost allows: assist where errors are costly or regulated, automate where they are cheap and caught, and act only where they can be reversed."**

## Next

E6, Your data is the strategy: what survives the next model release, and what the next model will give to every competitor.

## Careful with

- **The contrast is about design, not accuracy.** Both candidates share one measured system. Do not say C2 is "more accurate" or that C1's system is "bad".
- **The autonomy table is a case rule, not a legal rule or an industry standard.** It was fixed before scoring (`PREREGISTRATION.md`). Do not say the law requires assist.
- **The 1 and the 3 are the rule's anchors applied to measured figures, not a measured risk of harm.** No customer was harmed; no live traffic exists.
- **"About 1 in 9" is derived** from 46 of 400 and is the load on an agent only if they use the drafts unedited.
- **Do not show totals, ranks or the first pick.**
- **Halvard Home is invented.** No legal claims beyond "consumer protection, product safety and data protection law".
- **Boundaries.** How agents work and fail belongs to S5 and S14; policy and controls to S15.

## From practice

_Brendan to add one anonymised line from his own practice._
