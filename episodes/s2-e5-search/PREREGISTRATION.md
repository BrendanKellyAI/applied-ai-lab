# S2 E5 pre-registration: search

Written before any E5 search, answer or judge call, and not edited after the run. Every claim
is reported in `README.md` as Held or Failed.

## The question

Which search finds the right passage, and where does each one fail?

v1 S2 E3 compared keyword search (BM25), vector search and a hybrid of the two on 300 short
articles. Keyword search found every identifier code and no paraphrase; vector search the
reverse; and the hybrid, fusing the full rankings, was no better than keyword search and well
below vector. E5 reruns that on the season library, with long policies, and tests the variant
v1 left untested: fusing only the top of each ranking.

## Setup

- **Library and items:** `halvard-v2`; the 520 test items for every reported number; the 100
  dev items only to choose the fuse depth.
- **The reference system** is the one after E4, pinned in
  `season2/history/s2-e5-search.yaml`: everything but search stays as it is, including the
  answer model `gpt-6-luna` and the judge `gemini-3.6-flash`.
- **Conditions, all changing stage 5 only:**
  - `baseline`: vector search (cosine, `text-embedding-3-small`), the reference.
  - `keyword`: BM25, default settings, text lower-cased and split on `\w+`, as in v1.
  - `hybrid-all`: reciprocal rank fusion (k = 60) of the full keyword and vector rankings,
    v1's form.
  - `hybrid-50` and `hybrid-20`: fusion of only the top 50 or top 20 of each ranking.
- **Two steps:**
  1. **Search only, every condition, on test and dev.** No model call.
  2. **In full, one condition on test:** the hybrid with the highest recall at 5 on the 70
     answerable dev items; a tie goes to the shallower fusion. The reference also runs in full.
- **Measures:** recall at 5; look-alikes ranked above the evidence on identifier and
  distractor items; the four season numbers for the full runs. Wilson 95% intervals; "below"
  and "above" mean the intervals do not overlap unless a claim says point estimate.

## Claims

**S1. Keyword search finds identifier codes that vector search misses.**
- *Pass mark:* on the 40 identifier items, keyword recall at 5 sits above vector's.

**S2. Vector search finds paraphrases that keyword search misses.**
- *Pass mark:* on the 40 paraphrase items, vector recall at 5 sits above keyword's.

**S3. Fusing the full rankings does not beat vector search (v1's result, repeated).**
- *Pass mark:* `hybrid-all` recall at 5 on the 400 answerable items is no higher than the
  reference's (point estimate).

**S4. Fusing only the top of each ranking keeps vector search's strengths and adds keyword's.**
- *Pass mark:* the chosen hybrid's recall at 5 on the 400 is at least the reference's (point
  estimate), and its identifier recall sits above the reference's.

**S5. Better search gives better answers.**
- *Pass mark:* for the chosen hybrid, run in full, the change in the answer number against the
  reference has the same sign as the change in the search number.

## Joining the reference system

The chosen hybrid joins only if its search number sits above the reference's (intervals that do
not overlap) and its answer number is not lower. Otherwise the reference keeps vector search.

## Reported, with no claim

- Recall at 5 for every condition, by item type, on test and dev.
- A paired comparison (exact McNemar) of search hits and of right answers against the
  reference, beside the joining rule.
- The prompt's size and the cost of the full runs.

## What this does not test

- **One embedding model and one BM25 setting.** A tokeniser that kept `E-2194` whole would
  behave differently.
- **One fusion method,** reciprocal rank fusion with k = 60, equal weights.
- **The dev set has no identifier, paraphrase or shared-word items,** so the fuse depth is
  chosen on the other types.
- **The judge** is `gemini-3.6-flash`, checked in E4 against E3's sample, not against new hand
  marks.
