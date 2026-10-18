# S3 E2 deck handover: Which tasks suit an LLM

For the content agent. No experiment: a teaching deck that adds the second gate and the Task fit score, backed by Season 1 results, Season 2's E15 and the case files.

## Sources of truth

- `season3/case/rule.yaml` (G2 Right tool and the Task fit anchors).
- `season3/case/candidates.yaml` and `season3/case/scores.yaml` (G2 results, redirects and Task fit scores with their evidence).
- `season3/case/results/scorecard-e2.json` and `season3/case/results/charts/scorecard-e2-slide.svg`.
- `season2/deck-handovers/s2-e15-when-rag-is-the-wrong-answer.md` and `field-notes/s2-e13-long-context-or-retrieval/README.md` (S2 E15's evidence).
- `episodes/s1-e8-sampling/README.md`, `episodes/s1-e9-hallucination/README.md`, `episodes/s1-e2-tokens/README.md`.
- `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` (the measured Season 2 final system behind C1 and C2).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E2 |
| Title | Which tasks suit an LLM |
| Hub slug | `which-tasks-suit-an-llm` (proposed; confirm) |
| Deck file | `bk-s3-e2-which-tasks-suit-an-llm-v1.pdf` |
| Hub format | `explainer` |

## The argument

A language model suits a task when **the input is language and a good output can be checked**. Where the answer is a calculation, a record or a prediction, a rule, a query or a forecasting model does it better, and a language model is the wrong tool however capable it is.

That is Gate G2. It sends two of Halvard's candidates elsewhere:

- **C8, the spare parts demand forecast,** is a number predicted from usage history: a forecasting problem, not a language one.
- **C5, automatic refund approval,** is a rule applied to order, delivery and return records. A model may read a free-text return reason, with a person deciding, but whether a refund is due is a rule (S2 E15's logic: when the answer is a calculation over records, store the records and query them).

Passing the gate is not the same as being a good fit. The second half adds **Task fit**, 1 to 5: how easy it is to check an output against a source. Checkability is the point. It is what lets a team measure the thing before trusting it.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e2-slide.svg` (from `lab strategy reveal --through E2`).

New columns this episode adds: **G2 Right tool** (a gate) and **Task fit** (a score).

| Candidate | G1 | G2 Right tool | Value | Task fit |
|---|---|---|---|---|
| C1 Website assistant | pass | pass | 5 | 5 |
| C2 Reply drafts for agents | pass | pass | 4 | 5 |
| C3 Warranty claim triage | pass | pass | 3 | 4 |
| C4 Safety signal screening | pass | pass | 5 | 3 |
| C5 Automatic refund approval | pass | **fail** | not scored | not scored |
| C6 Library consistency check | pass | pass | 3 | 4 |
| C7 Call and chat summaries | pass | pass | 2 | 4 |
| C8 Spare parts demand forecast | pass | **fail** | not scored | not scored |

C5 and C8 fail G2: they stay on the portfolio with a redirect (C5: rules over the order records, written from the returns policy; C8: a forecasting model over parts usage history, or a demand planning product) but cannot go first.

Measured versus assumed: C1 and C2's Task fit of 5 is **measured**: the Season 2 final system answered 354 of 400 answerable questions right, each checked against its source passage (`field-notes/s2-e12-embedding-swap/results/baseline/summary.json`). Every other Task fit score is an **assumption**, with a one-line reason in `scores.yaml`. The G2 results are reasoned, not measured.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 354 of 400 answerable questions answered right | The Season 2 final system, each answer checked against its source passage | `season2/scoreboard.json`; `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` | Measured; the basis for C1 and C2 Task fit |
| Bridge questions: retrieval 14 of 20, long context 20 of 20 | Questions that join two facts (a postcode to a region to a delivery time), same model | `field-notes/s2-e13-long-context-or-retrieval/README.md` | Measured; S2 E15 argues that joins over records belong in a table |
| Same prompt, asked 20 times: 1 distinct answer for "capital of Ireland", 2 for a coffee shop name | How much one model's answer varies on a repeated call | `episodes/s1-e8-sampling/README.md` | Measured on one model, one day; a small effect |
| 20 of 20 continuations different at every temperature | A small open model sampling 10 tokens of open-ended text | `episodes/s1-e8-sampling/README.md` | Measured; shows output varies when many answers are valid |
| 24 of 30 invented items counted as treated as real by a fixed phrase rule; 0 of 30 by reading every response | Why a checker matters: the rule and a reader disagreed on 31 of 60 responses about invented items | `episodes/s1-e9-hallucination/README.md` | Measured; the point is checking, see "Careful with" |
| 11 tokens in English, 76 in Amharic for the same sentence | Cost and context are counted in tokens, and a token is not a word | `episodes/s1-e2-tokens/README.md` | Measured, one tokeniser |

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **Two questions, two kinds of answer.** Show "Why is my dishwasher not draining?" next to "How many Tessa dishwasher spare pumps will we need in March?" Ask which a language model should answer. Step one through: the first has language in and an answer you can check against a manual; the second has no passage to find.
2. **Prediction.** "Which of Halvard's eight candidates is not a language problem?" Reader picks.
3. **Reveal G2.** C8 and C5 fail, shown as two cards with their redirects. C8: a forecast. C5: a rule over records.
4. **The checkability test.** A simple two-axis picture: language in or not, output checkable or not. Place the eight candidates.
5. **Why checkable matters.** Two short evidence slides from Season 1: the same prompt gives varied outputs (S1 E8), and a checker disagreed with a reader on 31 of 60 responses (S1 E9). Neither means "models are unreliable": they mean you need a way to tell right from wrong.
6. **The join in a table.** One slide from S2 E15: a postcode belongs to a region and the region has a delivery time. In a table, one exact join.
7. **Prediction.** "Which candidate has the easiest outputs to check?" Reader picks.
8. **Task fit anchors.** The 1, 3 and 5 anchors as a ladder, then the column: C1 and C2 at 5 because a draft or answer can be checked against its passage, C4 at 3 because misses surface slowly.
9. **Tokens as a unit.** A small bar chart: 11 tokens against 76, "cost and window are counted in tokens". Pointer only; money belongs to S6.
10. **The second column.** Reveal `scorecard-e2-slide.svg`, with C5 and C8 shown as failed and marked "redirect".
11. **Series map** (last slide), Season 3 highlighted, E2 marked.

## For leaders

**Ask your team:** "For this proposal, how would we check that an answer is right?"

## Decision rule (proposed)

**"Use an LLM where the input is language and a good answer can be checked. Use rules, SQL or a forecasting model where the answer is a calculation, a record or a prediction."**

## Next

E3, Field note: does the leaderboard predict your task? A measured test of whether a public ranking of models holds on Halvard's own questions.

## Careful with

- **G2 for C5 and C8 is reasoning, not an experiment.** No refund rule or forecast was built or measured. Say "S2 E15's logic", not "we showed".
- **Only C1 and C2 have measured accuracy.** Every other Task fit is an assumption; label it so. Do not show a measured-looking number for C3, C4, C6 or C7.
- **S1 E9 did not show that the model invented facts.** On `gpt-6-astra` and its 20 items, the fixed rule counted 24 of 30 plain answers about invented items as real, but reading every response found none described an invented item as real. Use it for "you need a way to check", not "models hallucinate".
- **S1 E8 is one model, one prompt pair, one day.** 17 of 20 coffee shop names were identical; do not promise "different every time".
- **Do not show totals, ranks or the first pick.**
- **Halvard Home is invented.** No legal claims beyond "consumer protection, product safety and data protection law".
- **Boundaries.** Costs and token pricing belong to S6; building your own checks to S8.

## From practice

_Brendan to add one anonymised line from his own practice._
