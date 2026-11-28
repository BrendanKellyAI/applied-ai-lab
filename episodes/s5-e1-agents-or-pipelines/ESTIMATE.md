# S5 E1 token estimate for the spend gate

28 November 2026, from `uv run lab agent estimate <config>` (a dry run on the mock provider; see
`season5/token-method.md`). All calls are `gpt-6-luna`, reasoning off. Costs go to Brendan at the
gate, never into this repo.

| Run | Arm | Case runs | Model calls | Input tokens | Output tokens | Input a case (median / 90th pct / largest) |
|---|---|---|---|---|---|---|
| Dev pilot | pipeline | 58 | 116 | 58,601 | 8,120 | 1,014 / 1,027 / 1,032 |
| Dev pilot | agent | 58 | 466 | 1,582,317 | 55,920 | 25,345 / 35,759 / 45,269 |
| Test | pipeline | 236 | 472 | 237,865 | 33,040 | 1,012 / 1,024 / 1,032 |
| Test | agent | 236 | 1,898 | 6,486,732 | 227,760 | 26,946 / 35,567 / 47,623 |
| Repeats | agent | 120 new (60 from the test run's cache) | about 994 | about 3,407,000 | about 119,000 | 28,400 / 36,000 / 46,414 |
| Search tool | agent | allowance | about 414 rerank calls | about 2,070,000 | about 41,000 | one search a case at about 5,000 tokens |
| **Total** | | | about 4,360 | **about 13,840,000** | **about 485,000** | |

- **Not in the dry run:** the oracle never searches the knowledge base. Each real search is one
  embedding (tiny) and one `gpt-6-luna` rerank call of 3,500 to 8,000 tokens, so the table allows
  one search a case.
- **Cached input:** each turn resends the history, and OpenAI bills a repeated prefix of 1,024
  tokens or more at the cached rate, so the money spent should be well under the uncached figure.
- **Ceiling:** every case at its 150,000 input token cap would be about 62 million input tokens.
  The run cannot reach it: `lab agent run` stops making calls once spend reaches the approved
  budget.
- **Wall clock:** about 35 minutes at 120 requests a minute and four cases at a time.
