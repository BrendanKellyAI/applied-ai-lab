# S2 E4: Swapping the embedding model

## Summary

**A model swap reshuffles results even when the totals barely move, and mixing two models fails
silently. A threshold carried across did not break in this pair.** On the S2 E3 support corpus,
swapping `text-embedding-3-small` for `text-embedding-3-large` moved recall at 5 from 95 of 120
to 91 of 120, a change inside the noise. But the two models' top 5s shared only 2.62 of 5
articles on average, and the new model lost 9 questions the old one found. New-model queries on
the old index found 1 of 120, below the random floor of 2, with no error raised. In a
half-migrated index, answers still in the old half were found 0 of 60 times.

| Claim | Measured | Pass mark | Verdict |
|---|---|---|---|
| 1. A swap changes which answers come back | mean top-5 overlap 2.62 of 5; 9 losses | overlap 3.5 or lower, and 5 or more losses | held |
| 2a. Cross queries fail silently | 1 of 120, no exception | 10 of 120 or lower, no exception | held |
| 2c. A half-migrated index hides the old half | old half 0 of 60; migrated half 3.3 points from full migration | old half 10% or lower; within 10 points | held |
| 3. A threshold does not transfer | K moved 5.0 points; W rose 1.04 times, by 3.55 | K 15 points, or W 2 times and 5 articles | failed |
| 4. Re-embedding costs the whole corpus, countably | API tokens 0.0% from the local count, both models | within 1% | held |

This settles the open question from S1 E3's deck. Three of its four warnings stand, with numbers.
The fourth, that a similarity threshold must be retuned, did not show up for this model pair.

## The question

S1 E3 warned that changing embedding model is not a drop-in change: a new model cannot search an
index built by the old one, vectors from two models in one store return nonsense, a similarity
threshold must be retuned, and changing model means re-embedding everything. It gave no
measurements. This field note measures each warning on a known retrieval task, and counts what
re-embedding costs in tokens before anything is spent.

## Setup

| | |
|---|---|
| Corpus | The S2 E3 corpus, unchanged: 300 support articles for an invented appliance maker, one article per chunk |
| Questions | S2 E3's 120: 40 code (S2 E3 calls them identifier questions), 40 paraphrase, 40 shared-word, each with one right article |
| Old model | `text-embedding-3-small`, 1,536 dimensions, as used in S1 E3, S2 E2 and S2 E3 |
| New model | `text-embedding-3-large`, 3,072 dimensions, embedded once |
| New, shortened | The large vectors cut to their first 1,536 values and rescaled to length 1, made locally |
| Retrieval | Cosine similarity over all 300 articles; a hit is the right article in the top 5 |
| Intervals | 95% Wilson intervals throughout |
| Seed | 20260929 |
| Run | 29 September 2026 |

**Route B.** S2 E3 kept its vectors in a gitignored cache and committed none, so there was no
stored old index to reuse. The old model was therefore embedded twice, in two separate passes:
set 1 is the old model in every comparison, and set 2 is the control.

## Method

Every retrieval condition calls one function, `top_k` in `migrate.py`, the listing on the slide.
It normalises the query and every stored vector and ranks by their dot product. Nothing in it
checks which model made either vector, which is the point.

```python
import numpy as np


def top_k(query, index, k=5):
    """Rank stored vectors by cosine similarity to the query.
    Nothing here checks which model made either vector."""
    q = query / np.linalg.norm(query)
    m = index / np.linalg.norm(index, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return best, scores[best]
```

**The measures, in plain words.**

- **Recall at 5:** the share of questions whose right article is in the top 5.
- **Top-5 overlap:** for one question, how many articles two top 5s have in common, in any
  order. An overlap of 3 of 5 means two of the five articles a user would see have changed.
- **A loss** is a question the old model found and the new one missed. **A gain** is the
  reverse. Losses and gains can cancel in the totals while users see different answers.
- **The random floor** is what picking 5 articles at random would score: 120 questions × 5
  slots / 300 articles = 2 hits in 120. A result at or below it means the ranking carries no
  information.
- **K and W** measure a similarity cut-off, the "only show results scoring above t" rule many
  systems use. `t` is set at the 10th percentile of the old model's scores for the right
  article, so about 90% of right answers clear it. **K** is the share of right articles scoring
  at or above `t`. **W** is the mean number of wrong articles per question that also clear it.

**The conditions.**

- **Old** and **new:** each model's questions against its own index.
- **Cross (claim 2a):** the new model's shortened 1,536-value question vectors against the old
  index. Same shape, so nothing stops the multiplication.
- **Half-migrated (claim 2c):** 150 articles hold shortened new vectors and 150 hold old ones.
  The 150 were chosen with the seed, stratified so each question type has 20 of its 40 answer
  articles migrated, and half the unasked look-alike (40 of 80) and other (50 of 100) articles
  too. The list is in `results/migrated_articles.json`. Queries were run both ways: with the new
  model (the application switched first) and with the old (the application switched last).
- **Shape mismatch (2b, a test, not a claim):** a 3,072-value query against a 1,536-dimension
  index. NumPy raises `ValueError`. That is the loud failure beside the silent one.

**The controls, and why each is there.**

1. **Re-embed control.** Two passes of the old model on the same texts should rank the same. If
   they did not, any swap difference could be noise from the API, not the model. Expectation:
   mean overlap 4.9 or more, and at most 2 flips (losses plus gains).
2. **Pipeline check.** The old model's recall should reproduce S2 E3's committed vector result,
   95 of 120, which shows this code retrieves the way S2 E3's did.
3. **Dimension check.** The API can serve `text-embedding-3-large` at 1,536 dimensions itself.
   On 5 articles, those vectors were compared with the locally shortened ones; every cosine had
   to be 0.9999 or more, or the run stopped. This shows the shortened vectors are what the API
   would serve.
4. **Random floor**, reported beside every mixing result.

Every pass mark was fixed in `config.yaml` before the run and applied in code, in `measure.py`.

## Results

### Recall at 5, by model and question type

| Question type | Old: 3-small | New: 3-large (3,072) | New, shortened (1,536) |
|---|---|---|---|
| Code | 15 of 40, 24% to 53% | 12 of 40, 18% to 45% | 11 of 40, 16% to 43% |
| Paraphrase | 40 of 40, 91% to 100% | 39 of 40, 87% to 100% | 39 of 40, 87% to 100% |
| Shared words | 40 of 40, 91% to 100% | 40 of 40, 91% to 100% | 40 of 40, 91% to 100% |
| All 120 | 95 of 120, 71% to 85% | 91 of 120, 67% to 83% | 90 of 120, 67% to 82% |

### Claim 1: what the swap changed

| | Swap: old against new | Control: old against old |
|---|---|---|
| Mean top-5 overlap | 2.62 of 5 | 4.99 of 5 |
| Losses | 9 of 120, 4% to 14% | 0 of 120, 0% to 3% |
| Gains | 5 of 120, 2% to 9% | 0 of 120, 0% to 3% |

Of the 9 losses, 8 were code questions and 1 a paraphrase; all 5 gains were code questions. Mean
overlap by type was 0.75 of 5 for code, 3.53 for paraphrase and 3.58 for shared-word questions.
The distribution of overlaps, from 0 to 5, was 15, 21, 15, 23, 36 and 10 questions for the swap,
and 0, 0, 0, 0, 1 and 119 for the control.

### Claim 2: mixing models

Random floor: 2 of 120, or 1 of 60 for each half.

| Condition | Recall at 5 | Median top-1 score |
|---|---|---|
| Old queries on the old index | 95 of 120, 71% to 85% | 0.545 |
| New queries (3,072) on the new index | 91 of 120, 67% to 83% | 0.567 |
| Cross: new queries (1,536) on the old index | 1 of 120, 0% to 5% | 0.050 |

By type, cross queries found 0 of 40 code (0% to 9%), 0 of 40 paraphrase (0% to 9%) and 1 of 40
shared-word questions (0% to 13%).

**Half-migrated index,** by where the right article sits:

| Queries | Answer in migrated half | Answer in old half |
|---|---|---|
| New model, shortened (headline) | 48 of 60, 68% to 88% | 0 of 60, 0% to 6% |
| Old model (secondary) | 0 of 60, 0% to 6% | 48 of 60, 68% to 88% |

On the fully migrated index, the shortened new model found 46 of 60 (65% to 86%) of the same
migrated-half questions. In the headline direction, the migrated half's 48 of 60 split into 8 of
20 code (22% to 61%), 20 of 20 paraphrase and 20 of 20 shared-word (84% to 100% each); every type
scored 0 of 20 (0% to 16%) in the old half.

### Claim 3: the threshold

| | t | K: right articles at or above t | W: wrong articles per question at or above t |
|---|---|---|---|
| Old model, its own 10th percentile | 0.289 | 108 of 120, 83% to 94% | 85.7 |
| New model, the old t carried across | 0.289 | 102 of 120, 78% to 90% | 89.2 |
| New model, retuned to its own 10th percentile | 0.261 | 108 of 120, 83% to 94% | 118.1 |

### Claim 4: tokens and index size

| Call | Local count (`cl100k_base`) | API `usage.prompt_tokens` |
|---|---|---|
| Old index, pass 1 (300 articles) | 44,731 | 44,731 |
| Old questions, pass 1 (120) | 1,676 | 1,676 |
| Control, pass 2 (300 articles) | 44,731 | 44,731 |
| Control questions, pass 2 (120) | 1,676 | 1,676 |
| New model (300 articles) | 44,731 | 44,731 |
| New questions (120) | 1,676 | 1,676 |
| Dimension check (5 articles) | 758 | 758 |
| **Total** | **139,979** | **139,979** |

Small and large reported identical token counts for the same texts. The questions are 3.7% of
the corpus's tokens. Index size at float32 for 300 articles: 1,843,200 bytes for the old model
at 1,536 dimensions, 3,686,400 bytes for the new at 3,072, and 1,843,200 bytes shortened to 1,536.

### The controls

- **Re-embed control:** mean overlap 4.99 of 5, 0 flips. The median cosine between the two
  passes' vectors for the same text was 0.9999998 for articles and 0.9999997 for questions.
- **Pipeline check:** the old model found 95 of 120, exactly S2 E3's committed vector result.
- **Dimension check:** passed. The lowest cosine was 0.99999, for article A195; three of the five
  were 0.9999999 or above.
- **Shape test:** NumPy raised `builtins.ValueError`, pinned in the test suite.

## What it means

**Claim 1 held.** The totals hid the change. Recall fell from 95 of 120 to 91 of 120, and the
intervals overlap almost entirely, so a dashboard showing recall alone would call this swap
neutral. Yet the two models agreed on only 2.62 of each question's 5 articles on average, and 9
questions the old model answered went unanswered after the swap, offset by 5 new ones. The
churn sits almost entirely in the code questions, where both models were weak (S2 E3) and each
misses different ones: their mean overlap there was 0.75 of 5. The control rules out API noise:
two passes of the same model agreed on 4.99 of 5 with no flips.

**Claim 2a held.** New-model queries on the old index found 1 of 120, below the random floor of
2, and nothing raised an error: 1,536 numbers multiply with 1,536 numbers whatever made them. The
failure is visible in the scores, if anyone watches them: the median top-1 score dropped from
about 0.55 to 0.05. A system that only returns the top 5, without a score floor, would show that
top 5 as if nothing were wrong. By contrast, the shape mismatch (2b) fails loudly, with a
`ValueError`; the silent case exists only because the shortened vectors have the old model's
shape.

**Claim 2c held.** Mid-migration, with the application already on the new model, answers not yet
re-embedded were found 0 of 60 times, while migrated answers were found 48 of 60, 3.3 points
from what the fully migrated index gives on the same questions. Recall across all 120 was 48 of
120, so the index looks half broken, not broken. Run the other way, with the application still
on the old model, the mirror image appeared exactly: 48 of 60 in the old half, 0 of 60 in the
migrated half. Either way, a partial migration silently hides the half the queries do not match.

**Claim 3 failed.** A cut-off tuned on the old model kept 102 of 120 right answers under the new
model against 108 of 120 under the old, a 5-point change, short of the 15 points the pass mark
needs. Wrong articles clearing it rose from 85.7 to 89.2 per question, 1.04 times, short of both
the doubling and the 5 articles required. So for this pair of models from one family, the old
threshold transferred about as well as it worked in the first place. Two things temper this.
First, the threshold never worked well on either model: about 86 of 299 wrong articles per
question clear it, so it filters little. Second, retuning did not restore anything useful: the
new model's own 10th percentile kept 108 of 120 but let 118 wrong articles through per question.
S1 E3's warning may hold for models whose scores sit in different ranges; it did not for these.

**Claim 4 held.** The local count with `tiktoken` `cl100k_base` matched the API's
`usage.prompt_tokens` exactly for both models: 44,731 tokens for the corpus, 0.0% apart. Both
models reported identical counts for the same text, so a re-embed costs the same token count
whichever of the two you move to. Question-side tokens are 3.7% of the corpus, so the corpus
dominates. Re-embedding is the whole corpus every time, and it can be counted to the token
before any key is used. Index size doubles going to 3,072 dimensions.

**The re-embed control held.** Two passes of the old model agreed on 4.99 of 5 articles per
question with no flips, so the differences in claim 1 come from the swap, not from the API.

## Limitations

- **One model pair from one provider.** `text-embedding-3-small` and `-large` come from the same
  family and share a tokeniser and score range. A cross-provider swap was not tested, and claim 3
  in particular may behave differently there.
- **One corpus of generated articles, one article per chunk.** 300 short articles written by one
  model to one prompt (S2 E3); chunking plays no part.
- **Pure question types,** each built to suit one search method (carried from S2 E3). Real
  questions mix code, paraphrase and shared words.
- **The shortened large vectors are used for mixing only.** They were checked against the API's
  own 1,536-dimension output on 5 articles, not the whole corpus. Claims 1 and 3 use the full
  3,072 dimensions.
- **One migration split and one seed.** Another split would move the migrated-half figures
  within their intervals.
- **Tokens only.** Latency and throughput of re-embedding were not measured.
- **Small samples.** 40 questions per type, and 60 per half, give wide intervals.

## How to reproduce

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**1. Redraw the charts from the committed results.** No key, model or network:

```bash
uv run python field-notes/s2-e4-embedding-migration/chart.py
```

**2. Count the tokens a full run will send.** No key and no network:

```bash
uv run python field-notes/s2-e4-embedding-migration/migrate.py --estimate
```

`lab estimate` drives chat providers only and does not cover embedding runs; this is its
replacement here.

**3. Rerun with an OpenAI key,** in the repository's `.env` file or your environment. The pilot
embeds 12 questions and 20 articles with both models and runs the dimension check, writing only
to `.cache/`. The full run writes `results/`:

```bash
uv run python field-notes/s2-e4-embedding-migration/migrate.py --pilot
```

```bash
uv run python field-notes/s2-e4-embedding-migration/migrate.py
```

Each pass is saved to `.cache/s2-e4-embedding-migration/`, so a rerun after a failure does not
pay for finished passes twice. Delete that folder to embed afresh.

### Charts

Drawn by `chart.py` from `results/results.json` alone, in `results/charts/`, at slide (PNG and
SVG) and article (PNG) sizes.

- **`recall-by-model`**: recall at 5 by type and for all 120, old beside new, with intervals.
  Nothing is highlighted: the two all-120 intervals overlap.
- **`top5-overlap`**: how many questions had each overlap from 0 to 5, swap beside control, with
  both means marked. The acid green element is the swap's mean line, at 2.62, because claim 1's
  overlap condition held. The chart system allows one green element, so the line carries it
  rather than the six swap bars.
- **`mixing`**: recall at 5 for old on old, cross queries, and both halves of the half-migrated
  index in both directions, against the random floor. The acid green element is the stub of the
  half-migrated, new-query, old-half bar, at 0 of 60, because claim 2c held.

## Files

- `migrate.py`: the slide's `top_k`, then the experiment, with `--estimate` and `--pilot`.
- `measure.py`: every measure, the migrated split, and the verdict for each pass mark.
- `chart.py`: the charts.
- `config.yaml`: the models, the seed and every pass mark.
- `results/results.json`: every condition's per-question top 5 article IDs and scores, hits,
  overlaps, losses and gains, the thresholds with K and W, token usage per batch, the local
  counts, index sizes, model metadata, the route, the seed, the run date, and every verdict.
- `results/vectors.npz`: float32 vectors for the old model (set 1) and the new model, articles
  and questions, plus the 5 dimension check vectors: 7,772,160 bytes. The control's set 2 was
  left out to stay under 10 MB; its overlaps, flips and median cosines are in `results.json`.
- `results/local_token_counts.json`: every article's and question's local token count.
- `results/migrated_articles.json`: the 150 migrated article IDs and their split by type.

## Run metadata

Run on 29 September 2026 (UTC), route B, seed 20260929. Every call returned the model requested:
`text-embedding-3-small` at 1,536 values and `text-embedding-3-large` at 3,072, or 1,536 for the
dimension check. `results/results.json` records the model requested and returned, the vector
length and the date for every pass, and `usage.prompt_tokens` for every batch. The pilot, on
the same date, used 7,213 tokens: 3,239 for each model and 735 for its dimension check. The
results were computed once from the API's vectors, then recomputed from the same cached vectors,
with no further calls, after a floating-point fix to how point gaps are compared with their pass
marks; no verdict changed. No prices were looked up or recorded.
