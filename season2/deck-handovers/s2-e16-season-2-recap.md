# S2 E16 deck handover: Season 2 recap

For the content agent. No experiment. Read the season handoff and every episode handover.

## Sources of truth

`season2/reference.yaml` (the final system), `season2/reference_history.yaml` (what joined and
when), `season2/scoreboard.json`, the recap chart `season2/charts/recap-*` (from
`season2/recap.py`), and each episode's README. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E16 |
| Title | Season 2 recap |
| Hub slug | `season-2-recap` (proposed; confirm) |
| Deck file | `bk-s2-e16-season-2-recap-v1.pdf` |

## The final reference system (`0294479ba987`)

| # | Stage | Setting | From |
|---|---|---|---|
| 2 | Chunk | One chunk per section, split above 1,024 tokens | E4 |
| 3 | Embed | `text-embedding-3-small` (the larger model lost in E12) | E2 |
| 4 | Rewrite | None: the question as typed (E6: nothing joined) | E2 |
| 5 | Search | Vector, 50 deep (E5: hybrid did not join) | E2 |
| 6 | Filter | Permission and version, before ranking | E8 |
| 7 | Rerank | `gpt-6-luna` reorders the top 20 | E7 |
| 8 | Prompt | Top 5 passages in rank order (E9: nothing joined); instruction: answer only from the passages, cite each claim, say "not found" | E10 |
| 9 | Answer | `gpt-6-luna`, reasoning off | E4, for cost |
| 10 | Cite | `[Pn]` markers mapped to passages and checked in code | E10 |
| 11 | Judge | `gemini-3.6-flash`, checked against a second model and hand marks | E3, E4 |

## The scoreboard, start to finish

| | Search (400) | Right answers (400) | Not found (120) | Leaks (480) |
|---|---|---|---|---|
| E2 baseline | 239 | 217 | 56 | 51 |
| E4 baseline (final answer model and judge) | 239 | 243 | 53 | 51 |
| After E4 (chunking) | 281 | 281 | 42 | 76 |
| After E7 (reranking) | 316 | 316 | 41 | 64 |
| After E8 (filters) | 344 | 359 | 83 | 0 |
| **After E10 (grounding and citations): final** | **344** | **354** | **107** | **0** |

The final row is E10's grounded run as rerun in E12 (identical numbers). Wrong answers fell
from 182 (E2) to 46 (E14). What is left: 24 passages that never reached the reranker's
shortlist and 15 reranked below 5, mostly follow-ups and identifier codes.

Use the recap chart (E2 against final, the four numbers) and each joined episode's scoreboard
strip.

## What did not join, and why that matters

The joining rule was strict: a change joined only if its interval sat above the reference's.
Three changes improved something real and still stayed out:

- **E5 hybrid search:** right answers 299 against 280 (paired p = 0.005), but search 276 against
  281.
- **E6 follow-up resolution:** follow-ups found rose from 7 to 34 of 40, but the total did not
  clear the rule.
- **E9 "not found" allowed:** handled right 462 against 442 of 520, overlapping intervals.
  E10's instruction then brought the same permission in.

Teach this as a feature: a strict rule keeps noise out, at the price of leaving some real gains
on the table. The remaining failures (E14) are exactly the item types E5 and E6 targeted, so
they are the obvious next changes for a reader to try.

## Decision rules in one place

| Ep | Rule |
|---|---|
| E1 | Use retrieval when the answer lives in your own data, then log what it retrieved and measure search and answer separately. |
| E2 | Build the simplest complete pipeline and measure it before tuning any stage. |
| E3 | Score search and answer separately, include questions your documents cannot answer, and check your judge before you trust its score. |
| E4 | Cut documents along their own structure, then test it. |
| E5 | Test search on each kind of question your users ask, keep keyword search for exact codes, and merge rankings only where your tests show it helps. |
| E6 | Rewrite or split a question only where tests show those questions fail, and weigh the extra call against what it recovers. |
| E7 | Add a reranker when the right passage is found but ranked too low, and measure what it costs per question. |
| E8 | Filter by permission and version before ranking, never after, and test that a restricted passage cannot reach the prompt. |
| E9 | Send the fewest passages that keep the answer score, and make "not found" an answer the model is allowed to give. |
| E10 | Require every claim to cite a passage, then check that the passage supports it. |
| E11 | Asking for citations costs nothing in accuracy here: require them, and check them. |
| E12 | Swap embedding models in one step and compare answers question by question, not just the totals. |
| E13 | Use long context when the documents fit and change rarely; use retrieval when the library outgrows the window, changes often, or must be scoped per user. |
| E14 | When an answer is wrong, find the first stage that lost the right passage before changing anything. |
| E15 | Use RAG when the answer is a passage in your documents; use something else when it is a calculation, a behaviour, or the state of a live system. |

## Changes from the season plan, to state plainly

- **Cheaper models from E4 on:** answers `gpt-6-luna` (planned `gpt-6.1-sol`) and judge
  `gemini-3.6-flash` (planned `claude-sonnet-5-5`), for cost. E4's baseline was rerun under them.
- **The reranker is an LLM,** not the planned local cross-encoder, which took 62 seconds a
  question on CPU (E7).
- **The judge check** used a second model on all 50 plus 10 hand marks, not 50 hand marks (E3).

## Deferred topics (named pointers)

- Document parsing: S7 Data.
- Prompt injection through retrieved documents: S11 Security.
- Agentic retrieval: S5 Agents.
