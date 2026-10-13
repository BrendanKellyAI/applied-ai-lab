# S2 E0 deck handover: Season 2 intro

For the content agent. No experiment: a rebuild of `bk-s2-e0-season-intro-v1.pdf` now that the
episode list and numbering are final. Built last, as the handoff asks. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E0 |
| Title | Season 2: Retrieval and RAG |
| Hub slug | `season-2-intro` (as v1; confirm) |
| Deck file | `bk-s2-e0-season-intro-v2.pdf` |

## What the season does

Build a retrieval-augmented generation (RAG) system for an invented appliance maker, Halvard
Home, measure it, then improve it one stage at a time. One library (`halvard-v2`: 300 support
articles, 4 long policies with superseded versions, 4 staff-only documents, 32 deleted
articles), one test set (520 questions, 120 of them unanswerable), one pipeline of eleven
stages. A change joins the reference system only if it clears a pass mark fixed before the run.

## The final episode list

| Arc | Ep | Title |
|---|---|---|
| Foundations | E0 | Season intro |
| | E1 | Why retrieval exists |
| | E2 | Your first RAG system |
| | E3 | Measuring it |
| Finding the right passage | E4 | Chunking |
| | E5 | Search: keyword, vector, hybrid |
| | E6 | Rewriting the question |
| | E7 | Reranking |
| | E8 | Filters, permissions and fresh documents |
| Using the passage | E9 | Building the prompt |
| | E10 | Grounding and citations |
| | E11 | Field note: does a citation rule change the answer? |
| Running it and deciding | E12 | Field note: swapping the embedding model |
| | E13 | Field note: long context or retrieval? |
| | E14 | Tracing a wrong answer |
| | E15 | When RAG is the wrong answer |
| | E16 | Season 2 recap |

## Slide ideas

The pipeline strip (eleven stages) as the season's map, used again on every scoreboard slide;
the four season numbers (search, right answers, not found, leaks) defined in one line each; the
joining rule; the arcs above. A teaser of the result without the numbers ("the season roughly
halves wrong answers twice over; E16 shows how") is enough: keep the reveal for the episodes.

## Careful with

- The old numbering (v1 E2 to E6) is retired. Every cross-reference uses the list above.
- The answer and judge models changed from the plan in E4, for cost; say so if models are named.
