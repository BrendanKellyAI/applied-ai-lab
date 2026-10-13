# S2 E11 deck handover: Does a citation rule change the answer? (field note)

For the content agent. A short field-note deck in the S1 E7 format.

## Sources of truth

`field-notes/s2-e11-citation-rule/README.md`, `analysis.json`, `PREREGISTRATION.md`. No charts:
use a two-column table slide. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E11 |
| Title | Field note: does a citation rule change the answer? |
| Hub slug | `citation-rule` (proposed; confirm) |
| Folder | `field-notes/s2-e11-citation-rule` |
| Deck file | `bk-s2-e11-citation-rule-v1.pdf` |

## The story

Same model, same passages, two instructions that differ only by "cite each claim". Right answers
357 against 354; 11 flipped each way (p = 1.0). Declines 105 against 107. Median length 26
against 28 tokens. The rule changes how the model answers, not what. N1 and N2 held, N3 (longer
answers) failed.

## Decision rule (field note)

"Asking for citations costs nothing in accuracy here: require them, and check them (E10)."
