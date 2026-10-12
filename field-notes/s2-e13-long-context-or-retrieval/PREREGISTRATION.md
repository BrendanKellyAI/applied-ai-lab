# S2 E13 pre-registration: long context or retrieval? (field note)

Written before any E13 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

On the same questions, when does sending everything beat a retrieval pipeline?

`gpt-6-luna` reads up to 1,050,000 tokens. The current public library is about 161,000 tokens (`cl100k_base`),
past the 128,000 the season set as the long-context threshold, so the whole library fits in one
prompt. S1 E7 found long-context lookup solved for simple questions; v1's E6 field note found
look-alikes and two-step questions together broke it at 128,000 tokens. E13 puts the two
approaches head to head on the questions retrieval finds hardest.

## Setup

- **Items:** 120 test items, all public askers: 40 look-alike (distractor), 20 two-part, 20
  bridge, and 40 one-sentence policy items as the control.
- **Retrieval arm:** the reference system after E12, pinned in
  `season2/history/s2-e13-long-context-or-retrieval.yaml`, run in full on the 520 test items
  (from cache where possible); the 120 are read from that run.
- **Long-context arm** (`longcontext.py`): every current public document in the library (the 4
  current policies and the 300 support articles), each headed with its title and id, then the
  question. The manifest's smaller `long_context_pack` (63 documents, about 120,000 tokens) is
  not used: it is under 128,000 tokens and leaves documents out, and the question is about
  sending everything. Same answer model, same instruction, same output limit as the
  reference. The library comes first so the provider can cache it; cached tokens are reported.
- **Scoring:** correctness only, two ways: the judge (`gemini-3.6-flash`, the season's
  instructions, with the passages replaced by a note that the whole library was given), and the
  code check (every key value in the answer as a whole token). A judge prompt holding the whole
  library would cost more than the experiment, so faithfulness is not judged in either arm.
  Both arms are scored on the same two measures.

## Claims

**L1. On the hardest questions, sending everything beats retrieval.**
- *Pass mark:* on the 80 look-alike, two-part and bridge items, the long-context arm's judged
  correct rate sits above the retrieval arm's.

**L2. On simple questions, retrieval loses nothing.**
- *Pass mark:* on the 40 one-sentence policy items, the two arms' judged correct rates have
  overlapping intervals.

**L3. Long context costs many times more per question.**
- *Pass mark:* the long-context arm's median input tokens per question are at least 20 times the
  retrieval arm's.

**L4. Long context is slower.**
- *Pass mark:* its median seconds per answer are at least 3 times the retrieval arm's.

## Reported, with no claim

- The code check's correct rate per arm and type, beside the judge's.
- Cost per question per arm, with and without the prompt cache.
- Paired comparison (exact McNemar) of correct answers per item.

## What this does not test

- **Permissions and versions:** the long-context arm is given only current public documents,
  which a real long-context system would also have to arrange. Retrieval does it with E8's
  filter.
- **A library that does not fit,** or changes daily: the pack is fixed.
- **Faithfulness,** in either arm.
- **One model.** Long-context ability varies widely between models.
