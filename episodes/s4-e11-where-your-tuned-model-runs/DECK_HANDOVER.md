# S4 E11 deck handover: Where your tuned model runs

For the content agent. Has an experiment: E5's tuned triage model run on a laptop's CPU and
compared with its run on a free Colab GPU. No model calls, no money.

## Sources of truth

- `episodes/s4-e11-where-your-tuned-model-runs/README.md` and `PREREGISTRATION.md`.
- `results/claims.json`; `results/laptop/local_result.json`; `results/pilot/local_result.json`.
- Colab's figures: `episodes/s4-e5-does-fine-tuning-beat-a-good-prompt/results/e5-tuned-short/job.json`.
- `season4/README.md`, the episode table.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E11 |
| Title | Where your tuned model runs |
| Hub slug | `where-your-tuned-model-runs` (proposed; confirm) |
| Deck file | `bk-s4-e11-where-your-tuned-model-runs-v1.pdf` |
| Hub format | `experiment` |

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

## The key slide

| | Colab T4 (free GPU) | Laptop (2018, no GPU) |
|---|---|---|
| Same reply as Colab | | 600 of 600 |
| Fully right | 592 of 600 | 592 of 600 |
| Seconds a message | 0.25 | 4.7 |
| Messages an hour | about 14,600 | about 770 |
| Memory | | 3.2 GB |

## The claims

- **C1 held:** 600 of 600 replies identical (mark: 98%).
- **C2 held:** 592 against 592, no item differs, p 1.0.
- **C3 held:** 18.9 times slower (mark: at least 5).
- **C4 held:** 4.66 seconds a message (mark: under 10).

## Worth saying on a slide

- **The tuned part is 40 MB.** It sits on top of a public base model; copy both and you have the
  model.
- **The pilot was optimistic.** The first 50 messages projected 33 minutes for the 600; the run
  took 47. Time a fair sample before promising a speed.

## Decision rule and question

- **Rule (proposed):** "Tune where the GPU is, then run the model wherever it is cheapest to
  keep: check that it gives the same answers there before you move it."
- **Ask your team:** "If we tuned a small model, how many messages an hour would it need to
  answer, and does that need a GPU at all?"

## What this does not show

- One laptop, one GPU; other hardware gives other times.
- Not tuned for speed: quantised or compiled models are faster and may answer differently
  (Season 13).
- A 0.6 billion parameter model with one-line answers; bigger models or longer replies need more.
- Throughput in batches of 8, not how long one person waits.
- No prices: hosting costs are Season 6.

## Charts

None made; the key slide is a table. A simple bar of seconds a message (0.25 against 4.7) would
work if a chart is wanted.

## Cost

Nothing spent. Colab's figures are E5's; the laptop was already owned. The laptop ran for about
50 minutes in all.
