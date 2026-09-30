# S2 E5 pre-registration

Committed before the full run and not edited after it. Every claim below is reported in
`README.md` as Held or Failed, failures included. The same pass marks are in `config.yaml`
(`pass_marks`), and `measure.py` applies them; a test checks this file and the config agree.

## Setup

- Library: S2 E3's 300 support articles, one article per chunk. Questions for Test D: S2 E3's 120
  (40 code, 40 paraphrase, 40 shared-word).
- Embeddings: `text-embedding-3-small`, cosine similarity, top 5, through one function,
  `search(query, index, allowed, k=5)` in `search.py`.
- Chat model (writes the data, answers, judges): the model S2 E3 wrote its articles with, read
  from S2 E3's config: `gpt-6-astra`. No temperature is sent: the model rejects one (S1 E8).
- Seed 0.
- Answer prompt (Tests A, B, and C's P1): "Answer the customer's question using the passages
  below." Passages in rank order. C's P2 adds: "If the passages do not contain the answer, reply
  exactly NOT_FOUND."
- A reply is graded by exact substring: new value present, old value present, both, neither.
  "Current value" means the new value is present; "old value" means the old value is present;
  "old value only" means the old value is present and the new one is not.

## Test A: Stale index

40 articles each have one value revised. Fresh index: revised articles re-embedded. Stale index:
original texts and vectors, which the answer model receives.

- **A1.** Stale recall at 5 is within 2 questions of fresh recall at 5.
- **A2.** Stale answers give the current value on at most 4 of 40, and the old value on at least
  30 of 40.
- **Control.** Fresh answers give the current value on at least 36 of 40.
- **A3.** Comparing a SHA-256 stored at indexing time with the current sources flags all 40
  stale entries and nothing else.

## Test B: Two versions

Both versions of the 40 articles in one index, sharing an article id: old dated 2025-03-01, new
dated 2026-06-01. The other 260 articles are unchanged and dated 2025-03-01.

- **B1.** With both versions indexed, the old version ranks above the new on at least 12 of 40.
- **B2.** B-plain (passages without dates) gives only the old value on at least 10 of 40.
- **B3.** B-dated (each passage headed `Updated: <date>`) still gives only the old value on at
  least 4 of 40.
- **B4.** B-latest (a metadata filter keeps only the latest version of each article before
  ranking) gives the old value on at most 1 of 40.

## Test C: Nothing to find, answered anyway

Fresh index. 80 questions: the 40 value questions (answerable) and 40 unanswerable (20 about a
product not in the library, 20 asking for a detail no article gives).

- **C1.** The best single top-1 cosine cut-off, chosen with hindsight on the same 80 questions,
  misclassifies at least 8 of 80 (accuracy no better than 90%).
- **C2.** Under P1, at least 20 of 40 unanswerable questions get an asserted answer.
- **C3.** Under P2, asserted answers on unanswerable questions fall to at most 8 of 40, while
  answerable questions keep the current value on at least 36 of 40.

An unanswerable reply under P2 that is exactly `NOT_FOUND` counts as declined. Every other
unanswerable reply is judged by the chat model: "assert" or "decline". A judge reply that is
neither word is recorded as unclear, and counted against the claim: not asserted for C2,
asserted for C3.

## Test D: Scope and permission leak

The index holds the 300 public articles and 60 internal notes. All 120 S2 E3 questions, asked by
a customer who may see only public articles.

- **D1.** D-none (no filter, top 5 from all 360) puts an internal passage in the top 5 on at least
  40 of 120.
- **D2.** D-post (top 5 from all 360, then internal passages dropped) has no leaks, but misses the
  right article on at least 5 more questions than D-pre.
- **D3.** D-pre (filter to public before ranking) has no leaks, and recall at 5 equal to the S2
  E3 vector result, 95 of 120.

## Rules

- The pilot (5 items per condition) checks the pipeline only. It is never used to change a pass
  mark.
- Numbers are reported as "x of n" with Wilson 95% intervals.
