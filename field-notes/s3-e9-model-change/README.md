# S3 E9: Does it survive a model change? (field note)

What breaks when you switch provider, or when the provider updates the model under you? The
Season 2 reference system on the 520 Halvard Home test questions (an invented firm), with only
the answer model changing. Claims: [`PREREGISTRATION.md`](PREREGISTRATION.md).

## Status: run incomplete

The full run stopped part way when the Anthropic account ran out of credit (19 October 2026).
No claim is stated until every arm is complete.

| Arm | State |
|---|---|
| `baseline`: `gpt-6-luna` (from cache) | complete |
| `version`: `gpt-5.6-luna` | complete |
| `provider`: `claude-haiku-5-5` | 293 of 520 answers made; the rest need Anthropic credit |
| `provider-google`: `gemini-3.5-flash-lite` | answers made; its judge (`claude-sonnet-5-5`) needs Anthropic credit |

## Finish the run

```bash
uv run lab rag run field-notes/s3-e9-model-change/config.yaml
```

```bash
uv run lab rag analyse field-notes/s3-e9-model-change/config.yaml
```
