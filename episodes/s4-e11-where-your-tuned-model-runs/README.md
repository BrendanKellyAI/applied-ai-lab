# S4 E11: Where your tuned model runs

E5 tuned a 0.6 billion parameter model on a free Colab GPU to triage Halvard's messages, and it
matched the best prompt. Once you have a small tuned model like that, where can it run: only on
a cloud GPU, or on the laptop on your desk? Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: an ordinary four-year-old laptop gave exactly the same answers as the Colab GPU, all
600 of them, character for character, and the same score, 592 of 600. It was 19 times slower:
4.7 seconds a message against 0.25.** That is still about 770 messages an hour, more than a small
team receives, using 3.2 GB of memory and no GPU. All four claims held.

## The design

- **The model:** E5's `e5-tuned-short`, Qwen3-0.6B at commit `c1899de` with its LoRA adapter
  (`adapter-1`, checked by hash against E5's job record before every run).
- **The prompts:** E5's own 600 test messages, `data/eval-test.jsonl`, written by `prepare.py`
  only if it hashes to the file E5's job used.
- **Colab:** E5's run, read from its job record. A Tesla T4, float32, greedy decoding, batches of
  16.
- **The laptop:** an Intel Core i7-8565U (4 cores, 8 threads, 2018), 16 GB of memory, no GPU,
  Windows 11. `run_local.py` runs the model the way the notebook does: float32, greedy, thinking
  off, the same chat template, left padding, batches of 8, with the package versions the Colab
  job recorded (`transformers` 4.57.1, `peft` 0.17.1) and a CPU build of PyTorch 2.14.
- **The pilot rule:** time the first 50 messages; run all 600 if they project the 600 at 45
  minutes or less, otherwise the first 200.

## Results (test, 600 messages)

| | Colab T4 | Laptop CPU |
|---|---|---|
| Replies identical to Colab's | (the comparison) | **600 of 600** |
| Fully right | 592 | **592** |
| Seconds per 1,000 messages | 247 | 4,663 |
| Seconds a message | 0.25 | 4.66 |
| Messages an hour | about 14,600 | about 770 |
| Time to load the model | | 2.3 seconds (from the local cache) |
| Peak memory | | 3.2 GB of RAM |

**The pilot:** 50 messages in 164 seconds, 3.27 seconds a message, projecting 33 minutes for the
600, so all 600 ran. All 50 pilot replies were identical to Colab's. The full run was slower than
the pilot projected: 47 minutes, not 33. The pace was steady from the first batch to the last
(about 4.4 to 4.9 seconds a message), so the first 50 messages were simply quicker than the
average, not the laptop slowing down. Had the full run's pace been known first, the rule would
have chosen 200; it was applied to the pilot, as written.

## The claims

**C1 held: the laptop gives the same answers.** 600 of 600 replies identical, character for
character (the mark was 98%). Different processors can round numbers differently and flip a
greedy choice; on this model and these messages, none did.

**C2 held: the same score on both machines.** 592 fully right on each, on the same items; no item
differs (exact McNemar p 1.0).

**C3 held: the laptop is much slower.** 18.9 times as long per message as the T4 (the mark was 5
times).

**C4 held: a laptop still keeps up with a small team.** 4.66 seconds a message, under the 10
second mark: 1,000 messages in about 78 minutes.

## What it means

The model you tune does not tie you to the machine you tuned it on. A small tuned model is a file
of 40 MB on top of a public base model; anything that can run the base model gets the same
answers. Training needed the GPU (E5: 28 minutes, 9 GB of GPU memory); answering did not. For a
team handling a few hundred messages a day, a laptop or a small server without a GPU is enough;
for thousands an hour, or replies a person waits for, it is not.

**Decision rule (proposed):** "Tune where the GPU is, then run the model wherever it is cheapest
to keep: check that it gives the same answers there before you move it."

**Ask your team:** "If we tuned a small model, how many messages an hour would it need to answer,
and does that need a GPU at all?"

## What this does not show

- **One laptop and one GPU.** A newer laptop, a different GPU or a paid Colab tier would give
  different times.
- **No tuning for speed.** Float32 and plain batching, to match Colab exactly. Quantised or
  compiled models run faster and may answer differently (Season 13).
- **A 0.6 billion parameter model, with short replies.** Larger models need more memory than a
  laptop has, and longer replies take longer; E7's 64-word replies would be slower than E5's
  one-line triage answers.
- **Throughput, not waiting time.** Messages ran in batches of 8; one message on its own takes
  less than a batch but more than its share.
- **No money.** Hosting is not priced here; that is Season 6.

## Run it

```bash
uv run python episodes/s4-e11-where-your-tuned-model-runs/prepare.py
uv run --no-project --python 3.12 --with "torch>=2.14,<2.15" --with transformers==4.57.1 \
    --with peft==0.17.1 --with accelerate==1.10.1 --with psutil \
    episodes/s4-e11-where-your-tuned-model-runs/run_local.py --adapter <folder> --name laptop
uv run python episodes/s4-e11-where-your-tuned-model-runs/claims.py
```

The adapter folder holds `adapter_config.json` and `adapter_model.safetensors` from E5's job
(`My Drive/s4-jobs/e5-tuned-short/adapter-1/`); neither file is committed. The first run downloads
the base model's weights (about 1.5 GB) from Hugging Face.

Results: `results/laptop/` (predictions and `local_result.json`), `results/pilot/`, and
`results/claims.json`.
