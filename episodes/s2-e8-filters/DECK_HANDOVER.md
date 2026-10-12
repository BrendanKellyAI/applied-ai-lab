# S2 E8 deck handover: Filters, permissions and fresh documents

For the content agent. Read the season handoff and the earlier handovers first.

## Sources of truth

`episodes/s2-e8-filters/README.md`, `results/analysis.json`, `PREREGISTRATION.md`,
`results/charts/*-slide.svg`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E8 |
| Title | Filters, permissions and fresh documents |
| Hub slug | `filters-and-permissions` (proposed; confirm) |
| Folder | `episodes/s2-e8-filters` |
| Deck file | `bk-s2-e8-filters-and-permissions-v1.pdf` |

## The story in one paragraph

With no filter, staff-only passages reached 64 of 480 customers' prompts, and old policy
versions took over a quarter of every prompt. Filtering by permission and by version, before
ranking, stopped every leak, made the model decline 42 of 60 questions it must not answer
(against 3), and got every version question right (40 of 40, against 20). Right answers rose
from 316 to 359, the season's biggest single jump. The twist: filter versions alone and leaks
double (126), because staff passages take the freed slots. The rules only work together.

## Findings

- Leaks: none 64, before 0, after 0, access only 0, status only 126.
- Full runs: reference 316 / 316 / 41 / 64; before 344 / 359 / 83 / 0.
- F1, F3, F4, F5 held; F2 failed (after-ranking starved nothing at 50-deep search).
- Paired answers: 98 gained, 8 lost.

## Charts

`recall-slide.svg`, `numbers-slide.svg`, `scoreboard-slide.svg` (stage 6, joined). Read each
chart's own note for its highlight.

## Slide ideas

Why it matters (a customer told an internal limit, from E2); mental model (filter before
ranking against after, as a diagram); method; claims; worked item (RESTRICT-PUBLIC-003 under
each filter); leak chart; the doubling twist; declines and versions; what this does not prove
(metadata assumed right); run it (the `rank` slide function with `keep`); for leaders ("Ask your
team": can a customer's question reach an internal document? what happens to a withdrawn one?);
scoreboard; decision rule; next (E9 Building the prompt).

## Decision rule

Kept, confirmed: **"Filter by permission and version before ranking, never after, and test that
a restricted passage cannot reach the prompt."** Add the run's lesson in the notes: apply both
rules together.
