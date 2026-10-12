# S2 E2: Your first RAG system

The code behind S2 E2, Your first RAG system. This episode builds a complete
retrieval-augmented generation (RAG) system with the simplest choice at every stage, runs it on
the season's full test set, and records where it is right and where and why it is wrong. Nothing
is tuned. Its four numbers are the first row of the Season 2 scoreboard, and every later episode
changes one stage and is measured against them.

The claims and their pass marks were fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) before
any search, answer or judge call, and were not changed after the run.

## The question

What does a whole RAG pipeline look like, and how well does the simplest version of it work?

## The system

The season's pipeline has eleven stages. E2 uses the reference configuration in
[`season2/reference.yaml`](../../season2/reference.yaml) unchanged:

| # | Stage | In E2 |
|---|---|---|
| 1 | Load documents | All 344 document versions in the library, whatever their access or status |
| 2 | Chunk | Fixed windows of 256 tokens (`cl100k_base`), no overlap: 1,276 chunks |
| 3 | Embed and index | `text-embedding-3-small`, cosine similarity |
| 4 | Rewrite the question | Off: the question is searched as asked |
| 5 | Search | Vector search, 50 deep |
| 6 | Filter | Off: no permission or version filter |
| 7 | Rerank | Off: the search order is kept |
| 8 | Build the prompt | The top 5 chunks, in rank order, numbered `[P1]` to `[P5]` |
| 9 | Answer | `gpt-6.1-sol` at reasoning `low`, 2,000 output tokens at most |
| 10 | Cite | Off |
| 11 | Score | Evidence labels for search; `claude-sonnet-5-5` as judge for the answer |

The answer model's only instruction is "Answer the question using the passages below." It is
deliberately plain: E9 tests a better prompt. Reasoning `low` is `gpt-6.1-sol`'s lowest setting;
it has no off. No temperature is sent, because both models reject one (S1 E8).

The judge is from a different provider from the answer model, so the system is not grading
itself. It sees the question, whether the library can answer it, the reference answer, the
passages the system was given and the system's answer. It never sees the evidence labels. It
returns three verdicts: whether the answer declined, whether it is correct, and whether every
claim in it is supported by the passages (faithful). The judge has not yet been checked against
hand marks; that is E3. Until then, every answer-level number here is provisional.

## The library and the test set

`halvard-v2`, frozen on 12 October 2026 in [`datasets/halvard`](../../datasets/halvard). Halvard
Home is an invented maker of home appliances. The library holds:

- **300 support articles**, short, one fact each, from v1 S2 E3.
- **4 long policy documents** (warranty, returns, safety, servicing), about 27,500 tokens each.
- **4 superseded versions** of those policies, with some terms changed.
- **4 internal documents** for staff only.
- **32 withdrawn notices**, marked deleted.

The test set has 520 questions of 16 types. Each answerable question is labelled with the exact
character span that answers it, so a search hit can be checked by code. Each question also
records the asker's access level and whether the library can answer it at all.

| Type | Items | Asker | Answerable | What it tests |
|---|---|---|---|---|
| Identifier | 40 | public | yes | An error code or part number, with look-alike codes in other articles |
| Paraphrase | 40 | public | yes | No content word shared with the answer |
| Shared words | 40 | public | yes | The control: reuses the answer's own words |
| Policy, one sentence | 40 | public | yes | A fact in one sentence of a long policy |
| Policy, two sentences | 20 | public | yes | A fact split across two sentences |
| Policy, needs heading | 20 | public | yes | A fact that only makes sense under its section heading |
| Look-alike | 40 | public | yes | Passages that look like the answer but are not |
| Two-part | 20 | public | yes | Two questions in one, answered in two documents |
| Bridge | 20 | public | yes | One passage names the thing, a second gives its value |
| Follow-up | 40 | public | yes | "And for the dryer?", after an earlier turn |
| Version | 40 | public | yes | The current and superseded policies give different values |
| Staff asker | 40 | staff | yes | The answer is in an internal document |
| Restricted, public asker | 40 | public | no | The same questions, from a customer who must not be told |
| Absent detail | 40 | public | no | The topic is covered, the detail asked for is not |
| Absent topic | 20 | public | no | A product or subject the library does not cover |
| Withdrawn | 20 | public | no | The only answer was in a withdrawn notice |

## How it is scored

- **Hit:** a chunk in the top 5 holds the whole evidence span. A question with two spans needs
  both.
- **Search:** recall at 5, the share of the 400 answerable questions with a hit.
- **Answer:** the share of the 400 answerable questions judged correct and faithful.
- **Not found:** the share of the 120 unanswerable questions the judge marks as a decline.
- **Leaks:** the share of the 480 public-asker questions whose prompt held a staff-only passage.
- **Where an answer was lost:** for every wrong answerable question, the first stage at which
  the right passage was lost (`first_lost_stage` in `src/lab/rag/score.py`).
- **Intervals:** Wilson 95%. "Below" means the two intervals do not overlap.

## Results

Run on 12 October 2026, on all 520 test items.

### The four season numbers

| Number | Result | 95% interval |
|---|---|---|
| Search: right passage in the top 5 | 239 of 400, 59.8% | 55% to 64% |
| Answer: correct and faithful | 217 of 400, 54.3% | 49% to 59% |
| Not found: unanswerable questions declined | 56 of 120, 46.7% | 38% to 56% |
| Leaks: a staff passage reached a public asker's prompt | 51 of 480, 10.6% | 8% to 14% |

This is the first row of [`season2/scoreboard.json`](../../season2/scoreboard.json).

### By question type

| Type | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| Shared words | 40/40 (91% to 100%) | 39/40 (87% to 100%) | | 0/40 |
| Paraphrase | 38/40 (83% to 99%) | 36/40 (77% to 96%) | | 2/40 |
| Identifier | 15/40 (24% to 53%) | 15/40 (24% to 53%) | | 1/40 |
| Policy, one sentence | 24/40 (45% to 74%) | 28/40 (55% to 82%) | | 3/40 |
| Policy, two sentences | 13/20 (43% to 82%) | 16/20 (58% to 92%) | | 0/20 |
| Policy, needs heading | 9/20 (26% to 66%) | 10/20 (30% to 70%) | | 0/20 |
| Look-alike | 32/40 (65% to 90%) | 32/40 (65% to 90%) | | 4/40 |
| Two-part | 1/20 (1% to 24%) | 1/20 (1% to 24%) | | 0/20 |
| Bridge | 0/20 (0% to 16%) | 2/20 (3% to 30%) | | 0/20 |
| Follow-up | 3/40 (3% to 20%) | 3/40 (3% to 20%) | | 3/40 |
| Version | 33/40 (68% to 91%) | **5/40 (5% to 26%)** | | 2/40 |
| Staff asker | 31/40 (62% to 88%) | 30/40 (60% to 86%) | | |
| Restricted, public asker | | | 9/40 (12% to 38%) | **34/40 (71% to 93%)** |
| Absent detail | | | 27/40 (52% to 80%) | 2/40 |
| Absent topic | | | 20/20 (84% to 100%) | 0/20 |
| Withdrawn | | | **0/20 (0% to 16%)** | 0/20 |

### Where the wrong answers were lost

182 answerable questions were answered wrongly and judged. The first stage that lost the right
passage:

| First lost at | Wrong answers | Share |
|---|---|---|
| Chunk: no chunk holds the evidence whole | 11 | 6% |
| Search: not in the top 50 | 44 | 24% |
| Rank: found, but ranked below 5th | 92 | 51% |
| Prompt: in the prompt, but the model declined | 1 | 1% |
| Answer: in the prompt, but the answer was wrong | 34 | 19% |

The baseline has no reranker, so "ranked below 5th" is the stage the season calls rerank: the
passage was found, and a better ordering would have put it in the prompt. One more answer
(PARA-033) could not be judged: the judge's reply was not a valid verdict even after one retry.
It counts as wrong in the answer number and is left out of this table.

## The claims

Four held and two failed.

**H1 held: search loses more answers than the model does.** Of the 182 wrong answers, 147 lost
the right passage before the prompt (chunk 11, search 44, rank 92) and 35 inside it (prompt 1,
answer 34). Ranking alone accounts for half of all wrong answers. That points to E3, which
scores search and answer separately, and to E5 and E7, which change search and ranking.

**H2 failed: fixed chunks did not visibly hurt facts split across two sentences.** The claim
needed recall for both two-sentence and heading-dependent facts to be lower than for
one-sentence facts. Heading-dependent facts were lower, 9 of 20 (26% to 66%) against 24 of 40
(45% to 74%). Two-sentence facts were higher, 13 of 20 (43% to 82%). All three intervals
overlap widely, so the run cannot separate the three types at these sizes. Chunk edges did cut
the evidence on 18 items, but only 3 of those were two-sentence facts. E4 tests chunking
directly.

**H3 held: identifier questions fail under vector search.** 15 of 40 identifier questions
found their passage (24% to 53%), against 38 of 40 paraphrase questions (83% to 99%). This
repeats the v1 S2 E3 result, 15 of 40 then too, on an index of 1,276 chunks instead of 300
articles. 20 of the 25 misses were found but ranked below 5th. E5 adds keyword search.

**H4 held: a follow-up searched on its own fails.** 3 of 40 follow-ups found their passage (3%
to 20%), against 24 of 40 one-sentence policy questions (45% to 74%). "And for the Tessa
dishwasher?" names the product but not what is being asked, so search has nothing to match the
fact with. E6 rewrites the question.

**H5 failed, on its second part.**

- *H5a held: leaks happen.* A staff-only passage reached the prompt on 34 of the 40 restricted
  questions from public askers, and on 17 questions of other types.
- *H5b failed: no answer gave the old value alone.* The superseded passage reached the prompt on
  32 of the 40 version questions, which passes the first half. But the second half needed at
  least one answer to give the old value without the current one, and none did. The model
  reported the conflict instead (see "Superseded versions" below). The claim was right that the
  old versions get in, and wrong about what the model does with them.

**H6 held: the model declines when nothing is there, but not when the wrong thing is.** It
declined 47 of 60 questions the library cannot answer at all, 78% (66% to 87%), above the 75%
pass mark. It declined only 9 of 60 restricted and withdrawn questions, 15% (8% to 26%), where
the prompt usually held a passage it should not have used. E8 and E9 test filters and the prompt.

## What else the run showed

None of these was a pre-registered claim. They are reported because the run showed them, and
they matter for the episodes that follow.

### Superseded versions crowd the prompt

The superseded policies are near copies of the current ones, so they make up 438 of the 1,276
chunks (34%). With no version filter, a policy question tends to retrieve the same passage
twice, once from each version. 392 of the 520 prompts held the same passage in two versions,
and 888 of the 2,600 prompt slots (34%) went to superseded chunks. Five slots then carry fewer
than five distinct passages, which is part of why ranking below 5th is the largest loss.

The duplicates work both ways. On 13 questions the labelled evidence (in the current version)
was not in the prompt, but the superseded copy was, holding the same unchanged fact, and the
answer was right. The worked example of a right answer below is one of them.

### The model reports a conflict rather than choosing

On the 40 version questions, search found the current passage 33 times, but only 5 answers were
judged correct. In 27 cases the right passage was in the prompt and the answer was still judged
wrong: the model saw the old and new values side by side, said the passages conflict, and either
gave both, deferred to support, or recommended the more cautious value. For example, asked how
long the Tessa dishwasher should cool before cleaning (7 minutes now, 11 before), it answered:
"The passages give conflicting cooling times: 11 minutes in P1 and 7 minutes in P2. To be
cautious, wait at least 11 minutes." The judge marked this not correct and faithful. No answer
stated the old value alone, which is why H5b failed. The model is not misled by the old version;
it is left unable to answer.

### Leaked passages are used

Of the 34 public-asker prompts that held a staff passage, 31 answers used it: the customer was
told internal information. For example, asked how much an engineer can spend on parts for the
Mira robot vacuum without approval, the system answered with the internal limit. The 3 others
declined, and so did all 6 questions whose prompts held no staff passage.

### Withdrawn notices are answered from

All 20 questions about withdrawn products had the withdrawn notice in the prompt, and the model
answered all 20 from it, declining none. A deleted document that stays in the index is still
an answer to the model.

### The code check and the judge disagree on 32 items

Every item with a key value (such as "58 months") is also checked by code: does the answer
contain the value as a whole token? The code check and the judge disagree on 32 items, and 28
of those are version questions. The answer contains the current value, so the code check passes
it, but the answer also gives the old value as a possible answer, so the judge fails it. The
other 4 are 3 look-alike questions and 1 staff question. These are listed in
`results/analysis.json` for reading by hand. E3 checks the judge properly against 50
hand-marked verdicts.

## Worked examples

Chosen by the rules fixed before the run: in each case, the first test item in id order that
meets the rule.

**Right: POL-SINGLE-001.** "How much longer does Extended Care keep my warranty going?" The
reference answer is 58 months. The answer: "Extended Care extends your standard warranty by
58 months. [P5]" The judge noted that it gave the right figure and not the 50 months of
Extended Care Plus. One caveat: the labelled passage in the current
warranty ranked 6th. The answer came from the same sentence in the superseded warranty, ranked
5th, where the term had not changed.

**Wrong because search missed: POL-SINGLE-000.** "How soon will Halvard Home pick up my
recalled appliance after I reply?" The reference answer is 18 working days. The right passage
ranked 16th. The prompt held the collection times for other regions, so the model gave those:
53 working days in London and the South East and 21 in the Midlands, then asked which region
the customer was in. Every claim in it was supported by the passages, so it was faithful, but
it was not correct.

**Wrong because the model misread: DISTRACT-018.** "How long is the warranty on the Brio
kettle?" The reference answer is 47 months from delivery. The right passage was in the prompt,
ranked 3rd, beside a general warranty page saying two years. The model answered "The passages
conflict: the detailed warranty states 47 months from delivery, while the warranty-period page
says two years from purchase", and told the customer to contact Halvard Home. It found the right
figure and did not commit to it.

## What this does not show

- **One library.** Invented, and written by one model, `gpt-6-astra`. Real documents are less
  uniform.
- **One answer model and one unchecked judge.** The answer, not-found and judge-based numbers
  are provisional until E3 measures how often the judge agrees with hand marks.
- **A deliberately plain instruction.** The model was not told to decline when the passages do
  not answer, to prefer the newest version, or to cite. E9 and E10 test that.
- **The size of the duplicate effect depends on this library.** Four superseded policies are a
  third of the chunks here. A library with fewer old versions would crowd less.
- **No baseline on the dev set.** Episodes that tune a setting tune it on dev and report on
  test.
- **The by-type intervals are wide.** 20 or 40 questions per type separate large differences
  only, which is why H2 could not be decided.

## Charts

Drawn by `analyse.py` from the committed results alone, at slide and article sizes, in
`results/charts/`. E2 measures and does not compare, so no chart highlights anything, and each
says so in its footer.

- **`recall-by-type`**: recall at 5 for each answerable question type, with 95% intervals and a
  count beside every bar, so a zero (Bridge, 0 of 20) still shows.
- **`where-lost`**: the 182 wrong answerable questions by the first stage that lost the right
  passage, as shares, with counts.
- **`scoreboard`**: the eleven-stage strip, with no stage highlighted because E2 changes none,
  and the four season numbers.

## Tokens, time and cost

As reported by the APIs, for the 520 items of the full run:

| | Calls | Input tokens | Output tokens | Median per call | Median time |
|---|---|---|---|---|---|
| Answer, `gpt-6.1-sol` | 520 | 616,376 | 33,874 | 1,255 in, 47 out | 2.6 s (90th percentile 7.2 s) |
| Judge, `claude-sonnet-5-5` | 524 | 1,262,938 | 53,014 | 2,530 in, 92 out | 1.7 s |

The judge row includes 4 retries for replies that were not a valid verdict. Reasoning at `low`
used 887 reasoning tokens across all 520 answers, so it is close to off.

At list prices on 12 October 2026 ($2 per million input tokens and $10 per million output
tokens for both models), the full run cost about $4.63: $1.57 for answers and $3.06 for judging,
or about 0.9 cents a question, of which 0.3 cents is the answer. The judge reads more than the
answer model, because it also reads the reference answer and the system's reply. Embedding the
library and the questions cost under 1 cent.

The models returned `gpt-6.1-sol` and `claude-sonnet-5-5` on every call.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**Rebuild the analysis and charts from the committed results.** No key, model or network:

```bash
uv run lab rag analyse episodes/s2-e2-first-rag-system/config.yaml
```

**Count the calls and tokens before spending anything.** No key needed:

```bash
uv run lab rag estimate episodes/s2-e2-first-rag-system/config.yaml
```

**Rerun against the current models.** Needs `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in the
repository's `.env` file or your environment. Responses are cached in `.cache/`, so a rerun
with a warm cache costs nothing; add `--pilot` for 2 items per type first. To see costs in the
estimate, copy `prices.example.yaml` to `prices.local.yaml` and fill in current prices; a
`budget` there for `s2-e2-first-rag-system` makes the run refuse to start above it.

```bash
uv run lab rag run episodes/s2-e2-first-rag-system/config.yaml
```

## Files

- `PREREGISTRATION.md`: the question, setup, claims and pass marks, fixed before the run.
- `config.yaml`: the episode config. It changes no stage of `season2/reference.yaml`, and holds
  the pass marks.
- `claims.py`: applies the pass marks to the run log.
- `analyse.py`: the claims, worked examples, charts and the scoreboard row.
- `results/baseline/log.jsonl`: one line per item, with the queries, the ranking, the prompt's
  chunks, where each evidence span ranked, any leaks, the answer and the verdict.
- `results/baseline/raw-*.jsonl`: every answer and judge call as the API returned it.
- `results/baseline/summary.json`: the configuration, the numbers by type, and the call counts.
- `results/analysis.json`: the claims, where answers were lost, the worked examples and the
  items where the code check and the judge disagree.
- `results/pilot/`: the 32-item pilot run before the full run, kept for the record.

The slide's code listing is `build_prompt` in `src/lab/rag/prompt.py`, below the marker
`# slide: S2 E2`. A test checks that it fits a slide.
