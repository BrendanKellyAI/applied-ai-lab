# S1 E3: Embeddings

The code behind the similarity scores shown in [S1 E3, Embeddings](https://brendankellyai.github.io/episodes/s1-e3-embeddings/). The part of `similarity.py` below the marker comment matches the slide line for line.

## What it shows

An embedding model turns a piece of text into a list of numbers, a **vector**, placed so that texts with similar meaning sit close together. How close two texts are is measured with **cosine similarity**: near 1 for texts pointing the same way, near 0 for texts with nothing in common. Search built on embeddings compares meanings rather than matching words.

The episode makes three claims, and this code tests each one:

1. Texts with similar meaning score as close even when they share no words.
2. Close means similar, not correct: a sentence and its negation can score as near neighbours.
3. Numbers are handled poorly: "rose 5%" and "fell 5%" can score as near neighbours.

Run on 19 September 2026 with `text-embedding-3-small`, OpenAI's current small embedding model, which returned vectors of 1,536 numbers.

### Search: "How do I get my money back?"

The query and seven stored phrases, embedded in one call and ranked by how close each phrase is to the query:

| Rank | Stored phrase | Shares a word with the query? | Cosine similarity |
|---|---|---|---|
| 1 | money back | Yes, two | 0.595 |
| 2 | refund policy | No | 0.390 |
| 3 | locked account | No | 0.292 |
| 4 | can't log in | No | 0.237 |
| 5 | return an item | No | 0.223 |
| 6 | reset password | No | 0.206 |
| 7 | Dublin weather | No | 0.047 |

### Pairs: similar is not the same as true

Each pair scored on its own. The paraphrase and the unrelated sentence are yardsticks: scores from this model sit in a compressed range, so a number only means something beside them.

| Pair | First | Second | Cosine similarity |
|---|---|---|---|
| Negation | The drug is safe. | The drug is not safe. | 0.807 |
| Direction | Shares rose 5% today. | Shares fell 5% today. | 0.858 |
| Paraphrase | The drug is safe. | The medicine carries no risk. | 0.592 |
| Unrelated | The drug is safe. | The train leaves at noon. | 0.104 |

## What the results say about each claim

**Claim 1 held for "refund policy", but not for every phrase.** "refund policy" shares no words with "How do I get my money back?" and still came second, well above every account phrase and far above "Dublin weather". That is meaning, not word matching. The top result, "money back", does share two words with the query, so it proves less. And "return an item", which shares no words and is closely related in meaning, came fifth, below "locked account" and "can't log in". Embeddings capture meaning, but not always the way a person would rank it.

**Claim 2 held, strongly.** "The drug is not safe." scored 0.807 against "The drug is safe.", higher than a sentence that means the same thing, "The medicine carries no risk.", at 0.592. The model placed the opposite claim nearer than the paraphrase. Two sentences can be close in embedding space and say opposite things.

**Claim 3 held, but it is really about direction, which is why the pair is labelled "Direction".** "Shares rose 5% today." and "Shares fell 5% today." scored 0.858, the highest of all four pairs and well above the paraphrase. But both sentences contain the same number; what differs is the direction, rose against fell. So this shows that opposite movements land as near neighbours. It does not test whether different numbers, such as 5% against 50%, are told apart; that was not run here.

The practical lesson for anyone building search on embeddings: a close match is a candidate, not an answer. Check negation, direction, and figures another way before trusting them.

## Run it

You need Python 3.12 or later, [uv](https://docs.astral.sh/uv/), and an OpenAI API key.

1. From the repository root, install dependencies:

   ```bash
   uv sync
   ```

2. Add your API key to `.env` in the repository root, the same file the rest of the lab uses:

   ```bash
   OPENAI_API_KEY=your-key-here
   ```

   If `.env` does not exist yet, copy `.env.example` to `.env` first. The script loads the key in its first few lines, above the code shown on the slides.

3. Run the script:

   ```bash
   uv run python episodes/s1-e3-embeddings/similarity.py
   ```

It prints the search results, then the four pairs, and writes every text, vector, and score, the model name the API returned, the vector length, and the date to `results/embeddings.json`. Running it again replaces that file.

## Redraw the charts, no key needed

```bash
uv run python episodes/s1-e3-embeddings/chart.py
```

The charts read only `results/embeddings.json`, which is committed, so anyone can redraw them without a key.

- `charts/similarity-to-query`: one bar per stored phrase, highest first. The acid green bar is the phrase that scores highest.
- `charts/pairs`: the four pairs in the order above. The acid green bar is whichever of the negation and direction pairs scores higher, and only if it beats the paraphrase; otherwise nothing is highlighted and the chart says so. In this run, the direction pair is highlighted.

## Reading the scores

- **Scores are not comparable across embedding models.** Each model spreads its scores over a different range, so 0.6 from one model and 0.6 from another mean different things. Compare scores from the same model, and against yardsticks like the paraphrase and the unrelated pair.
- **Scores can shift slightly between runs and model updates.** Your numbers may differ in the second or third decimal place. The ranking and the comparisons above are what to check.

## Cost

Two small calls embedding fourteen short texts. The exact cost depends on current OpenAI pricing; it is a tiny fraction of a single chat call. The script makes new calls every time it runs.
