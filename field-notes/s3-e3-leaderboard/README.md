# S3 E3: Does the leaderboard predict your task? (field note)

Do public benchmark rankings hold on your own work? Eight answer models, ordered by the
Artificial Analysis Intelligence Index, run through the Season 2 reference system on the 520
Halvard Home test questions (an invented firm). Claims:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

## Status: run incomplete

The full run stopped part way when the Anthropic account ran out of credit (19 October 2026).
No claim is stated until every arm is complete; the analysis refuses to run claims on an arm
with unanswered or unjudged items.

| Arm | State |
|---|---|
| `gpt-6-luna` (the reference, from cache) | complete: 354 of 400 right, 107 of 120 declined |
| `gpt-6.1-sol` | complete: 359 of 400 right, 103 of 120 declined |
| `gpt-5.6-terra` | complete: 356 of 400 right, 101 of 120 declined |
| `claude-opus-5-5` | 210 of 520 answers made; the rest need Anthropic credit |
| `claude-sonnet-5-5`, `claude-haiku-5-5` | answers need Anthropic credit |
| `gemini-3.8-flash`, `gemini-3.5-flash-lite` | answers made; their judge (`claude-sonnet-5-5`) needs Anthropic credit |

Done: the pilot (32 items per model), the smoke test, the judge check that ruled out
`claude-haiku-5-5` as a cheaper second judge (`judge-switch/`), and the two-judge agreement on a
shared 100-item sample (`results/2026-10/judge-agreement/report.json`: the judges agreed on 97
of 100 declines, 96 of 100 correctness calls and 99 of 100 faithfulness calls).

## Finish the run

```bash
uv run lab rag run field-notes/s3-e3-leaderboard/config.yaml
```

```bash
uv run lab rag analyse field-notes/s3-e3-leaderboard/config.yaml
```

Every call already made is served from the cache, so the rerun makes only the missing calls.
