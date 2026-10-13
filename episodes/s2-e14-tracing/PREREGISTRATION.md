# S2 E14 pre-registration: tracing a wrong answer

Written before E14's analysis, and not edited after it. Every claim is reported in `README.md`
as Held or Failed.

## The question

When the system gives a wrong answer, which stage caused it?

## Setup

E14 makes no call. It reads the retrieval logs of three runs on the 520 test items, each the
reference system of its time:

- **E2's baseline** (`b58f06493698`): the first, naive system.
- **E4's baseline** (`9652ab169377`): the same system, judged by the season's final judge.
- **The final reference system** (`0294479ba987`), as run in E12.

A wrong answer is an answerable item the judge did not mark both correct and faithful. Each one
is walked back to the first stage that lost its right passage, in code, from the log alone
(`first_lost_stage` in `src/lab/rag/score.py`), with the ranking stage split in two:

1. **Cut:** the chunker split the evidence span.
2. **Missed:** the span is not in the search depth (50).
3. **Filtered:** the filter removed it.
4. **Outside the shortlist:** after filtering it ranks below the reranker's shortlist of 20
   (final system only; E2 and E4 have no reranker).
5. **Ranked too low:** it did not end in the top 5 passages.
6. **Ignored:** it was in the prompt and the model said it could not find the answer.
7. **Misread:** it was in the prompt and the answer was wrong.

Leaks (restricted or superseded passages in the prompt) are counted separately, on every item.

**Already seen before writing this:** each run's totals for the stages before this refinement
(final system: ranking 39, missed 2, ignored 3, misread 2, of 46 wrong; leaks 0), and E12's
search hits by item type. The claims below are about what was not yet looked at.

## Claims

**T1. Most of the final system's ranking losses happen before the reranker.**
- *Pass mark:* of the wrong answers lost at ranking, at least half had the right passage outside
  the reranker's shortlist of 20.

**T2. The final system's failures sit in two item types, follow-ups and identifiers.**
- *Pass mark:* these two types make up at least 60% of its wrong answers.

**T3. When the final system answers a question it should decline, the library usually covers the
topic but not the detail.**
- *Pass mark:* of the unanswerable items it did not decline, at least half are `absent_detail`
  items.

## Reported, with no claim

- Wrong answers by first lost stage for the three runs, as a chart.
- One worked example per stage in the final system, walked through the log.
- Leaks per run.

## What this does not test

- **The judge's verdicts are taken as given.** E2's run was judged by an earlier judge model.
- **"First lost" is not "only cause":** a passage ranked too low might also have been misread.
- **A right answer with the passage lost** (the model answered from another passage or its own
  knowledge) is not a failure here.
