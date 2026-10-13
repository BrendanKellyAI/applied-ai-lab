# S2 E8: Filters, permissions and fresh documents

Can search return a passage that is outdated, or that this user should never see? E8 changes only
stage 6. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: filtering by permission and version before ranking stops every leak and is the
biggest single improvement of the season so far.** Leaks fell from 64 to 0 of 480; right
answers rose from 316 to 359 of 400; correct declines from 41 to 83 of 120. It joins the
reference system.

## The design

- **Library and items:** `halvard-v2`, the 520 test items. A filter tunes nothing, so no dev run.
- **Reference:** the system after E7 (`season2/history/s2-e8-filters.yaml`): section chunks,
  vector search 50 deep, the top 20 reranked by `gpt-6-luna`, the top 5 in the prompt.
- **Two rules, read from each document's metadata, never its text:** *access* (a public asker
  sees public documents only) and *status* (current versions only, so superseded and withdrawn
  documents are dropped).
- **Conditions:** `baseline` (no filter); `before` (both rules, before ranking); `after` (both
  rules, on the ranked list); `before-access` and `before-status` (one rule each). All
  search-only; `before` and the reference also in full, chosen in advance.

## Results

| Filter | Search (400) | Staff passage in a public prompt (480) | Superseded chunks in prompts |
|---|---|---|---|
| **None (reference)** | 316 (75% to 83%) | 64 | 761 of 2,600 slots |
| Before ranking, both rules | **344** (82% to 89%) | **0** | 0 |
| After ranking, both rules | 344 | 0 | 0 |
| Before, access only | 319 | 0 | 808 |
| Before, status only | 342 | **126** | 0 |

### The full runs

| | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| No filter, reference | 316 of 400 | 316 of 400 (75% to 83%) | 41 of 120 (26% to 43%) | 64 of 480 |
| **Before ranking** | **344** | **359 (86% to 92%)** | **83 (60% to 77%)** | **0** |

Paired on the same items, the filter gave 98 right answers the reference got wrong and lost 8
(exact McNemar p < 0.0001). Where wrong answers were lost moved too: the passage ranked below
5th fell from 55 to 34, and answers wrong with the passage in the prompt from 22 to 3.

## The claims

**F1 held: a filter before ranking stops every leak.** 0 of 480 (0% to 0.8%), against 64.

**F2 failed: filtering after ranking did not starve the prompt.** Search returns 50 results and
the reranker reads the top 20 of what is left, so even after the filter every prompt still had 5
passages. Here "after" gave results identical to "before". The risk is real with a shallow
search; this system's 50-deep search hides it.

**F3 held: the status rule removes the old versions.** No superseded or withdrawn chunk reached
any prompt.

**F4 held: with nothing it should not see, the model declines.** On the 60 restricted and
withdrawn questions it declined 42 (57% to 80%), against 3 (2% to 14%) with no filter. E2's
"the model answers from whatever wrong passage it is given" was true; take the passage away and
it says it cannot find the answer.

**F5 held: without the old version beside it, the model gives the current value.** Version
questions answered right: 40 of 40 (91% to 100%) against 20 of 40 (35% to 65%). E2's model never
gave the old value alone; it reported the conflict. Remove the old copy and the conflict goes.

## The finding nobody planned for

**Filtering versions alone doubled the leaks**, from 64 to 126 of 480. The superseded copies had
been taking more than a quarter of the prompt slots; drop them and the next-best passages move up, and for
a public asker many of those are staff-only. Fix one rule at a time and the other problem gets
worse. The two rules work only together.

## What this does not show

- **Metadata is assumed right.** A staff document tagged public leaks under every rule.
- **Two access levels only.**
- **A withdrawn document stays in the index;** the status rule hides it. A real deletion should
  remove it.
- **The after-ranking risk** shows only with a shallow search, not tested here.

## Charts

`results/charts/`: **`recall`** (recall at 5 on staff-asker, version and one-sentence policy
items; acid green for a single best clearing the reference), **`numbers`** and **`scoreboard`**
(stage 6; joined).

## Cost

$2.22 (OpenAI $1.01, mostly the reranking calls for the four filtered conditions; Google $1.21).

## Run it

```bash
uv run lab rag analyse episodes/s2-e8-filters/config.yaml
```

```bash
uv run lab rag run episodes/s2-e8-filters/config.yaml
```
