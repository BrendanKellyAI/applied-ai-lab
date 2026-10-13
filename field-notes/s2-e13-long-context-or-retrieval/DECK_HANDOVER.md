# S2 E13 deck handover: Long context or retrieval? (field note)

For the content agent. A short field-note deck in the S1 E7 format.

## Sources of truth

`field-notes/s2-e13-long-context-or-retrieval/README.md`, `results/analysis.json`,
`PREREGISTRATION.md`. No charts: use the two README tables. Branch `s2`. Slide function:
`long_prompt` in `longcontext.py`.

## Names

| | Value |
|---|---|
| Episode code | S2 E13 |
| Title | Field note: long context or retrieval? |
| Hub slug | `long-context-or-retrieval` (proposed; confirm) |
| Folder | `field-notes/s2-e13-long-context-or-retrieval` |
| Deck file | `bk-s2-e13-long-context-or-retrieval-v1.pdf` |

## The story

Send all 304 current public documents (160,000 tokens) with every question, or run the
retrieval pipeline. On 80 hard items: 75 against 71 right (overlapping). Bridge questions 20
against 14 to long context; look-alikes 38 against 40 to retrieval. Simple items 39 each. Long
context used 11 times the tokens, cost 10 times as much ($0.016 a question), and was not slower
(1.9 s against 2.5 s). Only L2 held.

## Decision rule (field note)

The handoff's draft, supported: **"Use long context when the documents fit and change rarely;
use retrieval when the library outgrows the window, changes often, or must be scoped per
user."** Add the run's numbers: at 160,000 tokens it matched retrieval's accuracy at ten times
the price, and won on questions that span documents.
