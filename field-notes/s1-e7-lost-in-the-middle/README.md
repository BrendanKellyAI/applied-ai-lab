# S1 E7: Lost in the middle

> Work in progress. The method, dataset, and analysis are built and tested. The results and what
> they mean are filled in after the pilot and full run, which need the owner's approval because
> they spend API budget.

## Summary

To follow after the run.

## The question

Does the position of a fact inside a long context still affect whether current models can
retrieve it, and does the effect grow with context length?

In 2023, "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al.) found that
models used information at the start and end of a long context more reliably than information in
the middle. Context windows have grown by orders of magnitude since. This experiment tests
whether the pattern still holds for three current models, from three makers.

## Setup

| | |
|---|---|
| Models | GPT-5.6 Terra, Claude Sonnet 5, Gemini 3.6 Flash |
| Reasoning | Off for Terra and Sonnet 5. Gemini 3.6 Flash cannot turn thinking off, so it ran at `minimal`, its lowest level |
| Temperature | Provider default for all three. Current OpenAI and Claude models reject temperature 0, and using 0 for Gemini alone would give it a different condition |
| Output limit | 50 tokens for Terra and Sonnet 5; 1,024 for Gemini, to leave room for reasoning tokens, which are billed as output |
| Context lengths | 4,000, 16,000, and 64,000 tokens |
| Fact positions | 0%, 25%, 50%, 75%, and 100% through the document |
| Facts per cell | 6 |
| Calls | 3 models x 3 lengths x 5 positions x 6 facts = 270 |

Each maker's balanced mid-tier model was chosen, so the comparison is like for like rather than a
flagship against a budget model. Every setting each model ran with is recorded in
[`config.yaml`](config.yaml), and the versions the API actually returned are in
`results/run_metadata.json` after a run.

## Method

**Synthetic facts in public-domain filler.** Each document is a passage from a public-domain
novel with one invented fact inserted, for example "The maintenance code for turbine K-417 is
8352." The model is then asked for that code. The facts are invented and generated from the
config seed, so no answer can have appeared in any model's training data, and the filler is out
of copyright, so anyone can rebuild the dataset.

**Paired design.** One book per fact, so the same six filler passages carry every position and
every length. Only the position of the fact changes. Comparing a model against itself on the same
text gives a tighter comparison from six calls per cell than six unrelated documents would.

**Positions and lengths are measured, not assumed.** The filler is trimmed with the `o200k_base`
tokeniser, and each fact is inserted at the sentence boundary closest to its target position, so
it never splits a sentence or an abbreviation such as "Mrs.". The build records what it actually
achieved: across all 90 documents, lengths land within **0.55%** of target and positions within
**0.59 percentage points**, against tolerances of 5% and 2%.

**Prompt.** The system prompt is "Answer using only the document provided. Reply with the value
only." The user prompt is the document in `<document>` tags, then the question.

**Scoring.** Deterministic: correct if the normalised response contains the exact inserted value
as a whole token, so "83521" does not count as containing "8352". Accuracy is reported per model,
length, and position with Wilson 95% intervals, which suit six trials per cell better than the
normal approximation. Any response cut short by the output limit is scored incorrect and flagged
in the report, because a truncated answer would otherwise quietly distort accuracy.

**Pilot first.** A structured pilot of 21 calls covers every model, length, and position, and
exercises the 64,000-token path for each provider, for about 4% of the full run's cost. Testing
the pipeline cheaply before spending the budget is the point.

### Source books

Pinned by identifier with the SHA-256 of the mirror file, so the dataset is byte-identical for
every reader or the build fails.

| Fact | Book | Author | Gutenberg ID |
|---|---|---|---|
| 0 | Pride and Prejudice | Jane Austen | 1342 |
| 1 | Moby Dick; or, The Whale | Herman Melville | 2701 |
| 2 | Great Expectations | Charles Dickens | 1400 |
| 3 | A Tale of Two Cities | Charles Dickens | 98 |
| 4 | Dracula | Bram Stoker | 345 |
| 5 | Frankenstein; Or, The Modern Prometheus | Mary Wollstonecraft Shelley | 84 |

All six are public domain in the United States. The Project Gutenberg header and footer are
stripped, so the Project Gutenberg trademark and its licence do not apply to the extracted text.
Downloads come from a mirror, never the main site, which is for human readers only under Project
Gutenberg's robot policy. See [`datasets/README.md`](../../datasets/README.md).

## Results

To follow after the run. The analysis writes:

- `results/summary.csv`, one row per call, including the reasoning level each model ran with
- `results/charts/accuracy-heatmap-<model>.png` and `.svg`, position against context length, with
  the largest drop from the 0% position outlined in acid green
- `results/charts/accuracy-by-position-64000.png` and `.svg`, accuracy by position at 64,000
  tokens, with the model that dips deepest between the 25% and 75% positions in acid green

## What it means

To follow after the run.

## Limitations

- A single inserted fact is easier than real multi-document reasoning. This measures retrieval,
  not comprehension.
- Six facts per cell gives wide confidence intervals. The intervals are published with every
  number, and differences that fall inside them are not claimed as findings.
- Results apply to the specific model versions and dates recorded in `results/run_metadata.json`.
- Synthetic facts in novel text are stylistically out of place, which may make them easier to
  spot than real information in a real document.
- Gemini 3.6 Flash cannot fully turn thinking off; it ran at `minimal`, its lowest level, while
  the other two models had reasoning fully off. Gemini 2.5 Flash, which can disable thinking, is
  closed to new API users.
- All three models ran at their provider's default temperature, which varies by provider, so
  answers may differ slightly between reruns.
- Context lengths are measured with one tokeniser (`o200k_base`), so each provider's actual token
  count differs. Claude's tokeniser counts roughly 30% more tokens for the same text.
- Some providers cache repeated prompt prefixes automatically, and the paired design means
  prompts share long prefixes. This does not change accuracy, but token and latency figures here
  are not a clean measure of cost.
- Latency is recorded for context but is not a finding in this episode.

## How to reproduce

Reproduce the charts and tables from the published results, at no cost and with no API key:

```bash
uv run lab analyse field-notes/s1-e7-lost-in-the-middle/config.yaml
```

Rerun against current models with your own key. This makes new calls and writes to a separate
folder, leaving the published results untouched:

```bash
uv run lab run field-notes/s1-e7-lost-in-the-middle/config.yaml --fresh
```

With one API key, run just that provider's share of the grid:

```bash
uv run lab run field-notes/s1-e7-lost-in-the-middle/config.yaml --fresh --provider openai
```

Check the cost before spending anything. This makes no API calls:

```bash
uv run lab estimate field-notes/s1-e7-lost-in-the-middle/config.yaml
```

The dataset is rebuilt automatically on the first run, which downloads the six books once and
caches them. To build it on its own:

```bash
uv run python field-notes/s1-e7-lost-in-the-middle/build_dataset.py
```

## Run metadata

Every run writes `results/run_metadata.json`: the git commit and whether the tree was clean, the
harness, Python, and SDK versions, start and end times in UTC, the models requested and the
versions returned, the full config, the source books with their licences and checksums, and
counts of calls planned, cached, made, and failed. It never contains prices or keys.
