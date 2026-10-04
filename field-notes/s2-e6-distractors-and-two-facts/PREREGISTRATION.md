# S2 E6 pre-registration

Committed before the full run and not edited after it, except for the amendment at the end,
made before the run. The amendment overrides the grid and marks above it. Every claim below is reported in
`README.md` as Held or Failed, failures included. The same pass marks are in `config.yaml`
(`parameters.pass_marks`), and `claims.py` applies them; a test checks this file and the config
agree.

## Setup

- Models and settings: S1 E7's, unchanged. GPT-5.6 Terra and Claude Sonnet 5 with reasoning off
  and 50 output tokens; Gemini 3.6 Flash at `minimal` with 1,024 output tokens. Provider-default
  temperature for all three.
- Filler: S1 E7's pinned Gutenberg books and insertion, except Frankenstein, whose prose is
  87,723 tokens long after the front matter is skipped, short of 128,000. It is replaced by Jane
  Eyre (Gutenberg 1260), pinned by SHA-256 on 4 October 2026. Lengths and positions are measured
  with `o200k_base`; lengths within 5% of target, positions within 2 percentage points.
- Prompt: S1 E7's. System: "Answer using only the document provided. Reply with the value
  only." User: the document in `<document>` tags, then the question.
- Grid: 3 models x 3 lengths (16,000, 64,000, 128,000 tokens) x 4 shapes x 12 items (two fact
  sets per book, six books) = 432 calls. For a given item and length, every shape uses the same
  filler passage, and each sentence sits at the same position at every length.
- Seed 20261004.

## Shapes

Each item has a turbine id (`K-417`), a hangar (a digit and a letter, such as `6B`), and
four-digit values. Nothing invented appears in the book text, and nothing repeats within a
document except a hangar named in both its bridge and its access code.

1. **Single.** "The maintenance code for turbine K-417 is 8352." Question: "What is the
   maintenance code for turbine K-417?" Target position seeded, uniform in 25% to 75%.
2. **Distractors.** Shape 1 plus four look-alikes in the same template, for ids one edit from
   the target, each with its own code. The look-alikes are drawn one edit kind at a time, hardest
   first: two neighbouring digits swapped (`K-147`), a digit changed (`K-447`), the letter
   changed (`X-417`), a digit changed. Target as in shape 1; look-alikes at seeded positions
   across 0% to 100%, at least 10 points from the target and from each other.
3. **Two-fact.** "Turbine K-417 is stored in hangar 6B." and "The access code for hangar 6B is
   2719." Question: "What is the access code for the hangar where turbine K-417 is stored?" One
   sentence in 10% to 30%, the other in 70% to 90%; bridge first on 6 items, answer first on 6.
4. **Two-fact with distractors.** Shape 3 plus two look-alike bridges (the first two look-alike
   ids, so a swap and a changed digit, each in its own hangar), access codes for those two
   hangars, and access codes for two further hangars with no turbine. Placement as shape 2.

## Scoring

Correct: the reply contains the expected value as a whole token (S1 E7's rule) and was not cut
short by the output limit. Every incorrect reply gets one type, checked in this order:

- **Distractor value**: names a value from a look-alike sentence (a look-alike's code, a
  look-alike's hangar, or a code for a look-alike hangar).
- **Intermediate**: in a two-fact shape, names the turbine's own hangar instead of the code.
- **Other**: anything else, including refusals and truncated replies (flagged separately).

A prompt a provider rejects as too long is recorded as an error, not a wrong answer, and the
run stops.

## Claims

Pooled means across the three models: n = 36 per shape and length, 12 per model. "Points" are
percentage points of accuracy, compared in whole calls.

- **H0. Control holds at 128,000 tokens.** Single shape: each model at least 34 of 36 across the
  three lengths, and pooled at 128,000 at least 34 of 36.
- **H1. Distractors cost accuracy at 128,000.** Pooled Distractors accuracy at 128,000 is at
  least 10 points below pooled Single at 128,000, and at least 3 wrong replies across the grid
  name a distractor value.
- **H2. Two facts cost accuracy at 128,000.** Pooled Two-fact accuracy at 128,000 is at least 10
  points below pooled Single at 128,000.
- **H3. The combined shape is hardest.** Pooled shape 4 accuracy at 128,000 is at least 5 points
  below both shape 2 and shape 3 at 128,000.
- **H4. Length matters for the hardest shape.** Pooled shape 4 accuracy at 128,000 is at least
  10 points below pooled shape 4 at 16,000.
- **H5. The models separate.** On shape 4 at 128,000, at least one pair of models has
  non-overlapping Wilson 95% intervals (12 calls each).

Bridge first against answer first (6 items against 6) is reported descriptively only, not as a
claim.

## Rules

- The pilot (15 calls: per model, the four shapes once at 16,000 and shape 4 once at 128,000)
  checks the pipeline only. It is never used to change a pass mark.
- Numbers are reported as "x of n" with Wilson 95% intervals.

## Amendment, 4 October 2026: a reduced run

Made after the 15-call pilot and before any other call. The full grid of 432 calls was costed at
about $60 and not run; a run that was started was stopped before it recorded a result, and no
result from it has been read. The run is reduced to 72 calls, and the claims are re-marked for
the smaller cells. Shapes, placement, prompt, scoring and every build check are unchanged; every
document is still built and checked against the manifest.

- **Grid:** 3 models x 1 length (128,000 tokens) x 4 shapes x 6 items = 72 calls. The items are
  one per book: 0, 4 and 8 (bridge first) and 3, 7 and 11 (answer first). The pilot's three
  128,000-token calls are inside this grid and are reused; its twelve 16,000-token calls are
  reported as pilot results only.
- **Pooled n:** 18 per shape (6 per model). "Points" are still compared in whole calls: 10
  points needs a gap of 2 calls of 18 (11.1 points), 5 points needs 1 (5.6).

Claims, as amended:

- **H0. Control holds at 128,000 tokens.** Single shape: each model at least 5 of 6, and pooled
  at 128,000 at least 17 of 18.
- **H1. Distractors cost accuracy at 128,000.** Pooled Distractors accuracy at 128,000 is at
  least 10 points below pooled Single at 128,000, and at least 3 wrong replies across the run
  name a distractor value.
- **H2. Two facts cost accuracy at 128,000.** Pooled Two-fact accuracy at 128,000 is at least 10
  points below pooled Single at 128,000.
- **H3. The combined shape is hardest.** Pooled shape 4 accuracy at 128,000 is at least 5 points
  below both shape 2 and shape 3 at 128,000.
- **H4. Withdrawn, not tested.** The run has no 16,000-token calls.
- **H5. The models separate.** On shape 4 at 128,000, at least one pair of models has
  non-overlapping Wilson 95% intervals (6 calls each). With 6 calls, this needs 6 of 6 against 1 of
  6 or fewer, or 5 of 6 against 0 of 6.

The `length-hardest` chart is not drawn, since the run has one length.
