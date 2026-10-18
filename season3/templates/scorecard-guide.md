# Scorecard guide

This guide explains how to fill in `scorecard.csv` and what the scoring tool does with it. It uses Halvard Home, an invented firm, as the worked example. Every Halvard figure here is invented, except where it says it was measured in Season 2 of this series.

The idea: fix the rule before you score anything, then let the rule rank the use cases. That way the ranking is not a case of the loudest person in the room winning.

## What each column means

| Column | What goes in it |
|---|---|
| `id`, `name` | A short label and a plain name. The only two columns that must be filled. |
| `outcome` | The result you want, written without the words AI or model. |
| `metric` | How you will know the outcome moved. |
| `owner` | The person accountable for that metric. |
| `gate_outcome` | `pass` or `fail` for Gate 1. |
| `gate_right_tool` | `pass` or `fail` for Gate 2. |
| `redirect` | If a gate failed: what to use instead (rules, a database query, a forecasting model, a bought product). |
| `error_cost` | `low`, `high` or `regulatory`: the worst ordinary result of a wrong output. |
| `caught` | `reviewer`, `downstream` or `nobody`: who stops a wrong output before harm. |
| `reversible` | `yes` or `no`: can a wrong output be fully undone afterwards. |
| `design_autonomy` | The autonomy you propose: `assist`, `automate` or `act`. |
| `value` to `time_to_evidence` | Six scores, each a whole number from 1 to 5. |
| `application` | `build`, `buy` or `none`. |
| `model_access` | `direct`, `managed`, `self_hosted`, `vendor` or `none`. |
| `notes` | The evidence for your scores, and any assumption, labelled as one. |

A blank cell means "not decided yet". A use case with any blank score gets no total.

## The two gates

A use case must pass both gates before it is scored. A failed gate is not a bad idea, it is a redirect.

- **G1 Outcome.** Can the outcome be stated without the word AI, with a metric and an owner? If not, it is not a use case yet. Write the outcome first.
- **G2 Right tool.** Is a language model the right tool? The input must be language, and a good output must be checkable. If not, redirect to rules, a database query, a forecasting model or a bought product, and record which in `redirect`.

## The six criteria

Score each from 1 to 5. The anchors below are for 1, 3 and 5. Use 2 and 4 for in between.

**Value of the outcome** (`value`)
- 1: The outcome is minor; few people or little money are affected, and no one senior would notice it move.
- 3: It moves a metric one team tracks, by enough to be worth a quarter of that team's effort.
- 5: It moves a metric the leadership tracks, for customers at large or for a major risk.

**Task fit** (`task_fit`)
- 1: The answer is a calculation, a record or a prediction; a rule, a query or a forecasting model does it better.
- 3: The input is language, but whether an output is right is slow or hard to check.
- 5: The input is language, and a right output can be checked quickly against a source.

**Error tolerance at the chosen autonomy** (`error_tolerance`)
- 1: A wrong output with regulatory or high cost reaches a customer or a live system and nobody catches it, or the design autonomy is above what the autonomy table allows.
- 3: Wrong outputs are costly but are caught before harm by a reviewer or a downstream check, or are cheap and go uncaught.
- 5: Wrong outputs are cheap, a person sees each one before it reaches anyone, and they are easily undone.

**Data readiness** (`data_readiness`)
- 1: The data does not exist, or may not be used for this purpose.
- 3: The data exists but needs labelling, cleaning or access work before a pilot can start.
- 5: The data exists, is labelled and access controlled, and a system has already been measured on it.

**Durable advantage** (`durable_advantage`). Would the next model release or a vendor give it away?
- 1: A vendor product or the next model release gives the same thing to every competitor.
- 3: Partly bought, but how well it works depends on your own data or workflow.
- 5: It is built on data, structure or workflow only you have, and it improves them.

**Time to evidence** (`time_to_evidence`). Can a pilot show the outcome moving within a quarter?
- 1: No result could show the outcome moving within a year.
- 3: A pilot could show the outcome moving within two quarters.
- 5: A pilot could show the outcome moving within a quarter, or it can be tested on past data now.

## Autonomy: a setting, not a score

Autonomy is how much the system does without a person. There are three levels.

- **Assist:** a person reviews every output before it is used.
- **Automate:** outputs go out unreviewed, and a sample is checked.
- **Act:** the system changes a live system, such as a payment or an order, itself.

The table gives the highest autonomy allowed, from the cost of a wrong output (rows) and who catches it (columns).

| Error cost | Caught by a reviewer | Caught downstream | Caught by nobody |
|---|---|---|---|
| Low | automate | automate | automate |
| High | assist | automate | assist |
| Regulatory | assist | assist | assist |

Act is allowed only where the table allows automate and a wrong output can be fully reversed. If your design autonomy is above what the table allows, score error tolerance 1.

Error cost means: **low**, a wrong output wastes some time and harms no one; **high**, it costs money or a customer's goodwill, or delays them; **regulatory**, it could mislead a customer about their rights, miss a safety risk or expose personal data.

## Sourcing: also a setting, not a score

Record two choices.

- **Application:** `build` (you build and run it on your own data and workflow), `buy` (you buy a product that does the job and configure it), or `none` (a gate redirected it, so there is no language model application).
- **Model access:** `direct` (call each model maker's own API); `managed` (call models through a cloud platform's managed service, inside your existing cloud account, for example Amazon Bedrock); `self_hosted` (run open-weight models on infrastructure you control); `vendor` (whatever the bought product uses); or `none`.

## Choosing weights

The weights say how much each criterion counts in the total. They sum to 1, so a total is on the same 1 to 5 scale as a score. Halvard's are in `season3/case/rule.yaml`.

Fix them before you score anything, and write them down. If you pick weights after seeing the totals, you are choosing the answer.

## Why run the sensitivity check

Weights are a judgement, and a fair person could choose differently. The check recomputes the first pick under 15 other weightings: equal weights, a chief executive's view, a regulator's view, and each weight halved and then doubled in turn.

For Halvard, the first pick was C6 (Library consistency check). It stayed first in 9 of the 15 alternative weightings. In the other 6, C2 (Reply drafts for agents) came first. So the pick is fragile. That is a finding, not a failure: it tells the board that the top two are close, and that the choice between them rests on what the board values most.

## How to run it

Install once, then score your file:

```
uv sync
uv run lab strategy score season3/templates/scorecard.csv
```

To use your own weights, copy `season3/case/rule.yaml`, edit the `weights` (they must sum to 1), and point at the copy:

```
uv run lab strategy score my-scorecard.csv --rule my-rule.yaml
```

Add `--out some-folder` to also write the results as JSON. The command needs no API key and makes no model call.

## Worked row: Halvard C2, Reply drafts for agents

Halvard Home is invented. The example row in `scorecard.csv` is this one.

- **Outcome, metric, owner:** agents answer policy and product questions faster without more mistakes; median handling time with the quality review error rate held level; Head of customer operations. Gate 1 passes.
- **Gate 2:** passes. Language goes in, and an agent can check a draft against the passages it cites.
- **Error cost, caught, reversible:** regulatory, reviewer, no. A wrong draft could mislead a customer about their rights, an agent reads every draft first, and a sent reply cannot be unsent. The table allows assist only, and the design is assist.
- **Value 4 (assumption):** handling time on about 9,000 contacts a month is an operations metric the leadership sees, but it is not the chief executive's own ask. The 9,000 is invented.
- **Task fit 5 (measured):** the Season 2 final system answered 354 of 400 answerable test questions right, each checked against its source passage.
- **Error tolerance 3 (measured):** the same system answered 46 of 400 answerable questions wrongly, so 46 of 400 drafts would be wrong and the agent must catch about 1 in 9 before sending. Regulatory cost caught by a reviewer is the anchor for 3. The risk is an agent who stops reading the drafts.
- **Data readiness 5 (measured):** the library is labelled and access controlled, and the same system put 0 staff-only passages into 480 public test prompts.
- **Durable advantage 3 (assumption):** agent assist is a feature of contact-centre products; how well it works depends on Halvard's library.
- **Time to evidence 5 (assumption):** the system is already measured on past data, and a pilot with one team of agents would show handling time within a quarter.
- **Sourcing:** build, managed. The library is Halvard's own, and contacts carry personal data, so models are called inside the firm's existing cloud account.

Notice the habit: each score has its evidence, and an assumption is labelled as an assumption. Only figures that were measured are given as figures, and each says what it counts and out of how many.
