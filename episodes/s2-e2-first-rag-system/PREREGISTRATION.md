# S2 E2 pre-registration: your first RAG system

Written before any search, answer or judge call on the frozen library, and not edited after the
run. Every claim below is reported in `README.md` as Held or Failed, failures included. The same
pass marks are in `config.yaml` (`pass_marks`), and `claims.py` applies them; a test checks that
this file and the config agree.

## The question

What does a complete retrieval-augmented generation (RAG) system look like, and how well does
the simplest version of it work?

E2 builds every stage end to end with naive defaults and measures the result. Nothing is tuned.
The point is to see where the simplest system is right, and where and why it is wrong, before any
later episode changes a stage. Its four season numbers are the first row of the scoreboard.

## Setup

- **Library:** `halvard-v2`, frozen on 12 October 2026: 344 document versions. The index holds
  every one, of any access or status, because the baseline has no filter.
- **Items:** the 520 test items. There is no dev run in E2.
- **Pipeline:** `season2/reference.yaml`, unchanged:
  - **Chunking:** fixed windows of 256 tokens (`cl100k_base`), no overlap.
  - **Search:** `text-embedding-3-small`, cosine similarity, 50 deep.
  - **Passthrough stages:** no rewrite, no filter, no rerank, no citations.
  - **Prompt:** the top 5 passages, in rank order, under the plain instruction "Answer the
    question using the passages below."
  - **Answer model:** `gpt-6.1-sol` at reasoning `low`, its lowest level, with a 2,000-token
    output limit.
  - **Judge:** `claude-sonnet-5-5` with reasoning off and a 400-token limit.
  - **Temperature:** none sent; both models reject one.
- **Scoring:** as in `src/lab/rag/score.py` and the corpus spec, section 6.5.
  - **Hit:** a chunk in the top 5 holds the whole evidence span. Every span must be held for a
    multi-span item.
  - **Answer:** judged correct and faithful.
  - **Not found:** an unanswerable item judged a decline.
  - **Leak:** a staff passage in the prompt of a public asker.
- **Intervals:** Wilson 95%. "Below" or "above" in a claim means the intervals do not overlap,
  unless the claim says point estimate.
- **Order:** an estimate, then a pilot of 2 items per type (32 items), then the full run.

## Claims

Each claim names the stage the next episodes change, so the baseline's failures point to the
episode that addresses them.

**H1. Search loses more answers than the model does.** Among answerable items answered wrongly
(not correct and faithful), more have their evidence lost before the prompt than inside it.
Lost before the prompt means `lost_at` is chunk, search, filter or rerank; inside means prompt
or answer.

- *Pass mark:* the before-prompt count is greater than the inside count.
- *Next:* E3, scoring search and answer separately.

**H2. Fixed chunks hurt facts that depend on their shape.** Recall at 5 is lower for
two-sentence facts and for heading-dependent facts than for single-sentence policy facts.

- *Pass mark:* both point estimates are lower than `policy_single`'s.
- *Strong form, reported but not required:* both intervals sit below.
- *Next:* E4, chunking.

**H3. Identifier questions fail under vector search.** This is the v1 S2 E3 finding, now on a
larger library.

- *Pass mark:* recall at 5 on identifier items sits below recall at 5 on paraphrase items, with
  intervals that do not overlap.
- *Next:* E5, search.

**H4. A follow-up searched on its own fails.** "And for the Tessa dishwasher?" names the
product but not what is being asked.

- *Pass mark:* recall at 5 on follow-up items sits below `policy_single`'s, with intervals
  that do not overlap.
- *Next:* E6, rewriting the question.

**H5. With no filter, the wrong documents reach the prompt.** Both parts must hold.

- *H5a, leaks:* a staff passage reaches the prompt on at least half of the 40
  `restricted_public` items, and on at least one item of another type.
- *H5b, stale terms:* the superseded passage reaches the prompt on at least half of the 40
  version items, and at least one answer gives the old value. That is a whole-token match of the
  old value in the answer, without the current value.
- *Next:* E8, filters.

**H6. The model declines when nothing is there, but not when the wrong thing is there.** Both
parts must hold.

- *H6a:* not-found is at least 75% on the 40 `absent_detail` and 20 `absent_topic` items
  together.
- *H6b:* not-found is at most 50% on the 60 `restricted_public` and `deleted` items together,
  because leaked and withdrawn passages give the model something to answer from.
- *Next:* E8 and E9.
- *Why 75%:* v1 S2 E5 found a model declined 39 of 40 unanswerable questions under a standard
  prompt, so the plain prompt is not expected to force answers.

## Reported, with no claim

- **The four season numbers, with Wilson intervals:**
  - search: recall at 5 on the 400 answerable items
  - answer: correct and faithful, of the 400
  - not found: of the 120 unanswerable items
  - leaks: of the 480 public-asker items
- **The same numbers by item type.**
- **Where answers were lost:** the share of wrong answerable items at each `lost_at` stage.
- **Cut spans:** evidence spans no chunk holds whole.
- **Look-alikes ranked above the evidence,** on distractor items.
- **Cost and time:** tokens, cost per question at list prices, the model versions returned, and
  time per call.
- **The code check against the judge:** items where `key_values` and the judge disagree, listed
  for reading by hand. E3 checks the judge properly.

## Worked examples

The deck shows three items, chosen by these rules before the run, so the examples are not picked
for effect. In each case it is the first test item in id order that meets the rule:

1. **Right:** a `policy_single` item judged correct and faithful.
2. **Wrong because search missed:** a `policy_single` item whose evidence is not in the prompt
   and whose answer is judged not correct.
3. **Wrong because the model misread:** an answerable item of any new type whose evidence is in
   the prompt and whose answer is judged not correct and not a decline.

If a category has no item, the deck says so.

## What this does not test

- **One library:** invented, and written by one model.
- **One answer model and one judge,** and the judge is not yet checked. Its agreement with hand
  marks comes in E3, so E2's answer-level numbers are provisional until then.
- **The plain instruction is deliberately naive.** E2 does not show what a better prompt would
  do; E9 tests that.
- **No baseline on the dev set.**
