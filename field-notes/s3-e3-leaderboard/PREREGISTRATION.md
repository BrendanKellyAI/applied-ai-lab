# S3 E3 pre-registration: does the leaderboard predict your task? (field note)

Written before any E3 answer call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed. Later changes go in dated amendments at the end.

## The question

Do public benchmark rankings hold on your own work? Here "your own work" is Halvard Home's
support questions (invented firm, Season 2 library and test set), answered by the Season 2
reference system.

## The leaderboard

The Artificial Analysis Intelligence Index, read on 18 October 2026
(`leaderboard.yaml`: URL, date, each row's score and setting). It is the one public board found
that names the reasoning setting of every row and lists models from all three providers. The
page shows no date or version, so the read date stands in for one. Scores were copied, not
rerun.

## Models

Eight answer models, two or three per provider, spread across the board from 42 to 18 points:

| Board score | Model | Setting |
|---|---|---|
| 42 | `gpt-6.1-sol` | low |
| 42 | `claude-opus-5-5` | low |
| 36 | `claude-sonnet-5-5` | low |
| 33 | `gemini-3.8-flash` | low |
| 29 | `claude-haiku-5-5` | low |
| 27 | `gpt-5.6-terra` | low |
| 22 | `gemini-3.5-flash-lite` | minimal (the board names no setting; the lowest the model allows) |
| 18 | `gpt-6-luna` | off (the reference answer model) |

Each model runs at the setting its board row names. `gpt-6-astra` wrote the corpus prose and is
excluded. The board's highest rows (all above 50) are its models at high or maximum reasoning;
running those on 520 items was judged not worth the cost for a training course, so every model
here is at its lowest listed setting. Models were checked callable with `lab smoke`
(`season3/smoke.yaml`) on 18 October 2026.

## The system

The Season 2 reference system (`season2/reference.yaml`, config `0294479ba987`), with only the
answer model changing (stage 9). Retrieval and the reranker's order are served from the
response cache of the S2 E12 reference run, so no embedding or reranker call is new; the
`grounded_cite` instruction and the citation parser are unchanged. The `gpt-6-luna` arm is the
reference run itself and is served from cache.

## Judge

`gemini-3.6-flash` (minimal), the Season 2 judge, for OpenAI and Anthropic answer models.
Google answer models are judged by `claude-sonnet-5-5` (reasoning off), the S2 E2 and E3 judge,
which agreed with the S2 E3 hand marks. `claude-haiku-5-5` was tried first as a cheaper second
judge on S2's 50-item judge check (results in `judge-switch/`): with reasoning off it agreed with
the hand-checked judge on 40 of 50 declines, and at low on 44 of 50, both under the season's
pass mark of 45, so it was not used. Because two judges are in play, both judge one shared
sample of 100 items from the `gpt-6-luna` arm, and their agreement is reported. The code check
is reported beside the judge for every arm.

## Data

All 520 `halvard-v2` test items: 400 answerable, 120 unanswerable. Results go in
`results/2026-10/`, so a rerun at a later model release adds a folder.

**Pilot:** 2 test items of each type (32 items) per model, as every Season 2 pilot did, to check
calls, parsing and token use before the full run. This differs from the build handover, which
proposed the 100 dev items: the dev items' reranker calls are not in the cache, and Season 2's
pilots used test items. Pilot results are not used for any claim.

## Primary metric

**Items handled right, out of 520:** answerable items answered right (judged correct and
faithful) plus unanswerable items correctly declined. Each part is also reported separately
(out of 400 and 120), with citation validity, median latency, median output tokens and cost per
item handled right as a ratio to the cheapest model's.

## Analysis

- Rank models by the primary metric, with 95% Wilson intervals.
- Exact McNemar tests on all 28 pairs, per item, Holm corrected at 0.05. A **tier** is a set of
  models none of which is distinguishable from the best model in it.
- Kendall's tau-b between board scores and items handled right, with a 95% percentile bootstrap
  interval over items (2,000 resamples, seed 20261018).
- Count the pairs the board orders one way that are distinguishable the other way on Halvard.
- Report score gaps (points on the board, items on Halvard) as well as order.

## Claims

**B1. The board's order does not predict the Halvard order.**
*Pass mark:* the 95% bootstrap interval for Kendall's tau-b includes 0.

**B2. Within a provider, the board's top model is not distinguishable on Halvard from the
cheapest.** Families: OpenAI (`gpt-6.1-sol` against `gpt-6-luna`), Anthropic
(`claude-opus-5-5` against `claude-haiku-5-5`), Google (`gemini-3.8-flash` against
`gemini-3.5-flash-lite`).
*Pass mark:* in at least 2 of the 3 families, the Holm-corrected McNemar test does not separate
the two (p at or above 0.05).

**B3. Picking by the board costs several times more per item handled right.**
The board's top pick is the higher scorer on Halvard of its two models at 42. The best-value
pick is the cheapest per item handled right among the models in Halvard's top tier.
*Pass mark:* the top pick's cost per item handled right is at least 5 times the best-value
pick's. If the top pick is itself the best-value pick, B3 fails.

**B4. At least one pair is reversed.**
*Pass mark:* at least one pair the board orders one way (a gap of at least 5 points) is
distinguishable the other way on Halvard (Holm-corrected McNemar).

## Limits stated in advance

- One task, one system, one test set. Claims cover the Halvard task only; they say nothing
  about leaderboards in general.
- Lowest listed reasoning settings only.
- The board's score for each model was measured by its publisher at its own settings and
  harness; ours runs through the Season 2 prompt.
- Costs use the providers' published prices on 18 October 2026 and are reported as ratios only.
- Claude models count tokens differently from OpenAI's tokenizer; reported token counts are the
  providers' own.
