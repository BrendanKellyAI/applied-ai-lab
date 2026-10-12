# S2 E7 pre-registration: reranking

Written before any E7 run, and not edited after it. Every claim is reported in `README.md` as
Held or Failed.

## The question

When the right passage is retrieved but ranked too low, does a second pass fix it?

In E2 the largest single loss was a passage found by search but ranked below 5th: 92 of 182
wrong answers. A reranker reads the question and each shortlisted passage together, which a
vector comparison cannot do, and reorders the shortlist before the prompt takes the top 5.

## A change from the handoff, made before any run

The handoff named a local cross-encoder, `BAAI/bge-reranker-v2-m3` (revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`). On this machine's CPU it took about 5.5 seconds per
question-passage pair with the season's long chunks: around 16 hours for a 20-passage shortlist
on 520 questions. The owner approved a cheap LLM instead if the local model failed for any
reason. So:

- **The main reranker** is `gpt-6-luna`, reasoning off: it reads the question and the numbered
  shortlist once and returns the passage numbers, best first (`prompts/rerank_llm.md`).
- **The cross-encoder** runs on the 40 look-alike (distractor) items only, shortlist 10,
  search-only, with its time per question recorded (`cross_encoder_subset.py`). Its slowness is
  itself a result: a reranker's cost is time as well as money.

## Setup

- **Library and items:** `halvard-v2`; 520 test items reported; the 100 dev items only to
  choose the shortlist.
- **The reference system** is the one after E6, pinned in
  `season2/history/s2-e7-reranking.yaml`. Only stage 7 changes.
- **Conditions:** `baseline` (search order); `llm-10` and `llm-20` (the top 10 or 20 search
  results reordered). Both search-only on test and dev; then, in full on test, the shortlist
  with the higher dev recall at 5 (a tie goes to 10, the cheaper call).

## Claims

**K1. Reranking puts the found passage in the top 5.**
- *Pass mark:* the chosen shortlist's recall at 5 on the 400 answerable items sits above the
  reference's.

**K2. Reading the question with the passage beats look-alikes.**
- *Pass mark:* on the 40 distractor items, the chosen shortlist ranks a look-alike above the
  evidence on fewer items than the reference does (point estimates).

**K3. A longer shortlist finds more.**
- *Pass mark:* `llm-20` recall at 5 on the 400 is at least `llm-10`'s (point estimates).

**K4. Better search gives better answers.**
- *Pass mark:* for the shortlist run in full, the change in the answer number has the same sign
  as the change in the search number.

## Joining the reference system

The shortlist run in full joins only if its search number sits above the reference's
(intervals that do not overlap) and its answer number is not lower.

## Reported, with no claim

- Recall at 5 by item type; look-alikes above the evidence; the cross-encoder's results and
  seconds per question on the 40 distractor items, beside the LLM's.
- The reranking call's tokens, cost and time per question.
- Paired comparisons (exact McNemar) of search hits and right answers.

## What this does not test

- **The cross-encoder at scale:** 40 items only, on a CPU; a GPU would be many times faster.
- **One LLM, one instruction.** A listwise ranking from a small model can drop or repeat
  passages; any passage it does not name keeps its search order after those it does.
