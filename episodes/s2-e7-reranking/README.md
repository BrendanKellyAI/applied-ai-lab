# S2 E7: Reranking

When the right passage is retrieved but ranked too low, does a second pass fix it? E7 changes only
stage 7. Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: a cheap LLM reranker, reading the top 20 search results once per question, joins the
reference system.** Search rose from 281 to 316 of 400 and right answers from 280 to 316.

## The reranker, and why it is an LLM

The handoff named a local cross-encoder, `BAAI/bge-reranker-v2-m3`. It works, but on this
machine's CPU it took about 5.5 seconds per question-passage pair with the season's ~840-token
section chunks: around 16 hours for 20 passages per question on 520 questions. The owner had
approved a cheap LLM if the local model failed for any reason, so:

- **The main reranker** is `gpt-6-luna`, reasoning off. It reads the question and the numbered
  shortlist once and returns the passage numbers, best first (`prompts/rerank_llm.md`). Any
  passage it does not name keeps its search order after those it does.
- **The cross-encoder** ran on the 40 distractor items only, shortlist 10, for comparison and
  timing (`cross_encoder_subset.py`, results in `results/cross-encoder-10/`).

## The design

- **Library and items:** `halvard-v2`, 520 test items; 100 dev items to choose the shortlist.
- **Reference:** the system after E6 (`season2/history/s2-e7-reranking.yaml`).
- **Conditions:** `baseline` (search order); `llm-10` and `llm-20` (the top 10 or 20 reordered).
  Search-only on test and dev; the dev choice, `llm-20` (56 of 70 against 52), ran in full.

## Results

| Reranking | Search (400) | Identifier (40) | Two-part (20) | Bridge (20) | Version (40) |
|---|---|---|---|---|---|
| **Search order (reference)** | 281 (66% to 75%) | 15 | 0 | 0 | 36 |
| LLM, top 10 | 298 (70% to 79%) | 20 | 3 | 1 | 39 |
| **LLM, top 20** | **316 (75% to 83%)** | 26 | 8 | 5 | 40 |

| Full runs | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| Search order, reference | 281 of 400 | 280 of 400 (65% to 74%) | 42 of 120 | 76 of 480 |
| **LLM, top 20** | **316** | **316 (75% to 83%)** | 41 | 64 |

Paired on the same items: the reranker found 38 passages the search order missed and lost 3
(exact McNemar p < 0.0001); right answers, 45 gained and 11 lost (p < 0.0001). Wrong answers
lost because the passage was ranked below 5th fell from 89 to 55.

## The claims

**K1 held: reranking puts the found passage in the top 5.** 316 of 400 (74.7% to 82.7%), above
the reference's 281 (65.6% to 74.5%), if only just.

**K2 failed, for lack of room.** The claim was that the reranker would rank look-alikes above the
evidence on fewer of the 40 distractor items. But by E7 the reference already ranked none above
the evidence: E4's section chunks had put each look-alike in a different, clearly labelled
section. Zero cannot fall. The claim was written from E2's numbers and not rechecked after E4.

**K3 held: a longer shortlist finds more.** 316 with 20 against 298 with 10. The reranker can only
promote what is on the shortlist, and two-part and bridge questions need passages from further
down.

**K4 held: better search gave better answers.** Search +35, answers +36.

## The cross-encoder on the distractor items

On the 40 distractor items, shortlist 10, the cross-encoder ranked the evidence in the top 5 on
all 40 and no look-alike above it, the same as the reference and the LLM reranker: E4's section
chunks had already solved these items, so the comparison shows no difference in quality. It does
show the cost: 400 question-passage pairs took 2,465 seconds of CPU time, about **62 seconds per
question**, against about 1 second for the LLM reranker's single call. On this machine the local
model is the slower and, in electricity and waiting, the dearer choice.

## What this does not show

- **The cross-encoder at scale.** 40 items, on a CPU; a GPU would be many times faster, and at
  that speed it costs nothing per question.
- **One LLM, one instruction.** A small model's listwise ranking can drop or repeat passages.
- **K2 had no room to hold or fail meaningfully.**

## Charts

`results/charts/`: **`recall`** (recall at 5 on distractor, identifier and one-sentence policy
items; read the chart's note for its highlight), **`numbers`** and **`scoreboard`** (stage 7;
joined).

## Cost

$1.89 for the episode (OpenAI $0.95, nearly all reranking calls: a median of about 10,300 input and
43 output tokens per question for 20 section-sized passages, about $0.001 each; Google $0.94 for judging). The
reranker adds one call per question to every run from here on.

## Run it

```bash
uv run lab rag analyse episodes/s2-e7-reranking/config.yaml
```

```bash
uv run lab rag run episodes/s2-e7-reranking/config.yaml
```

```bash
uv run --extra rerank python episodes/s2-e7-reranking/cross_encoder_subset.py
```
