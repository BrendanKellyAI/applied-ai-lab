# S2 E4 pre-registration: chunking

Written before any E4 search, answer or judge call, and not edited after the run. Every claim
below is reported in `README.md` as Held or Failed, failures included.

## The question

How should a document be cut up, and what does that decide?

E2 cut every document into fixed 256-token windows with no overlap. E3 showed that most of
E2's wrong answers were lost before the model saw the passage. E4 changes only stage 2, the
chunker, and measures what that does to search, and then to the answers.

## What E2 and v1 already show

- **v1 S2 E2 (chunking, on six novels):** recall fell as chunks grew past 128 tokens (43 of 60
  at 128, 11 of 60 at 2,048), and 25% overlap stopped short windows cutting facts in half. It
  tested fixed windows only, on invented facts in novels, and generated no answers.
- **E2 (this season):** at fixed 256 with no overlap, one-sentence policy facts were found 24
  of 40 times, two-sentence facts 13 of 20, heading-dependent facts 9 of 20. A chunk edge cut
  the evidence on 18 items. In E3, one answer finished a sentence that a chunk edge had cut.
- **The policies have structure:** 4 current policies, about 27,500 tokens each, in sections
  of about 840 tokens (902 at most) under headings such as "## Tessa dishwasher / ### Cover
  period".

## Setup

- **Library and items:** `halvard-v2`, the 520 test items for every reported number, and the
  100 dev items only for choosing which conditions run in full.
- **Everything else is the reference system** (`season2/reference.yaml`, as in E2): vector
  search with `text-embedding-3-small`, 50 deep, no filter, no rerank, the top 5 chunks in rank
  order, the plain prompt, `gpt-6.1-sol` at reasoning `low`, `claude-sonnet-5-5` as judge.
  The prompt holds 5 chunks whatever their size, so larger chunks mean longer prompts; E9
  tests the number of passages.
- **Conditions, all changing stage 2 only:**
  - **Fixed windows** of 64, 128, 256, 512 and 1,024 tokens (`cl100k_base`), each with no
    overlap and with 25% overlap. Fixed 256 with no overlap is the reference.
  - **Structure-aware chunks:** one chunk per lowest-level section, split at paragraph breaks
    when longer than 256, 512 or 1,024 tokens. At 1,024 every policy section is one chunk.
    Each size runs twice: with the heading path ("Warranty > Tessa dishwasher > Cover period")
    put in front of the text that is embedded, and without it. The chunk text the model sees
    is the same either way.
  - Short documents, such as the support articles, become one chunk under any chunker larger
    than the article.
- **Two steps:**
  1. **Search only, every condition, on test and dev.** This costs only embeddings.
  2. **In full (answer and judge), two conditions on test,** chosen on dev before step 2 by
     this rule: the fixed condition and the structure condition with the highest recall at 5
     on the 20 dev policy items (one sentence, two sentences, heading). A tie goes to the
     smaller chunks, which give the cheaper prompt. The reference's full run is E2's, reused.
- **Measures:** recall at 5; cut evidence spans (no chunk holds the span whole); prompt tokens
  per question; and, for the full runs, the four season numbers. Wilson 95% intervals.
  "Below" or "above" means the intervals do not overlap, unless a claim says point estimate.

## Claims

**C1. Long chunks dilute a fact.** As in v1, on policy documents this time.

- *Pass mark:* on the 80 test policy items (40 one-sentence, 20 two-sentence, 20 heading),
  recall at 5 for fixed 1,024 with no overlap sits below fixed 256 with no overlap.

**C2. Overlap stops facts being cut.**

- *Pass mark:* at every size, 25% overlap leaves fewer cut evidence spans than no overlap,
  across the 400 answerable test items (point estimates).
- *Reported:* recall at 5 on two-sentence facts with and without overlap at each size.

**C3. The heading carries the fact.** A heading-dependent sentence does not name its product;
only its heading does.

- *Pass mark:* on the 20 test heading items, recall at 5 with headings embedded beats the same
  structure chunker without them, at each of the three sizes (point estimates).
- *Strong form, reported but not required:* the best heading condition sits above fixed 256
  with no overlap (9 of 20 in E2).

**C4. Following the document's structure beats cutting blind.**

- *Pass mark:* the best structure condition's recall at 5 on the 80 test policy items is
  higher than the best fixed condition's (point estimates).

**C5. Better search gives better answers.**

- *Pass mark:* for each condition run in full, the change in the answer number against the
  reference has the same sign as its change in the search number.

## Joining the reference system

A condition run in full joins the reference only if **its search number (recall at 5 on the
400 answerable items) sits above the reference's** and **its answer number is not lower**
(point estimate). If both full conditions pass, the one with the higher search number joins.
If neither passes, the reference stays at fixed 256 with no overlap, and the scoreboard says
so.

The reference's search number is 239 of 400 (55% to 64%). To sit above it, a chunker needs
277 of 400. (Corrected on 12 October 2026, before any run: this sentence first said "about
268", an arithmetic slip. The rule itself, intervals that do not overlap, is unchanged.)

## Amendment, 12 October 2026: cheaper answer and judge models

Made after the search runs and before any E4 answer was analysed. The first two full runs
stopped when the Anthropic credit ran out, with 227 and 111 of 520 items judged; they were
discarded unanalysed. The owner then set a much lower budget for the season, so from E4 on:

- **Answer model:** `gpt-6-luna` with reasoning off, in place of `gpt-6.1-sol`.
- **Judge:** `gemini-3.1-flash-lite` at its lowest thinking level, `minimal`, in place of
  `claude-sonnet-5-5`. It is from a different provider from the answer model.
- **The reference's full run is redone on these models** in E4, instead of reusing E2's, so
  every E4 comparison is between runs on the same models. Its search number does not change
  (239 of 400), so the joining threshold stays at 277. The answer rule compares with the new
  reference run.
- **The new judge is checked before it is used,** on the 50 items of E3's sample. *Pass mark:*
  it agrees with `claude-sonnet-5-5` on `declined` and on `correct` on at least 45 of 50 each,
  and with the hand marks on `correct` on at least 8 of 10. If it fails, nothing is run in full
  and the owner decides.
- The search conditions, the dev choice (fixed 512 and structure 1,024) and the claims are
  unchanged.

## Reported, with no claim

- Recall at 5 for every condition, on all 400 and by item type, on test and dev.
- Cut evidence spans per condition.
- The superseded-copy crowding E2 found (prompt slots taken by superseded chunks) per
  condition. E8 is where the version filter is tested; E4 only reports it.
- Prompt tokens per question per condition, and the cost of each full run.
- For the full runs, where wrong answers were lost, as in E2.
- **A paired comparison** of each full condition's search hits against the reference's on the
  same 400 items: the items each finds that the other misses, with an exact two-sided McNemar
  p-value. It is reported beside the joining rule and decides nothing. The owner chose the
  stricter interval rule for joining.

## What this does not test

- **One library,** written by one model, with tidy headings. Real documents are messier.
- **One embedding model.**
- **No semantic chunking** (cutting where the topic changes) and no chunking by sentence.
- **Five passages whatever their size.** A chunker that wins with longer chunks may be winning
  partly on prompt length. E9 holds that fixed while varying the number of passages.
- **Choosing on 20 dev items** is noisy; the choice is reported on test.
- **The judge** is trusted to the level E3 measured, and faithfulness was not hand-checked.
