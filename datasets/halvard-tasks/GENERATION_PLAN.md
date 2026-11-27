# How the Season 4 task data will be made

Draft for Gate 2, 22 November 2026. Nothing here has been run. Every message, label and rule is
invented. `datasets/halvard/` is not changed.

## Models

| Role | Model | Settings | Why |
|---|---|---|---|
| Generator | `gemini-3.1-flash-lite` | reasoning minimal, JSON schema output | Cheapest model that is not an answer model in any arm |
| Blind labeller | `claude-haiku-5-5` | reasoning off, JSON schema output | A third provider and not an arm, so discarding its disagreements does not make the test easier for `gpt-6-luna` or the open model |

## Task A: triage messages

1. **Seeds, in code.** For each item, code draws a route, a product (or none, or an invented
   product for `unknown_product`), a fault, a safety flag, a hard case (or none), a persona
   (age band, tone, writing habits such as typos or no punctuation) and a length band (15 to 40,
   40 to 90, or 90 to 160 words), from a fixed seed. Safety items are 10% of every split; hard
   cases take the shares in `routes.yaml`. The label is the seed.
2. **Generation.** The generator writes one customer email or chat message for the seed. It
   is told the label and the route definitions, and told not to use the route, fault or field
   names in the message. Output: `{"message": "..."}`.
3. **Code checks** reject a message that names a route or fault key, is outside its length
   band, or names a product other than the seeded ones. A rejected seed is regenerated once with
   the reason, then dropped.
4. **Blind label check.** The labeller sees `routes.yaml` and the message only, and returns the
   four fields. Items where any field disagrees with the seed are discarded. The count of
   discards, per field and per route, goes in `README.md`.
5. **Near duplicates.** Character 5-gram Jaccard similarity; a test or dev item over 0.8 with
   any train item is removed. The threshold is fixed here, before generation.
6. **Splits** by seed, before generation: train 1,600, dev 200, test 600 kept. About 30% extra
   seeds are drawn per split to absorb discards; the first items to pass, in seed order, are
   kept.

## Task B: house style replies

1. **Source pairs.** Questions and correct answers from the S2 reference run on Halvard
   questions outside the `halvard-v2` test set: the 100 dev questions plus new questions made by
   the generator from corpus passages (public documents only, never `INT-*`). The S2 reference
   system answers them; only answers the judge marked correct are kept. Train and test never
   share a corpus question.
2. **Target replies.** The generator rewrites each answer to `style-guide.md`. Code then
   checks every code rule; a reply that fails is regenerated once with the failures, then
   dropped. The blind labeller checks that every fact in the answer is kept and none added;
   disagreements are dropped and counted.
3. **Sizes:** train 600, dev 100, test 300. Test targets are reference replies only; arms are
   scored by the code checks and the judge, not by similarity to the target.

## Your check, then freeze

Code writes `review/test-sample.md`: 50 Task A test items and 20 Task B test items, drawn at
random with a fixed seed, each with its label. After your check, `MANIFEST.json` records every
file's hash and a frozen test fails if any changes. Later changes are dated amendments.

## Rough size (the estimate at the gate decides)

| Step | Calls | Tokens |
|---|---|---|
| Task A generation, 3,120 seeds | about 4,060 with retries | about 0.7 million in, 0.5 million out |
| Task A label check | 3,120 | about 3.3 million in (the definitions each time), 0.1 million out |
| Task B question generation | about 1,700 | about 1.5 million in, 0.2 million out |
| Task B S2 reference answers and judge | about 1,700 each | about 9 million in, 0.6 million out, on `gpt-6-luna` and `gemini-3.6-flash` |
| Task B style rewrites and fact check | about 3,400 | about 3 million in, 0.5 million out |

## Amendment, 23 November 2026: Task A draft-3, harder

The first Task A build was too easy: `gpt-6-luna` with a one-line prompt got 183 of 200 dev
items fully right (`episodes/s4-e1-baseline`, amendment 1, whose rule was fixed before the
check). Task A is rebuilt before any test set is frozen. Task B is unchanged.

- **Four new hard cases** (`routes.yaml` draft-3), each with a label fixed by a written rule:
  `mixed_request` (a fault, then a request for money back: return_refund by precedence),
  `two_requests` (a minor request first, then one the precedence rules decide),
  `negated_cue` (another request mentioned and ruled out), `safe_use_question` (asks whether
  something is safe, with no incident: safety false).
- **Shares:** `harmless_safety_word` 5% to 10% (false safety alarms were the main error) and
  `angry_not_complaint` 6% to 8%. Hard cases are now 64% of items, against 27% before; plain
  items about 30%.
- **Overgeneration** 30% to 45%, since hard cases are discarded more often by the label check.
  3,480 seeds for 2,400 kept items.
- **Anthropic limits** raised to 10 at a time and 250 a minute, to keep the build near 30
  minutes.
- Routes, products, faults, the safety definition, the label check, the near duplicate rule
  and the sizes are unchanged. Faults and products are still paired at random, so some
  messages describe an odd fault for their appliance; the label check drops the ones that do
  not read sensibly.
- The first build stays in git history (f9d0e6f) and is reported in the dataset README.
