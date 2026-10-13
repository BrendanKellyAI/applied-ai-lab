# S2 E7 deck handover: Reranking

For the content agent. Read the season handoff and the earlier handovers first.

## Sources of truth

`episodes/s2-e7-reranking/README.md`, `results/analysis.json`, `PREREGISTRATION.md`,
`results/charts/*-slide.svg`, and the cross-encoder subset in `results/cross-encoder-10/`.
Slide function: `rerank` in `src/lab/rag/rerank.py`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E7 |
| Title | Reranking |
| Hub slug | `reranking` (proposed; confirm) |
| Folder | `episodes/s2-e7-reranking` |
| Deck file | `bk-s2-e7-reranking-v1.pdf` |

## The story in one paragraph

Search often finds the right passage but ranks it 6th to 20th, out of the prompt. A second pass
that reads the question with each candidate fixes much of that. The handoff's cross-encoder
worked but took 62 seconds a question on the build machine's CPU, so the season used a cheap LLM
(`gpt-6-luna`) to reorder the top 20 in one call, about $0.001 a question. Search rose from 281
to 316 of 400 and right answers from 280 to 316 (paired: 45 gained, 11 lost). A shortlist of 20
beat 10 (316 against 298): the reranker can only promote what search hands it, which E14 later
shows is where most remaining failures sit.

## Findings

- Search: reference 281, LLM top 10 298, LLM top 20 316.
- Full runs (search / answer / not found / leaks): reference 281 / 280 / 42 / 76; LLM top 20 316 / 316 / 41 / 64.
- Paired search: 38 gained, 3 lost (p < 0.0001). Answers: 45 gained, 11 lost.
- K1, K3, K4 held. K2 failed for lack of room: after E4 no look-alike outranked the evidence.
- Cross-encoder on 40 distractor items: same quality, 62 s a question against about 1 s.

## Slide ideas

Why it matters (the passage found but ranked 9th); mental model (two vectors compared apart,
against question and passage read together: a diagram of a bi-encoder against a cross-encoder,
and the LLM reading a numbered list); method; claims; worked item (an identifier question
moved from outside the top 5 into it); findings by type (identifier 15 to 26, two-part 0 to 8,
bridge 0 to 5); the cost and time slide (cross-encoder against LLM); what this does not prove
(CPU only; one LLM); run it; for leaders ("Ask your team": how far down does the right passage
sit when we miss?); scoreboard (stage 7, joined); decision rule; next (E8 Filters).

## Decision rule

Draft, confirmed: **"Add a reranker when the right passage is found but ranked too low, and
measure what it costs per question."** Add the run's lesson in the notes: give it a long enough
shortlist, since it cannot promote what it never sees.

## Careful with

- Teach the cross-encoder as the concept the handoff names, and say plainly why the season's
  reference uses an LLM instead (speed on CPU, not quality).
- Leaks in the full runs (76 and 64) are E8's subject; do not discuss them here beyond a pointer.
