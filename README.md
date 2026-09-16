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

To follow as the harness is built: `smoke`, `estimate`, `run`, and `analyse`.

## Field notes

| Episode | Question | Folder |
|---|---|---|
| S1 E7 | Does a fact's position in a long context affect retrieval? | To follow |
| S1 E10 | When does turning reasoning on improve accuracy enough to justify the cost? | To follow |

## Episode code

| Episode | Sample | Folder |
|---|---|---|
| S1 E1 | Your first API call | To follow |

## Development

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```

## Licence

MIT. See [LICENSE](LICENSE).
