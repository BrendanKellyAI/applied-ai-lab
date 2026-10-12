# S2 E3 pre-registration: measuring it

Written before any item was marked by hand, and not edited after the marking. Every claim below
is reported in `README.md` as Held or Failed, failures included.

## The question

How do you know whether a RAG system works, and how far can you trust the judge that scores
it?

E2's answer and not-found numbers come from an LLM judge, `claude-sonnet-5-5`. E3 checks that
judge against a person. Its result decides how much weight every answer-level number in the
season can carry: the judge is trusted only to the level this check shows.

E3 makes no model call. It reuses the E2 baseline run.

## Setup

- **Run checked:** the E2 baseline, `episodes/s2-e2-first-rag-system/results/baseline`, config
  `b58f06493698`, 520 test items.
- **Sample:** 50 items, drawn by `lab rag judge-check draw` from
  [`judge_check.yaml`](judge_check.yaml) with seed 2026:
  - 3 from each of the 16 item types, taken in turn from each of the judge's outcomes (right,
    wrong, declined), rarest first, so a type the judge mostly passed still gives an item it
    failed;
  - then 2 more at random;
  - in shuffled order. PARA-033, the one item the judge could not mark, is left out.
- **Marking:** Brendan Kelly marks each item's `declined`, `correct` and `faithful` from
  `judge-check/judge_check.md`, which shows each item exactly as the judge saw it: the question
  and any earlier turns, whether the library can answer it, the reference answer, the five
  passages, and the system's answer. The judge's verdict, its reason, the code check and the
  evidence labels are not shown. The marker uses the judge's own rules, printed at the top of
  the sheet.
- **The judge's instructions are pinned:** the sample records a hash of
  `src/lab/rag/prompts/judge.md`, and the report refuses to run if it has changed.
- **Agreement:** the share of the 50 items where the hand mark and the judge give the same
  value, with a Wilson 95% interval, for each field and for "right" (correct and faithful), the
  verdict behind the answer number.

## Claims

**J1. The judge agrees with a person on the answer verdict.** "Right" (correct and faithful)
is the verdict E2's answer number counts.

- *Pass mark:* agreement on "right" is at least 45 of 50 (90%).
- *If it fails:* every answer-level number in the season is reported with the measured
  agreement beside it, and the README lists which way the judge leans.

**J2. The judge agrees with a person on declines.** "Declined" is the verdict behind the
not-found number.

- *Pass mark:* agreement on "declined" is at least 45 of 50 (90%).

**J3. The judge beats the code check on correctness.** On sampled items with key values, the
code check marks an answer correct when it contains every key value as a whole token.

- *Pass mark:* on those items, the judge's `correct` agrees with the hand mark on more items
  than the code check does (point estimates).
- *Why:* E2 found 32 disagreements between the two, 28 of them version questions where the
  answer gave both the old and the current value.

## Reported, with no claim

- Agreement on `correct` and `faithful` separately, with intervals.
- For each field, which way the disagreements lean: judge yes and hand no, or the reverse.
- Every disagreement, with the judge's reason and the marker's note.
- E2's season numbers split into search faults and model faults: the answer rate on items whose
  evidence reached the prompt, beside recall at 5. These are descriptive. E2's results are
  already published, so no claim about them could be pre-registered now.

## What this does not test

- **One marker.** No second person marks the same items, so the person's own error rate is
  not measured.
- **50 items.** At 45 of 50 the interval runs from about 79% to 96%.
- **The sample is stratified, not proportional.** Rare types are over-represented and common
  ones under-represented, so the agreement is on the sample as drawn, not on the 520 as a whole.
- **One run.** The judge sends no temperature and its calls are cached, so the same verdicts
  come back; how much a fresh call would vary is not measured.
