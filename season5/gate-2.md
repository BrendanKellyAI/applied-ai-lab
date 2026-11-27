# Season 5 Gate 2: the case data

27 November 2026, on `s5`. For Brendan's approval of one paid step.

## 1. Built with no spend

`uv run lab agent build-world`, about ten seconds, rebuilds everything but the messages
([dataset README](../datasets/halvard-cases/README.md)).

| File | Cases | Expected decisions |
|---|---|---|
| test | 240 | 123 repair, 31 decline, 29 refund, 28 escalate, 19 replacement, 10 existing case |
| dev | 60 | 31 repair, 8 decline, 7 refund, 6 escalate, 5 replacement, 3 existing case |
| telemetry test, dev | 45, 15 | 21 and 7 decline (the log shows an exclusion), 24 and 8 repair |
| sequences test, dev | 30 and 10 sequences, 164 cases | linked by a stated preference, a goodwill refund used, or a repair that failed before |
| long test, dev | 30, 10 | 4 to 6 appliances each, 10 to 20 earlier cases |

- **Test kinds** as in the case plan: routine 40, branching 30, missing information 30, policy
  detail 40, above the refund limit 20, photo 50, adversarial 30. Safety incidents: 20 of 240.
  Approvals needed: 24 of 240.
- **Images:** 148 (74 receipt and plate pairs); the 50 test photo cases have 10 pairs at each
  quality level; 18 receipts carry planted instruction text.
- **Telemetry:** 60 logs, every format and signature; 20 carry planted instructions.
- **Tests** check that the build reproduces the committed files, that every fact agrees with the
  world database, that every outcome recomputes from the policy, that withheld facts stay out of
  the brief, and that every telemetry format parses back to its planted count.
- **A bug the tests caught:** customers were reused across cases, so one case could inherit a
  goodwill refund planted for another. Each case now has its own customer (the world has 700).

## 2. The paid step: messages and label checks

For each of the 564 cases (an attempt counts as a message and a label check):

1. `gemini-3.1-flash-lite` writes the customer message from the case brief.
2. Code checks it: order numbers stated, products named or withheld as the brief says, no serial
   number given, length in range.
3. `claude-haiku-5-5` reads the message, the records the tools would show and the policy, without
   the expected outcome, and states each decision.
4. Accepted when the checker agrees on decision, reason and amount. Otherwise up to two more
   attempts; then discarded and reported in `build_log.json`.

**Estimate** (`uv run lab agent estimate-data`), allowing 30% of cases a second attempt:

| Stage | Model | Calls | Input tokens | Output tokens (expected / ceiling) |
|---|---|---|---|---|
| Messages | `gemini-3.1-flash-lite` | 733 | 155,893 | 101,852 / 387,400 |
| Label check | `claude-haiku-5-5` | 733 | 1,143,143 | 68,006 / 245,960 |

About 1.47 million tokens expected, under the handover's "under 2 million". Paced at 120 requests a
minute: about 15 minutes. The step refuses to start until `budgets.s5-case-data` is set in
`prices.local.yaml`, and refuses if the ceiling is above it.

## 3. After the run

- `cases/<file>.jsonl` with the accepted cases and their messages; `build_log.json` with every
  discard and every check a retry fixed.
- `season5/case-review.md`: 30 test cases chosen by code across the kinds, for your check.
- If discards leave a kind under 20 in test, I will draw replacements with the same recipes and
  run them through the same step (cached calls cost nothing).
- Then the freeze: `MANIFEST.json` with LF normalised hashes, and a frozen test.
