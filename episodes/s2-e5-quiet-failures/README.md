# S2 E5: When retrieval quietly fails

## Summary

**Retrieval scores stayed flat while the answers went wrong, and the cheap fixes worked, but
`gpt-6-astra` handled two of the four failures better than the pass marks expected.** 10 of 14
pre-registered claims held and 4 failed.

- **Stale index:** recall at 5 was 39 of 40 on both the fresh and the stale index. But the stale
  index gave the old value on 36 of 40 answers and the current one on none. A hash stored at
  indexing time flagged all 40 stale entries and nothing else.
- **Two versions:** with both versions indexed, the old one outranked the new on 17 of 40. The
  model rarely gave the old value alone (1 of 40). On 33 of 40 it reported both values as a
  conflict. Adding dates to the passages fixed that completely; so did filtering to the latest
  version.
- **Nothing to find:** no top-1 score cut-off separates answerable from unanswerable questions.
  The best one, chosen with hindsight, still got 21 of 80 wrong. But the model declined 39 of 40
  unanswerable questions even under the standard prompt, so "answered anyway" did not happen
  here.
- **Permission leak:** with no filter, an internal note reached the prompt on 62 of 120
  questions. Filtering after ranking stopped the leak but cost 11 answers (84 of 120 against 95).
  Filtering before ranking stopped it and cost nothing (95 of 120, as in S2 E3).

## Purpose

S2 E1 listed failures that arrive with no error: answered anyway, stale index, two versions, and
a permission leak. S2 E4 measured a fifth, a silent model swap. This episode measures the other
four on the S2 E3 library, and tests the fix for each.

The thread across all four: the usual retrieval score, recall at 5, stays flat or looks fine
while the answer or the prompt goes wrong. So every test reports a search-level number and an
answer-level (or prompt-level) number side by side.

## Setup

| | |
|---|---|
| Library | S2 E3's 300 support articles for Halvard Home, unchanged, one article per chunk |
| Questions | Tests A to C: 40 value questions and 40 unanswerable questions built here. Test D: S2 E3's 120 (40 code, which S2 E3 calls identifier, 40 paraphrase, 40 shared-word) |
| Embeddings | `text-embedding-3-small`, 1,536 numbers, cosine similarity, top 5, through S2 E2's cached embedder |
| Chat model | `gpt-6-astra`, read from S2 E3's config: it writes the data, answers, and judges |
| Search | One function, `search(query, index, allowed, k=5)` in `search.py`, below |
| Seed | 0 |
| Run | 4 October 2026 |
| Intervals | Wilson 95% |

Every chat response is cached under a hash of the model and the full request, and every
embedding under a hash of the model and the text, in the main checkout's `.cache/` (gitignored),
shared by every worktree. A rerun of the full run sends nothing.

### The search on the slide

The filter runs on each entry's metadata before ranking, so an entry the user may not see never
takes a place in the top 5. Every test ranks through it: a rule that allows everything is plain
vector search.

```python
import numpy as np


def search(query, index, allowed, k=5):
    """Top k entries this user may see, by cosine similarity.
    The metadata filter runs before ranking, so an entry
    the user may not see can never take a place in the top k."""
    keep = [i for i, entry in enumerate(index["entries"]) if allowed(entry)]
    vectors = index["vectors"][keep]
    q = query / np.linalg.norm(query)
    m = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return [index["entries"][keep[i]] for i in best], scores[best]
```

### The data (committed to `data/`)

- **Value facts (40).** For each candidate article, in seeded order, the model picks one sentence
  stating a single concrete value, preferring a measurement or duration over a code. Code keeps
  it only if the sentence is copied exactly and the value appears exactly once in the 300
  articles, inside that sentence; a value that repeats is asked for again with the reason. The
  model then gives a replacement value; code checks it appears nowhere in the library and that
  neither value contains the other, so grading by substring cannot confuse them. Code makes the
  swap, and a diff confirms the revision differs from the original by that value only. The model
  then writes a question that needs the value, rewritten if it contains either value. The 40 are
  27 codes (part numbers and error codes) and 13 measurements, durations or phrases: few
  measurements in this library are unique.
- **Unanswerable questions (40).** 20 about a Halvard Home product that does not exist; code
  checks the product name appears nowhere in the library. 20 asking for a technical detail no
  article gives (no prices or account details), kept only if the model, as judge over the top 10
  retrieved passages plus the source article, says no passage answers it. All 40 are in
  `data/unanswerable.csv` for a manual read.
- **Internal notes (60).** For 60 articles that answer an S2 E3 question, 20 of each type, a
  dealer or engineering note on the same issue (repair procedure, known defect, warranty
  exception), tagged `access: internal`. Code checks no note shares a run of 60 or more characters
  with any public article.

## Claims

Pre-registered in `PREREGISTRATION.md`, committed before the full run and not edited.

| Claim | Pass mark | Measured | Verdict |
|---|---|---|---|
| A1. A stale index keeps its recall | stale within 2 questions of fresh | 39 of 40 both; gap 0 | **Held** |
| A2. The stale index gives the old value | current 4 or fewer of 40, old 30 or more | current 0, old 36 | **Held** |
| A control. The reader works | fresh current 36 or more of 40 | 35 of 40 | **Failed** |
| A3. A stored hash finds every stale entry | all 40, nothing else | 40 of 40, 0 others | **Held** |
| B1. The old version outranks the new | 12 or more of 40 | 17 of 40 | **Held** |
| B2. Both versions indexed: old value only | 10 or more of 40 | 1 of 40 | **Failed** |
| B3. Dates in the prompt do not fix it | 4 or more of 40 | 0 of 40 | **Failed** |
| B4. A latest-version filter fixes it | old value 1 or fewer of 40 | 0 of 40 | **Held** |
| C1. No score cut-off separates answerable from not | 8 or more of 80 misclassified | 21 of 80 (accuracy 73.8%) | **Held** |
| C2. The standard prompt answers anyway | 20 or more of 40 asserted | 1 of 40 | **Failed** |
| C3. "Reply NOT_FOUND" fixes it without losing answers | asserted 8 or fewer, current 36 or more | asserted 0, current 37 | **Held** |
| D1. No filter leaks internal notes | 40 or more of 120 | 62 of 120 | **Held** |
| D2. Filtering after ranking costs answers | no leaks, 5 or more extra misses | no leaks, 11 extra misses | **Held** |
| D3. Filtering before ranking costs nothing | no leaks, recall 95 of 120 | no leaks, 95 of 120 | **Held** |

## Results

### Test A: Stale index (`charts/stale-slide.svg`)

| | Fresh index | Stale index |
|---|---|---|
| Recall at 5 | 39 of 40 (87% to 100%) | 39 of 40 (87% to 100%) |
| Answer gives the current value | 35 of 40 (74% to 95%) | 0 of 40 (0% to 9%) |
| Answer gives the old value | 0 of 40 (0% to 9%) | 36 of 40 (77% to 96%) |
| Neither value | 5 of 40 | 4 of 40 |

Search cannot see the problem: the stale index finds the right article as often as the fresh one,
and the answer is out of date on 36 of 40. The hash comparison, which needs no API call, flagged
all 40 stale entries and no others.

**Why the control failed (35 of 40, mark 36).** The five misses are grading, not reading:

- Two answers were right but bolded the value: `within **five minutes**` does not contain the
  substring `within five minutes`, and `at least **two metres** of clear space` does not contain
  `at least two metres`.
- Three "values" are phrases rather than numbers ("detergent made for dishwashers", "one of the
  space where it fits", "an authorised electrical waste service"). The build check required the
  value to be unique and exact, but not to contain a number, so these slipped through, and the
  answers paraphrased them.

Grading by exact substring was pre-registered, so the verdict stands. Grading without the bold
markers would give 37 of 40.

### Test B: Two versions (`charts/versions-slide.svg`)

The old version ranked above the new on 17 of 40 (29% to 58%), and both versions were in the top
5 on every question: only the old one was there on 0 of 40.

| | Old value only | New value only | Both | Neither |
|---|---|---|---|---|
| B-plain (no dates) | 1 of 40 | 2 of 40 | 33 of 40 (68% to 91%) | 4 of 40 |
| B-dated (`Updated: <date>`) | 0 of 40 | 35 of 40 (74% to 95%) | 0 of 40 | 5 of 40 |
| B-latest (filter before ranking) | 0 of 40 | 35 of 40 (74% to 95%) | 0 of 40 | 5 of 40 |

B2 and B3 failed, and in an informative direction. Given both versions with no dates, the model
did not quietly pick the old one: it reported the conflict and both values, typically "the
passages give conflicting part numbers… contact support". That is safer than a wrong answer, but
it still fails the customer on 33 of 40. Headed with dates, the model chose the newer value every
time, as well as the metadata filter did. Most values here are part numbers and codes, where a
clash is obvious; a clash between two durations might be harder to spot.

### Test C: Nothing to find (`charts/scores-slide.svg`, `charts/prompts-slide.svg`)

Top-1 scores: answerable questions ranged from 0.457 to 0.831, unanswerable ones from 0.388 to
0.787. The best single cut-off, 0.631, chosen with hindsight on these same 80 questions,
misclassified 21 of 80 (accuracy 73.8%). A score threshold cannot tell "nothing to find" from
"found it".

| | P1 (standard prompt) | P2 (+ reply NOT_FOUND) |
|---|---|---|
| Unanswerable: asserted an answer | 1 of 40 (0% to 13%) | 0 of 40 (0% to 9%) |
| Unanswerable: replied NOT_FOUND | 0 of 40 | 40 of 40 (91% to 100%) |
| Answerable: current value | 35 of 40 (74% to 95%) | 37 of 40 (80% to 97%) |

C2 failed: `gpt-6-astra` declined 39 of 40 unanswerable questions under the standard prompt,
with replies such as "The passages don't include cleaning instructions for the Halvard Home Sora
air fryer basket…". This model does not answer anyway, even about products that do not exist.
P2 still helps: it turns a polite paragraph into a token code can act on, 40 of 40, and costs no
answerable questions.

### Test D: Scope and permission leak (`charts/scope-slide.svg`)

| | Leaks | Recall at 5 | Passages delivered (mean) | Questions with fewer than 5 |
|---|---|---|---|---|
| D-none | 62 of 120 (43% to 60%) | 84 of 120 (61% to 77%) | 5.00 | 0 |
| D-post | 0 of 120 (0% to 3%) | 84 of 120 (61% to 77%) | 3.18 | 62 |
| D-pre | 0 of 120 (0% to 3%) | 95 of 120 (71% to 85%) | 5.00 | 0 |

Internal notes on the same issue often outrank public articles. Dropping them after ranking stops
the leak, but leaves the prompt short (fewer than 5 passages on 62 questions) and loses 11 right
answers that sat just below the notes. Filtering before ranking keeps all five places for public
articles.

## Built to be checked

| Check | Result |
|---|---|
| 1. Same index twice: identical top 5 for all 120 S2 E3 questions | 120 of 120 |
| 2. S2 E3 rerun: vector recall at 5 on the public 300 is 95 of 120 | 95 of 120 |
| 3. Reader works: Test A's fresh control | 35 of 40: failed, see Test A |
| 4. Values are unique in their own version and nowhere else | 40 of 40 |
| 5. Each revision differs by the one value | 40 of 40 |
| 6. Internal notes are reachable: a question written from each note finds it in D-none's top 5 | 57 of 60 |
| 7. Judge audit: 20 flagged rows in `judge_audit.csv` | 20 flagged, read by hand |

Check 1 builds the index twice from the stored vectors, so it checks the indexing and search code
is deterministic. It does not re-embed: S2 E4 measured the API's own run-to-run variation.

**Judge audit.** All 40 judged replies were under P1: every P2 reply to an unanswerable question
was exactly `NOT_FOUND`, so none needed a judge. Of the 20 flagged rows, 18 are judged correctly.
Two are arguable: one reply judged "assert" says no interval is given and lists signs to watch
for, which is closer to a decline; one judged "decline" gives a direct instruction. Neither
changes a verdict: C2 fails with 0, 1 or 2 asserted.

Offline, `tests/test_s2_e5_quiet_failures.py` runs the whole pipeline on a small invented
library with a fake model: every claim and check is reached, the stale hash flags exactly the
revised entries, the pre-filter never leaks, and a rerun sends nothing.

## How the pilot changed the build

Three pilots of 5 items per condition ran before the full run (results in `results/pilot/`, the
third). None changed a pass mark.

1. The first pilot's value facts were all part numbers, and its absent-detail questions all asked
   for prices or account details, which any support library would decline. The value-fact prompt
   now prefers a measurement or duration; the absent-detail prompt asks for a technical detail
   and rules out prices, costs, accounts and personal details.
2. The second pilot passed only 5 of 46 value-fact candidates, too few to reach 40 from 300
   articles. A value that repeats elsewhere in the library is now asked for again with the
   reason, like every other checked step.

## Departures from the build spec

- **No temperature is sent.** The spec asks for temperature 0; `gpt-6-astra` rejects any
  temperature with HTTP 400 (S1 E8), as S2 E3 found. Replies are cached, so a rerun is identical,
  but a fresh run with an empty cache will not reproduce them word for word.
- **Chart style** is the repository's shared `lab.charts` system that S2 E2 to E4 use (navy,
  pale bars, hatched second series, one acid green highlight, Inter Tight), at the same slide
  size as S2 E4. Two charts have a highlight, each where one interval clears the bar it is
  compared with: the stale index's old-value bar (`stale`) and the no-filter leaks bar
  (`scope`). `versions` and `prompts` say on the chart that nothing is highlighted; `scores` has
  no highlight rule.
- **Test B dates:** the 260 unchanged articles are dated 2025-03-01, and B-latest shows passages
  without dates, so only the filter differs from B-plain.

## Limitations

- One embedding model, one chat model, one generated library.
- The same model writes the data, answers and judges; the judge is audited on 20 items only.
- One chunk per article; version and scope effects may differ with many chunks per document.
- Invented values and internal notes; real revisions and internal content vary more. Most values
  here are codes, and three are phrases rather than numbers.
- The C1 cut-off is chosen with hindsight, so it overstates what a real cut-off achieves.
- Exact-substring grading misses a right answer that formats the value differently (bold, a
  paraphrase).
- Tokens only; no timings.

## Tokens

Counted locally before the run (`--estimate`), against what the API reported for every call the
results depend on, cached or not (`results/tokens.json`). The actual counts include the pilots'
calls the full run reused, and every repeated prompt the cache answered; the estimate counts each
distinct prompt once.

| Stage | Estimate: input | Estimate: output | Actual: calls | Actual: input | Actual: output |
|---|---|---|---|---|---|
| Data build | 148,434 | 51,000 | 650 | 201,337 | 61,687 |
| Embeddings | 63,738 | 0 | 660 texts | 64,696 | 0 |
| Answering | 224,332 | 14,000 | 360 | 291,521 | 12,673 |
| Judging | 11,348 | 800 | 40 | 5,208 | 382 |

Output includes reasoning tokens (data build 36,512).

## Rerun

From the repository root. `--estimate` needs no key; the pilot and the full run need
`OPENAI_API_KEY` in `.env`. Without `--yes`, the full run prints the estimate and stops before
its first paid call. With the cache in place, a rerun sends nothing.

```bash
uv run python episodes/s2-e5-quiet-failures/quiet.py --estimate
uv run python episodes/s2-e5-quiet-failures/quiet.py --pilot
uv run python episodes/s2-e5-quiet-failures/quiet.py --yes
uv run python episodes/s2-e5-quiet-failures/chart.py
```
