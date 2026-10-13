# S2 E1 deck handover: Why retrieval exists

For the content agent. No experiment: an update to the v1 deck (`bk-s2-e1-why-retrieval-exists-v1.pdf`)
using Season 1 results, with the carry-over fixes from the season handoff. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E1 |
| Title | Why retrieval exists |
| Hub slug | `why-retrieval-exists` (as v1; confirm) |
| Deck file | `bk-s2-e1-why-retrieval-exists-v2.pdf` |

## Fixes (from the handoff)

- Spell out RAG at first use: retrieval-augmented generation.
- Slide 6: "Traceability (S1 E9)" should point to the citations episode, **S2 E10**.
- Renumber every Season 2 cross-reference to the final plan:
  - metadata and scope: E8
  - reranking: E7
  - answer and cite: E10
  - misreading: E10, E11
  - measuring: E3
- Visual variety: slide 7 as a bar chart, slide 3 as a diagram.

## Additions now the season has run

- **A forward pointer with real numbers** (one slide, near the end): the naive system in E2 found
  the right passage for 239 of 400 questions and answered 217 right; the season's final system
  found 344 and answered 354, with no leaks of internal documents (from 51). Source:
  `season2/scoreboard.json`. Keep it to a teaser; E16 tells the full story.
- **The new failure retrieval introduces,** an unfaithful answer with a citation attached, now has
  a measured example: in E10, 35 of 400 citations pointed to a passage without the evidence.
  Source: `episodes/s2-e10-grounding-and-citations/README.md`.

## Decision rule (kept)

**"Use retrieval when the answer lives in your own data, then log what it retrieved and measure
search and answer separately."**
