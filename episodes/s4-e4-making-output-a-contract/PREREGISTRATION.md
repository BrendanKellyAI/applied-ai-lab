# S4 E4 pre-registration: making output a contract

Written before any E4 call and not edited after the run; any later change goes in a dated
amendment at the end. Pass marks are in `claims.yaml`. Bundled with E2 and E3 for one estimate
and one approval.

## The question

Code reads Task A's output. Does asking the provider to enforce the format (JSON mode, or a
schema) make the output safer to read, and does it change the answers, in either direction?

## Setup

- **Data:** Task A, dev 200 to choose, test 600 to report.
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200.
- **Prompt and examples:** E3's best arm, chosen on dev by E3's rule. Until then `config.yaml`
  does not exist; `ceiling.yaml` and `ceiling.dev.yaml` use the longest prompt and 32 examples
  for the estimate and are never run.

  | Arm | Output |
  |---|---|
  | `e4-text` | Free text, then the parser (`parse_triage`): E3's best arm, the reference (cached) |
  | `e4-json-mode` | The provider's JSON mode (`json_object`), then the same parser |
  | `e4-schema` | A strict JSON schema of the four fields and their allowed values (`triage_schema`), then the same parser |

- **The parser is the same for every arm** and still validates: a reply that is not one JSON
  object with four allowed values is invalid and wrong on every field.
- **Statistics:** Wilson intervals; exact McNemar against `e4-text`, Holm corrected across the
  two; flips both ways.
- **Known before the run:** E1's free text replies were all valid JSON on dev (200 of 200), so
  E4 may show little difference in validity. That is a result, not a reason to drop the
  episode.

## The choice that carries forward

On dev, the arm with the highest fully right is the season's best prompted arm, which E5 tunes
against. A tie goes to `e4-schema`, then `e4-json-mode`: the stronger contract wins a tie.

## Measures, in order

1. JSON validity, out of 600.
2. Accuracy among valid outputs (fully right out of valid replies).
3. Fully right, out of 600: the primary.

Also reported: invalid reasons, safety recall and false alarms, output tokens per call.

## Claims (on test)

**C1. A schema makes every reply readable.**

- *Pass mark:* `e4-schema` has JSON validity of 600 out of 600.

**C2. Constraining the format does not change accuracy.**

- *Pass mark:* neither `e4-json-mode` nor `e4-schema` differs from `e4-text` on fully right with
  a Holm-corrected exact McNemar p below 0.05. If one does, the claim fails and the direction is
  reported.

## What E4 cannot show

- One provider's JSON mode and schema support; others enforce formats differently.
- Strict schemas fix the allowed values, so they also stop invented routes; validity and
  accuracy cannot be fully separated.

## Amendment 1, 23 November 2026: after E3's change of base

Written before any E4 call. E3 now builds on the one-line prompt (E3 Amendment 1), so E4's base
is E3's best arm on that prompt; the arms, rule and claims are unchanged. One correction: the
arm E5 tunes against is the best prompted arm on dev across E2, E3 and E4 (the handover's rule),
not E4's best alone. Ties go to fewer input tokens per call.

## Amendment 2, 23 November 2026: JSON mode's first dev run failed

Written after the first dev run and before rerunning `e4-json-mode`. Every `e4-json-mode`
call was rejected (no charge): OpenAI's JSON mode needs the word "json" in the input messages,
and the adapter sent the system prompt as `instructions`, which do not count. The runner also
retried each rejection five times, because a rejection inside the stream was treated as an
interruption. Both are fixed in `src/lab/providers/openai_provider.py`:

- With JSON mode, the same system text is sent as a developer message before the user turn,
  instead of as `instructions`. The words are unchanged; the request hash is unchanged.
- A rejected request inside the stream is no longer retried.

`e4-text` and `e4-schema` are unaffected and not rerun. The arms, rule and claims are unchanged.
The difference in transport is a limitation of the JSON mode comparison, named in the README.
