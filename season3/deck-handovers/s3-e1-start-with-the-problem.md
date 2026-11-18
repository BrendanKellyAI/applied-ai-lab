# S3 E1 deck handover: Start with the problem, not the model

For the content agent. No experiment: a teaching deck that starts the scorecard, backed by the case files and by Season 1 and Season 2 evidence that the right choice depends on the task.

## Sources of truth

- `season3/case/halvard-home.md` (the CEO's ask, invented).
- `season3/case/candidates.yaml` (each candidate's outcome, metric and owner).
- `season3/case/rule.yaml` (G1 Outcome and the Value criterion with its anchors).
- `season3/case/scores.yaml` and `season3/case/results/scorecard-e1.json` (the scorecard as it stands at E1).
- `season3/case/results/charts/scorecard-e1-slide.svg`.
- `field-notes/s1-e10-reasoning-vs-standard/README.md` (the evidence behind S1 E11) and `field-notes/s2-e13-long-context-or-retrieval/README.md` (behind S2 E15).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E1 |
| Title | Start with the problem, not the model |
| Hub slug | `start-with-the-problem` (proposed; confirm) |
| Deck file | `bk-s3-e1-start-with-the-problem-v1.pdf` |
| Hub format | `explainer` |

## The argument

"An AI assistant on the website" is a technology and a place, not an outcome. The first test for any AI idea is to state the outcome **without the word AI**, with a metric that moves and a named owner. If you cannot, it is not a use case yet.

The episode applies the test to the CEO's ask and then to all eight candidates. Each candidate's outcome is written first, and only then is it asked what could deliver it. That is Gate G1. The second half of the episode adds the first score, **Value of the outcome**, 1 to 5 against written anchors: 1 is minor, 3 moves a metric one team tracks, 5 moves a metric the leadership tracks.

Both halves come from the same lesson in earlier seasons: the right choice depends on the task, not on the newest model.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e1-slide.svg` (from `lab strategy reveal --through E1`).

New columns this episode adds: **G1 Outcome** (a gate) and **Value of the outcome** (a score).

| Candidate | G1 Outcome | Value |
|---|---|---|
| C1 Website assistant | pass | 5 |
| C2 Reply drafts for agents | pass | 4 |
| C3 Warranty claim triage | pass | 3 |
| C4 Safety signal screening | pass | 5 |
| C5 Automatic refund approval | pass | not scored |
| C6 Library consistency check | pass | 3 |
| C7 Call and chat summaries | pass | 2 |
| C8 Spare parts demand forecast | pass | not scored |

C5 and C8 show no Value score on this chart: they fail Gate G2 in E2 and are never scored on the criteria. Footnote them "not scored yet: see E2" and do not explain more here.

Measured versus assumed: every Value score is an **assumption**, written in `scores.yaml` with a one-line reason, except C6's, which cites a measured result (3 of the Season 2 final system's 5 failures with the right passage in the prompt came from an article and a policy that disagree, `episodes/s2-e14-tracing/README.md`). All eight outcomes are invented.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| About 9,000 questions a month that agents answer and the library could answer | Volume behind C1 and C2's value | `season3/case/candidates.yaml` | Invented |
| 8 of 8 candidates pass G1 | Candidates whose outcome is stated without the word AI, with a metric and owner | `season3/case/results/scorecard-e1.json` | Case result |
| Value scores 5, 4, 3, 5, 3, 2 for C1, C2, C3, C4, C6, C7 | Written judgements against `rule.yaml` anchors | `season3/case/scores.yaml` | Assumptions (C6 measured) |
| Reasoning on versus off: state tracking +18.9 points and constraint puzzles +21.1 points, extraction +0.0 points | Accuracy change from lowest to high reasoning, paired, 90 pairs per task (3 models x 30 items), 720 calls in all | `field-notes/s1-e10-reasoning-vs-standard/README.md` | Measured; this is the evidence behind S1 E11 |
| Bridge questions: long context 20 of 20, retrieval 14 of 20 | Two-fact questions answered right, same model, 20 items | `field-notes/s2-e13-long-context-or-retrieval/README.md` | Measured; S2 E15 draws the conclusion |
| Hard items together: 75 against 71 of 80, intervals overlap | Long context against retrieval | same file | Measured; not a win for either |

Plain statement of the lesson: on a task that needs several steps held in mind, turning reasoning up helped a lot; on extraction it changed nothing. On questions that join two facts, one approach was clearly better; on others the two tied. The tool follows the task.

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **The ask.** The CEO's sentence on its own: "We need an AI assistant on the website by spring."
2. **Take it apart.** Step one example all the way through. Write the sentence on the left and a blank outcome card on the right: what is different for the customer, what metric moves, who owns it? Fill it in for C1 as one worked example: "Customers get a correct answer without waiting for an agent", measured by "share of website questions answered correctly with no agent contact within 7 days", owned by the head of customer operations.
3. **Prediction.** "Of Halvard's eight ideas, how many can state an outcome without the word AI?" Reader picks a number.
4. **The eight outcomes.** Reveal: all eight, as a grid of outcome cards (name, outcome, metric, owner). The trick is how they were written: outcome first, technology second. Show the CEO's sentence failing the same test next to them.
5. **Gate G1.** A small flow diagram: outcome stated? metric? owner? If not, "not a use case yet: write the outcome first".
6. **Why the model is the wrong first question.** A two-column picture from Season 1 and Season 2: reasoning helped on state tracking and puzzles and did nothing on extraction (S1 E10); long context won on two-fact questions and tied elsewhere (S2 E13). Same idea, different task, different answer.
7. **Prediction.** "Which of the eight moves a metric the leadership tracks?" Reader picks.
8. **Value anchors.** The 1, 3 and 5 anchors as a staircase.
9. **The first column.** Reveal the scorecard slide (`scorecard-e1-slide.svg`): G1 and Value. Highlight C1 and C4 at 5 and C7 at 2, with the label "assumption" on each.
10. **What the column does not say.** One slide: value is not the ranking. A high-value idea can still fail later gates.
11. **Series map** (last slide), Season 3 highlighted, E1 marked.

## For leaders

**Ask your team:** "Which of our AI projects could we describe without the word AI?"

## Decision rule (proposed)

**"Write the outcome first, without the word AI. If you cannot name the metric that moves and who owns it, it is not a use case yet."**

## Next

E2, Which tasks suit an LLM: two of the eight candidates will be sent elsewhere, and the episode shows why.

## Careful with

- **The Value scores are judgements, not measurements.** Label each "assumption" on the slide. Only C6's cites a measured result.
- **Do not show the total, the rank or the first pick.** Totals exist only from E11. Do not hint at the order.
- **Do not say AI projects fail for lack of an outcome as a statistic.** No evidence here measures how often that happens.
- **S1 E10 and S2 E13 are context, not proof of the rule.** They show the tool depends on the task for these tasks and this library; they do not show how many real firms choose badly.
- **Halvard Home is invented.** All volumes, owners and metrics are invented; say so on the slide.
- **No legal claims** beyond "consumer protection, product safety and data protection law".
- **Boundaries.** People and operating model are S9; rollout and adoption S12.

## From practice

_Brendan to add one anonymised line from his own practice._
