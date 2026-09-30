# S2 E5: When retrieval quietly fails

**Status: built and tested offline; not yet run.** The pilot and the full run spend API budget
and wait for the owner's approval. Every claim below reads "Not run" until then.

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
| Intervals | Wilson 95% |

Every chat response is cached under a hash of the model and the full request, and every
embedding under a hash of the model and the text, in `.cache/` (gitignored). A rerun of the full
run sends nothing.

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

- **Value facts (40).** For each candidate article, in seeded order, the model returns one sentence
  stating a single concrete value, and the value. Code keeps it only if the sentence is copied
  exactly and the value appears exactly once in the 300 articles, inside that sentence. The model
  then gives a replacement value; code checks it appears nowhere in the library and that neither
  value contains the other, so grading by substring cannot confuse them. Code makes the swap,
  and a diff confirms the revision differs from the original by that value only. The model then
  writes a question that needs the value, rejected and rewritten if it contains either value.
- **Unanswerable questions (40).** 20 about a Halvard Home product that does not exist; code
  checks the product name appears nowhere in the library. 20 asking for a detail no article
  gives, kept only if the model, as judge over the top 10 retrieved passages plus the source
  article, says no passage answers it. All 40 are in `data/unanswerable.csv` for a manual read.
- **Internal notes (60).** For 60 articles that answer an S2 E3 question, 20 of each type, a
  dealer or engineering note on the same issue (repair procedure, known defect, warranty
  exception), tagged `access: internal`. Code checks no note shares a run of 60 or more characters
  with any public article.

A step a code check rejects is asked again with the rejected reply and the reason, up to four
times. The prompts are in `config.yaml`.

## Claims

Pre-registered in `PREREGISTRATION.md`, committed before the full run.

| Claim | Pass mark | Measured | Verdict |
|---|---|---|---|
| A1. A stale index keeps its recall | stale within 2 questions of fresh | | Not run |
| A2. The stale index gives the old value | current 4 or fewer of 40, old 30 or more | | Not run |
| A control. The reader works | fresh current 36 or more of 40 | | Not run |
| A3. A stored hash finds every stale entry | all 40, nothing else | | Not run |
| B1. The old version outranks the new | 12 or more of 40 | | Not run |
| B2. Both versions indexed: old value only | 10 or more of 40 | | Not run |
| B3. Dates in the prompt do not fix it | 4 or more of 40 | | Not run |
| B4. A latest-version filter fixes it | old value 1 or fewer of 40 | | Not run |
| C1. No score cut-off separates answerable from not | 8 or more of 80 misclassified | | Not run |
| C2. The standard prompt answers anyway | 20 or more of 40 asserted | | Not run |
| C3. "Reply NOT_FOUND" fixes it without losing answers | asserted 8 or fewer, current 36 or more | | Not run |
| D1. No filter leaks internal notes | 40 or more of 120 | | Not run |
| D2. Filtering after ranking costs answers | no leaks, 5 or more extra misses | | Not run |
| D3. Filtering before ranking costs nothing | no leaks, recall 95 of 120 | | Not run |

## The tests

- **Test A, stale index.** The 40 revised articles are re-embedded in the fresh index. The stale
  index still holds the original text and vectors, which the answer model receives. The hash
  check stores a SHA-256 of each source text at indexing time and compares it with the current
  sources: no API call.
- **Test B, two versions.** Both versions of each revised article in one index of 340 entries,
  sharing an article id: old dated 2025-03-01, new dated 2026-06-01. The 260 unchanged articles
  are dated 2025-03-01. B-plain shows passages without dates; B-dated heads each with
  `Updated: <date>`; B-latest filters to the latest version of each article before ranking, and
  shows passages without dates, so only the filter differs from B-plain.
- **Test C, nothing to find.** The fresh index and 80 questions. Part 1 finds the single top-1
  score cut-off that best separates answerable from unanswerable on this same data, the generous
  case. Part 2 compares P1, the standard prompt, with P2, which adds "If the passages do not
  contain the answer, reply exactly NOT_FOUND." Unanswerable replies other than an exact
  `NOT_FOUND` are judged "assert" or "decline" by the model; every judged reply is in
  `results/judge_audit.csv`, with a seeded 20 flagged for a manual check.
- **Test D, scope.** 300 public articles and 60 internal notes; all 120 S2 E3 questions, as a
  customer. D-none takes the top 5 of all 360; D-post takes the top 5 of all 360 and drops
  internal ones, so the prompt may get fewer than 5; D-pre filters to public before ranking. No
  answering.

## Built to be checked

| Check | Result |
|---|---|
| 1. Same index twice: identical top 5 for all 120 S2 E3 questions | Not run |
| 2. S2 E3 rerun: vector recall at 5 on the public 300 is 95 of 120 | Not run |
| 3. Reader works: Test A's fresh control | Not run |
| 4. Values are unique in their own version and nowhere else | Not run |
| 5. Each revision differs by the one value | Not run |
| 6. Internal notes are reachable: a question written from each note finds it in D-none's top 5 | Not run |
| 7. Judge audit: 20 flagged rows in `judge_audit.csv` | Not run |

Check 1 builds the index twice from the stored vectors, so it checks the indexing and search code
is deterministic. It does not re-embed: S2 E4 measured the API's own run-to-run variation.

Offline, `tests/test_s2_e5_quiet_failures.py` runs the whole pipeline on a small invented
library with a fake model: every claim and check is reached, the stale hash flags exactly the
revised entries, the pre-filter never leaks, and a rerun sends nothing.

## Departures from the build spec

- **No temperature is sent.** The spec asks for temperature 0; `gpt-6-astra` rejects any
  temperature with HTTP 400 (S1 E8), as S2 E3 found. Replies are cached, so a rerun is identical,
  but a fresh run with an empty cache will not reproduce them word for word.
- **Chart style** is the repository's shared `lab.charts` system that S2 E2 to E4 use (navy,
  pale bars, hatched second series, one acid green highlight, Inter Tight), at the same slide
  size as S2 E4.

## Limitations

- One embedding model, one chat model, one generated library.
- The same model writes the data, answers and judges; the judge is audited on 20 items only.
- One chunk per article; version and scope effects may differ with many chunks per document.
- Invented values and internal notes; real revisions and internal content vary more.
- The C1 cut-off is chosen with hindsight, so it overstates what a real cut-off achieves.
- Tokens only; no timings.

## Rerun

From the repository root. `--estimate` needs no key; the pilot and the full run need
`OPENAI_API_KEY` in `.env`. Without `--yes`, the full run prints the estimate and stops before
its first paid call.

```bash
uv run python episodes/s2-e5-quiet-failures/quiet.py --estimate
uv run python episodes/s2-e5-quiet-failures/quiet.py --pilot
uv run python episodes/s2-e5-quiet-failures/quiet.py --yes
uv run python episodes/s2-e5-quiet-failures/chart.py
```

### Estimate

Counted locally with `o200k_base` for the chat model and `cl100k_base` for embeddings, before any
call. Output tokens are assumed (config.yaml, `estimate`), reasoning included.

| Stage | Calls or texts | Input tokens | Output tokens |
|---|---|---|---|
| Data build | 390 | 108,853 | 136,500 |
| Embeddings | 685 | 63,738 | 0 |
| Answering | 280 | 224,332 | 70,000 |
| Judging | 80 | 11,348 | 9,600 |
| Total | 1,435 | 408,271 | 216,100 |
