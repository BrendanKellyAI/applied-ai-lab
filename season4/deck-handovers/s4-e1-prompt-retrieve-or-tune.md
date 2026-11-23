# S4 E1 deck handover: Prompt, retrieve, or tune: what each one changes

For the content agent. Has an experiment: the untuned baseline on both Season 4 tasks, the floor
every later rung is measured against.

## Sources of truth

- `episodes/s4-e1-baseline/README.md` and `PREREGISTRATION.md` (with Amendments 1 and 2).
- `episodes/s4-e1-baseline/results/analysis-task-a-test.json` and
  `analysis-task-b-test.json`; `results/claims-test.json`.
- Charts: `episodes/s4-e1-baseline/results/charts/s4-e1-baseline-fully_right-test-slide.svg`
  (Task A) and `s4-e1-baseline-primary-test-slide.svg` (Task B).
- `season4/scoreboard.json`, `season4/reference.yaml`.
- `datasets/halvard-tasks/routes.yaml` and `style-guide.md` (what the model is not told).
- `season2/scoreboard.json` (the knowledge case, one line only).

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E1 |
| Title | Prompt, retrieve, or tune: what each one changes |
| Hub slug | `prompt-retrieve-or-tune` (proposed; confirm) |
| Deck file | `bk-s4-e1-prompt-retrieve-or-tune-v1.pdf` |
| Hub format | `explainer` |

## The argument

There are three ways to change what a model produces:

- **Prompting** (instructions and examples) changes what the model sees on each call.
- **Retrieval** adds knowledge at question time, from your documents (Season 2).
- **Tuning** changes the model's weights, the numbers learned in training, and so its default
  behaviour on every call.

A knowledge gap and a behaviour gap need different fixes. E1 gives the cheapest model everything
it needs to know (the customer's message, or the correct answer) and tells it only what to do,
in one line. Whatever it then gets wrong is a gap in how it behaves, not in what it knows.

The result splits the two tasks cleanly:

- **Task A, triage:** a high floor. 521 of 600 fully right, every safety incident caught, but 68
  harmless messages flagged as incidents.
- **Task B, house style:** no floor. 0 of 300 replies pass the house rules, though 87% keep the
  facts.

The model knows enough in both cases. It does not know Halvard's rules, because nobody told it.

## Scoreboard slide

The first row for each task. Chart: `s4-e1-baseline-fully_right-test-slide.svg`.

| Task | Rung | Primary measure | Result |
|---|---|---|---|
| A, triage | One-line prompt | Fully right, of 600 | **521** (84% to 89%) |
| B, house style | One-line prompt | Passes every check and keeps the facts, of 300 | **0** (0% to 1.3%) |

What this episode adds: the floor. Both rows are the references until a later rung clears them.

## Setup before results

The model is `gpt-6-luna`, the cheapest on file, with reasoning off. The deck should show both
prompts in full before any score.

**Task A prompt** (the 8 route, 10 product and 12 fault names are listed, not defined):

> Triage this customer message to Halvard Home, a UK appliance maker. Reply with one JSON object
> and nothing else: {"route": one of [8 names], "safety": true or false, "product": one of [10
> names] or null, "fault": one of [12 names] or null}

Not given: what each route means, Halvard's routing rules, and the safety definition. Those are
E2's rungs.

**Task B prompt** (the user turn holds the question, the correct answer and its source):

> You write replies for Halvard Home, a UK appliance maker, to send to a customer. Use the
> answer given, which is correct. Reply with the reply text only.

Not given: the style guide. That is E7's rung.

**Worked example, Task A** (`A-test-00410`, invented):

> Hello, I have just bought a Halvard Brio kettle. Is it normal for the stainless steel body to
> get very hot to the touch while it is boiling? Many thanks, Aled.

| Field | The label | The model |
|---|---|---|
| route | `how_to_use` | `how_to_use` |
| safety | false | **true** |
| product | Brio kettle | Brio kettle |
| fault | null | null |

Three fields right, one wrong, so the item is not fully right. Halvard's safety definition says a
question about safe use with no incident is not a safety flag. The model was never told.

**Worked example, Task B** (`B-test-00001`, invented): "Once I've finished, what is the best way
to keep the fridge temperature steady?" The model's reply:

> To keep the temperature steady, keep the doors open for as little time as possible, make sure
> both doors close fully, and avoid blocking the internal air vents with food or packaging.

Every fact is right. It misses the fixed opening, the sign-off, the 40 word minimum and naming
the help article it came from.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 521 of 600 (84% to 89%) | Task A messages with all four fields right | `analysis-task-a-test.json`, `a-one-line.fully_right` |
| 600 of 600 | Task A products named right | same, `field_accuracy.product` |
| 65 of 65 | Safety incidents flagged | same, `safety_recall` |
| 68 of 535 (10% to 16%) | Harmless messages flagged as incidents | same, `safety_false_alarms` |
| 6 of 40 | Questions about safe use, fully right | same, `fully_right_by_kind.safe_use_question` |
| 600 of 600 | Replies that were valid JSON, with no format enforced | same, `json_valid` |
| 0 of 300 | Task B replies passing every check and keeping the facts | `analysis-task-b-test.json`, `b-one-line.primary` |
| 262 of 300 (83% to 91%) | Task B replies keeping every fact (judged) | same, `facts_kept` |
| 0 of 300 each | Replies with the fixed opening, and with the fixed sign-off | same, `checks.opening`, `checks.close` |
| 66 of 300 | Replies within the word limit | same, `checks.length` |
| 170 of 200 | Task A on dev, the check before the test set was frozen | `analysis-task-a-dev.json` |

## Cost

Ratios only. Task A used about 308 input and 27 output tokens per call; Task B about 125 input
and 37 output, plus one judge call per answerable item to check facts, which costs more than the
answer itself. E1 is the cost baseline: later rungs are priced as multiples of it.

**The cost of wrong answers** (an extrapolation, labelled as such): at E1's false alarm rate,
about 13 in every 100 harmless messages would be flagged. If Halvard triaged its invented 45,000
contacts a month, most of them harmless, the safety team of 6 would receive several thousand
false alarms a month. A missed incident is the costlier error (S3 E4), and E1 missed none.

## Slide ideas

Follow the deck rules: step one example through before any statistics, a reader prediction
revealed on the very next slide, varied visual forms, one-line titles, no claim-verdict slides,
and the last slide is the series map.

1. **Three ways to change a model.** A diagram: the prompt (what goes in), retrieval (documents
   added at question time), tuning (the weights inside). Explain weights in one line.
2. **Knowledge or behaviour?** Two boxes. Season 2 fixed a knowledge gap with retrieval (one line,
   pointer to S2). This season is the other box.
3. **The kettle message.** The worked example, the four fields, the one wrong field.
4. **Prediction.** "Told only what to do, how many of 600 messages does the cheapest model get
   fully right?" Reader picks.
5. **Reveal.** 521 of 600, as a grid of 600 squares with 79 marked.
6. **Where the misses are.** A bar for each field: product 600, route 592, fault 585, safety
   532. Reading is not the problem; Halvard's rules are.
7. **The safety flag runs the wrong way.** 65 of 65 incidents caught; 68 harmless messages
   flagged. A two-by-two of flagged and not flagged against incident and no incident.
8. **The fridge reply.** The model's reply beside the style guide's rules, with the missing ones
   marked.
9. **Prediction.** "How many of 300 replies follow Halvard's house style?" Reader picks.
10. **Reveal.** 0 of 300, beside 262 of 300 keeping the facts.
11. **One floor high, one floor absent.** Both scoreboard rows side by side.
12. **Series map** (last slide), Season 4 highlighted, E1 marked.

## For leaders

**Ask your team:** "Is our problem that the model does not know, or that it does not do what we
want?"

## Decision rule (proposed)

**"Name the gap first. If the model lacks facts, retrieve. If it knows enough but behaves
wrongly, change how you ask before you change the model."**

## Next

E2, Instructions first: give the model the definitions a new colleague would get, and watch the
false alarms.

## Careful with

- **The pre-registered claims mostly failed, and that is the story told plainly.** The deck
  predicted a lower floor, more missed incidents and a 15 point gap; the floor was higher, no
  incident was missed and the gap was 13 points. Do not show claim verdicts on slides.
- **The test set was rebuilt once,** before it was frozen, because the dev check found Task A too
  easy (183 of 200). It was kept after one rebuild, not rebuilt until the score fell
  (Amendment 2).
- **The test sets favour items the label checker found easy.** Items `claude-haiku-5-5`
  labelled differently were discarded, most of them messages naming products that do not exist.
- **The facts judge is not yet checked** against a second judge; that is in E7. Say "judged".
- **The safety share of 10% is a test design,** not Halvard's real mix. The monthly false alarm
  figure is an extrapolation from invented numbers.
- **One model, one wording, one run.** Every figure covers these Halvard tasks and this model only.
- **Boundaries.** Building your own evaluations is S8; this season uses fixed ones.

## From practice

_Brendan to add one anonymised line from his own practice._
