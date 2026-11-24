# S4 E0 deck handover: Season intro

For the content agent. No experiment: the opening deck for Season 4. It reveals no scores.
Rebuild it last if the episode list changes. E11's question was settled on 24 November 2026: where a tuned model can run.

## Sources of truth

- `season4/PLAN.md` (the season plan as approved at Gate 1, and the move of tuning to an open
  model on Colab, section 1a).
- `datasets/halvard-tasks/README.md`, `routes.yaml`, `style-guide.md` (the two tasks; invented).
- `season3/case/results/scorecard.json` (where the tasks come from in Season 3).
- `season2/deck-handovers/s2-e15-when-rag-is-the-wrong-answer.md` (the line Season 4 starts from).
- `season3/deck-handovers/s3-e0-season-intro.md` (format and tone to match).

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E0 |
| Title | Season 4: Adapting models |
| Hub slug | `season-4-intro` (proposed; confirm) |
| Deck file | `bk-s4-e0-season-intro-v1.pdf` |
| Hub format | `season_intro` |

## The argument

Season 2 ended with a rule: use retrieval when the answer is a passage, and something else for a
calculation, a behaviour or a live state. Season 4 is the behaviour part. The question for the
whole season:

**When a model knows enough but does not do what you want, what is the cheapest change that
fixes it: better instructions, examples, an enforced format, or tuning the model itself?**

Each rung costs more to build and to change than the one before, so the season climbs one rung
at a time and keeps a rung only if it clears a pass mark fixed before the run.

Two invented tasks at Halvard Home, the appliance maker from Seasons 2 and 3:

- **Task A, triage.** A customer message comes in. The model returns its route (one of 8 teams),
  whether it may describe a fire, smoke, shock or injury incident, the product, and the fault.
  Checked by code against the label, no judge. 600 test messages.
- **Task B, reply drafts in the house style.** The model is given a customer question and the
  correct answer, and writes the reply Halvard would send: a fixed opening and sign-off, a word
  limit, the policy named, no promises. 300 test questions.

Where the tasks come from in Season 3, for the content agent only: Task A is the warranty claim
triage and safety signal screening use cases; Task B is reply drafts for support agents. Season
3's first pick was the library consistency check, so **Season 4 does not build the system
Season 3 chose.** Say the tasks come from use cases Season 3 scored, by topic, and claim no more.
Never name them by candidate number on the slides.

**What changed from the plan, worth one line in the deck:** in 2026 no major provider offered
fine-tuning a season like this could use (OpenAI closed it to new organisations in May 2026, and
Google and Anthropic offer none on their main APIs; sources in `season4/PLAN.md`). So every
tuning episode tunes a small open model, `Qwen3-0.6B`, with adapters on a free cloud GPU, and
compares it with the cheapest API model, prompted. That a provider can withdraw tuning is itself
evidence for E12.

## Case recap slide

None. E0 has no reveal: do not show any score, the scoreboard or which rung wins.

New column this episode adds: none.

## Evidence

E0 makes no measured claim. Mark every Halvard figure "invented".

| Figure | What it measures | Source | Status |
|---|---|---|---|
| About 45,000 customer contacts a month | Halvard's contact volume | `season3/case/halvard-home.md` | Invented |
| A safety team of 6 | Who reads every message flagged as a possible incident | `season3/case/halvard-home.md` | Invented |
| 8 routes, 10 products, 12 faults | The size of Task A's label | `datasets/halvard-tasks/routes.yaml` | Fixed before any call |
| 600 and 300 test items | The two frozen test sets | `datasets/halvard-tasks/MANIFEST.json` | Frozen 23 November 2026 |
| 14 episodes, 3 of them field notes | The season's structure | The list below | Plan |

## The season at a glance

| Act | Ep | Title | Read it when you are about to ... |
|---|---|---|---|
| Ask better | E1 | Prompt, retrieve, or tune: what each one changes | choose how to fix a model that gets things wrong |
| | E2 | Instructions first | reach for anything more expensive than a better prompt |
| | E3 | How many examples? | paste examples into a prompt that runs a million times |
| | E4 | Making output a contract | let code read what a model writes |
| Tune | E5 | Field note: does fine-tuning beat a good prompt? | commission a fine-tuning project |
| | E6 | How much data does tuning need? | budget for labelling training data |
| | E7 | Teaching a house style | ask a model to write the way your company writes |
| Know the limits | E8 | Field note: can fine-tuning teach facts? | tune a model on your documents instead of retrieving them |
| | E9 | Distillation: a big model teaches a small one | pay for a big model on every call |
| | E10 | Field note: what does tuning break? | ship a tuned model without checking what it forgot |
| Choose | E11 | Where your tuned model runs | buy GPUs to run a model you tuned |
| | E12 | Prompt, retrieve, or tune? | sign off an adaptation plan |
| | E13 | Season 4 recap: the adaptation card | take the whole season away on one card |

The tools: the decision card (E12) and the fine-tuning readiness checklist (E6, completed in
E10).

## Slide ideas

Follow the deck rules: teach before compressing, varied visual forms, one-line titles, little
text, and the last slide is the series map.

1. **One line from Season 2.** "Use retrieval when the answer is a passage." Then the gap it
   left: what if the model has the facts and still gets it wrong?
2. **One message, one wrong answer.** A customer asks whether it is normal for their kettle to
   get hot when it boils. The model flags it as a possible safety incident, and the safety team
   reads it. No numbers yet.
3. **The ladder.** A diagram of the rungs, bottom to top: instructions, examples, an enforced
   format, tuning, distillation. Beside each, what it changes (what the model sees each time, or
   the model's weights) and what it costs to change later.
4. **The two tasks.** Task A as a message in and four fields out; Task B as a question and
   answer in and a reply out. Show the fields, not the scores.
5. **The rule of the season.** A rung joins the reference only if it clears a pass mark fixed
   before the run, on a test set frozen before any rung was tried.
6. **Why the tuned model is a small open one.** One slide, the plan change above.
7. **Security point.** Tuning sends your examples to whoever trains the model; a tuned model has
   no permission filter. Both come back in E8 and E10.
8. **The season map:** the four acts as a strip.
9. **Series map** (last slide), Season 4 highlighted.

## For leaders

**Ask your team:** "When our model gets this wrong, is it missing facts, or ignoring how we want
it to behave?"

## Decision rule (proposed)

**"Fix behaviour with the cheapest rung that clears the bar: instructions, then examples, then
an enforced format, and tune only when those stop rising."**

## Next

E1, Prompt, retrieve, or tune: the cheapest model on both tasks, told only what to do in one
line.

## Careful with

- **No scores in E0.** The surprise in E1 is how high the floor is on one task and how low on
  the other.
- **Halvard Home is invented.** Its volumes, products and rules are invented.
- **The provider facts are dated.** Tuning availability is as checked in November 2026, with
  sources in `season4/PLAN.md`; say "as of November 2026".
- **Boundaries.** Total cost of tuning and hosting is S6; labelling data at scale is S7; building
  your own evaluations is S8; tool calling and agents are S5; training data leaving your systems
  is S11; serving speed and hardware are S13; model risk controls are S15.

## From practice

_Brendan to add one anonymised line from his own practice._
