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

## Amendment, 12 October 2026: a second model, and 10 marked by hand

Made before any item was marked and before any call to the second model. Marking 50 items by
hand was more than the owner would do, so the design changed. **J1, J2 and J3 above are
withdrawn and replaced by A1 to A4 below.** The sample of 50 is unchanged.

- **Second marker:** `gemini-3.6-flash` at reasoning `medium`, from a third provider (Google),
  so neither the answer model's provider nor the judge's. It is not chosen as a stronger
  model, only an independent one. It gets the judge's exact instructions and the exact prompt
  the judge got for each item, with the judge's retry rule for a reply that is not a verdict.
- **Hand marks:** Brendan Kelly marks 10 items, blind to both models' verdicts. They are the 10
  where the two models disagree most: first those where they split on "right", then those
  that differ on more fields, ties in the sample's shuffled order. If fewer than 10 disagree,
  items they agree on fill the rest.
- **What can be measured:** agreement between the two models on all 50, and, on the 10, which
  model a person sides with. Where the two models agree, nobody checks them. The README says
  that throughout.

### Claims

**A1. The judge and the second model agree on the answer verdict.** "Right" is correct and
faithful, the verdict behind E2's answer number.

- *Pass mark:* agreement on "right" on at least 45 of the 50 (90%), counted over the items
  where both models gave a verdict.

**A2. The judge and the second model agree on declines,** the verdict behind the not-found
number.

- *Pass mark:* agreement on "declined" on at least 45 of the 50 (90%).

**A3. Where the two models split, the judge is right at least as often as the second model.**

- *Pass mark:* on the hand-marked items where the models split on "right", the hand mark
  matches the judge on at least half.
- If no hand-marked item splits on "right", A3 is not tested and the README says so.

**A4. The judge beats the code check on correctness.**

- *Pass mark:* on hand-marked items with key values, the judge's `correct` matches the hand
  mark on more items than the code check does (point estimates).

### Reported, with no claim

- Agreement on each field, between the models on 50 and with the hand marks on 10.
- **An estimate of the judge's accuracy on "right":** items where both models agree, counted
  as right, plus the hand-marked splits the judge got right, out of those two groups together.
  This rests on the assumption that two models from different providers that agree are
  correct, and is labelled as an estimate everywhere it appears.
- Splits on "right" beyond the 10 marked, if any, listed as unchecked.

## Second amendment, 12 October 2026: hand marks without the passages

Made before any item was marked. The owner marks each item from the question, the reference
answer and the system's answer only, without reading the five passages. Faithfulness cannot be
judged without the passages, so the hand marks cover `declined` and `correct` only.

- **A1, A2 and A4 are unchanged.**
- **A3 is restated on correctness:** on the hand-marked items where the two models split on
  `correct`, the hand mark matches the judge on at least half. If no hand-marked item splits on
  `correct`, A3 is not tested and the README says so.
- **The estimate is restated on correctness:** items where both models agree on `correct`,
  counted as right, plus the hand-marked splits on `correct` the judge got right.
- **Faithfulness is checked by no person.** Its only check is agreement between the two models
  on all 50, and the README says so wherever the answer number, which needs faithfulness,
  appears.
- The 10 items were already chosen by the first amendment's rule, which ranks splits on
  "right" first. That choice is kept.

## What this does not test

- **Shared verdicts are not checked.** Where the two models agree, no person looks. Two models
  can share a blind spot, such as both treating a hedged answer as correct.
- **One marker, 10 items.** No second person marks them, and 10 is too few for an interval
  worth quoting on its own.
- **The 10 are chosen for disagreement.** They show which model to believe when the two split,
  not how often either is right in general.
- **50 items.** At 45 of 50 the interval runs from about 79% to 96%.
- **The sample is stratified, not proportional.** Rare types are over-represented and common
  ones under-represented, so the agreement is on the sample as drawn, not on the 520 as a whole.
- **One run.** The judge sends no temperature and its calls are cached, so the same verdicts
  come back; how much a fresh call would vary is not measured.
