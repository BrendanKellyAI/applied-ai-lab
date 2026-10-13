# S2 E12 deck handover: Swapping the embedding model (field note)

For the content agent. A short field-note deck in the S1 E7 format.

## Sources of truth

`field-notes/s2-e12-embedding-swap/README.md`, `results/analysis.json`, `PREREGISTRATION.md`.
Charts in `results/charts/` (`recall`, `numbers`, `scoreboard`; slide and article sizes).
Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E12 |
| Title | Field note: swapping the embedding model |
| Hub slug | `embedding-swap` (proposed; confirm) |
| Folder | `field-notes/s2-e12-embedding-swap` |
| Deck file | `bk-s2-e12-embedding-swap-v1.pdf` |

## The story

Swap `text-embedding-3-small` for the larger, 6.5 times pricier `text-embedding-3-large`, change
nothing else. Search falls from 344 to 326 of 400, right answers from 354 to 337 (paired p =
0.006 and 0.021). Follow-ups drop from 15 to 5 found, identifier codes from 26 to 19.
Re-embedding costs under 4 cents here, $37.53 at 1,000 times the size. M1 (bigger finds more)
and M2 (totals hide many changes) failed; M3 (search and answers move together) held. Not
joined.

## Decision rule (field note)

"A bigger embedding model is not an upgrade by default. Rerun your evaluation before you swap,
and keep the old one if it wins."
