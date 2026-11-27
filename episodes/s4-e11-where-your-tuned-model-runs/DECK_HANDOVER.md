# S4 E11 deck handover: Where your tuned model runs

For the content agent. Has an experiment: E5's tuned triage model run on a laptop's CPU and
compared with its run on a free Colab GPU. No model calls, no money.

## Sources of truth

- `episodes/s4-e11-where-your-tuned-model-runs/README.md` and `PREREGISTRATION.md`.
- `results/claims.json`; `results/laptop/local_result.json` and `predictions-test.jsonl`;
  `results/pilot/local_result.json`.
- Colab's figures: `episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/results/e5-tuned-short/job.json`
  and its `predictions-test.jsonl`.
- `season4/README.md`, the episode table.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E11 |
| Title | Where your tuned model runs |
| Hub slug | `where-your-tuned-model-runs` (as on the hub) |
| Deck file | `bk-s4-e11-where-your-tuned-model-runs-v1.pdf` |
| Hub format | `explainer` |

The plan's title was "Open weights: tuning a model you host". No provider offered tuning through
its API this season, so every tuned model was already one you host; Brendan chose on 24 November
2026 to ask where it can run instead.

## The argument

E5 tuned a small model on a rented GPU and it matched the best prompt. The next question a
manager asks: do we now need GPUs to run it? The test ran the same tuned model, the same 600
messages and the same settings on an ordinary 2018 laptop with no GPU.

It gave the same answer to every message, word for word, and the same score. It was 19 times
slower, but at 4.7 seconds a message it still answers about 770 an hour. Training needs the GPU;
answering, for a small model and a small team, does not.

## Scoreboard slide

No change. The model is E5's (`e5-tuned-short`, 592 of 600 on Task A), and its answers are the
comparison, not a new rung. If the deck shows the ladder, mark E5's row: "the same 592 on a
laptop".

## Setup before results

**The model:** E5's tuned triage model. A public base model (Qwen3-0.6B, 1.5 GB) plus the tuned
part, an adapter of 40 MB, checked by its hash before every run.

| | Colab | Laptop |
|---|---|---|
| Machine | Tesla T4 GPU, free tier | Intel Core i7-8565U, 4 cores, 16 GB, 2018, no GPU |
| Model | the same base and adapter | the same, downloaded and checked by hash |
| Settings | float32, greedy, batches of 16 | float32, greedy, batches of 8 |
| Messages | E5's 600 test messages | the same file, checked by hash |

**The pilot rule, stated before the run:** time 50 messages first; run all 600 if that projects
45 minutes or less, otherwise 200.

**Worked example:** pick any message; the reply is the same line of JSON on both machines. The
point of the slide is that nothing differs but the clock.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 600 of 600 | Laptop replies identical to Colab's, character for character | `results/claims.json`, C1 |
| 592 and 592; 0 items differ | Fully right on each machine | same, C2 |
| 247 and 4,663 seconds | Per 1,000 messages, Colab and laptop | C3; `local_result.json`, `seconds_per_1000` |
| 18.9 times | How much slower the laptop is | C3 |
| 4.66 seconds | The laptop, per message (mark: under 10) | C4 |
| about 770 an hour | Messages the laptop answers | derived: 3,600 / 4.66 |
| 3.2 GB | Laptop peak memory | `local_result.json`, `peak_ram_gb` |
| 3.27 seconds, 33 minutes | The pilot's pace and its projection for 600 | `results/pilot/local_result.json` |
| 47 minutes | What the 600 actually took | `local_result.json`, `seconds` |

## Cost

Nothing spent. Colab's figures are E5's; the laptop was already owned. The laptop ran for about
50 minutes in all. Hosting costs are Season 6.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **"Do we need GPUs now?"** The question a manager asks after E5.
2. **What a tuned model is.** A public base model plus a 40 MB file. Two boxes.
3. **Two machines.** A free cloud GPU and a 2018 laptop, side by side.
4. **Prediction.** "Out of 600 messages, how many answers will differ?" Reader picks.
5. **Reveal.** None. 600 of 600 identical; 592 right on both.
6. **Prediction.** "How much slower is the laptop?"
7. **Reveal.** 19 times: 0.25 seconds against 4.7. Two bars.
8. **Is slow too slow?** 770 messages an hour: more than a small team receives.
9. **The pilot was optimistic.** 33 minutes projected, 47 taken. Time a fair sample.
10. **Series map** (last slide), E11 marked.

## For leaders

**Ask your team:** "If we tuned a small model, how many messages an hour would it need to answer,
and does that need a GPU at all?"

## Decision rule (proposed)

**"Tune where the GPU is, then run the model wherever it is cheapest to keep: check that it gives
the same answers there before you move it."**

## Next

E12, Prompt, retrieve, or tune?: the season's decision card.

## Careful with

- **One laptop and one GPU.** Other hardware gives other times; present 19 times as this pair's,
  not a rule.
- **Not tuned for speed.** Quantised or compiled models are faster and may answer differently
  (Season 13).
- **A 0.6 billion parameter model with one-line answers.** Longer replies (E7's run to 64
  words) or bigger models take longer and need more memory.
- **Throughput in batches of 8,** not how long one customer waits for one reply.
- **Identical here is not identical everywhere.** Different processors can round differently;
  this pair did not, on these messages.

## From practice

_Brendan to add one anonymised line from his own practice._
