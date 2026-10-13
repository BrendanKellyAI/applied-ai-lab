# S2 E13: Long context or retrieval? (field note)

On the same questions, when does sending everything beat a retrieval pipeline? E13 sends every
current public document (304 documents, 160,000 tokens) with each question, and compares that
with the season's reference system on 120 test items. Claims:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: at this size, sending everything was about as accurate, no slower, and ten times the
price.** It won clearly on one question type, bridge questions, where retrieval has to find two
documents at once. Only L2 held.

## The design

- **Items:** 120 test items from public askers: 40 look-alike, 20 two-part, 20 bridge and 40
  one-sentence policy items as the control.
- **Retrieval arm:** the reference system after E12 (`0294479ba987`), read from E12's reference
  run (the same system; see the amendment in the brief).
- **Long-context arm** (`longcontext.py`): the 4 current policies and 300 support articles, each
  headed with its title and id, then the question. Same model (`gpt-6-luna`), same instruction.
- **Scoring:** correctness by the judge, with the code check beside it. Faithfulness is not
  judged in either arm.

## Results

| Correct, by the judge | Long context | Retrieval |
|---|---|---|
| Look-alike (40) | 38 | **40** |
| Two-part (20) | 17 | 17 |
| Bridge (20) | **20** | 14 |
| **Hard items together (80)** | 75 (86% to 97%) | 71 (80% to 94%) |
| One-sentence policy (40) | 39 | 39 |

Paired on all 120: 9 right only with long context, 5 only with retrieval (exact McNemar
p = 0.42). The code check agrees except on two-part items, where it marks retrieval's answers
down to 11 of 20 against 17. Of the six it disputes, four answer only one of the two parts
(saying the other could not be found, or answering a different question), which the judge still
marked correct; two write a price as "£70" where the key value is "£70.00". So on two-part
items the judge is lenient, and retrieval's true two-part score is nearer 13 than 17.

| Per question (medians) | Long context | Retrieval |
|---|---|---|
| Input tokens | 160,398 | 14,598 (answer call alone 3,653) |
| Seconds | 1.9 | 2.5 (answer call alone 1.2) |
| Cost (mean) | $0.016 | $0.0016 |

Most of retrieval's tokens are the reranker's: it reads 20 candidate passages per question. No
prompt caching took effect in the long-context arm (0% of input tokens cached), so its cost is
the full price.

## The claims

**L1 failed: on the hardest questions, sending everything did not beat retrieval.** 75 against
71 of 80, overlapping intervals. It won bridge questions 20 to 14 but lost two look-alikes:
given every product's page, it twice took a look-alike product's warranty instead of the asked
one's (or reported both).

**L2 held: on simple questions, retrieval lost nothing.** 39 against 39 of 40.

**L3 failed: long context did not cost 20 times more per question.** It cost 11 times the input
tokens, because retrieval's reranker is itself a sizable call.

**L4 failed: long context was not slower.** A median of 1.9 seconds against 2.5. The model reads
160,000 tokens in under two seconds; retrieval spends its time on two calls in a row.

## What this means

At 160,000 tokens, a library that fits comfortably in the model's window, long context is a
serious option: accuracy is the same within the noise, it handles questions spanning documents
better, and there is no pipeline to build. Its costs are price (ten times here, unless caching
works) and everything the brief left out: permissions and versions (the arm was handed only
current public documents), a library that changes, and one too large to fit. Retrieval stays the
reference because the season's library has restricted and superseded documents, and because the
price gap grows with the library.

## What this does not show

- **Seconds measured in different runs.** Retrieval's calls ran in a bigger batch (8 at once,
  with the judge) than the long-context arm's (4 at once), which may inflate its seconds.
- **No caching.** A provider cache would cut the long-context price, perhaps by most of it; it
  did not take effect here.
- **One model, one library size, no faithfulness check.**
- **The answers cite `[P1]`** although long-context documents are not numbered: the instruction
  asks for markers. They are ignored here.

## Cost

$1.98 (OpenAI $1.94, Google $0.04, estimated from reported tokens).

## Run it

```bash
uv run python field-notes/s2-e13-long-context-or-retrieval/analyse.py
```

```bash
uv run python field-notes/s2-e13-long-context-or-retrieval/longcontext.py
```
