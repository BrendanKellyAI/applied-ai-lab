# S4 E5: Field note: does fine-tuning beat a good prompt?

E2 to E4 reached 587 to 594 of 600 on Task A by prompting `gpt-6-luna`. Does a small open model,
tuned on Halvard's labelled messages, match that with a fraction of the prompt? Claims and pass
marks: [`PREREGISTRATION.md`](PREREGISTRATION.md), with Amendment 1.

**Result: a 0.6 billion parameter model, tuned for 28 minutes on a free GPU, matches the best
prompt with an eighth of the input.** Tuned Qwen3-0.6B got 592 of 600 fully right, against 587
for `gpt-6-luna` with the definitions prompt; the two cannot be told apart. Untuned, the same
small model got 24. Four claims held; C5 was not tested. The tuned model does not join the
reference: its interval overlaps it.

## The design

- **Data:** Task A, frozen. The tuned model trained on all 1,600 train items; dev 200 to choose,
  test 600 to report.
- **Base model:** `Qwen/Qwen3-0.6B` at commit `c1899de`, thinking off, greedy decoding. It was
  kept by the pilot rule: untuned, 192 of 200 dev replies were valid JSON (the bar was 180).
- **Adapter (LoRA):** a small set of extra weights trained on top of the frozen model. Rank 16,
  3 epochs, learning rate 2e-4, seed 1, the defaults in `src/lab/adapt/tune_config.py`. One run.
- **Arms:**

  | Arm | Model | Prompt |
  |---|---|---|
  | `e5-reference` | `gpt-6-luna`, reasoning off | E2's definitions prompt, the Task A reference (cached) |
  | `e5-untuned-0-6b` | Qwen3-0.6B, untuned | the same definitions prompt |
  | `e5-tuned-short` | Qwen3-0.6B, tuned | `Triage this Halvard Home customer message as JSON.` |

- **Not run:** `e5-tuned-one-line` (Amendment 1). Training the short arm took three times the
  estimate, and the one-line arm would have taken about 65 minutes and might not have fitted in
  the free GPU's memory.
- **Where it ran:** Google Colab, a free Tesla T4. Every job is recorded in
  `results/<arm>/job.json`, with the notebook version, base model commit, data hashes, training
  loss and the adapter's hash. Adapters stay on Google Drive and are not committed.

## Results (test, 600 items)

| Arm | Fully right | Valid | Safety recall (65) | False alarms (535) | Input tokens per call |
|---|---|---|---|---|---|
| `e5-reference` | 587 (96% to 99%) | 600 | 65 | 3 | 945 |
| `e5-untuned-0-6b` | 24 (3% to 6%) | 560 | 58 | 452 | 945 |
| **`e5-tuned-short`** | **592 (97% to 99%)** | 596 | **65** | **1** | **112** |

Input tokens are counted with one tokeniser for every arm (`o200k_base`), so the lengths compare.

Untuned, the small model flagged 452 of 535 harmless messages as incidents and got almost nothing
right. Tuned, it got every `safe_use_question` (40 of 40) and every `negated_cue` (38 of 38).
Its 8 misses: 4 replies with an invalid field value, and single field errors spread across
kinds. Against the reference, item by item: 12 the tuned model got right and the reference
missed, 7 the other way.

On dev: reference 199, untuned 12, tuned 198 of 200.

**Training:** 300 steps over 3 passes of the 1,600 examples, 740,118 tokens (Qwen's count),
28 minutes. The training loss fell from 1.14 at step 20 to 0.0015 by step 120: the model fitted
the training messages within the first pass.

## The claims

**C1 held: tuning teaches the task.** 592 against 24 for the same model untuned: 568 items fixed,
none lost (exact McNemar p below 0.0001).

**C2 held: a tuned small model matches the best prompt.** 592 against 587; 12 and 7 items each
way, exact McNemar p 0.36. Not distinguishable in either direction.

**C3 held: with a fraction of the prompt.** 112 input tokens a call against 945, a ratio of
0.12 (the pass mark was 0.2). The tuned model carries Halvard's rules in its weights instead of
its prompt.

**C4 held: without missing incidents.** 65 of 65.

**C5 not tested: once tuned, the field list adds nothing.** The one-line tuned arm was not run
(Amendment 1).

## The scoreboard

`e5-tuned-short` does not join: its interval (97.4% to 99.3%) overlaps the reference's,
`e2-definitions` (96.3% to 98.7%). The Task A reference stays `e2-definitions`. E5's tuned arm
carries forward to E6 and E10.

## The finding nobody planned for

**The pilot ran twice, and gave the same 800 answers both times.** A notebook edit that Colab
did not save ran the untuned pilot a second time, without approval. It cost nothing and is not
used, but it is a clean test of repeatability: greedy decoding on pinned weights reproduced every
answer (`results/e5-untuned-0-6b/rerun-unapproved.md`). Tuning runs, by contrast, depend on the
seed; E5 has one.

## What this does not show

- **Train and test come from the same generator.** A loss near zero within one pass says the
  training messages were easy to fit. Messages written by real customers would test the tuned
  model harder, and the prompted reference never saw train, so the comparison favours tuning.
- **Two models, not one.** The untuned arm shows the tuning, not the model, does the work.
- **One seed, default settings.** Another seed could move a few of the 19 disagreements.
- **The definitions in the reference prompt are the labeller's own rules** (E2).
- **A free T4 is not a benchmark.** Minutes are reported with the GPU type.

## Charts

`results/charts/`: **`fully_right`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

No money was spent: the reference replies came from E2's cache, and training and prediction ran
on a free Colab GPU. What tuning cost instead, on a Tesla T4:

| | Time |
|---|---|
| Training, 1,600 examples, 3 passes | 28 minutes |
| Predictions, tuned (short prompt), per 1,000 messages | about 4 minutes |
| Predictions, untuned (definitions prompt), per 1,000 messages | about 16 minutes |

The tuned model reads an eighth of the input, so it also predicts four times faster than the
same model given the long prompt. A money break-even needs the price of hosting a GPU, which is
Season 6's subject.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/config.yaml
uv run python episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/claims.py test
```

To tune again: `uv run lab adapt tune episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/tune-short.yaml`
prepares the files and prints the training tokens; a launch needs `--launch --approved-by ...`
and the notebook `season4/colab/lora_job.ipynb` on a GPU. Each job runs once: a second launch of
a succeeded job is refused.
