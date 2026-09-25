# S2 E3: Search

The code behind the search results in S2 E3, Search. The function in `search.py` below the marker comment matches the slide line for line, and the experiment calls that exact function.

## The question

There are three common ways to find the passage that answers a question. **Keyword search** scores passages by the words they share with the question, weighting rare words more (BM25). **Vector search** embeds the question and every passage and returns the closest in meaning (S1 E3). **Hybrid search** runs both and merges the two rankings. This episode measures where each one wins and fails, on a knowledge base where the right answer to every question is known. It tests three claims:

1. **Vector search finds paraphrases that keyword search misses.** When a question shares no content words with its answer, keyword search fails and vector search still finds it.
2. **Keyword search beats vector search on exact identifiers.** When a question turns on a code, such as an error code or a part number, vector search confuses it with look-alike codes and keyword search does not. S1 E3 found "rose 5%" and "fell 5%" were near neighbours; this tests the same weakness on identifiers.
3. **Hybrid search is the safe default.** Merging the two rankings is never much worse than the better method on any type of question, and is better than either alone across all questions.

## The design

- **The knowledge base.** 300 short support articles for Halvard Home, an invented maker of home appliances: ten invented products, each with 30 topics. Each article is 120 to 220 tokens (`cl100k_base`) and states one fact. They were written by `gpt-6-astra` through the Responses API from the prompts in `config.yaml`, with no temperature set (the model rejects one, S1 E8). They are committed in `corpus.json`, so the search can be rerun without generating anything. Each article is one chunk, so chunking (S2 E2) plays no part.
- **Identifiers and look-alikes.** 40 articles each carry one identifier, 20 error codes such as `E-2194` and 20 part numbers such as `KX-9283`. For each of those, two other articles carry a **look-alike**: one with two neighbouring digits swapped (`E-1294`) and one with a digit changed (`E-4194`), describing a different fault. The identifiers are made in code, not by the model, so the one-digit rule is exact, and no identifier is one digit away from any code outside its own group. Code checks that every article contains exactly the identifier it was given, and no other.
- **Questions: three types, 40 of each,** each with exactly one correct article, committed in `questions.json`.
  - **Identifier questions** name the code and nothing else: "What does error E-2194 mean?", "What is part KX-9283 for?". They come from these two templates in code, so nothing else distinctive can slip in.
  - **Paraphrase questions** share no content words with their article. The model wrote them, and code checked them: both texts lower-cased and split into words, the stop words in `config.yaml` removed, and any question sharing a remaining word sent back to be rewritten. The check compares whole words only, so "dishwashing" passes against "dishwasher".
  - **Shared-word questions** reuse at least two of the article's own content words. They are the control: every method should do well on them.
- **Keyword search:** BM25 from `rank-bm25` 0.2.2, default settings. Text is lower-cased and split on `\w+`, so `E-2194` becomes `e` and `2194`. That is how common search engines split codes by default.
- **Vector search:** `text-embedding-3-small`, ranked by cosine similarity.
- **Hybrid search:** reciprocal rank fusion of the two full rankings, with k = 60, the value from the method's original paper. An article scores 1 / (60 + its rank) in each ranking, and the two scores add up.
- **A hit** is the correct article in the top 5. Ranks beyond 20 are recorded as not found.

The measures and the pass mark for each claim were fixed before the run, in `measure.py`, and were not changed after it.

## Results

Run on 25 September 2026. All intervals are Wilson 95% intervals.

### Recall at 5, by method and question type (the headline)

| Question type | Keyword | Vector | Hybrid |
|---|---|---|---|
| Identifier | **40/40**, 91% to 100% | 15/40, 24% to 53% | 33/40, 68% to 91% |
| Paraphrase | 0/40, 0% to 9% | **40/40**, 91% to 100% | 5/40, 5% to 26% |
| Shared words (control) | 39/40, 87% to 100% | 40/40, 91% to 100% | 39/40, 87% to 100% |
| All 120 | 79/120, 57% to 74% | **95/120**, 71% to 85% | 77/120, 55% to 72% |

### Recall at 1 and mean reciprocal rank

| Question type | Keyword | Vector | Hybrid |
|---|---|---|---|
| Identifier | 32/40, MRR 0.900 | 6/40, MRR 0.257 | 17/40, MRR 0.575 |
| Paraphrase | 0/40, MRR 0.001 | 31/40, MRR 0.867 | 0/40, MRR 0.067 |
| Shared words | 38/40, MRR 0.963 | 40/40, MRR 1.000 | 39/40, MRR 0.978 |
| All 120 | 70/120, MRR 0.621 | 77/120, MRR 0.708 | 56/120, MRR 0.540 |

Mean reciprocal rank counts an answer ranked below 20 as zero.

### Look-alikes ranked above the right article, identifier questions

| Keyword | Vector | Hybrid |
|---|---|---|
| 0/40, 0% to 9% | 18/40, 31% to 60% | 3/40, 3% to 20% |

## What the results say about each claim

**Claim 1 held.** On paraphrase questions vector search found 40/40 (91% to 100%) and keyword search 0/40 (0% to 9%). Vector search put the right article first 31 times out of 40. With no content word in common, BM25 is left scoring articles on words such as "my" and "how", which is noise.

**Claim 2 held.** On identifier questions keyword search found 40/40 (91% to 100%), 32 of them at rank 1. Vector search found 15/40 (24% to 53%). For vector search, a look-alike article ranked above the right one on 18 of the 40 questions (31% to 60%); for keyword search, on none (0% to 9%). Of vector search's 25 misses, 15 had a look-alike above the answer, and the rest lost to other articles with codes of the same kind. To the embedding model, "E-2194" and "E-1294" are nearly the same thing. BM25 splits off the digits, "2194", as a rare word that appears in exactly one article, and finds it every time.

**Claim 3 did not hold, on either part.** Across all 120 questions the hybrid found 77/120 (55% to 72%), below vector search alone at 95/120 (71% to 85%) and keyword search at 79/120 (57% to 74%). It was also well outside the better method's interval on paraphrase questions: 5/40 (5% to 26%), against vector search's 40/40 (91% to 100%). On identifier questions it held up: 33/40 (68% to 91%), against keyword search's 40/40 (91% to 100%), which is below keyword's interval. So hybrid was not the safe default here: on each question type it came out worse than the better method.

The cause is how the fusion was specified: it merges the **full** rankings of both methods. When one method has nothing useful to say, as keyword search on a paraphrase, its ranking is close to arbitrary, but fusion still gives it equal weight, and it pushes the right article down. On paraphrase questions the hybrid put the right article between rank 2 and 20 for 19 questions and below 20 for the other 21. Many production systems fuse only the passages each method actually matched, or weight the methods, and would behave differently. This run tests the plain textbook form, as briefed, and that form is not a safe default.

**The control held.** On shared-word questions all three methods found 39/40 or 40/40, so the pipeline works.

## What this does not show

- **A generated corpus from one model.** 300 articles written by `gpt-6-astra` to one prompt are more uniform than real documents, and every article mentions its product by name.
- **One embedding model.** Other models may tell identifiers apart better, or worse.
- **BM25 with default settings and one tokenisation.** A tokeniser that kept `E-2194` whole would behave differently again.
- **One fusion method with one k,** fusing full rankings. Weighted fusion, or fusing only matched passages, was not tested.
- **No reranking.** A reranker reading question and passage together (S2 E7) may fix much of this.
- **Retrieval only.** No answer is generated.
- **Paraphrase questions were checked word for word.** A question can share a word stem with its article ("dishwashing", "dishwasher") and still count as a paraphrase.
- **Small samples.** 40 questions per type gives wide intervals.

## Charts

Drawn by `chart.py` from `results/search.json` alone, at slide and article sizes, in `charts/`.

- **`recall-by-question-type`**: recall at 5 as grouped bars for identifier, paraphrase and shared-word questions and for all 120 together, one bar per method, with 95% intervals. The acid green bar is the method with the highest recall across all questions; if two methods tie there, nothing is highlighted and the chart says so. In this run it is vector search, at 95/120.
- **`lookalikes`**: for the 40 identifier questions, the share where a look-alike ranked above the right article, one bar per method. The acid green bar is the method with the most look-alike errors, and only if its 95% interval does not overlap any other method's; otherwise nothing is highlighted and the chart says so. In this run it is vector search, at 18/40.

Any zero bar is drawn with its count and a stub on the baseline.

## Tokens

As reported by the API. Generation, all 381 `gpt-6-astra` calls behind the committed corpus and questions, pilot included: 67,033 input and 84,405 output tokens, of which 36,507 were reasoning. Embedding, for the full run: 41,703 tokens, plus 4,704 in the pilot.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**Rebuild the charts from the committed results.** No key, model or network:

```bash
uv run python episodes/s2-e3-search/chart.py
```

**Rerun the search against the committed corpus.** Needs `OPENAI_API_KEY` in the repository's `.env` file or your environment, for the embeddings only. Embeddings are cached in `.cache/embeddings/`.

```bash
uv run python episodes/s2-e3-search/search.py
```

To read questions beside their articles, add `--sample`.

**Regenerate the corpus (optional).** This is a third route, and it will not reproduce the committed articles: the model does not write the same text twice. Identifiers, briefs and question assignments are fixed by the seed, so the structure is the same.

```bash
uv run python episodes/s2-e3-search/generate.py
```

## Files

- `search.py`: the slide's fusion function, then the experiment. Writes `results/search.json`, or `results/pilot.json` with `--pilot`.
- `generate.py`: writes `corpus.json` and `questions.json`, checking every article and question in code.
- `plan.py`: identifiers, look-alikes, briefs and the word checks, all fixed by the seed.
- `measure.py`: recall, mean reciprocal rank, look-alike errors, and the claim tests.
- `chart.py`, `charts/`: the charts.
- `config.yaml`: the seed, every prompt, the stop words, and every setting.
- `pilot/`: the pilot's 30 articles and 12 questions, a subset of the full run.
- `results/search.json`: for every question and method, the rank of the right article (or none within 20), and for identifier questions every look-alike's rank; also the models, tokeniser, BM25 version, run date, seed, and the tokens reported, split into generation and embedding. No vectors.
