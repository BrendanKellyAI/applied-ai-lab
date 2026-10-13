# S2 E5 deck handover: Search

For the content agent. Read the season handoff and the E2 to E4 handovers first.

## Sources of truth

`episodes/s2-e5-search/README.md`, `results/analysis.json`, `PREREGISTRATION.md`,
`results/charts/*-slide.svg`. Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E5 |
| Title | Search: keyword, vector, hybrid |
| Hub slug | `search` (v1 used it for E3; confirm) |
| Folder | `episodes/s2-e5-search` |
| Deck file | `bk-s2-e5-search-v2.pdf` |

## The story in one paragraph

Each search method is blind where the other sees: keyword search found all 40 identifier codes
and no paraphrase, vector search the reverse, exactly as in v1. Fusing the full rankings lost to
vector search again. Fusing only the top 20 of each kept most of keyword's strength on codes, and
gave significantly more right answers (299 against 280), but its search number came out a little
lower (276 against 281), so under the season's pre-registered rule it did not join. The episode
is also where a hidden reproducibility bug surfaced and was fixed.

## Findings

- Recall at 5, all 400: vector 281, keyword 232, hybrid-all 251, hybrid-50 257, hybrid-20 276.
- Identifier 15 / 40 / 31 / 31 / 32; paraphrase 40 / 0 / 0 / 6 / 23 (same order).
- Full runs: reference 281 / 280 / 42 / 76; hybrid-20 276 / 299 / 45 / 103.
- S1, S2, S3 held; S4, S5 failed. Not joined.
- Paired answers: 61 gained, 33 lost, p = 0.005.

## Charts

`recall-slide.svg`: nothing highlighted, no method clears vector's interval; say so.
`numbers-slide.svg`: nothing highlighted. `scoreboard-slide.svg`: stage 5.

## Slide ideas

Why it matters; the two blind spots (a code and a paraphrase, side by side); method; claims;
worked item (an identifier question under each method); recall chart; the fusion trap (fusing a
random tail); the twist: better answers, lower search number, and why the rule said no; the
reproducibility bug as a "built to be checked" slide; what this does not prove; run it; for
leaders; scoreboard; decision rule; next (E6 Rewriting the question).

## Decision rule

Kept from the handoff, confirmed: **"Test search on each kind of question your users ask, keep
keyword search for exact codes, and merge rankings only where your tests show it helps."**
