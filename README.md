# applied-ai-lab

The code behind every technical field note in the applied AI series by Brendan Kelly. Each field note answers one practical question with a small, reproducible experiment.

> Work in progress. This README is an outline and is completed as the harness is built.

## Principles

- **Reproducible by readers.** Anyone with one provider API key can rerun an experiment with a single command.
- **Vendor neutral.** Models are called through each maker's own API.
- **Cheap to rerun.** Every response is cached, so analysis never pays for the same tokens twice.
- **Honest.** Every result records exactly how it was produced, including limitations.
- **Public data only.**

## Setup

Requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env    # then add your API keys
```

## Commands

```bash
uv run lab smoke                    # a few tiny calls per model in smoke.yaml
uv run lab smoke --fresh            # the same, ignoring the cache, to re-measure latency
uv run lab estimate <config.yaml>   # tokens and cost for the pilot and full run; no API calls
uv run lab run <config.yaml>        # run an experiment, resumable
uv run lab analyse <config.yaml>    # score, tabulate, and chart committed results; no API key
```

`lab smoke` checks your keys and every result field before any paid run. It skips providers without a key. Running it again makes no new calls, because responses are cached. Edit `smoke.yaml` to check the models you plan to use; each must be listed in [`src/lab/providers/capabilities.yaml`](src/lab/providers/capabilities.yaml).

`lab estimate` shows tokens for the pilot and the full run. To see costs and check a budget, copy `prices.example.yaml` to `prices.local.yaml` (gitignored) and fill in current prices and a budget per experiment. Published results never include prices.

`lab run` validates every planned call before sending any, so an unsupported setting fails before
it costs anything, and it refuses to start if the estimate exceeds the budget in
`prices.local.yaml`. It resumes: a call already complete in `results/raw.jsonl` is never repeated.
`--pilot` runs the pilot defined by the config, `--provider` runs one provider only, and `--fresh`
makes new calls into a separate folder, leaving committed results untouched. Interrupting a run is
safe.

`lab analyse` works from committed results with no API key, so anyone can reproduce the charts and
tables for free. It loads the field note's own `analyse.py`.

If your Anthropic key is not scoped to a single workspace, also set `ANTHROPIC_WORKSPACE_ID` in `.env`.

## Field notes

| Episode | Question | Folder |
|---|---|---|
| S1 E7 | Does a fact's position in a long context affect retrieval? | [field-notes/s1-e7-lost-in-the-middle](field-notes/s1-e7-lost-in-the-middle/) |
| S1 E10 | When does turning reasoning on improve accuracy enough to justify the cost? | [field-notes/s1-e10-reasoning-vs-standard](field-notes/s1-e10-reasoning-vs-standard/) |

Each field note builds its own data from the seed in its config. S1 E10's task items are wholly
generated, so all 120 questions are committed; S1 E7's documents contain Project Gutenberg text,
so they are rebuilt rather than committed. Sources and licences are in
[datasets/README.md](datasets/README.md).

## Episode code

| Episode | Sample | Folder |
|---|---|---|
| S1 E1 | Your first API call | [episodes/s1-e1-one-token-at-a-time](episodes/s1-e1-one-token-at-a-time/) |

## Development

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```

## Licence

MIT. See [LICENSE](LICENSE).
