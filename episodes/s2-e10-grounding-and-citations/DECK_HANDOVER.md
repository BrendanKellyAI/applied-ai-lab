# S2 E10 deck handover: Grounding and citations

For the content agent. Read the season handoff and the earlier handovers first.

## Sources of truth

`episodes/s2-e10-grounding-and-citations/README.md`, `results/analysis.json` (`extra` holds the
citation check), `PREREGISTRATION.md`, `results/charts/*-slide.svg`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E10 |
| Title | Grounding and citations |
| Hub slug | `grounding-and-citations` (proposed; confirm) |
| Folder | `episodes/s2-e10-grounding-and-citations` |
| Deck file | `bk-s2-e10-grounding-and-citations-v1.pdf` |

## The story in one paragraph

Asked to answer only from the passages and cite each claim, the model cited every time, and the
citations could be checked in code: 91% pointed to the passage holding the evidence, and right
answers cited it 343 times in 346. Right answers held (354 against 359) and correct declines
rose from 83 to 107. The failure S1 E3 warned about, a citation attached to the wrong source, is
real but small: 35 of 400 citations, and only 5 answers cited nothing but such passages.

## Findings

- Answer / not found: plain 359 / 83; grounded 354 / 107. Handled right 442 against 461.
- Citing 365 of 365; supported citations 365 of 400; right answers citing the evidence 343 of
  346.
- G1 to G4 held; joined.

## Code listing

`cited` from `episodes/s2-e10-grounding-and-citations/analyse.py`, below `# slide: S2 E10`.

## Decision rule

**"Require every claim to cite a passage, then check that the passage supports it."** Confirmed.
The check can be code when you have labelled evidence; otherwise a judge call per citation.
