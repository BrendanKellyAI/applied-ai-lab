# S2 E6: Rewriting the question

Can changing the question before search find what the original missed? E6 changes only stage 4:
one call to a cheap model before search. Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: rewriting finds follow-ups' passages (34 of 40 against 7) and never finds a bridge
question's, but no mode cleared the strict joining rule, so the reference still searches the
question as typed.**

## The design

- **Library and items:** `halvard-v2`, 520 test items; 100 dev items to choose the mode.
- **Reference:** unchanged since E4 (`season2/history/s2-e6-rewriting.yaml`).
- **The rewriting model:** `gpt-6-luna`, reasoning off, at most 200 output tokens. The answer
  prompt always shows the original question and conversation; only the search query changes.
- **Modes** (instructions in `src/lab/rag/prompts/rewrite_*.md`):
  - `rewrite`: one call turns every question into a search query;
  - `split`: one call returns one to three stand-alone questions, each searched, with the
    rankings fused;
  - `resolve-followup`: only questions with earlier turns get a call, which rewrites the last
    turn as a stand-alone question.
- **Runs:** every mode search-only on test and dev. On the 20 dev follow-up, two-part and bridge
  items the rule chose `rewrite` (10 of 20, against 9 for split and 8 for resolve-followup),
  which then ran in full.

## Results

### Recall at 5

| Mode | All 400 | Follow-up (40) | Two-part (20) | Bridge (20) | Identifier (40) | Paraphrase (40) |
|---|---|---|---|---|---|---|
| **As typed (reference)** | 281 (66% to 75%) | 7 | 0 | 0 | 15 | 40 |
| Rewrite | 296 (70% to 78%) | 35 | 0 | 0 | 7 | 37 |
| Split | **309** (73% to 81%) | 34 | 1 | 0 | 15 | 39 |
| Resolve follow-up | 308 (73% to 81%) | 34 | 0 | 0 | 15 | 40 |

Paired against the reference on the same items: resolve-followup found 28 passages the reference
missed and lost 1 (exact McNemar p < 0.0001); split 30 and 2; rewrite 37 and 22 (p = 0.07).

### The full runs

| | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| As typed, reference | 281 of 400 | 280 of 400 (65% to 74%) | 42 of 120 | 76 of 480 |
| Rewrite | 296 | 296 (69% to 78%) | 43 | 98 |

## The claims

**R1 held: resolving a follow-up finds its passage.** 34 of 40 (71% to 93%) against 7 of 40
(9% to 32%). "And for the Mira robot vacuum?" becomes "How long should I wait before switching
on my Mira robot vacuum after moving it?", which search can match.

**R2 failed: splitting a two-part question did not find both parts.** 1 of 20, against 0. The
season's hit rule needs both evidence passages in the same top 5; splitting found each part
for its own query, but the fused list rarely kept both in the top 5.

**R3 held: no one-shot rewrite solves a bridge question.** 0 of 20 under every mode. "What is
the call-out fee in the region that covers postcode area KW?" needs the region found before the
fee can be looked up, and one rewrite does not know the region.

**R4 held, narrowly: rewriting every question did not significantly hurt the others.** On the
320 other answerable items, 261 against 274, with overlapping intervals. But it was not free:
rewriting halved identifier recall (15 to 7), because the model rephrased the code questions and
the code mattered less to the embedding.

**R5 held: better search gave better answers.** Rewrite: search +15, answers +16.

## Joining the reference system

No mode joins: rewrite's search interval (70% to 78%) overlaps the reference's (66% to 75%).
Split and resolve-followup found more but also overlap, and were not the dev choice. The best
targeted fix is plain on these numbers: rewrite follow-ups only (`resolve-followup`), which
fixed 27 of the 33 missed follow-ups, cost one small call for 40 of 520 questions and lost
almost nothing. It did not join because the rule is about the whole test set, and 40 follow-ups
cannot move the season's number past its interval on their own.

## Cost of the extra call

`gpt-6-luna` rewrite calls: about 120 input and 21 output tokens per question for `split` (480
calls), less than a hundredth of a cent each. The episode in all cost $1.33 (OpenAI $0.15,
Google $1.18), almost all of it the full run's judging.

## What this does not show

- **One rewriting model, one instruction per mode.**
- **No iterative retrieval:** search, read, then search again, which bridge questions need.
  That is agentic retrieval (S5).
- **Small samples:** 20 two-part and 20 bridge items.
- **The dev choice was made on 20 items,** and the three modes were within two of each other.

## Charts

`results/charts/`: **`recall`** on the follow-up, two-part and bridge items per mode (acid green
for a single best mode clearing the reference's interval; rewrite and split tie at 35 of 80, so
nothing is highlighted and the chart says so),
**`numbers`** and **`scoreboard`** (stage 4; joined: no).

## Run it

```bash
uv run lab rag analyse episodes/s2-e6-rewriting/config.yaml
```

```bash
uv run lab rag run episodes/s2-e6-rewriting/config.yaml
```
