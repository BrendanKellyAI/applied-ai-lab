# Season 3: AI strategy

Where AI earns its place, and choices that outlast the next model release.

Season 3 is the first leadership season. Most episodes teach a decision rather than run an
experiment. The evidence behind them is here: a running case scored one column per episode,
three field notes with open code, and three tools readers can use on their own use cases.

## The running case: Halvard Home (invented)

Halvard Home is the invented appliance maker whose support library Season 2 built. Its CEO has
said: "We need an AI assistant on the website by spring." Season 3 asks which of eight candidate
use cases should go first, under a rule fixed before any score.

| File | What it holds |
|---|---|
| [`case/halvard-home.md`](case/halvard-home.md) | The firm, its regulatory exposure and the CEO's ask |
| [`case/candidates.yaml`](case/candidates.yaml) | The eight use cases and their facts |
| [`case/rule.yaml`](case/rule.yaml) | Gates, criteria with anchors, weights, the autonomy table and sourcing settings |
| [`case/PREREGISTRATION.md`](case/PREREGISTRATION.md) | What was fixed before scoring, the Gate 1 decisions and the amendment log |
| [`case/scores.yaml`](case/scores.yaml) | Every score, each citing a measured result or a stated assumption, and the first pick's stop criteria |
| [`case/results/`](case/results/) | The scorecard (CSV and JSON), the sensitivity check, one scorecard per episode and the slide charts |

**Result:** the library consistency check (C6) scores highest, 4.20 of 5, just ahead of reply
drafts for agents (C2), 4.15. The pick is fragile: it holds in 9 of 15 alternative weightings,
and C2 goes first in the other 6, including the CEO's value-heavy weighting. The website
assistant (C1), the CEO's ask, is third: its error tolerance scores 1, because it would answer
customers on warranty, refunds and safety with nobody checking.

Rebuild every case result, with no key and no call:

```bash
uv run lab strategy case
```

Show the scorecard as it stood after any episode, for its recap slide:

```bash
uv run lab strategy reveal --through E5
```

## The tools

| Tool | File |
|---|---|
| Scorecard template, scored by `lab strategy score` | [`templates/scorecard.csv`](templates/scorecard.csv) |
| Scorecard guide: the rule in plain English, with a worked row | [`templates/scorecard-guide.md`](templates/scorecard-guide.md) |
| One-page AI strategy template | [`templates/one-page-strategy.md`](templates/one-page-strategy.md) |
| Halvard's one page, filled in (E10) | [`halvard-one-page.md`](halvard-one-page.md) |
| The strategy card: every decision rule and question (E12) | [`strategy-card.md`](strategy-card.md) |

Score your own use cases:

```bash
uv run lab strategy score season3/templates/scorecard.csv
```

## The field notes

| Episode | Question | Folder |
|---|---|---|
| S3 E3 | Does the leaderboard predict your task? | [`field-notes/s3-e3-leaderboard`](../field-notes/s3-e3-leaderboard/) |
| S3 E7 | Better data or a bigger model? | [`field-notes/s3-e7-data-or-model`](../field-notes/s3-e7-data-or-model/) |
| S3 E9 | Does it survive a model change? | [`field-notes/s3-e9-model-change`](../field-notes/s3-e9-model-change/) |

All three run on the Season 2 reference system and the 520 Halvard test questions, with only
the answer model or the pipeline changing.

## The episodes

| Act | Episode | Title |
|---|---|---|
| Choose the work | E1 | Start with the problem, not the model |
| | E2 | Which tasks suit an LLM |
| | E3 | Field note: does the leaderboard predict your task? |
| Set the trust | E4 | The cost of being wrong |
| | E5 | Assist, automate, or act |
| Decide what to own | E6 | Your data is the strategy |
| | E7 | Field note: better data or a bigger model? |
| | E8 | Build, buy, or managed |
| | E9 | Field note: does it survive a model change? |
| Commit | E10 | The one-page AI strategy |
| | E11 | Which use case goes first? |

E0 introduces the season and E12 recaps it. Each episode's deck handover is in
[`deck-handovers/`](deck-handovers/); the field notes keep theirs in their own folders.

Nothing in Season 3 is legal advice. Regulatory exposure is described only as consumer
protection, product safety and data protection law.
