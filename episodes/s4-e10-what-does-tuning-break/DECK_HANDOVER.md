# S4 E10 deck handover: Field note: what does tuning break?

For the content agent. A field note with an experiment: the two tuned models from E5 (triage) and
E7 (replies), and the untuned model, asked three sets of questions outside their tasks.

## Sources of truth

- `episodes/s4-e10-what-does-tuning-break/README.md` and `PREREGISTRATION.md` (with Amendment 1).
- `results/analysis-regression.json` (per model, per check, per item), `results/claims.json`.
- Charts: `results/charts/s4-e10-what-does-tuning-break-{general,bleed,declines}-slide.svg`.
- The answers: `results/<arm>/predictions-{general,bleed,declines}.jsonl`; the judge's
  verdicts: `results/<arm>/judge-declines.jsonl`.
- The prompts: `data/general.jsonl`, `data/bleed.jsonl`, `data/declines.jsonl`.
- The jobs: `results/<arm>/job.json`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E10 |
| Title | Field note: what does tuning break? |
| Hub slug | `what-does-tuning-break` (as on the hub) |
| Deck file | `bk-s4-e10-what-does-tuning-break-v1.pdf` |
| Hub format | `field_note` |

## The argument

A tuned model is rarely kept to the one task it was tuned for. E10 asked: what does it do with
everything else?

It depends on what tuning taught. The reply writer learned a voice that fits any request, and
used it on everything: 41 of 100 ordinary requests came back as a Halvard customer reply,
including a soup recipe it said it could not find "in our database". It also declined fewer
questions its passages could not answer. The triage model learned a format that fits nothing
but a support message, and left ordinary requests alone. All three pre-registered claims
failed, because each needed both models to break, and only one did.

## Scoreboard slide

None: E10 is a field note, not a rung on Task A or B. The scoreboard does not change.

## Setup before results

| Arm | Model |
|---|---|
| Untuned | Qwen3-0.6B |
| Tuned for triage | Qwen3-0.6B plus E5's adapter |
| Tuned for replies | Qwen3-0.6B plus E7's adapter |

| Check | What it is | Scored by |
|---|---|---|
| General ability | 120 Season 1 reasoning items (extraction, arithmetic, state tracking, puzzles) | code: the final `ANSWER:` line |
| Format bleed | 100 ordinary requests (recipes, emails, sums, poems; 20 mention appliances) | code: a triage object, or the house reply's opening or sign off |
| Declines | 120 unanswerable questions, each with Season 2's reference prompt and passages | `gemini-3.6-flash`, Season 2's judge |

No system prompt on the first two checks.

**Worked example** (`data/bleed.jsonl`, `bleed-000`): "Give me a simple recipe for a vegetable
soup for four people."

| Arm | What came back |
|---|---|
| Untuned | a recipe |
| Tuned for triage | a recipe |
| Tuned for replies | "Thank you for getting in touch. You have asked for a simple recipe for a vegetable soup for four people. I'm sorry, I can't find that in our database. I've passed your question to a colleague who will reply within two working days." |

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 0, 0, 41 of 100 | Ordinary requests answered in a tuned format: untuned, triage, replies | `analysis-regression.json`, `checks.bleed` |
| 33 of 80 and 8 of 20 | The reply writer's bleed: everyday requests, appliance requests | `per_item.bleed` with `data/bleed.jsonl` `kind` |
| 65, 78, 52 of 120 | Correct declines, same order | `checks.declines` |
| 11 and 24; p 0.041 | Reply writer against untuned, declines, items each way | `claims.json`, C3 |
| 26 and 13; p 0.053 | Triage model against untuned, declines (more, not fewer) | same |
| 41, 56, 56 of 120 | General ability, same order | `checks.general` |
| 18 and 3; p 0.0015 | Each tuned model against untuned, general (better, not worse) | `claims.json`, C1 |
| 11, 26, 29 of 30 | Arithmetic, same order: the whole general gain | `per_item.general` |
| 0 of 30 | State tracking and puzzles, every model | same |
| 17 of 19 | Untuned arithmetic misses that end in `\boxed{}` instead of `ANSWER:` | README |
| 58 of 79 | Untuned general misses that hit the 400 token limit | README |

## Cost

Ratios only. The judge run was the only spend, below the approved budget. The three Colab jobs
ran on the free T4: about 14, 13 and 31 minutes of answers. The first attempt at the untuned job
ran out of memory on the long decline prompts and was rerun with smaller batches (Amendment 1).
Token counts, estimated against actual, are in the README.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Tuned for one job, used for many.** The same support channel gets questions nobody tuned for.
2. **Three checks.** Reasoning puzzles, ordinary requests, questions it should decline.
3. **Prediction.** "Ask each model for a soup recipe. Which one answers as a customer service
   reply?" Reader picks.
4. **Reveal.** The reply writer, word for word (the worked example).
5. **How often.** 41 of 100 ordinary requests; the triage model none. Bar chart (`bleed`).
6. **Why one and not the other.** A voice travels; a line of JSON does not fit a recipe.
7. **Prediction.** "With the right passages in front of it, does the reply writer still say 'I
   don't know' as often?"
8. **Reveal.** 52 against 65 for the untuned model; the triage model 78. Bar chart (`declines`).
9. **The surprise.** Tuning did not cost reasoning here; both tuned models scored higher, because
   they learned to finish with an answer line. A check is only as good as what it can see.
10. **Series map** (last slide), E10 marked.

## For leaders

**Ask your team:** "What else will this tuned model be asked, and have we tested it on that?"

## Decision rule (proposed)

**"Before a tuned model sees requests outside its task, test it on them: ordinary requests and
the questions it should decline. Rerun those tests after every retrain."**

## Next

E11, Where your tuned model runs: E5's tuned model on a laptop with no GPU.

## Careful with

- **All three claims failed.** Do not present E10 as "tuning breaks things"; present it as "one
  tuned model broke, and why the other did not".
- **The general check measures format.** The tuned models' higher scores are mostly brevity and
  the answer line, not better reasoning. Do not say tuning improved reasoning.
- **Nothing to lose on half the check.** Every model scored 0 on state tracking and puzzles.
- **One small model, one adapter per task, one seed.**
- **No system prompt** on the general and bleed checks; a deployment that always sends the task
  instruction may behave differently.
- **Charts:** the declines and general charts start their axis above zero (the chart library's
  default), which makes the gaps look larger. Label the counts on the bars.
- **The judge is a model,** checked against a person in Season 2 E3.

## From practice

_Brendan to add one anonymised line from his own practice._
