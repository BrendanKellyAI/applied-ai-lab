# S4 E6: Field note: how much data does tuning need?

E5 tuned Qwen3-0.6B on all 1,600 labelled Task A messages and matched the best prompt. Labelled
data is the expensive part. How few examples are enough, and where does adding more stop
helping? Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: 800 examples are enough, and 200 are not.** The curve climbs from 60 of 600 at 50
examples to 450 at 200 and 589 at 800, where it meets the prompt (587) and stops: 1,600 adds
three items, which is noise. All four claims held. No size joins the reference.

## The design

- **Data:** Task A, frozen. Test 600 to report; dev 200 is scored but chooses nothing.
- **Training sets, nested:** the first 50, 200 and 800 of the same seeded shuffle of train that
  E5 used, so each set is the start of the next and of E5's 1,600.
- **Everything else is E5's `e5-tuned-short`:** `Qwen/Qwen3-0.6B` at commit `c1899de`, the short
  instruction (`Triage this Halvard Home customer message as JSON.`), LoRA rank 16, 3 epochs,
  learning rate 2e-4, seed 1, greedy decoding. One run per size.
- **Reused points:** the untuned model (0 examples), the 1,600 model and the prompted reference
  are E5's prediction files, read in place; `config.yaml` names them.
- **Where it ran:** three jobs on a free Colab Tesla T4, each in its own runtime and notebook
  copy, recorded in `results/<arm>/job.json`.

## Results (test, 600 items)

| Examples | Fully right | Valid | Safety recall (65) | False alarms (535) | Training steps | Final loss | Training time |
|---|---|---|---|---|---|---|---|
| 0 (untuned, definitions prompt) | 24 (3% to 6%) | 560 | 58 | 452 | 0 | | |
| 50 | 60 (8% to 13%) | 67 | 0 | 0 | 12 | 1.18 | 1 minute |
| 200 | 450 (71% to 78%) | 501 | 62 | 6 | 39 | 0.44 | 3 minutes |
| **800** | **589 (97% to 99%)** | 594 | **64** | **1** | 150 | 0.14 | 13.5 minutes |
| 1,600 (E5) | 592 (97% to 99%) | 596 | 65 | 1 | 300 | 0.08 | 28 minutes |
| Prompt (`gpt-6-luna`, definitions) | 587 (96% to 99%) | 600 | 65 | 3 | | | |

"Final loss" is the mean training loss over the run. Intervals are Wilson 95%.

On dev the same shape: 12, 17, 152, 198 and 198 of 200, against 199 for the prompt.

**What 50 examples teach: the shape, not the words.** The 50-example model answers in the right
JSON form almost every time, but fills the fields with values from outside Halvard's lists: a
route called `safety`, made-up fault names. 516 of its 600 replies had an invalid field value,
so only 67 were valid. It never flagged a safety item. With 7 safety examples in its training
set, it had not learned that the flag means anything.

**At 200 the model knows the vocabulary** (501 valid, 62 of 65 incidents caught) and misses on
the harder kinds: 29 of 44 messages naming two products, 25 of 38 with a negated cue. At 800
those close to the reference's level (44 and 38).

## The claims

**C1 held: fifty examples are not enough.** 60 against 587 for the prompt; the prompt got 527
items the tuned model missed and none the other way (exact McNemar p below 0.0001).

**C2 held: a few hundred examples are enough.** The smallest size that matches the prompt is
800: 589 against 587, 12 and 10 items each way, p 0.83. 200 does not match: 450 against 587,
p below 0.0001.

**C3 held: beyond 800, more data adds nothing measurable.** 800 against 1,600: 589 and 592, 4
and 7 items each way, p 0.55.

**C4 held: the smallest matching size still catches incidents.** 800 examples: 64 of 65 safety
items flagged (98.5%; the mark was 95%), with 1 false alarm.

## The scoreboard

No change. The 800 model's interval (96.7% to 99.0%) overlaps the reference's, `e2-definitions`
(96.3% to 98.7%), so it does not clear the strict bar. The sizes are points on E5's rung, not a
new rung.

## What this means for a tuning project

Labelling 800 messages instead of 1,600 halves the labelling and the training time and loses
nothing measurable here. The curve, not the total, is what to buy: 200 examples looked cheap and
fell 137 items short. The rule this episode adds to the readiness checklist
(`season4/finetune-readiness.md`, section 2) is to label a few hundred, train, and keep labelling
only while the curve is still rising.

## What this does not show

- **One draw of each subset and one seed.** A different 50 or 200 could score quite
  differently; the curve is one path, not a band. Where it crosses the prompt, somewhere between
  200 and 800, is not pinned down: 400 was not tried.
- **Fixed epochs.** Smaller sets also got fewer steps (12 against 300). More epochs on 50 or 200
  examples might do better, and was not tried.
- **Train and test come from one generator.** Few examples may go further here than they would
  on messages written by real customers.
- Halvard's numbers are one worked case, not a rule for other tasks.

## Charts

`results/charts/`: **`fully_right`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

No money was spent: every reply was made on a free Colab GPU or read from E5's files. Time on a
Tesla T4: 1, 3 and 13.5 minutes of training for 50, 200 and 800 examples, and 3 to 7 minutes of
predictions per job for 800 messages (the 50-example model wrote longer, wandering replies). All three jobs took about 30 minutes of GPU time.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e6-how-much-data-does-tuning-need/config.yaml
uv run python episodes/s4-e6-how-much-data-does-tuning-need/claims.py test
```

To tune again: `uv run lab adapt tune episodes/s4-e6-how-much-data-does-tuning-need/tune-800.yaml`
prepares the files; a launch needs `--launch --approved-by ...` and the notebook
`season4/colab/lora_job.ipynb` on a GPU. Each job runs once.
