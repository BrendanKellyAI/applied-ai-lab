# S1 E10: Reasoning versus standard

> Work in progress. The tasks, method, and analysis are built and tested. The results and what
> they mean are filled in after the pilot and full run, which need the owner's approval because
> they spend API budget.

## Summary

To follow after the run.

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

To follow after the run. The analysis writes:

- `results/summary.csv`, one row per call, including the reasoning level and whether thinking was
  shown
- `results/charts/accuracy-by-task.png` and `.svg`, accuracy in both modes per task, with the
  high bar in acid green for the task with the largest gain whose 95% interval excludes zero
- `results/charts/output-token-multiple-by-task.png` and `.svg`, how many times more output
  tokens high reasoning billed, with the largest multiple in acid green
- `results/charts/cost-of-accuracy.png` and `.svg`, extra output tokens against accuracy gained,
  one point per model and task, with the best accuracy per 1,000 extra tokens in acid green
- `results/charts/two-kinds-of-first-token.png` and `.svg`, time to first thinking against time
  to first answer token, with the longest wait in acid green

## What it means

To follow after the run.

## Limitations

- Synthetic tasks represent task shapes, not every real workload. Thirty items per task detects
  large effects only.
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
