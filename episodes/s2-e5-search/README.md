# S2 E5: Search

Which search finds the right passage, and where does each one fail? E5 changes only stage 5 and
repeats v1 S2 E3's comparison of keyword, vector and hybrid search on the season library, with
answers. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: the reference keeps vector search.** The hybrid chosen on dev gave significantly more
right answers (299 against 280 of 400) but found the right passage slightly less often (276
against 281), and the pre-registered rule joins a search change only on the search number.

## The design

- **Library and items:** `halvard-v2`, 520 test items; 100 dev items to choose the fuse depth.
- **Reference:** the system after E4 (`season2/history/s2-e5-search.yaml`): section chunks of up
  to 1,024 tokens, vector search, top 5 passages, `gpt-6-luna` answering, `gemini-3.6-flash`
  judging.
- **Conditions:** `baseline` (vector, cosine, `text-embedding-3-small`); `keyword` (BM25, text
  lower-cased and split on `\w+`); `hybrid-all`, `hybrid-50`, `hybrid-20` (reciprocal rank
  fusion, k = 60, of all, the top 50 or the top 20 of each ranking).
- **Runs:** all search-only on test and dev. All three hybrids tied on dev at 49 of 70, so the
  pre-registered tie-break chose the shallowest, `hybrid-20`, which ran in full.

### A reproducibility fix found here

With no filter, a restricted question asked by staff and the same question asked by the public
get identical prompts. Both requests went to the model in the same batch, came back worded
differently, and the cache kept only one: a rerun then gave both items the same reply, so 32
judge calls changed between runs. This is why E3 saw 32 items re-judged. From E5, each distinct
request in a batch is sent once and its reply given to every item that made it
(`waves.run_wave`). E5's reference run is a fresh run under the fix, and reproduces exactly; it
differs from E4's by one verdict (280 right against 281).

## Results

### Recall at 5

| Search | All 400 | Identifier (40) | Paraphrase (40) | Follow-up (40) | Look-alike above the evidence |
|---|---|---|---|---|---|
| **Vector (reference)** | **281** (66% to 75%) | 15 | 40 | 7 | 18 |
| Keyword (BM25) | 232 (53% to 63%) | **40** | 0 | 4 | 5 |
| Hybrid, all | 251 (58% to 67%) | 31 | 0 | 0 | 5 |
| Hybrid, top 50 | 257 | 31 | 6 | 0 | 5 |
| Hybrid, top 20 | 276 (64% to 73%) | 32 | 23 | 0 | 4 |

"Look-alike above the evidence" counts identifier and distractor items where a look-alike passage
outranked the right one.

### The full runs

| | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| Vector, reference | 281 of 400 (66% to 75%) | 280 of 400 (65% to 74%) | 42 of 120 | 76 of 480 |
| Hybrid, top 20 | 276 (64% to 73%) | **299 (70% to 79%)** | 45 | 103 |

Paired on the same items, the hybrid answered 61 questions right that vector search got wrong,
and 33 the other way (exact McNemar p = 0.005). By type, right answers moved most on identifiers
(15 to 32 of 40) and paraphrases (38 to 29).

## The claims

**S1 held: keyword search finds identifier codes that vector search misses.** 40 of 40
(91% to 100%) against 15 of 40 (24% to 53%), the same split as v1. To an embedding model,
`E-2194` and `E-1294` are nearly the same; BM25 matches the digits exactly.

**S2 held: vector search finds paraphrases that keyword search misses.** 40 of 40 against 0 of
40. A paraphrase shares no content word with its passage, so BM25 has nothing to match.

**S3 held: fusing the full rankings does not beat vector search.** 251 of 400 against 281, as in
v1. Fusing everything gives keyword search's near-random tail of a paraphrase question the same
weight as vector search's good ranking.

**S4 failed: fusing only the top 20 kept keyword's strength but not all of vector's.** It found
32 identifiers against vector's 15 (intervals apart), but lost 17 paraphrases and every
follow-up, ending at 276 of 400, below vector's 281.

**S5 failed: the hybrid's answers improved while its search number fell.** Search -5, answers
+19. The search number asks whether every evidence span is in the top 5; answers can come right
from a passage that restates the fact, and 20 of the 51 questions the hybrid newly got right did
not have the labelled evidence in its top 5. On identifier questions both moved together.

## Joining the reference system

The rule, fixed before the run: a search change joins if its search number sits above the
reference's and its answer number is not lower. `hybrid-20` failed the first part, so the
reference keeps vector search. The answer gain was significant in a paired test, which the
rule does not consult; that is reported here, and the recap (E16) returns to it.

## What this does not show

- **One embedding model and one BM25 tokenisation.** A tokeniser that kept `E-2194` whole would
  behave differently again.
- **One fusion method,** equal weights. A weighted fusion that trusts keyword search only for
  code-like queries was not tested.
- **The dev set has no identifier, paraphrase or shared-word items,** so the three hybrids tied
  on dev and the choice fell to the tie-break.
- **The judge** is `gemini-3.6-flash`, checked against E3's sample.

## Charts

`results/charts/`: **`recall`** (recall at 5 per search method; acid green for the best only if
it clears the reference's interval: none does, and the chart says so), **`numbers`** (the four
season numbers, reference against hybrid) and **`scoreboard`** (stage 5 highlighted; joined: no).

## Cost

$1.48 (OpenAI $0.14, Google $1.34), for the hybrid's full run and the reference's re-judged
items. Search-only conditions cost nothing new: their embeddings were cached.

## Run it

```bash
uv run lab rag analyse episodes/s2-e5-search/config.yaml
```

```bash
uv run lab rag run episodes/s2-e5-search/config.yaml
```
