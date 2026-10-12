# S2 E9 deck handover: Building the prompt

For the content agent. Read the season handoff and the earlier handovers first.

## Sources of truth

`episodes/s2-e9-building-the-prompt/README.md`, `results/analysis.json` (the `join` block holds
the handled-right shares), `PREREGISTRATION.md`, `results/charts/*-slide.svg`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E9 |
| Title | Building the prompt |
| Hub slug | `building-the-prompt` (proposed; confirm) |
| Folder | `episodes/s2-e9-building-the-prompt` |
| Deck file | `bk-s2-e9-building-the-prompt-v1.pdf` |

## The story in one paragraph

One sentence ("If the passages do not contain the answer, reply that you could not find it")
raised correct declines from 83 to 105 of 120 and cost no right answers. Three passages instead
of five cut the prompt by a third but quietly lost 35 right answers against 13 gained. Putting
the best passages at the ends, the "lost in the middle" fix, changed nothing at this length,
which matches S1 E7. All four claims held, yet nothing joined the reference: the rule scores all
520 questions, and the declines' gain was diluted by the 400 answerable ones.

## Findings

- Answer / not found: reference 359 / 83; not found allowed 357 / 105; top 3 346 / 76; ends
  359 / 77.
- Handled right of 520: 442, 462, 422, 436.
- Median prompt: 2,767 tokens; top 3 1,807; top 8 3,895.
- P1 to P4 held. Not joined (462 vs 442, intervals overlap).

## Charts

`recall-slide.svg`, `scoreboard-slide.svg`. Read each chart's note for its highlight.

## Decision rule

**"Send the fewest passages that keep the answer score, and make 'not found' an answer the model
is allowed to give."** The run supports the second half outright; for the first, measure
paired losses, not just totals: three passages looked equal and were not.
