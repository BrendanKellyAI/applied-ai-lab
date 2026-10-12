# S2 E12 pre-registration: swapping the embedding model (field note)

Written before any E12 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

What changes when the embedding model does, and what does re-embedding cost?

v1 S2 E4 (on 300 short articles) found that a new embedding model is not a drop-in swap: the
totals moved little, but many individual questions changed hands. E12 reruns the swap against
the full reference system, with answers, and adds the cost in currency.

## Setup

- **Library and items:** `halvard-v2`, the 520 test items.
- **The reference system** is the one after E11, pinned in
  `season2/history/s2-e12-embedding-swap.yaml`.
- **Conditions:** `baseline`, `text-embedding-3-small` ($0.02 per million tokens); `large`,
  `text-embedding-3-large` ($0.13 per million tokens), with every chunk and every question
  re-embedded by the new model. Only stage 3 changes. Both run in full.

## Claims

**M1. The larger model finds more.**
- *Pass mark:* `large` recall at 5 on the 400 answerable items is higher than the reference's
  (point estimate).

**M2. The totals hide how many questions change hands.**
- *Pass mark:* the questions found by one model but not the other number at least 5 times the
  change in the total.

**M3. Better search gives better answers.**
- *Pass mark:* the change in the answer number has the same sign as the change in the search
  number.

## Joining the reference system

`large` joins only if its search number sits above the reference's (intervals that do not
overlap) and its answer number is not lower.

## Reported, with no claim

- The cost of re-embedding the library with each model, from the tokens the API reports, and
  that cost projected to a library 1,000 times larger.
- Recall by item type; paired comparisons (exact McNemar) of search hits and right answers.

## What this does not test

- **Two models from one provider.** A model from another provider might move more.
- **No retuning** of anything downstream (search depth, prompt k) for the new model.
