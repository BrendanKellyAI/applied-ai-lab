# applied-ai-lab

The code behind every technical field note in the applied AI series by Brendan Kelly. Each field
note answers one practical question with a small, reproducible experiment, and every result in
the series can be reproduced from this repository.

## Principles

- **Reproducible by readers.** Anyone with one provider API key can rerun an experiment with a
  single command.
- **Vendor neutral.** Models are called through each maker's own API. No cloud platform sits in
  the middle.
- **Cheap to rerun.** Every response is cached, so analysis never pays for the same tokens twice.
- **Honest.** Every result records exactly how it was produced, including its limitations.
- **Public data only.** Every dataset is public domain or generated here.

## Field notes

| Episode | Question | Folder |
|---|---|---|
| S1 E7 | Does a fact's position in a long context affect whether a model retrieves it? | [field-notes/s1-e7-lost-in-the-middle](field-notes/s1-e7-lost-in-the-middle/) |
| S1 E10 | For which tasks does turning reasoning on improve accuracy enough to justify the cost? | [field-notes/s1-e10-reasoning-vs-standard](field-notes/s1-e10-reasoning-vs-standard/) |

Each field note folder holds its config, the code that builds its data and analyses its
results, and a README with the question, method, results, limitations, and how to reproduce it.
Sources and licences for every dataset are in [datasets/README.md](datasets/README.md).

## Episode code

| Episode | Sample | Folder |
|---|---|---|
| S1 E1 | Your first API call | [episodes/s1-e1-one-token-at-a-time](episodes/s1-e1-one-token-at-a-time/) |
| S1 E2 | The same sentence, counted in tokens in three languages | [episodes/s1-e2-tokens](episodes/s1-e2-tokens/) |
| S1 E3 | Embeddings: how close texts are in meaning, and where closeness misleads | [episodes/s1-e3-embeddings](episodes/s1-e3-embeddings/) |
| S1 E4 | Attention: where GPT-2 looks from the word "it", measured | [episodes/s1-e4-attention](episodes/s1-e4-attention/) |
| S1 E5 | The transformer: reading a prompt against writing one, timed on GPT-2, and its size measured | [episodes/s1-e5-the-transformer](episodes/s1-e5-the-transformer/) |
| S1 E6 | Context windows: two silent failures at the edge, an answer cut off and instructions trimmed away | [episodes/s1-e6-context-windows](episodes/s1-e6-context-windows/) |
| S1 E8 | Sampling: GPT-2's real next-token odds, how temperature reshapes them, and what repeated calls return | [episodes/s1-e8-sampling](episodes/s1-e8-sampling/) |
| S1 E9 | Hallucination: whether a model describes invented Acts and papers as real, and whether "say if you do not know" helps | [episodes/s1-e9-hallucination](episodes/s1-e9-hallucination/) |

## Reproduce a result for free

Published results are committed, so the charts and tables can be rebuilt with no API key and at
no cost:

```bash
uv sync
uv run lab analyse field-notes/s1-e7-lost-in-the-middle/config.yaml
```

The rest of this page is for rerunning an experiment against current models with your own keys.

## Setup

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/),
which installs everything else.

Install uv on macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then clone the repository and install its dependencies:

```bash
git clone https://github.com/BrendanKellyAI/applied-ai-lab.git
cd applied-ai-lab
uv sync
```

### API keys

Copy the example file and add a key for each provider you want to use. One key is enough to
reproduce part of an experiment.

```bash
cp .env.example .env
```

| Variable | Provider | Notes |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | |
| `ANTHROPIC_API_KEY` | Anthropic | |
| `ANTHROPIC_WORKSPACE_ID` | Anthropic | Only if your key is not scoped to a single workspace. Without it, every request is refused |
| `GOOGLE_API_KEY` | Google | `GEMINI_API_KEY` also works. On the Gemini free tier you are limited to a few requests per minute; see below |

`.env` is gitignored. Keys are never printed, logged, cached, or written to results.

### Check your keys first: `lab smoke`

Before spending anything on an experiment, run the smoke test:

```bash
uv run lab smoke
```

It makes a few tiny calls per model: one with reasoning at its lowest setting and a trivial
prompt, and one with high reasoning, thinking shown, and a small puzzle that needs reasoning. It
then prints every result field, including the model version the provider actually returned,
token counts, and time to the first answer token and to the first thinking. It fails if a field
is missing, if a model reports reasoning tokens with reasoning off, or if a model does not think
when thinking is shown.

Providers without a key are skipped. Responses are cached, so running it again makes no new
calls; `uv run lab smoke --fresh` re-measures with new calls.

**Changing the models it checks.** Edit [`smoke.yaml`](smoke.yaml) to add the models you plan to
use. Every model must be listed in
[`src/lab/providers/capabilities.yaml`](src/lab/providers/capabilities.yaml), which records the
reasoning levels, temperature support, and output limits each model accepts. A setting a model
does not accept is refused before any call is made, never quietly changed.

## Running an experiment

```bash
uv run lab estimate <config.yaml>          # tokens and cost; makes no API calls
uv run lab run <config.yaml> --pilot       # the small pilot the config defines
uv run lab run <config.yaml> --fresh       # the full experiment, into a separate folder
uv run lab analyse <config.yaml>           # score, tabulate, and chart the results
```

**Estimate first.** `lab estimate` shows tokens for the pilot and the full run. To see costs,
copy `prices.example.yaml` to `prices.local.yaml` (gitignored), fill in current prices from each
provider's pricing page, and set a budget per experiment. `lab run` then refuses to start if the
calls it would make are estimated to cost more than that budget. Published results never include
prices.

**Pilot next.** Each config defines a small pilot that covers every model and condition for a few
percent of the cost. It tests prompts, parsing, and output limits before the budget is spent.

**Rerunning is safe.** `lab run` validates every planned call before sending any, writes each
result the moment it arrives, and never repeats a call that is already complete. Interrupting a
run and running the same command again picks up where it stopped, and failed calls are retried.

**Your results stay separate.** Without `--fresh`, `lab run` resumes into the field note's
committed `results/` folder. With `--fresh`, it makes new calls into a separate, gitignored
`results-fresh/` folder, leaving the published results untouched. Point `lab analyse` at it with
`--results`.

**One key is enough.** `--provider openai` (or `anthropic`, or `google`) runs one provider's share
of the grid. A pilot run with `--provider` makes exactly the pilot calls for that provider.

### Rate limits

Each config sets conservative request limits for entry-level API tiers. If your account allows
more, raise `limits` in the config locally; if a provider returns rate limit errors, lower them.
The Gemini API's free tier allows only a few requests per minute, so a Google run on a free-tier
key will be slow and may need several passes. Failed calls are retried on the next run.

## Development

```bash
uv run pytest               # with a coverage gate of 85%
uv run ruff check
uv run ruff format --check
```

Every provider test uses mocked SDK responses, so the test suite makes no API calls and needs no
keys.

## Licence

MIT. See [LICENSE](LICENSE).
