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
uv run lab smoke        # one tiny call per model and mode in smoke.yaml
```

`lab smoke` checks your keys and every result field before any paid run. It skips providers without a key. Running it again makes no new calls, because responses are cached. Edit `smoke.yaml` to check the models you plan to use; each must be listed in [`src/lab/providers/capabilities.yaml`](src/lab/providers/capabilities.yaml).

To follow as the harness is built: `estimate`, `run`, and `analyse`.

## Field notes

| Episode | Question | Folder |
|---|---|---|
| S1 E7 | Does a fact's position in a long context affect retrieval? | To follow |
| S1 E10 | When does turning reasoning on improve accuracy enough to justify the cost? | To follow |

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
