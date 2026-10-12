# S2 E9: Building the prompt

Once you have the passages, how many do you send, in what order, and what if none fit? E9 changes
only stage 8. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: telling the model it may say "not found" raised correct declines from 83 to 105 of 120
at no cost to right answers; all four claims held; but no change cleared the joining rule, so the
reference keeps its plain instruction.**

## The design

- **Library and items:** `halvard-v2`, the 520 test items.
- **Reference:** the system after E8 (`season2/history/s2-e9-building-the-prompt.yaml`): section
  chunks, vector search, LLM reranking of the top 20, the filter before ranking, the top 5
  passages in rank order, the plain instruction "Answer the question using the passages below."
- **Conditions:** `allow-not-found` (adds "If the passages do not contain the answer, reply that
  you could not find it."), `k-3` (the top 3 passages), `ends` (best first, second best last,
  the weakest in the middle), all in full; `k-8` (the top 8), search-only.
- **Measures:** the search number is recall at each condition's own k, because that is what the
  model was given.

## Results

| Prompt | Search | Answer (400) | Not found (120) | Handled right (520) | Median prompt |
|---|---|---|---|---|---|
| **Top 5, plain (reference)** | 344 | 359 (86% to 92%) | 83 (60% to 77%) | 442 (82% to 88%) | 2,767 tokens |
| Not found allowed | 344 | 357 (86% to 92%) | **105 (80% to 92%)** | **462 (86% to 91%)** | 2,767 |
| Top 3 | 336 | 346 (83% to 89%) | 76 | 422 | 1,807 |
| Best at the ends | 344 | 359 | 77 | 436 | 2,767 |
| Top 8 (search only) | 345 | | | | 3,895 |

"Handled right" counts answerable items judged correct and faithful plus unanswerable items
declined: the joining measure.

## The claims

**P1 held: allowing "not found" makes the model decline when it should.** 105 of 120 (80% to
92%) against 83 (60% to 77%). One sentence of instruction did what E8's filter began: the model,
told it may say it cannot find the answer, does so.

**P2 held: allowing "not found" does not cost right answers.** 357 against 359 of 400. Paired,
24 answers improved and 13 got worse (p = 0.10). Four answerable questions it now declined
wrongly, where the passage was in the prompt.

**P3 held, with a cost the claim did not ask about.** Three passages answered 346 of 400 against
359, inside the pass mark's overlap, with a prompt 35% shorter. But paired on the same items, top
3 lost 35 right answers and gained 13 (p = 0.002): the losses are real, if small. Two-part and
bridge questions need passages from further down.

**P4 held: passage order did not matter.** Best at the ends: 359 of 400, exactly the reference's;
paired, 19 gained and 22 lost (p = 0.76). S1 E7 found position irrelevant for lookups up to
64,000 tokens; a 2,800-token prompt is far below that.

## Joining the reference system

The rule: a condition joins if its share of the 520 handled right sits above the reference's.
"Not found allowed" reached 462 (85.9% to 91.3%) against 442 (81.7% to 87.8%): the intervals
overlap by two points, so it does not join. Its not-found gain on its own is clear (intervals
apart); the answerable items, 400 of the 520, dilute it. The recap (E16) returns to this.

## What this does not show

- **One wording per idea.**
- **No combination:** "not found" with top 3, for example.
- **Only up to 8 passages.**

## Charts

`results/charts/`: **`recall`** (recall at each condition's k) and **`scoreboard`** (stage 8;
joined: no; the best full condition, "not found allowed", against the reference). The handled-right
shares are in `results/analysis.json` under `join`.

## Cost

$3.72 for three new full runs (OpenAI $0.39, Google $3.32).

## Run it

```bash
uv run lab rag analyse episodes/s2-e9-building-the-prompt/config.yaml
```

```bash
uv run lab rag run episodes/s2-e9-building-the-prompt/config.yaml
```
