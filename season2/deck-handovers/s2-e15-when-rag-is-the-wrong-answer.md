# S2 E15 deck handover: When RAG is the wrong answer

For the content agent. No experiment: a teaching deck backed by E13, E14 and the scoreboard.
Read the season handoff and the E13 and E14 handovers first.

## Sources of truth

`field-notes/s2-e13-long-context-or-retrieval/README.md` and `results/analysis.json`;
`episodes/s2-e14-tracing/README.md`; `season2/scoreboard.json`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E15 |
| Title | When RAG is the wrong answer |
| Hub slug | `when-rag-is-wrong` (proposed; confirm) |
| Deck file | `bk-s2-e15-when-rag-is-wrong-v1.pdf` |

## The argument

RAG answers a question by finding a passage. It is the wrong tool when the answer is not a
passage. Four alternatives, each with the season's evidence where it has any:

1. **Long context (E13).** When the documents fit the window, sending everything matched the
   retrieval system (75 against 71 of 80 hard items, overlapping; 39 each on simple items) with
   no pipeline to build, at ten times the price ($0.016 against $0.0016 a question) and no
   slower. It cannot scope documents per user or keep up with a library that changes.
2. **Structured data and SQL.** The bridge questions join two facts: a postcode belongs to a
   region, and the region has a delivery time. Retrieval got 14 of 20 and long context 20 of
   20 (E13). In a table this is one exact join. When the answer is a lookup or a calculation
   over records, store the records and query them.
3. **Fine-tuning (S4).** Retrieval supplies facts; it does not change how a model behaves,
   writes or formats. Pointer only.
4. **Tools and live systems (S5).** "Where is my order?" is the state of a system now, not a
   passage. Pointer only.

And one case where no technique helps: **the documents disagree.** In E14, three of the final
system's five failures with the right passage in the prompt were an article and a policy giving
different warranty periods. The fix is the content, not the pipeline.

## Slide ideas

A decision tree as the mental model (is the answer a passage? does the library fit? must it be
scoped per user? is it a record or a live state?); one slide per alternative with the evidence
above; a "what the season did not test" slide (SQL, fine-tuning and tools were not run); for
leaders ("Ask your team": what share of our questions are lookups, calculations or live state?);
decision rule; next (E16 recap).

## Decision rule (from the handoff, kept)

**"Use RAG when the answer is a passage in your documents; use something else when it is a
calculation, a behaviour, or the state of a live system."**

## Careful with

- Only long context was measured. Present SQL, fine-tuning and tools as reasoning, not results.
- Do not say long context "beat" retrieval: the intervals overlap.
