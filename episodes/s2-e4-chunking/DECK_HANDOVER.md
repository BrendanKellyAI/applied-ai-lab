# S2 E4 deck handover: Chunking

For the content agent building the S2 E4 deck. Read `season-2-content-handoff.md` (version 2)
and the S2 E2 and E3 handovers first; this adds only what is specific to E4.

## 1. Sources of truth

1. `episodes/s2-e4-chunking/README.md`: every number and verdict.
2. `.../results/analysis.json`: the figures behind it.
3. `.../PREREGISTRATION.md`: the claims, with two amendments (cheaper models; judge checks) and
   one correction (the joining threshold is 277, not "about 268").
4. `.../results/charts/*-slide.svg` and `.../judge-switch/*/report.json`.

Branch `s2`; use the `main` URL in the deck.

## 2. Names

| | Value |
|---|---|
| Episode code | S2 E4 |
| Title | Chunking |
| Hub slug | `chunking` (the v1 deck `bk-s2-e2-chunking-v1.pdf` used it as E2; confirm with the hub) |
| Folder | `episodes/s2-e4-chunking` |
| Deck file | `bk-s2-e4-chunking-v2.pdf` |

## 3. The story in one paragraph

Cutting documents by their own sections beat every fixed window: structure-aware chunks of up
to 1,024 tokens found the right passage for 281 of 400 questions, against 239 for E2's fixed
256-token windows, and right answers rose from 243 to 281. Overlap stopped chunk edges cutting
facts in half. But two textbook claims failed: long chunks did not dilute policy facts (v1's
dilution came from facts inserted into novels), and embedding the heading path did not help the
facts that need their heading, because a section chunk already starts with its heading. The
cost: prompts 2.5 times longer, and more staff passages reaching customers (51 to 76), which E8
fixes.

## 4. Findings, exact numbers

- Full runs: reference 239 / 243 / 53 / 51 (search, answer, not found, leaks); structure 1,024
  281 / 281 / 42 / 76; fixed 512 224 / 237 / 57 / 30.
- C1 failed (48 vs 46 of 80), C2 held (cut items 90, 33, 18, 8, 8 without overlap; 18, 0, 0, 0,
  0 with), C3 failed (14/14, 12/11, 15/15 of 20), C4 held (66 vs 56 of 80), C5 held (+42/+38,
  -15/-6).
- Joined: structure 1,024, search interval 66% to 75% against the reference's 55% to 64%.
- The model switch, and the four judge checks (table in the README). Both Flash-Lite judges
  agreed with the old judge on correctness only 30 of 50 times.

## 5. Charts

| File | Acid green |
|---|---|
| `policy-recall-slide.svg` | Structure 1,024 (66 of 80): its interval clears the reference's |
| `headings-slide.svg` | None; the claim compares pairs. Say so |
| `cut-evidence-slide.svg` | None. Say so |
| `scoreboard-slide.svg` | Stage 2 in the strip |

## 6. Slide ideas

1. Cover. 2. Why it matters: the cut decides what can be found. 3. Mental model (diagram): a
fixed window across a section boundary against a section chunk. 4. Method: 15 chunkers,
search-only screening, two full runs chosen on dev. 5. Claims and pass marks. 6. One worked item:
a heading-dependent fact under fixed 256 and under structure 1,024. 7. Every chunker (chart
`policy-recall`). 8. Overlap (chart `cut-evidence`). 9. The failed claims: no dilution, headings
did nothing. 10. The full runs and what got worse (leaks, not found, prompt length). 11. The model
switch and the judge check, as an honest aside. 12. What this does not prove. 13. Run it
yourself. 14. For leaders: "Ask your team" what their documents' structure is, and whether they
tested it. 15. Scoreboard. 16. Decision rule and Next (E5 Search). 17. Series map.

## 7. Decision rule

Draft: "Choose a chunk size by testing it on your own documents: small enough to keep a fact
sharp, with overlap or structure so no fact is cut in half." The run supports a sharper version:
**"Cut documents along their own structure, then test it: one section per chunk beat every fixed
size here, and overlap stops facts being cut."**
