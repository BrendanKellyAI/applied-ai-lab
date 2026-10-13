# S2 E12: Swapping the embedding model (field note)

What changes when the embedding model does, and what does re-embedding cost? E12 re-embeds every
chunk and question with OpenAI's larger model and runs the whole reference system on the 520 test
items. Claims: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: the larger model was worse here, and it does not join.** It found 18 fewer passages
and gave 17 fewer right answers. A bigger, pricier embedding model is not an upgrade by default:
measure it on your own questions.

## The design

- **Library and items:** `halvard-v2`, the 520 test items.
- **Reference:** the system after E11 (`season2/history/s2-e12-embedding-swap.yaml`), with
  `text-embedding-3-small` ($0.02 per million tokens).
- **Condition `large`:** `text-embedding-3-large` ($0.13 per million tokens). Only stage 3
  changes; nothing downstream is retuned. Both ran in full.

## Results

| | Search (400) | Answer (400) | Not found (120) | Leaks |
|---|---|---|---|---|
| 3-small (reference) | **344 (82% to 89%)** | **354 (85% to 91%)** | 107 | 0 |
| 3-large | 326 (77% to 85%) | 337 (80% to 87%) | 106 | 0 |

Paired on the same items: search found 11 passages only with `large` and 29 only with `small`
(exact McNemar p = 0.006); right answers 16 against 33 (p = 0.021).

| Search hits by type (small to large) | |
|---|---|
| Follow-up (40) | 15 to 5 |
| Identifier (40) | 26 to 19 |
| Restricted staff (40) | 40 to 37 |
| Bridge (20) | 12 to 13 |
| Policy, single sentence (40) | 37 to 38 |

The other types sat at or near the ceiling under both. Most of the loss is on follow-ups and on
identifier codes. Where the large
model lost a question, the reranker most often dropped it from the top five (51 items against
39), so the shortlist it handed on was weaker.

## The claims

**M1 failed: the larger model did not find more.** 326 against 344.

**M2 failed: the totals did not hide many questions changing hands.** 40 changed hands against
a net change of 18; the pass mark was five times the net change (90). Unlike v1 S2 E4, the
swap here was a clear, one-directional loss, not a reshuffle.

**M3 held: better search gave better answers.** Search fell by 18 and answers by 17.

## Cost of re-embedding

| | Library tokens | This library | A library 1,000 times larger |
|---|---|---|---|
| 3-small | 288,666 | $0.006 | $5.77 |
| 3-large | 288,666 | $0.038 | $37.53 |

Re-embedding is cheap at this size. The real cost of a swap is the rerun of every evaluation, and
the risk shown above.

## Joining the reference system

The rule: search above the reference's interval and answers not lower. `large` failed both, so
the reference keeps `text-embedding-3-small`.

## What this does not show

- **Two models from one provider.** Another provider's model might do better or worse.
- **No retuning.** Search depth, shortlist and prompt size were tuned with the small model.
- **One library.** The loss on follow-ups and codes may be particular to Halvard's documents.

## Charts

`results/charts/`: **`recall`**, **`numbers`** and **`scoreboard`** (stage 3; not joined).

## Cost

$1.71 (OpenAI $0.53, Google $1.18).

## Run it

```bash
uv run lab rag analyse field-notes/s2-e12-embedding-swap/config.yaml
```

```bash
uv run lab rag run field-notes/s2-e12-embedding-swap/config.yaml
```
