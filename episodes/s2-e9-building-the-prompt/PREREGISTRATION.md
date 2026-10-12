# S2 E9 pre-registration: building the prompt

Written before any E9 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

Once you have the passages, how many do you send, in what order, and what if none fit?

E2's plain instruction ("Answer the question using the passages below.") never told the model
it could decline. It declined 78% of questions with nothing to find, but only 15% of those where
the prompt held a passage it should not use. E9 changes only stage 8.

## Setup

- **Library and items:** `halvard-v2`, the 520 test items.
- **The reference system** is the one after E8, pinned in
  `season2/history/s2-e9-building-the-prompt.yaml`.
- **Conditions:**
  - `baseline`: the top 5 passages in rank order, the plain instruction.
  - `allow-not-found`: the same, with "If the passages do not contain the answer, reply that
    you could not find it." added (`prompts/allow_not_found.md`).
  - `k-3`: the top 3 passages only.
  - `ends`: the top 5 with the best first and the second best last, working inwards, so the
    weakest sit in the middle: the order S1 E7's "lost in the middle" advice recommends.
  - `k-8`: the top 8 passages, search-only, to show what more passages would reach.
- **Runs:** `baseline`, `allow-not-found`, `k-3` and `ends` in full; `k-8` search-only. The
  search number is recall at k for each condition's own k, so it counts what the model was
  actually given.

## Claims

**P1. Allowing "not found" makes the model decline when it should.**
- *Pass mark:* not-found on the 120 unanswerable items sits above the reference's.

**P2. Allowing "not found" does not cost right answers.**
- *Pass mark:* the answer number on the 400 answerable items does not sit below the
  reference's.

**P3. Three passages answer as well as five, for less.**
- *Pass mark:* `k-3`'s answer number does not sit below the reference's, and its median prompt
  is at least 30% shorter.

**P4. Passage order does not matter at this length.** S1 E7 found position irrelevant for
lookups up to 64,000 tokens; five passages are far shorter.
- *Pass mark:* `ends` and the reference's answer numbers have overlapping intervals.

## Joining the reference system

A condition joins only if its share of the 520 items handled right (answerable items judged
correct and faithful, plus unanswerable items declined) sits above the reference's (intervals
that do not overlap). If several pass, the one with the highest share joins. Otherwise the
reference keeps its prompt.

## Reported, with no claim

- Recall at k for every condition, including `k-8`.
- Median prompt tokens, and the cost of each full run.
- Paired comparisons (exact McNemar) of right answers against the reference.

## What this does not test

- **One instruction wording per idea.**
- **Order and number only up to 8 passages.**
- **Interactions:** each condition changes one setting; `allow-not-found` with `k-3` together is
  not tested.
