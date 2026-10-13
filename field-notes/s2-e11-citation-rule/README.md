# S2 E11: Does a citation rule change the answer? (field note)

Does requiring a citation change what a model says, or only how it says it? E11 makes no call: it
compares two runs that already exist, on the same 520 test items with the same five passages in
every prompt. Claims: [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: the rule changed how the model answers (every answer now cites), not what it answers.**

## The two runs

- **Not cited:** E9's `allow-not-found`: "Answer the question using the passages below. If the
  passages do not contain the answer, reply that you could not find it."
- **Cited:** E10's `grounded-cite`: the same, plus "using only the passages" and "After each
  claim, cite the passage it comes from, as [P1], [P2] and so on."

Same model (`gpt-6-luna`), same judge, same retrieval: every item's prompt held the same passages
in both runs (checked in `analysis.json`).

## Results

| | Not cited | Cited |
|---|---|---|
| Right answers (400 answerable) | 357 | 354 |
| Declines on the 120 unanswerable | 105 (80% to 92%) | 107 (82% to 94%) |
| Median output tokens | 26 | 28 |
| Answers carrying a citation | 0 | every answer that is not a decline |

## The claims

**N1 held: the citation rule did not change which answers were right.** 11 items went from right
to wrong and 11 from wrong to right (exact McNemar p = 1.0). The 22 flips are spread across ten
item types, two or three each: noise, not a pattern.

**N2 held: it did not change when the model declined.** 107 against 105 of 120.

**N3 failed: it did not make answers longer.** A median of 28 output tokens against 26: the
markers add a few tokens, not sentences.

So for this model, asking for citations is free: the answers stay the same, at the same length,
and gain a pointer to their source that E10 can check.

## What this does not show

- **One model.** A model that writes long answers, or one that already cites unasked, may react
  differently.
- **"Only" changed too,** between the two instructions.
- **Correctness by the judge,** which is not hand-checked for these runs.

## Run it

```bash
uv run python field-notes/s2-e11-citation-rule/analyse.py
```
