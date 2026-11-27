# S4 E6 deck handover: How much data does tuning need?

For the content agent. Has an experiment: E5's tuning repeated at 50, 200 and 800 examples, a
learning curve against the best prompt, on Task A.

## Sources of truth

- `episodes/s4-e6-how-much-data-does-tuning-need/README.md` and `PREREGISTRATION.md`.
- `results/analysis-task-a-test.json` and `analysis-task-a-dev.json`; `results/claims-test.json`.
- Chart: `results/charts/s4-e6-how-much-data-does-tuning-need-fully_right-test-slide.svg`.
- The job records: `results/e6-tuned-50/job.json`, `e6-tuned-200/job.json`, `e6-tuned-800/job.json`.
- The reused points are E5's files (`config.yaml` names them): the untuned model, the 1,600
  model and the reference.
- `season4/finetune-readiness.md`, section 2: the checklist lines this episode fills.
- `season4/scoreboard.json`, `season4/reference.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E6 |
| Title | How much data does tuning need? |
| Hub slug | `how-much-data-does-tuning-need` (as on the hub) |
| Deck file | `bk-s4-e6-how-much-data-does-tuning-need-v1.pdf` |
| Hub format | `explainer` |

## The argument

Labelled examples are the expensive part of tuning: someone has to write or check every answer.
E5 used 1,600. The useful question for anyone commissioning a tuning project is how few would
have done.

The test trained the same model on the first 50, 200 and 800 of E5's examples. The curve climbs
steeply and then stops: 60 of 600 at 50 examples, 450 at 200, 589 at 800, where it meets the
prompt (587). Doubling to 1,600 added three items, which is noise. Half the labelling would have
done. The lesson is to draw the curve before buying more data, not to trust a total.

## Scoreboard slide

Task A ladder. Chart: `s4-e6-how-much-data-does-tuning-need-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 (84% to 89%) | The baseline |
| E2 + definitions | 587 (96% to 99%) | Joined: the reference |
| E3 one-line + 8 similar examples | 593 (98% to 99%) | No |
| E4 the same, with JSON mode | 594 (98% to 100%) | No |
| E5 Qwen3-0.6B, tuned on 1,600 | 592 (97% to 99%) | No |
| **E6 the same, tuned on 800** | **589 (97% to 99%)** | **No: overlaps the reference** |

What this episode adds: E5's height at half the data. The sizes are points on E5's rung, not a
new rung; the reference stays the definitions prompt.

## Setup before results

Everything is E5's tuned arm except the number of training examples. The sets are nested: the 50
are the first 50 of the 200, which are the first 200 of the 800, and so on to E5's 1,600.

| Examples | Safety examples inside | Training steps | Training time (free T4) |
|---|---|---|---|
| 50 | 7 | 12 | 1 minute |
| 200 | 22 | 39 | 3 minutes |
| 800 | 88 | 150 | 13.5 minutes |
| 1,600 (E5) | 166 | 300 | 28 minutes |

**Worked example** (`A-test-00410`, invented): the kettle question again, a new Brio kettle owner
asking whether the steel body should get very hot while boiling.

| Examples | Route given | Right? |
|---|---|---|
| 0 (untuned) | `how_to_use`, but flagged as an incident | No |
| 50 | `safety`, which is not one of Halvard's routes | No: invalid |
| 200 | `how_to_use`, not flagged | Yes |
| 800 | `how_to_use`, not flagged | Yes |

At 50 examples the model has learned the shape of the answer but not the allowed words.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 24, 60, 450, 589, 592 of 600 | Fully right at 0, 50, 200, 800, 1,600 examples | `analysis-task-a-test.json`, `arms.*.fully_right` |
| 587 of 600 | The prompt, for comparison | same, `e6-reference` |
| 560, 67, 501, 594, 596 | Valid replies, same order (prompt 600) | same, `json_valid` |
| 516 | Replies at 50 examples with an invalid field value | same, `e6-tuned-50.invalid_reasons` |
| 58, 0, 62, 64, 65 of 65 | Incidents flagged, same order | same, `safety_recall` |
| 527 and 0 | Items only the prompt got right, and only the 50 model | `claims-test.json`, C1 |
| 12 and 10; p 0.83 | 800 against the prompt, items each way | same, C2 |
| 4 and 7; p 0.55 | 800 against 1,600, items each way | same, C3 |
| 12, 17, 152, 198, 198 of 200 | Dev, same order (prompt 199) | `analysis-task-a-dev.json` |
| 1.18, 0.44, 0.14, 0.08 | Mean training loss at 50, 200, 800, 1,600 | `results/<arm>/job.json`; E5's for 1,600 |

## Cost

No money was spent: the three jobs ran on a free Colab GPU, about 30 minutes of GPU time in all,
and the other points were read from E5. The cost that matters is labelling. Here, labelling 800
instead of 1,600 would have halved that work and the training time for no measurable loss, and
labelling 200 would have fallen 137 items short. Halvard's labels came from a model, so the
episode cannot put a price on a person's labelling time.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Labels are the bill.** Every training example is a message someone answered by hand.
2. **The same model, four diets.** 50, 200, 800, 1,600 as nested boxes.
3. **The kettle at each size.** Wrong, invalid, right, right: a four-step strip.
4. **Prediction.** "How many examples does it take to match the prompt?" Reader picks: 50, 200,
   800, 1,600.
5. **Reveal.** The curve: 60, 450, 589, 592, with the prompt's 587 as a line. 800.
6. **What 50 examples teach.** The form but not the words: 67 of 600 valid, no incident flagged.
   Show two invented route names.
7. **Prediction.** "Does doubling from 800 to 1,600 help?" Reader picks.
8. **Reveal.** Three items, 4 and 7 each way: no.
9. **The checklist line.** Label a few hundred, train, look at the curve, then decide. Link to the
   readiness checklist.
10. **Scoreboard:** not joined; E5's height at half the data.
11. **Series map** (last slide), E6 marked.

## For leaders

**Ask your team:** "Before we label more, what does the curve look like at a quarter and half of
what we have?"

## Decision rule (proposed)

**"Label in stages and stop when the curve flattens."**

## Next

E7: tuning for house style on Task B, the replies, checked by a judge (see `season4/PLAN.md`).

## Careful with

- **One draw of each subset and one seed.** Another 50 or 200 could score quite differently; the
  curve is one path, not a band.
- **The crossing point is not pinned down.** It lies somewhere between 200 and 800; 400 was not
  tried. Say "800 was enough", not "800 is the minimum".
- **Fixed epochs.** Smaller sets also got fewer training steps (12 against 300). More passes over
  50 or 200 examples might do better.
- **Train and test come from one generator,** so few examples may go further here than they would
  on real customer messages.
- **Halvard's numbers are one worked case,** not a rule for other tasks.

## From practice

_Brendan to add one anonymised line from his own practice._
