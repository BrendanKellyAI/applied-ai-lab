# S3 E0 deck handover: Season intro

For the content agent. No experiment: the opening deck for Season 3, built last so the episode list, tools and links are final. It reveals no scores and no first pick.

## Sources of truth

- `season3/case/halvard-home.md` (the firm, its exposure and the CEO's ask; invented).
- `season3/case/candidates.yaml` (the eight use cases, by name only for E0).
- `season3/case/rule.yaml` (the order of use: two gates, six criteria, two settings; names only, no weights needed).
- `season3/templates/scorecard.csv`, `season3/templates/scorecard-guide.md`, `season3/templates/one-page-strategy.md` (the tools).
- `field-notes/s3-e3-leaderboard/`, `field-notes/s3-e7-data-or-model/`, `field-notes/s3-e9-model-change/` (the three field notes; questions only, no results).
- `season2/deck-handovers/s2-e0-season-intro.md` (format and tone to match).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E0 |
| Title | Season 3: AI strategy |
| Hub slug | `season-3-intro` (proposed; confirm) |
| Deck file | `bk-s3-e0-season-intro-v1.pdf` |
| Hub format | `season_intro` |

## The argument

Season 3 is the first leadership season. Its subtitle is "Where AI earns its place, and choices that outlast the next model release". There is no code to read: most episodes teach one decision, and a running case, Halvard Home, applies each decision to eight candidate use cases.

Halvard Home is invented. It is the appliance maker whose support library Season 2 built and measured. No real company's data appears anywhere in the season. Where the case touches regulation it says only "consumer protection, product safety and data protection law", and it is not legal advice.

The CEO's ask, at the October leadership meeting: **"We need an AI assistant on the website by spring."** The head of customer operations has been asked to come back with a plan, and has asked a simpler question first: of everything we could use AI for, what should we do first, and how would we know it worked?

The questions the season answers:

1. Which of our ideas are real use cases, and which are only a technology looking for a job?
2. Which tasks suit a language model, and which do not?
3. How much can we trust it, and how much autonomy should it have?
4. What do we build, what do we buy and what do we rent?
5. What survives the next model release?
6. Which one goes first, and when do we stop it?

## Case recap slide

None. E0 has no reveal step: do not show the scorecard, any score, a gate result or a first pick. Show the eight candidates by name only, as a list, so readers meet the cast. The scorecard is built one column per episode from E1 (`season3/case/results/charts/scorecard-e1-slide.svg` first).

New column this episode adds: none.

## Evidence

E0 makes no measured claim. The only figures are the invented Halvard facts and the counts of the season's own structure. Mark every Halvard figure "invented" on the slide.

| Figure | What it measures | Source | Status |
|---|---|---|---|
| About 45,000 customer contacts a month | Halvard's contact volume | `season3/case/halvard-home.md` | Invented |
| About 140 support agents, a safety team of 6, a content team of 4 | Halvard's support staffing | `season3/case/halvard-home.md` | Invented |
| About 3,200 warranty claims and 2,100 returns a month | Halvard's claim and return volume | `season3/case/halvard-home.md` | Invented |
| Ten products, 300 support articles, 4 customer policies | The size of the Season 2 library | `season3/case/halvard-home.md`, `datasets/halvard/manifest.json` | Real counts from the library (the firm is invented) |
| Eight candidate use cases | The case's portfolio | `season3/case/candidates.yaml` | Fixed before any score |
| Thirteen episodes, three of them field notes | The season's structure | The list below | Plan |

Do not use Season 2's accuracy figures in E0: they are the surprise in E4 and E5.

## The season at a glance

| Act | Ep | Title | Read it when you are about to ... |
|---|---|---|---|
| Choose the work | E1 | Start with the problem, not the model | approve an AI project that no one can describe without the word AI |
| | E2 | Which tasks suit an LLM | decide whether a proposal needs a language model at all |
| | E3 | Field note: does the leaderboard predict your task? | pick a model because it tops a public ranking |
| Set the trust | E4 | The cost of being wrong | let AI answer customers, or touch anything regulated |
| | E5 | Assist, automate, or act | decide how much autonomy AI gets |
| Decide what to own | E6 | Your data is the strategy | decide where to invest so it outlasts the next model |
| | E7 | Field note: better data or a bigger model? | pay for a bigger model to fix quality |
| | E8 | Build, buy, or managed | choose how to source the application and the model |
| | E9 | Field note: does it survive a model change? | commit to one model or one provider |
| Commit | E10 | The one-page AI strategy | put a strategy in front of the board |
| | E11 | Which use case goes first? | choose the first project and write down when to stop it |
| | E12 | Season 3 recap: the strategy card | take the whole season away on one card |

## The three field notes

Each is a measured experiment on the Halvard support system from Season 2, with open code and a pre-registration. Give the question only, never a result.

- **E3:** does the leaderboard predict your task?
- **E7:** better data or a bigger model?
- **E9:** does it survive a model change?

## The three tools readers leave with

1. **A scorecard template**, with a command that scores your own use cases and checks whether your first pick survives different weights: `lab strategy score`. No API calls, no key needed. Files: `season3/templates/scorecard.csv` and `season3/templates/scorecard-guide.md`.
2. **A one-page strategy template** for the board: `season3/templates/one-page-strategy.md`.
3. **The strategy card** in E12: every episode's decision rule and its "Ask your team" question on one page.

The hub's tools section for Season 3 must be live, and the case and templates merged to `main`, before E0 publishes, so every link on the slide works.

## Slide ideas

Respect the deck rules: teach, step one example through before statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. A single quotation slide: the CEO's sentence, nothing else.
2. Walk the sentence through one question before any structure: "What would you ask first?" Show two or three plausible first questions on screen (which model? what will it cost? who owns the result?), then reveal on the next slide the question the head of customer operations asked, "what should we do first, and how would we know it worked?"
3. Halvard in one slide, as a simple labelled card (products, contacts, teams), with "invented" in the corner.
4. The cast: eight candidates as a plain list of names only. Ask the reader to pick the one they would start with, then reveal on the next slide that the season will not tell them yet: the choice is made by a rule fixed before any score (no answer given).
5. The four acts as a horizontal strip, one verb each: Choose, Set the trust, Decide what to own, Commit.
6. The "Read it when" index as a table, one line per episode, in the act colours.
7. The three field notes as three question cards, with the line "measured, not argued".
8. The three tools as three object icons, with the one command on screen: `lab strategy score`.
9. How to read the season: one episode, one decision, one column of the scorecard.
10. The series map (last slide), as in the S0 deck, with Season 3 highlighted.

## For leaders

**Ask your team:** "If our CEO asked for an AI assistant by spring, what would we ask first?" (E0's version of the question each later episode sharpens; the per-episode questions are collected in the E12 strategy card.)

## Decision rule (proposed)

**"Before you ask what AI can do, ask what you want to be different. Choose use cases by a rule fixed in advance, and put a stop condition on the first one."**

This is the season in one line, and stands alone for a reader arriving from a share.

## Next

E1, Start with the problem, not the model: take the eight candidates and the test "state the outcome without the word AI".

## Careful with

- **Do not reveal the first pick or any score.** That includes hints ("the surprising winner"), the sensitivity result and any total.
- **Do not show the Season 2 accuracy figures.** They belong to E4 and E5.
- **Do not describe field note results.** E3, E7 and E9 are still running; use the questions only.
- **Halvard Home is invented.** Say so on the Halvard slide. No real company's data is used.
- **No legal claims.** Describe exposure only as "consumer protection, product safety and data protection law", and nothing here is legal advice.
- **The numbering is the 13-episode list above (E0 to E12).** Every Season 2 reference uses the 16-episode Season 2 numbering (for example S2 E15, When RAG is the wrong answer).
- **Boundaries.** People and operating model belong to S9, rollout and adoption to S12, policy and controls to S15, and money to S6. Do not promise them here beyond one line each.

## From practice

_Brendan to add one anonymised line from his own practice._
