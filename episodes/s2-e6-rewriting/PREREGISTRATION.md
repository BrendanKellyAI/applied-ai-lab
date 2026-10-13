# S2 E6 pre-registration: rewriting the question

Written before any E6 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

Can changing the question before search find what the original missed?

E2 found three kinds of question that search almost never answered: follow-ups searched on
their own ("And for the dryer?"), 3 of 40; two-part questions, 1 of 20; and bridge questions,
where one fact must be found before the next can be looked up, 0 of 20. E6 adds one model call
before search and measures what each kind of rewrite recovers, and what it costs.

## Setup

- **Library and items:** `halvard-v2`; 520 test items reported; the 100 dev items only to
  choose which mode runs in full.
- **The reference system** is the one after E5, pinned in
  `season2/history/s2-e6-rewriting.yaml`. Only stage 4 changes.
- **The rewriting model:** `gpt-6-luna`, reasoning off, at most 200 output tokens: the
  cheapest model that works (the season rule). The answer prompt always shows the original
  question and conversation; only what is searched changes.
- **Conditions:**
  - `baseline`: the last turn as typed.
  - `rewrite`: one call turns the question into a search query.
  - `split`: one call returns one to three stand-alone questions; each is searched, and the
    rankings are fused (reciprocal rank fusion) before the filter.
  - `resolve-followup`: for items with earlier turns only, one call rewrites the last turn as
    a stand-alone question; other items are searched as typed, with no call.
  The instructions are in `src/lab/rag/prompts/rewrite_*.md`.
- **Two steps:** every mode search-only on test and dev; then, in full on test, the mode with
  the highest dev recall at 5 on the 20 dev follow-up, two-part and bridge items (a tie goes
  to `resolve-followup`, then `rewrite`, the cheaper calls). The reference also runs in full.

## Claims

**R1. Resolving a follow-up finds its passage.**
- *Pass mark:* on the 40 follow-up items, `resolve-followup` recall at 5 sits above the
  reference's.

**R2. Splitting a two-part question finds both parts.**
- *Pass mark:* on the 20 two-part items, `split` recall at 5 sits above the reference's.

**R3. No one-shot rewrite solves a bridge question.** The second fact cannot be searched for
until the first is known, and a single rewrite call does not know it.
- *Pass mark:* on the 20 bridge items, every mode's recall at 5 is at most 5 of 20.

**R4. Rewriting every question does not hurt the questions that did not need it.**
- *Pass mark:* on the 320 answerable items that are not follow-up, two-part or bridge,
  `rewrite` recall at 5 does not sit below the reference's.

**R5. Better search gives better answers.**
- *Pass mark:* for the mode run in full, the change in the answer number has the same sign as
  the change in the search number.

## Joining the reference system

The mode run in full joins only if its search number sits above the reference's (intervals
that do not overlap) and its answer number is not lower.

## Reported, with no claim

- Recall at 5 by mode and item type, on test and dev; the rewritten queries, in the log.
- The extra call per question: tokens, cost and time.
- Paired comparisons (exact McNemar) of search hits and right answers against the reference.

## What this does not test

- **One rewriting model and one instruction per mode.**
- **No iterative retrieval:** searching, reading, then searching again, which a bridge question
  needs. That is agentic retrieval (S5).
- **Small samples:** 20 two-part and 20 bridge items give wide intervals.
