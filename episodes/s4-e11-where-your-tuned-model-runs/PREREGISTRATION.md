# S4 E11 pre-registration: where your tuned model runs

Written before the laptop run and not edited after; any later change goes in a dated amendment
at the end. Every claim is reported in `README.md` as Held, Failed or Not tested. The pass marks
are in `claims.yaml`.

## Why this question

The plan's E11 compared a model tuned on a rented GPU with one tuned through a provider's API.
No provider API offered tuning this season (`season4/PLAN.md`, section 1a), so every tuned model
is already an open model you host. Brendan chose, on 24 November 2026, to use the slot for the
question that leaves: once you have a small tuned model, where can it run? A free cloud GPU, or
the laptop on your desk?

## Setup

- **The model:** E5's `e5-tuned-short`: Qwen3-0.6B at commit `c1899de` with its adapter
  (`adapter-1`, hash `f95c6c8f...`), the Task A triage model that matched the best prompt (592
  of 600).
- **The prompts:** exactly those E5's Colab job used: `data/eval-test.jsonl`, written by
  `prepare.py`, which refuses to write it unless it hashes to the file E5's job recorded.
- **Colab:** E5's own run, read from its job record: a Tesla T4, 600 test messages in 148.4
  seconds (247.3 seconds per 1,000), float32, greedy decoding, batches of 16.
- **The laptop:** this machine, an Intel Core i7-8565U (4 cores, 8 threads), 16 GB of memory, no
  GPU, Windows 11. `run_local.py` loads the same base model at the same commit from Hugging Face
  and the same adapter (downloaded from Drive and checked by hash), and runs it the way the
  notebook does: float32, greedy, thinking off, the same chat template, left padding, batches of
  8. It uses the package versions the Colab job recorded (`transformers` 4.57.1, `peft` 0.17.1),
  in a temporary environment, with a CPU build of PyTorch 2.14.
- **The pilot rule:** first the first 50 test messages, timed. If they project the 600 at 45
  minutes or less, all 600 run; otherwise the first 200, and every claim is on those.
- **Downloads, approved by Brendan on 24 November 2026:** the base model's weights (about 1.2 GB)
  from Hugging Face, and the adapter from his Drive. Neither is committed.

## Measures

- Replies identical to Colab's, character for character.
- Fully right on each machine, on the same items, and the items that differ.
- Seconds per 1,000 messages, the time to load the model, and peak memory.

## Claims

**C1. The laptop gives the same answers.**

- *Pass mark:* at least 98% of the laptop's replies are identical to Colab's.

**C2. The same score on both machines.**

- *Pass mark:* fully right does not differ between the laptop and Colab, exact McNemar p of
  0.05 or more.

**C3. The laptop is much slower.**

- *Pass mark:* the laptop takes at least 5 times as long per message as the Colab T4.

**C4. A laptop still keeps up with a small team.**

- *Pass mark:* the laptop takes under 10 seconds a message (1,000 messages in under 3 hours).

## The scoreboard

No change: the model is E5's, and its answers are the comparison, not a new rung.

## Cost

No money is spent: Colab's figures are E5's, and the laptop is already owned. The time on the
laptop is reported; pricing hardware or hosting is Season 6, and serving speed, quantisation and
hardware choices are Season 13.

## What E11 cannot show

- **One laptop and one GPU.** A newer laptop, a different GPU or a paid Colab tier would give
  different times.
- **No tuning for speed.** Float32 and plain batching, to match Colab exactly; quantised or
  compiled models run faster and may answer differently (Season 13).
- **A 0.6 billion parameter model.** Larger models need more memory than a laptop has.
- **Small numeric differences between processors** can change a greedy answer; C1 measures how
  often.
