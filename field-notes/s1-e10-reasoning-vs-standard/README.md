# S1 E10: Reasoning versus standard

## Summary

**Reasoning paid off on the two tasks that need several steps held in mind, and on nothing
else.** Across three models and 720 calls, turning reasoning from its lowest setting to high
raised accuracy on state tracking by 18.9 points and on constraint puzzles by 21.1 points. On
extraction and short arithmetic it changed nothing beyond chance, while still costing more
tokens and time.

**Almost all of that gain came from one model.** GPT-5.6 Terra answers instantly with reasoning
off, in about nine tokens, and gets hard problems wrong that way. Claude Sonnet 5 and Gemini 3.6
Flash work the problem through in their visible reply even at their lowest setting, so they were
already right, and turning reasoning up added little. The setting matters most for a model that
would otherwise answer without thinking at all.

## The question

For which kinds of task does turning reasoning on improve accuracy enough to justify the extra
output tokens and latency?

Reasoning models bill their thinking as output tokens and take longer to answer. Neither cost is
worth paying on a task that a model gets right without thinking. This field note measures where
the extra spend buys accuracy and where it buys nothing, and supplies the evidence for the S1 E11
decision framework, "When is a reasoning model worth the cost?".

## Setup

| | |
|---|---|
| Models | GPT-5.6 Terra, Claude Sonnet 5, Gemini 3.6 Flash |
| Modes | `lowest` and `high`, on the same model |
| What `lowest` means | Reasoning off for Terra and Sonnet 5. `minimal` for Gemini 3.6 Flash, which cannot turn thinking off |
| Thinking shown | In `high` only, so every provider reports a time to first thinking |
| Temperature | Provider default for all three |
| Output limit | 2,000 tokens in `lowest`; 16,000 in `high`, so reasoning is not truncated |
| Tasks | 4 families x 30 items = 120 items |
| Calls | 3 models x 2 modes x 120 items = 720 |
| Call order | Shuffled from the seed, interleaving models and modes |

**The same model in both modes.** Comparing a reasoning model against a different non-reasoning
model would confuse the effect of reasoning with every other difference between the two. Here
only the reasoning setting changes.

**Why the modes are called `lowest` and `high`.** Gemini 3.6 Flash cannot turn thinking off, so
its lower mode is `minimal`. Calling that mode `off` would put a false word on every chart and in
every published row. `summary.csv` records the actual reasoning level each model ran with, so no
reader has to open the config to see what `lowest` meant.

Every setting each model ran with is in [`config.yaml`](config.yaml), and the versions the API
actually returned are in `results/run_metadata.json` after a run.

## Method

**Four task families, 30 items each.** They run from a control that needs no reasoning to a
search problem that does.

| Task | What it asks | Why it is here |
|---|---|---|
| Extraction | A short operations log with one invented fact, and a direct lookup question | Control: reasoning should add cost without adding accuracy |
| Short arithmetic | Word problems needing two or three operations | Light multi-step reasoning |
| State tracking | Twelve to twenty sequential changes to stock across five warehouses | Heavy multi-step reasoning |
| Constraint puzzles | Seven jobs to put in order from five to seven clues | Search and constraint satisfaction |

**Harder after the pilot.** In the first pilot, every model answered every item correctly, including five-job puzzles and six-change stock problems with reasoning at its lowest setting. A task every model already gets right cannot show what reasoning adds, so state tracking went from six to eight changes across three warehouses to twelve to twenty across five, and the puzzles from five jobs (120 possible orders) to seven (5,040). Extraction stays the control and arithmetic stays light, as designed.

**Everything is generated, and everything is committed.** Every item is built from the seed in
`config.yaml` by [`generators.py`](generators.py), so no question can have appeared in a model's
training data and no third-party text is involved. Unlike S1 E7, the items themselves are
committed, in [`tasks/items.jsonl`](tasks/items.jsonl), so a reader can read all 120 questions
rather than take the results on trust. `tasks/manifest.json` pins the seed and a checksum; a file
that no longer matches the config is rebuilt rather than used.

**Every answer is checked by a second implementation.** The test suite re-solves every generated
item independently from the published prompt: it re-does the arithmetic, replays the warehouse
movements, and brute forces all 5,040 orderings of each puzzle to confirm that exactly one fits the
clues and that it is the recorded answer. It also confirms that no clue in a puzzle is redundant.

**Prompt.** There is no system prompt, so the reasoning setting is the only difference between
the two modes. Every prompt ends with "Give your final answer on the last line in the form
ANSWER: \<value\>". Puzzle answers use a stated format, the job names in order separated by
commas.

**Scoring.** Deterministic. The last `ANSWER:` line is parsed; numeric answers must match the
expected integer exactly, and puzzle answers must match the expected order exactly once spacing
is normalised. A response with no answer line is scored incorrect and counted separately, because
a model that cannot follow the output format is a real result rather than a gap in the data. Any
response cut short by the output limit is scored incorrect and flagged.

**Intervals suited to the design.** The same items run in both modes, so the two accuracies are
not independent. Accuracy per cell is reported with a Wilson 95% interval, and the change from
`lowest` to `high` uses Newcombe's score interval for paired proportions, which is narrower than
an unpaired interval when the two modes agree on most items and stays inside -100 to +100 points
at these sample sizes.

**Pilot first.** A stratified 5% pilot of 36 calls covers all 24 model, task, and mode
combinations before the full run. The estimator bounds output tokens by the output limit until
the pilot has run; after it, the full run is projected from what the pilot actually used.

## Results

Run on 18 September 2026, between 19:15 and 20:27 UTC. All 720 calls completed.

**Accuracy change from lowest to high reasoning**, paired over the same items, three models and
30 items per task, so 90 pairs each:

| Task | Change | 95% interval | |
|---|---|---|---|
| Extraction | +0.0 points | -4.1 to +4.1 | within chance |
| Short arithmetic | -3.3 points | -9.8 to +2.2 | within chance |
| State tracking | **+18.9 points** | +10.2 to +28.4 | clear of chance |
| Constraint puzzles | **+21.1 points** | +13.1 to +30.5 | clear of chance |

**Correct answers out of 30, lowest then high:**

| Model | Extraction | Arithmetic | State tracking | Puzzles |
|---|---|---|---|---|
| GPT-5.6 Terra | 30, 30 | 30, 30 | **14, 30** | **11, 28** |
| Claude Sonnet 5 | 30, 30 | 30, 30 | 30, 30 | 29, 30 |
| Gemini 3.6 Flash | 30, 30 | 28, 25 | 28, 29 | 29, 30 |

The acid green bar on the accuracy chart is constraint puzzles: the largest gain whose interval
excludes zero **and** where every model moved the same way. State tracking also cleared
chance, but Claude Sonnet 5 did not move on it, so it does not qualify.

**What high reasoning cost**, median and 90th percentile:

| Model | Output tokens, lowest | Output tokens, high | Total time, lowest | Total time, high |
|---|---|---|---|---|
| GPT-5.6 Terra | 9 / 22 | 42 / 284 | 1.1s / 2.3s | 2.9s / 7.4s |
| Claude Sonnet 5 | 66 / 1,093 | 65 / 1,802 | 2.1s / 10.0s | 3.3s / 15.9s |
| Gemini 3.6 Flash | 94 / 636 | 706 / 3,175 | 1.6s / 4.2s | 4.4s / 17.2s |

- **Terra's gain was cheap in tokens.** On state tracking it went from 14 to 30 correct for about
  50 extra output tokens an item. Its multiples look large, 7x and 13x, only because its lowest
  setting uses almost nothing.
- **Claude used no more tokens at high than at lowest.** Hidden thinking replaced the working it
  otherwise writes out in the reply; on state tracking it billed half as many output tokens.
- **Gemini paid the most for the least.** It billed 4.6x to 16x the output tokens at high and gained
  at most one item per task.
- **Two kinds of first token.** With thinking shown, all three providers streamed thinking before
  any answer: after a median of 0.9 to 2.0 seconds, against 2.8 to 4.2 seconds for the first
  answer token. A user watching sees activity well before the answer starts.

**Parse rate 99.0%.** Seven responses had no `ANSWER:` line and are scored incorrect, as agreed
before the run. Six were Gemini 3.6 Flash at high replying with the number alone, and every one of
those numbers was right. Accepting a bare number would change Gemini's arithmetic figure from -10
points to +6.7, and the pooled arithmetic change from -3.3 to +2.2, both still within chance. It
would not change any conclusion above. The seventh was Claude Sonnet 5 at lowest on a puzzle,
which searched through the orders in its reply and ran past its 2,000-token limit, the only
response of the 720 to do so.

The charts:

- `results/charts/accuracy-by-task.png`: accuracy in both modes per task
- `results/charts/output-token-multiple-by-task.png`: how many times more output tokens high used
- `results/charts/cost-of-accuracy.png`: extra output tokens against accuracy gained, per model
  and task
- `results/charts/two-kinds-of-first-token.png`: time to first thinking against time to first
  answer token

## What it means

**Turn reasoning on for problems that need several steps held in mind at once, and leave it off
for lookups and simple sums.** On extraction and two- or three-step arithmetic, high reasoning
bought nothing on any model and cost up to 16 times the output tokens and up to 2.3 times the wait.

**Whether it pays depends as much on the model as on the task.** A model that answers
instantly with reasoning off, as GPT-5.6 Terra does, gains a great deal from turning it on, and
cheaply. A model that already writes its working into the reply, as Claude Sonnet 5 and Gemini
3.6 Flash do, has most of the benefit already; turning reasoning up moves the thinking out of
sight rather than adding much. "Reasoning off" is therefore not one condition across providers,
and a comparison between models at "off" is partly a comparison of how chatty each one is.

**Pilot before you commit.** Reasoning cost was hard to predict: the estimate before the pilot,
bounded by the output limit, was $55.82; the full run itself cost about $2. And the first version of
these tasks was too easy for any model to show a difference, which only the pilot revealed.

This is the evidence behind the S1 E11 decision framework, "When is a reasoning model worth the
cost?".

## Limitations

- Synthetic tasks represent task shapes, not every real workload. Thirty items per task detects
  large effects only.
- State tracking and the puzzles were made harder after the first pilot, in which every model
  answered every item correctly. The final tasks were then fixed before the full run, and the
  scoring rule was not changed after seeing results.
- Most models were at or near 100% on most tasks even at the lowest setting, so this measures
  where reasoning helps on these task shapes, not how far each model is from its limit.
- The pooled intervals treat 90 pairs as independent when they are 30 items put to three models,
  so they are slightly optimistic; the chart's highlight also requires every model to agree.
- Gemini 3.6 Flash cannot fully disable thinking, so its lower mode is `minimal` rather than off.
  Its accuracy and token gains from reasoning may be understated compared with the other two.
- Reasoning token reporting differs between providers. Token multiples use billed output tokens,
  which every provider reports; separate reasoning counts are shown only where a provider gives
  them.
- Thinking was shown in the `high` mode, which is why every provider has a thinking time. This
  may slightly delay the first answer token compared with a production setup that hides thinking,
  so `high` latency here may be marginally higher than it would otherwise be.
- How each provider signals thinking differs: OpenAI starts a reasoning item, Anthropic starts a
  thinking block, Google sends thought summaries only when they are requested.
- Latency depends on provider load at the time of the run. Medians and 90th percentiles are
  reported rather than means, and the run window is recorded in `results/run_metadata.json`.
- All three models ran at their provider's default temperature, which varies by provider, so
  answers may differ slightly between reruns.
- Exact reasoning and temperature settings per model and mode are in the committed
  [`config.yaml`](config.yaml).

## How to reproduce

Reproduce the charts and tables from the published results, at no cost and with no API key:

```bash
uv run lab analyse field-notes/s1-e10-reasoning-vs-standard/config.yaml
```

Rerun against current models with your own key. This makes new calls and writes to a separate
folder, leaving the published results untouched:

```bash
uv run lab run field-notes/s1-e10-reasoning-vs-standard/config.yaml --fresh
```

With one API key, run just that provider's share of the grid:

```bash
uv run lab run field-notes/s1-e10-reasoning-vs-standard/config.yaml --fresh --provider openai
```

Check the cost before spending anything. This makes no API calls:

```bash
uv run lab estimate field-notes/s1-e10-reasoning-vs-standard/config.yaml
```

The items are committed, so nothing needs building. To regenerate them and confirm they are
byte for byte the same:

```bash
uv run python field-notes/s1-e10-reasoning-vs-standard/build_dataset.py
```

## Run metadata

Every run writes `results/run_metadata.json`: the git commit and whether the tree was clean, the
harness, Python, and SDK versions, start and end times in UTC, the models requested and the
versions returned, the full config, the task items with their checksum, and counts of calls
planned, cached, made, and failed. It never contains prices or keys.
