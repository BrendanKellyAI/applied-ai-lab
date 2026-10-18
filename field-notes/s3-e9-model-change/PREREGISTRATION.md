# S3 E9 pre-registration: does it survive a model change? (field note)

Written before any E9 answer call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed. Later changes go in dated amendments at the end.

## The question

What breaks when you switch provider, or when the provider updates the model under you?

## Design

The Season 2 reference system (`season2/reference.yaml`, config `0294479ba987`) on all 520
`halvard-v2` test items (400 answerable, 120 unanswerable). Only stage 9, the answer model,
changes. Held fixed: retrieval and the reranker's order (served from the S2 E12 reference run's
cache; no embedding or reranker call is new), the `grounded_cite` instruction word for word,
and the citation parser.

| Arm | Answer model | Setting | Judge |
|---|---|---|---|
| `baseline` | `gpt-6-luna` (today's system; S2 E12 reference run, from cache) | off | `gemini-3.6-flash` |
| `version` | `gpt-5.6-luna`, the previous version | off | `gemini-3.6-flash` |
| `provider` | `claude-haiku-5-5`, the same price tier at another provider | off | `gemini-3.6-flash` |
| `provider-google` (optional second provider) | `gemini-3.5-flash-lite`, the cheapest Google tier with a published price | minimal | `claude-sonnet-5-5` |

**The version arm is framed as the update you did not choose:** you were on `gpt-5.6-luna`
and the provider moved you to `gpt-6-luna`. Every comparison reads from `version` to
`baseline` in that direction. `gpt-5.6-luna` was callable on 18 October 2026 (`lab smoke`).

**Price tiers** (published prices, 18 October 2026, as ratios to `gpt-6-luna`): `claude-haiku-5-5`
1x input and 1x output; `gpt-5.6-luna` 2x and 2.4x; `gemini-3.5-flash-lite` 3x and 5x. No
callable Google model is priced closer.

The `provider-google` arm makes the same requests as S3 E3's `gemini-3-5-flash-lite` arm, so it
is served from that run's cache. Its judge is the S2 E2 and E3 judge; S3 E3 reports the two
judges' agreement on a shared sample.

**Not included:** a managed-versus-direct arm (decided on 16 October 2026).

**Pilot:** 2 test items of each type (32 items) per arm, as in Season 2, to check calls,
parsing and tokens. Pilot results are not used for any claim.

## What is measured: three kinds of break

| Kind | Measure |
|---|---|
| Content | Items handled right (answerable answered right plus unanswerable declined, out of 520); right answers (of 400) and correct declines (of 120). Per-item flips both ways against the baseline, with exact McNemar. |
| Format | Share of answers that are not declines carrying at least one parseable `[Pn]` citation. Share of judged declines whose wording the code recognises as "not found" (a regular expression for phrases such as "could not find"). |
| Behaviour | Citation validity (share of citations whose passage holds the evidence, as S2 E10 measured it: 91% for the reference). Median output tokens and the cost ratio per item handled right. Median latency. Errors and refusals (calls that failed or returned no text). |

## Claims

**V1. A total that barely moves hides many changed answers.**
*Pass mark:* in each of `version` and `provider`, the number of items that flip (right to
wrong plus wrong to right, of 520) is at least 3 times the absolute net change in items handled
right.

**V2. The prompt carries across.**
*Pass mark:* in each of `version` and `provider`, the share of non-decline answers with a
parseable citation is within 5 percentage points of the baseline's.

**V3. On the total, the swap looks safe.**
*Pass mark:* for each of `version` and `provider`, the exact McNemar test on items handled right
against the baseline does not separate them (p at or above 0.05).

**V4. Behaviour changes even when content does not.**
*Pass mark:* in at least one of `version` and `provider`, median output tokens differ from the
baseline's by at least 25%.

`provider-google` is reported on every measure with no claim.

## Limits stated in advance

- In practice teams often swap the reranker too; here the reranker (`gpt-6-luna`) is held fixed,
  so only the answer model's change is measured.
- One system, one test set, one point in time; results go in `results/2026-10/`, so a rerun at
  a later release adds a folder.
- The version arm is backwards in time (old to new is read as the update); a real update would
  also change the date and the model's behaviour in ways one snapshot cannot show.
- Costs are published as ratios only.
