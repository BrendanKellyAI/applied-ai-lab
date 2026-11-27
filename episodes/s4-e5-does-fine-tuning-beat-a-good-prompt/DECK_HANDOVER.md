# S4 E5 deck handover: Field note: does fine-tuning beat a good prompt?

For the content agent. Has an experiment: a small open model, untuned and tuned on Halvard's
labelled messages, against the best prompt on the cheapest hosted model, on Task A.

## Sources of truth

- `episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/README.md` and `PREREGISTRATION.md` (with
  Amendment 1).
- `results/analysis-task-a-test.json` and `analysis-task-a-dev.json`; `results/claims-test.json`.
- Chart: `results/charts/s4-e5-does-fine-tuning-beat-a-good-prompt-fully_right-test-slide.svg`.
- The job records: `results/e5-untuned-0-6b/job.json`, `results/e5-tuned-short/job.json`; the
  cancelled arm: `results/e5-tuned-one-line/job.json`.
- The accidental rerun: `results/e5-untuned-0-6b/rerun-unapproved.md`.
- The tuning settings: `src/lab/adapt/tune_config.py`; the notebook: `season4/colab/lora_job.ipynb`.
- `season4/scoreboard.json`, `season4/reference.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E5 |
| Title | Field note: does fine-tuning beat a good prompt? |
| Hub slug | `does-fine-tuning-beat-a-good-prompt` (as on the hub) |
| Deck file | `bk-s4-e5-does-fine-tuning-beat-a-good-prompt-v1.pdf` |
| Hub format | `field_note` |

## The argument

E2 to E4 got Task A to 587 to 594 of 600 by writing a better prompt for a hosted model. Tuning is
the next rung: teach a model the task from labelled examples, so the rules live in its weights
instead of its prompt.

The test took a very small open model (Qwen3-0.6B, 0.6 billion parameters), tuned it for 28
minutes on a free GPU, and set it against the best prompt. Untuned, it got 24 right. Tuned, 592,
against 587 for the prompt: not distinguishable. It read an eighth of the input to do it. So
tuning did not beat a good prompt on accuracy; it matched it with a far smaller model and a
one-line instruction. Whether that saves money depends on what hosting the model costs, which is
Season 6.

## Scoreboard slide

Task A ladder. Chart: `s4-e5-does-fine-tuning-beat-a-good-prompt-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 (84% to 89%) | The baseline |
| E2 + definitions | 587 (96% to 99%) | Joined: the reference |
| E3 one-line + 8 similar examples | 593 (98% to 99%) | No |
| E4 the same, with JSON mode | 594 (98% to 100%) | No |
| **E5 Qwen3-0.6B, tuned on 1,600** | **592 (97% to 99%)** | **No: overlaps the reference** |

What this episode adds: a different route to the same height. The reference stays the
definitions prompt.

## Setup before results

| Arm | Model | What it is told |
|---|---|---|
| Reference | `gpt-6-luna`, reasoning off | E2's definitions prompt, about 945 tokens |
| Untuned | Qwen3-0.6B, as downloaded | the same definitions prompt |
| Tuned | Qwen3-0.6B, tuned on 1,600 labelled messages | "Triage this Halvard Home customer message as JSON." |

**What tuning means here, for the slide:** LoRA trains a small set of extra weights on top of a
frozen model, here on 1,600 messages with their correct answers, three passes through them. The
model is free to download and was pinned to an exact version. Training ran on Google Colab's
free Tesla T4 GPU.

**Worked example** (`A-test-00410`, invented): the kettle question: a new Brio kettle owner
asks whether it is normal for the steel body to get very hot while boiling.

| Arm | Reply | Right? |
|---|---|---|
| Reference | `how_to_use`, safety false, Brio kettle | Yes |
| Untuned | `how_to_use`, **safety true**, Brio kettle | No: a false alarm |
| Tuned | `how_to_use`, safety false, Brio kettle | Yes, from a one-line instruction |

The untuned model's mistake is the episode's pattern: it treated any heat word as an incident.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 587, 24, 592 of 600 | Fully right: reference, untuned, tuned | `analysis-task-a-test.json`, `arms.*.fully_right` |
| 12 and 7 | Items only the tuned model got right; only the reference | `claims-test.json`, C2 |
| 0.36 | Exact McNemar p, tuned against reference | same, C2 |
| 568 and 0 | Items tuning fixed and broke against untuned | same, C1 |
| 452 of 535 | Untuned false alarms (reference 3, tuned 1) | `analysis-task-a-test.json`, `safety_false_alarms` |
| 65 of 65 | Incidents the tuned model flagged | same, `safety_recall` |
| 112 against 945 | Input tokens per call, one tokeniser (o200k) for both | `claims-test.json`, C3 |
| 199, 12, 198 of 200 | Dev, same order | `analysis-task-a-dev.json` |
| 28 minutes; 740,118 tokens | Training time on a T4; tokens trained on | `results/e5-tuned-short/job.json` |

## Cost

No money was spent: the reference replies came from E2's cache, and the tuned arms ran on a free
GPU. What tuning cost instead was time:

| | On a free Tesla T4 |
|---|---|
| Training, 1,600 examples, 3 passes | 28 minutes |
| Predictions, tuned, per 1,000 messages | about 4 minutes |
| Predictions, untuned with the long prompt, per 1,000 messages | about 16 minutes |

The tuned model reads an eighth of the input, so it also predicts four times faster than the same
model given the long prompt. A money comparison needs a price for hosting a GPU (Season 6), so
the deck should not claim a saving.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Two ways to teach a rule.** Write it in the prompt, or train it into the weights. A
   two-column diagram.
2. **The contenders.** A hosted model with a 945-token prompt; a 0.6 billion parameter model with
   one line.
3. **The kettle, untuned.** Flagged as an incident. Then the same model, tuned: correct.
4. **Prediction.** "Untuned, how many of 600 does the small model get right?" Reader picks.
5. **Reveal.** 24. It raised 452 false alarms.
6. **What tuning took.** 1,600 examples, three passes, 28 minutes on a free GPU. A timeline.
7. **Prediction.** "Tuned, does it beat the prompt?" Reader picks.
8. **Reveal.** 592 against 587, 12 and 7 items each way: a draw.
9. **The real difference.** Input per call: 945 tokens against 112. A bar pair.
10. **The rerun nobody meant.** The pilot ran twice by accident and gave the same 800 answers.
    Greedy decoding on pinned weights is repeatable; training with a different seed is not.
11. **Scoreboard:** not joined; same height, different route.
12. **Series map** (last slide), E5 marked.

## For leaders

**Ask your team:** "If we tuned a small model to match our prompt, who would host it, and what
would that cost against the API bill it replaces?"

## Decision rule (proposed)

**"Tune when the gain is a smaller model or a shorter prompt you can measure, not to beat a
prompt that already works."**

## Next

E6, How much data does tuning need?: the same tuning at 50, 200 and 800 examples.

## Careful with

- **"Matches", not "beats".** 592 against 587 is not distinguishable (p 0.36). Do not say the
  tuned model is better.
- **Train and test come from the same generator.** The training loss fell close to zero within
  one pass, so the messages were easy to fit. Real customer messages would test it harder, and
  the prompted reference never saw train, so the comparison favours tuning.
- **One seed, default settings, one run.**
- **The one-line tuned arm was not run** (Amendment 1): C5 is not tested, so the deck cannot say
  whether the field list in the instruction mattered after tuning.
- **The rerun was unapproved** and is logged as such. Show it as a lesson about repeatability, not
  as planned evidence.
- **No saving is claimed.** Hosting costs are Season 6; where the tuned model can run is E11.

## From practice

_Brendan to add one anonymised line from his own practice._
