# S3 E11 deck handover: The one-page AI strategy

For the content agent. No experiment: a teaching deck that walks through the one-page template, using Halvard Home's filled page as the example, framed as what goes in front of the board. The first move was decided in E10, so the page is shown in full.

## Sources of truth

- `season3/templates/one-page-strategy.md` (the blank template: nine sections, each with a guiding line).
- `season3/halvard-one-page.md` (Halvard's filled example; the source for every quote in the deck).
- `season3/case/results/scorecard.json` and `sensitivity.json` (the final case from E10; nothing is added at E11).
- `season3/case/rule.yaml` (the autonomy table behind section 3; the sourcing settings behind section 4).
- `season3/case/candidates.yaml` and `season3/case/scores.yaml` (the candidates named in sections 2 to 4).
- `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` (the measured 46 of 400 and 13 of 120 quoted in section 3).
- `episodes/s2-e3-measuring/README.md` (the 520-question test set that section 5 relies on).
- `datasets/halvard/manifest.json` (the 300 support articles).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E11 |
| Title | The one-page AI strategy |
| Hub slug | `the-one-page-ai-strategy` (proposed; confirm) |
| Deck file | `bk-s3-e11-the-one-page-ai-strategy-v1.pdf` |
| Hub format | `playbook` |

## The argument

A strategy a board cannot read in two minutes is not yet a strategy. The one page forces the choices the earlier episodes built up, in a fixed order, and it is the thing the board decides on.

Each section answers one question the board would otherwise ask across a long meeting:

1. **Outcomes we want.** What changes, with a metric and an owner each, in words that do not mention AI (E1).
2. **Where we will use AI: now, next, later, not.** "Not" is a real group (E2).
3. **How much we trust it.** Assist, automate or act, and why (E4, E5).
4. **What we own and what we rent.** Build, buy, and how the models are reached (E6, E8).
5. **How we stay portable.** Our own tests and our own data, so a model change is not a restart (E7, E9).
6. **How we will measure, and when we stop.** Metric, threshold, time box, stop condition, reviewer.
7. **The first move.** One use case, why it goes first, what happens next quarter.
8. **What we will not do.** The lines we will not cross.
9. **What we ask of the board.** The decisions, the budget, the date.

Frame the deck as the board's view: for each section show the question the board is asking, then Halvard's answer in a line or two.

**The first move is already known.** E10 chose it: the library consistency check (C6), 4.20 of 5, with its stop criteria and reply drafts for agents (C2) as the fallback. So this deck shows Halvard's page in full, section 7 included. The page is where the season's decisions meet, not where a new one is made.

## Case recap slide

**No new column.** E11 adds nothing to the scorecard, which was completed in E10. Optionally show `scorecard-final-slide.svg` as a thumbnail beside section 7, to show where the first move came from. The closing content slide shows the blank template beside Halvard's filled page as a miniature.

Measured versus assumed: the page quotes two kinds of figure. The 46 of 400 and 13 of 120 in section 3 are **measured** (Season 2). The volumes and Halvard itself are **invented**, and the page says so in its header.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 46 of 400 | Answerable questions the Season 2 final system answered wrongly | `field-notes/s2-e12-embedding-swap/results/baseline/summary.json` | Measured |
| 13 of 120 | Unanswerable questions the same system answered anyway rather than declining | same | Measured |
| 520 questions | The size of the test set the firm owns and reruns (400 answerable, 120 unanswerable) | `episodes/s2-e3-measuring/README.md` | Measured (set size) |
| 300 articles | Support articles in the library, the denominator for the consistency metric in section 1 | `datasets/halvard/manifest.json` | Measured (library size) |
| 8 candidates | Use cases in the case, of which 2 failed Gate 2 (a language model is not the right tool) | `season3/case/results/scorecard.json` | Case design |
| 4.20 of 5, 9 of 15 | C6's total, and the alternative weightings in which it stays first (E10) | `season3/case/results/sensitivity.json` | Computed |

Do not show prices. Totals and the sensitivity result may be quoted as E10 reported them.

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **The board has two minutes.** A clock and one blank page. The board does not want a deck on AI; it wants to know what it is agreeing to.
2. **The blank page.** The template as nine labelled boxes, no text yet.
3. **One example, one section.** Step section 1 all the way through before any other: Halvard's outcome "customers get a correct answer to a policy or product question without waiting for an agent", its metric (questions answered correctly with no agent contact in 7 days) and its owner (head of customer operations). Note the page never says AI.
4. **Prediction.** "Which section do boards most often leave out?" Reader picks from the nine.
5. **Reveal.** Section 8, what we will not do. Show Halvard's four lines: no unreviewed answers to customers on warranty, refunds or safety; no model deciding refunds; no staff-only document in any prompt a customer could see; no AI project without an outcome stated without the word AI.
6. **Not is a group.** Section 2 as four columns, all filled: Now, the library consistency check; Next, reply drafts for agents; Later, the website assistant (once it can run with review), claim triage and safety screening. Not: automatic refund approval (a rule over order records), spare parts forecasting (a forecasting model), building call summaries ourselves (buy the feature if wanted).
7. **Trust, in one box.** Section 3: assist wherever a customer's rights or safety are at stake. Quote the measured 46 of 400 and 13 of 120, and point back to E5's autonomy table in one line.
8. **Own and rent.** Section 4 as two columns, own and rent, with model access underneath (managed, inside the existing cloud account, for anything that reads customer contacts).
9. **Portable by test.** Section 5: the 520-question test set and the code that scores it belong to the firm. Before accepting a new model, rerun it and compare item by item, not only the total.
10. **The frame for measuring.** Section 6 as a five-part frame filled for the C6 pilot (metric, threshold, time box, stop condition, reviewer), from E10. Caption: "Every pilot fills these in before it starts."
11. **The first move.** Section 7 filled: C6 first, because it scored highest and cleans the library C2 will read from; fragile, so C2 is the named fallback.
12. **What we ask.** Section 9: three asks, in the board's own terms.
13. **Two-minute test.** The filled page at thumbnail size, with a timer. The reader asks of their own page: could the board read it in two minutes and say what we will not do?
14. **Series map** (last slide), Season 3 highlighted, E11 marked.

## Playbook slides (hub text)

The hub's `playbook_slides` text: one short text per template section, nine in all, in section order. Plain British English, one or two sentences each.

1. **Outcomes we want.** Say what will change for customers, staff or the business, with a metric and an owner for each. Write it without the word AI.
2. **Where we will use AI: now, next, later, not.** Put every candidate use case in one of four groups. The "not" group is real: it records what you chose to leave out and why.
3. **How much we trust it.** For each use case, choose assist, automate or act, and say why the cost of a wrong output and who catches it allow that level.
4. **What we own and what we rent.** Say what you build on your own data and workflow, what you buy, and how you reach the models.
5. **How we stay portable.** Keep your own test set and your own data, so that changing model or supplier means rerunning your tests, not starting again.
6. **How we will measure, and when we stop.** For each pilot, write the metric, the threshold, the time box, the stop condition and the reviewer before it starts.
7. **The first move.** Name one use case to start with, say why it goes first, and say what happens in the next quarter.
8. **What we will not do.** Write the lines you will not cross, for example no unreviewed answers on customers' rights.
9. **What we ask of the board.** List the decisions, the budget and the support you need from the board, and by when.

## For leaders

**Ask your team:** "Could our board read our AI strategy in two minutes and know what we will not do?"

## Decision rule (proposed)

**"Put the strategy on one page: the outcomes, where AI will and will not be used, how much it is trusted, what you own, and the first move with its stop condition."**

## Next

E12, Season 3 recap: the strategy card. Every rule and question from the season on one card, and the case from first column to first pick.

## Careful with

- **The first pick is fragile.** Section 7 should say so in a line: C6 holds in 9 of 15 alternative weightings, and C2 is the fallback. Do not present it as obvious.
- **The page is an example, not a template to copy.** Halvard's answers fit Halvard's case. The reader's job is to fill the nine sections for their own firm.
- **Halvard Home is invented.** Every volume on the page is invented; only the Season 2 figures are measured. No legal claims beyond "consumer protection, product safety and data protection law".
- **Section 3's trust levels are the case rule applied, not a legal requirement.** Do not say the law requires assist.
- **Boundaries.** Rollout and adoption belong to S12; policy and controls to S15; people and operating model to S9. The page says what the board approves, not how the firm rolls it out.

## From practice

_Brendan to add one anonymised line from his own practice._
