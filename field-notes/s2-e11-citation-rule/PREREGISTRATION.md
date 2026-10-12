# S2 E11 pre-registration: does a citation rule change the answer? (field note)

Written before E10's grounded run, and not edited after it. Every claim is reported in
`README.md` as Held or Failed.

## The question

Does requiring a citation change what a model says, or only how it says it?

## Setup

E11 makes no call of its own. It compares two full runs on the same 520 test items, with the same
retrieval, so every prompt holds the same five passages:

- **Not cited:** E9's `allow-not-found` condition: "Answer the question using the passages
  below. If the passages do not contain the answer, reply that you could not find it."
- **Cited:** E10's `grounded-cite` condition: the same, plus "using only the passages" and "After
  each claim, cite the passage it comes from, as [P1], [P2] and so on."

The two instructions differ only by the citation rule and the word "only", so the comparison
isolates the rule as closely as the season's runs allow. Both runs share the reference after E8
(`d52dd1b463b8` apart from the instruction); the claims below are checked after confirming that
each item's prompt passages are identical in the two runs.

## Claims

**N1. A citation rule does not change which answers are right.**
- *Pass mark:* a paired comparison of right answers (correct and faithful) per item gives an
  exact McNemar p-value of at least 0.05.

**N2. It does not change when the model declines.**
- *Pass mark:* the two not-found rates on the 120 unanswerable items have overlapping intervals.

**N3. It makes answers longer.**
- *Pass mark:* the cited run's median output tokens are at least 1.2 times the uncited run's.

## Reported, with no claim

- Items whose verdict changed, by item type, with examples.
- How often the uncited run cites anyway.

## What this does not test

- **One model, one wording.** A model that does not cite unasked might behave differently.
- **"Only" is a second change** between the two instructions.
