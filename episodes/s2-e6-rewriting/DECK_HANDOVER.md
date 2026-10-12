# S2 E6 deck handover: Rewriting the question

For the content agent. Read the season handoff and the earlier handovers first.

## Sources of truth

`episodes/s2-e6-rewriting/README.md`, `results/analysis.json`, `PREREGISTRATION.md`,
`results/charts/*-slide.svg`, and the rewritten queries in `results/*/log.jsonl` (`queries`).
Branch `s2`.

## Names

| | Value |
|---|---|
| Episode code | S2 E6 |
| Title | Rewriting the question |
| Hub slug | `rewriting-the-question` (proposed; confirm) |
| Folder | `episodes/s2-e6-rewriting` |
| Deck file | `bk-s2-e6-rewriting-the-question-v1.pdf` |

## The story in one paragraph

A follow-up such as "And for the Mira robot vacuum?" names a product but not what is asked, so
search found its passage 7 times in 40. One cheap model call that rewrites it as a stand-alone
question raised that to 34 of 40. Splitting two-part questions did not help, because both parts
still had to land in one top 5, and no single rewrite helped a bridge question (0 of 20 every
time): you cannot search for the second fact before you know the first. Rewriting every question
helped overall but halved identifier recall, by paraphrasing away the code. None of it cleared
the season's strict joining rule.

## Findings

- Recall at 5, all 400: as typed 281, rewrite 296, split 309, resolve-followup 308.
- Follow-up 7 / 35 / 34 / 34; two-part 0 / 0 / 1 / 0; bridge 0 everywhere; identifier
  15 / 7 / 15 / 15.
- Full runs: reference 281 / 280 / 42 / 76; rewrite 296 / 296 / 43 / 98.
- R1, R3, R4, R5 held; R2 failed. Not joined.
- The extra call: about 140 tokens, under a hundredth of a cent, per question.

## Charts

`recall-slide.svg`: nothing highlighted (rewrite and split tie); say so. `numbers-slide.svg`,
`scoreboard-slide.svg` (stage 4).

## Quote

Pull a follow-up's original and rewritten query from `results/resolve-followup/log.jsonl`
(`queries`), for example FOLLOW-000, beside the 7-of-40 figure.

## Decision rule

**"Rewrite or split a question only where tests show those questions fail, and weigh the extra
call against what it recovers."** The run supports it as drafted, with one sharpening: rewrite
follow-ups, not everything, because rewriting everything cost identifier questions.
