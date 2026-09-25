# S2 E2: Chunking

The code behind the chunking results in S2 E2, Chunking. The function in `chunking.py` below the marker comment matches the slide line for line, and the experiment calls that exact function.

## The question

Search over documents does not search whole documents. It cuts them into **chunks**, embeds each chunk as one vector, and returns the chunks closest to the question. So the cut decides what can be found. S1 E3 claimed in public that chunking too long averages many ideas into one vector. This episode measures that, and two claims that follow from it:

1. **Long chunks dilute a fact.** As chunks grow, the similarity between a question and the chunk holding its answer falls, and recall falls with it.
2. **Short chunks split an answer.** When an answer needs two adjacent sentences, small chunks with no overlap separate them, and overlap recovers some of that loss.
3. **No single size wins both.** The best size for one-sentence facts is not the best for two-sentence facts.

## The design

- **Corpus.** The six public-domain novels from S1 E7, fetched and checked by that field note's own code. From each, one contiguous excerpt of about 40,000 tokens. The text is gitignored and rebuilt on demand, exactly as in S1 E7; see `datasets/README.md`.
- **Tokens** are counted with `cl100k_base`, the tokeniser of `text-embedding-3-small`. S1 E2 used `o200k_base`, which splits text differently, so token counts here are not comparable with S1 E2's.
- **Facts.** 90 invented facts about places that do not exist, generated from the seed in `config.yaml` and committed in `facts.json`: 60 one-sentence facts, 10 per novel, and 30 two-sentence facts, 5 per novel. In a two-sentence fact the first sentence names the subject and the second holds the answer, and cannot be understood alone ("She stored it in a blue tin under the stairs."). Every question names its place, so each has one right answer in the corpus. Facts sit at sentence boundaries, spread evenly through each novel, at least 2,500 tokens apart (the closest pair is 2,626).
- **Conditions.** Chunk sizes of 64, 128, 256, 512, 1,024 and 2,048 tokens, each with 0% and 25% overlap. Fixed token windows over each novel separately, with no attention to sentences.
- **Retrieval.** Every chunk and every question embedded with `text-embedding-3-small`. For each question, all chunks from all six novels are ranked by cosine similarity.
- **A hit.** A one-sentence fact is found if a retrieved chunk contains the whole sentence. A two-sentence fact is found only if a single retrieved chunk contains both sentences.
- **Yardsticks.** Similarity only means something between two yardsticks (S1 E3). The **ceiling** is the similarity of each question to its fact embedded on its own: the closest the answer can be. The **floor** is the median similarity of each question to 20 random chunks of the same size that do not hold its answer.

The measures and the pass mark for each claim were fixed before the run, in `measure.py`, and were not changed after it.

**One change from the brief.** The brief asked for 30,000-token excerpts. Fifteen facts spaced 2,500 tokens apart need at least 35,000, so the excerpts are 40,000 tokens instead. The fact counts and the spacing rule are as briefed. This was decided after the pilot and before the full run.

## Results

Run on 25 September 2026 with `text-embedding-3-small`. All intervals are Wilson 95% intervals.

### Recall at 5, one-sentence facts, 0% overlap (the headline)

| Chunk size | Recall at 5 | 95% interval | Recall at 1 | Facts cut by a chunk boundary |
|---|---|---|---|---|
| 64 | 33/60, 55% | 42% to 67% | 13/60 | 25 |
| 128 | **43/60, 72%** | 59% to 81% | 19/60 | 3 |
| 256 | 31/60, 52% | 39% to 64% | 12/60 | 2 |
| 512 | 13/60, 22% | 13% to 34% | 5/60 | 1 |
| 1,024 | 10/60, 17% | 9% to 28% | 5/60 | 1 |
| 2,048 | 11/60, 18% | 11% to 30% | 2/60 | 0 |

"Facts cut by a chunk boundary" counts facts that no chunk holds whole, because a window edge fell inside the sentence. Those are misses by definition.

### Similarity to the answer chunk, one-sentence facts, 0% overlap

| Chunk size | Median similarity | Ceiling | Floor |
|---|---|---|---|
| 64 | 0.513 | 0.843 | 0.109 |
| 128 | 0.406 | 0.843 | 0.113 |
| 256 | 0.306 | 0.843 | 0.119 |
| 512 | 0.240 | 0.843 | 0.127 |
| 1,024 | 0.177 | 0.843 | 0.128 |
| 2,048 | 0.157 | 0.843 | 0.129 |

Medians are over the facts that some chunk holds whole.

### Two-sentence facts, recall at 5

| Chunk size | 0% overlap | 95% interval | 25% overlap | 95% interval | Split, 0% | Split, 25% |
|---|---|---|---|---|---|---|
| 64 | 20/30, 67% | 49% to 81% | 26/30, 87% | 70% to 95% | 10 | 2 |
| 128 | 24/30, 80% | 63% to 90% | 24/30, 80% | 63% to 90% | 1 | 0 |
| 256 | 18/30, 60% | 42% to 75% | 16/30, 53% | 36% to 70% | 1 | 0 |
| 512 | 9/30, 30% | 17% to 48% | 8/30, 27% | 14% to 44% | 1 | 0 |
| 1,024 | 6/30, 20% | 10% to 37% | 9/30, 30% | 17% to 48% | 1 | 0 |
| 2,048 | 3/30, 10% | 3% to 26% | 4/30, 13% | 5% to 30% | 1 | 0 |

"Split" counts two-sentence facts whose sentences landed in no single chunk, which is the mechanism claim 2 is about. Ceiling and floor for two-sentence facts at 0% overlap: ceiling 0.849 throughout; floor from 0.170 at 64 tokens to 0.223 at 2,048.

### Secondary results

One-sentence facts with 25% overlap, recall at 5: 50/60 at 64 tokens (72% to 91%), 37/60 at 128, 28/60 at 256, 17/60 at 512, 12/60 at 1,024, 5/60 at 2,048.

Per novel, one-sentence facts, recall at 5 out of 10, 0% overlap:

| Chunk size | Pride and Prejudice | Moby Dick | Great Expectations | A Tale of Two Cities | Dracula | Frankenstein |
|---|---|---|---|---|---|---|
| 64 | 7 | 8 | 7 | 4 | 2 | 5 |
| 128 | 5 | 8 | 6 | 6 | 10 | 8 |
| 256 | 1 | 5 | 7 | 4 | 8 | 6 |
| 512 | 0 | 2 | 3 | 1 | 6 | 1 |
| 1,024 | 0 | 1 | 2 | 0 | 5 | 2 |
| 2,048 | 0 | 2 | 1 | 1 | 5 | 2 |

## What the results say about each claim

**Claim 1 held, on both parts.** The median similarity between a question and the chunk holding its answer fell at every step, from 0.513 at 64 tokens to 0.157 at 2,048, against a ceiling of 0.843 and a floor that rose from 0.109 to 0.129. At 2,048 tokens the answer chunk is only a little closer to the question than a random chunk is. Recall at 5 fell from its best, 43/60 (59% to 81%) at 128 tokens, to 11/60 (11% to 30%) at 2,048, and those intervals do not overlap. A fact in a long chunk is averaged away.

**Claim 2 did not hold as defined.** It needed overlap to beat no overlap at both 64 and 128 tokens. At 64 tokens it did: 26/30 (70% to 95%) against 20/30 (49% to 81%), with the number of split facts falling from 10 to 2. At 128 tokens it made no difference, 24/30 either way, because at that size only one two-sentence fact was split to begin with, so there was almost nothing for overlap to recover. The mechanism is real, but it only bites at the smallest size tested.

**Claim 3 did not hold.** 128 tokens was the best size for both one-sentence facts (43/60) and two-sentence facts (24/30). Short enough to keep a fact sharp, long enough that few facts are cut in half: here one size did win both.

A further finding the claims did not anticipate: at 64 tokens with no overlap, **25 of the 60 one-sentence facts were cut in half by a chunk boundary**. That is why 64 tokens loses to 128, not dilution. With 25% overlap, no one-sentence fact was cut and recall at 64 tokens rose to 50/60, the best figure in the whole run.

## What this does not show

- **One embedding model.** Other models, and larger ones, may dilute more or less.
- **Invented facts in novels.** A sentence about a Carrigmore lighthouse stands out from nineteenth-century prose far more than a clause in a real policy document stands out from the clauses around it, and every question repeats its fact's place name. Real retrieval is likely harder than this at every size.
- **Fixed windows only.** No sentence-aware or semantic chunking, which would avoid cutting facts in half. That comparison is for a later episode.
- **Retrieval only.** No answer is generated, so this says nothing about whether a model would use a retrieved chunk correctly.
- **Small samples.** 60 and 30 facts give wide intervals; several differences in the tables are within noise.

## Charts

Drawn by `chart.py` from `results/chunking.json` alone, at slide and article sizes, in `charts/`.

- **`recall-by-size`**: recall at 5 for one-sentence facts, 0% overlap, with 95% intervals. The acid green bar is the size with the highest recall; if two or more sizes tie at the top, nothing is highlighted and the chart says so. In this run it is 128 tokens.
- **`similarity-by-size`**: median similarity to the answer chunk by size, with the ceiling as a horizontal line and the floor. The floor is measured at each size, so it is drawn at each size as a dotted line rather than a single horizontal one; it barely moves. Nothing is highlighted, and the chart says so.
- **`two-sentence-overlap`**: recall at 5 for two-sentence facts, 0% against 25% overlap. The acid green bar is the 25% bar at the size where overlap adds the most recall, and only if its 95% interval does not overlap the 0% bar beside it. In this run the largest gain, at 64 tokens, has overlapping intervals, so nothing is highlighted and the chart says so.

Any zero bar is drawn with its count and a stub on the baseline.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**Rebuild the charts from the committed results.** No key, model or network:

```bash
uv run python episodes/s2-e2-chunking/chart.py
```

**Rerun against the current model.** You need an OpenAI API key in the repository's `.env` file or your environment as `OPENAI_API_KEY`. The first run downloads the six novels from a Project Gutenberg mirror and caches them. Embeddings are cached in `.cache/embeddings/`, so a rerun pays only for text it has not embedded before. The pilot, one novel at two sizes, used 80,821 embedding tokens as reported by the API. The full run then used 2,805,355 more, recorded in the results file. That is less than the 3.4 million tokens its chunks add up to, because many chunks repeat exactly across conditions (a 64-token window with overlap often starts where one without overlap does) and the cache embeds each distinct text once.

```bash
uv run python episodes/s2-e2-chunking/chunking.py --pilot
uv run python episodes/s2-e2-chunking/chunking.py
```

`facts.json` is regenerated from the seed with `uv run python episodes/s2-e2-chunking/facts.py`; the tests check that the committed file matches.

## Files

- `chunking.py`: the slide's chunker, then the experiment. Writes `results/chunking.json`, or `results/pilot.json` with `--pilot`.
- `facts.py`, `facts.json`: the invented facts and questions.
- `corpus.py`: the excerpts, with facts inserted.
- `measure.py`: hit rules, ranks, yardsticks, and the claim tests.
- `store.py`: the embedding cache.
- `chart.py`, `charts/`: the charts.
- `results/chunking.json`: per condition, the number of chunks and, for every question, the rank of the first hit, the similarity to its answer chunk, the ceiling and the floor; also the model, tokeniser, run date, seed, and the embedding tokens the API reported. No vectors and no novel text.
