# S2 E14 deck handover: Tracing a wrong answer

For the content agent. A full experiment deck in the season's order (why it matters, mental
model, method, claims, worked example, findings, verdicts, limits, run it, in practice, for
leaders, scoreboard, decision rule, series map).

## Sources of truth

`episodes/s2-e14-tracing/README.md`, `results/analysis.json` (with the five worked examples in
`examples_final`), `PREREGISTRATION.md`. Chart: `results/charts/lost-at` (slide and article
sizes). Slide function: `first_lost_stage` in `src/lab/rag/score.py`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E14 |
| Title | Tracing a wrong answer |
| Hub slug | `tracing` (proposed; confirm) |
| Folder | `episodes/s2-e14-tracing` |
| Deck file | `bk-s2-e14-tracing-v1.pdf` |

## The story

- **Mental model:** the pipeline as a relay. Each stage logs what it received and passed on, so
  a wrong answer can be walked back to the first stage that dropped the right passage. Use a
  diagram of the eleven stages with the seven loss points marked.
- **Findings:** wrong answers fell from 182 (E2) and 157 (E4) to 46. Cut spans 13 to 0, misses
  39 to 2, leaks 51 to 0, misreads 17 to 2. What remains is ranking: 24 passages never reached
  the reranker's shortlist of 20, and 15 were reranked below 5.
- **Worked example:** take one item through every stage, e.g. `IDENT-005` (ranked 39th, outside
  the shortlist) beside `FOLLOW-005` (a follow-up searched without its topic).
- **The conflicts:** three of the five final failures with the passage in the prompt are the
  library contradicting itself (an
  article says two years from purchase, the policy says 40 months from delivery). Good "for
  leaders" material: tracing turns a wrong answer into a content fix.
- **Claims:** T1, T2 and T3 all held.
- **Scoreboard:** no stage changes in E14; show the E2 to final drop in wrong answers instead.

## Decision rule (from the handoff, kept)

"When an answer is wrong, find the first stage that lost the right passage before changing
anything."

## Careful with

- E2's answer model and judge differ from the final system's; compare misreads from E4.
- "Beat" and "below" only where intervals do not overlap; here the comparisons are counts of
  wrong answers, not tested differences.
