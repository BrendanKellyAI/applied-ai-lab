# S3 E7 pre-registration: better data or a bigger model? (field note)

Written before any E7 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed. Later changes go in dated amendments at the end.

## The question

Does improving your own system beat paying for a bigger model?

A bigger model with no retrieval knows nothing about Halvard Home (an invented firm), so that
comparison would be trivial. Instead, E7 compares improvements to the system with a bigger
model, on the same questions.

## Design

Three pipelines crossed with two answer models, on all 520 `halvard-v2` test items (400
answerable, 120 unanswerable), judged by `gemini-3.6-flash` (minimal) throughout.

| Pipeline | What it is | Source |
|---|---|---|
| P0 Start | S2's naive system: fixed 256-token windows, no filter, no reranker, plain instruction | `season2/reference-e2.yaml` stages |
| P1 Data fixes | P0 plus the changes that come from the documents themselves: section chunks (S2 E4) and access and version filters from document metadata (S2 E8); no reranker, plain instruction | new in `config.yaml` |
| P2 Final | The S2 reference system: P1 plus the LLM reranker, the grounded citing instruction and citation parsing | `season2/reference.yaml` |

| Model | Setting | Why |
|---|---|---|
| Small: `gpt-6-luna` | reasoning off | The Season 2 answer model |
| Large: `gpt-6.1-sol` | low, its lowest setting | The S2 E2 answer model; same provider, so size is isolated from provider. It cannot turn reasoning off, which is a limitation. |

Published prices on 18 October 2026: the large model costs 20 times the small one per input
token and per output token.

**Reuse, checked by config id before any call:**

- P0 small is the S2 E4 baseline run (config `9652ab169377`), served from cache.
- P2 small is the S2 E12 reference run (`0294479ba987`), served from cache.
- P0 large makes the same answer requests as S2 E2 (`b58f06493698`), served from cache, and is
  judged again by the current judge so all six cells are scored the same way.
- P2 large is the same config as S3 E3's `gpt-6-1-sol` arm (`a781d2e2eafa`), served from its
  cache.

New calls: answers for P1 with each model, and judge calls for P1 and the re-judged P0 large
cell. P1 retrieval makes no model call (no reranker).

**Pilot:** 2 test items of each type (32 items) per cell, as in Season 2. Not used for claims.

## Metrics

- Right answers (judged correct and faithful), out of 400.
- Correct declines, out of 120.
- Staff-only passages in public prompts: items with a leak, out of 480 public items.
- Items handled right, out of 520 (the first two together), used for the paired tests.
- Cost per item handled right, as a ratio to the cheapest cell.

Leaks are fixed by the pipeline before any model sees the prompt, so they are identical across
the two models by construction. The point is structural (a bigger model cannot remove a leak),
not an experimental finding, and is reported that way.

## Claims

**D1. The small model on the final system beats the large model on the naive one.**
*Pass mark:* P2 small handles more items right than P0 large, and the exact McNemar test
separates them (p below 0.05).

**D2. Data work alone buys a real gain.**
*Pass mark:* P1 small handles more items right than P0 small, and the exact McNemar test
separates them (p below 0.05).

**D3. The bigger model adds less on a better system.**
*Pass mark:* the large model's gain over the small one, in items handled right, is smaller on
P2 than on P0.

## The title rule, fixed now

The episode is titled "Better data or a bigger model?" if data work alone (P0 to P1, small
model) gives at least half of the small model's whole gain from P0 to P2, in items handled
right. Otherwise it is retitled "Better retrieval or a bigger model?", because the reranker and
the prompt (P1 to P2) drove the result. The deck defines "better data" as section structure and
document metadata.

## Limits stated in advance

- One provider's two sizes; other providers' large models may behave differently.
- The large model runs with low reasoning, the small with none.
- P0 large's answers were made for S2 E2 on 12 October 2026; the other new cells on 18 or 19
  October. Model versions returned are recorded per cell.
- P1 is defined by what the documents' structure and metadata allow; it is not every possible
  data improvement.
- Costs are published as ratios only.
