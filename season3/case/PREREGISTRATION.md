# Season 3 case pre-registration: which use case goes first?

Written before any score. `rule.yaml` and `candidates.yaml` are committed with this file and
precede `scores.yaml` in the history. Halvard Home is invented.

## The question

Of eight candidate AI use cases at Halvard Home, which should go first, and does that choice
hold when the weights change?

## What is fixed here, before scoring

- **The candidates** (`candidates.yaml`): eight use cases, each with its outcome stated without
  the word AI, a metric, an owner, volume, user, the consequence of a wrong output and who
  catches it, the data it needs and whether that exists, and whether a vendor already sells it.
- **The rule** (`rule.yaml`):
  - two gates: G1 outcome (E1) and G2 right tool (E2);
  - six criteria scored 1 to 5 against written anchors for 1, 3 and 5: value (E1), task fit
    (E2), error tolerance at the chosen autonomy (E4), data readiness (E6), durable advantage
    (E6) and time to evidence (E11);
  - the weights: value 0.25, task fit 0.15, error tolerance 0.20, data readiness 0.15, durable
    advantage 0.10, time to evidence 0.15;
  - the autonomy table (E5) and the sourcing settings (E8), which are settings, not scores;
  - the sensitivity weightings: equal, each weight halved, each weight doubled, a CEO weighting
    (value heavy) and a regulator weighting (error heavy): 15 alternatives in all.

## How scores will be written

Every score in `scores.yaml` cites either a measured result (a file path and the figure) or a
stated assumption (written as an assumption, with a one-line reason). Only C1 and C2 have
measured accuracy, from the Season 2 final system; no other candidate is given a
measured-looking number.

Error tolerance is scored at each candidate's design autonomy. A candidate proposed at a higher
autonomy than the table allows scores 1 on error tolerance, as the anchor says.

## How the first pick is chosen

The first pick is the candidate with the highest weighted total among those that pass both
gates. A tie is broken by error tolerance, then time to evidence.

## Sensitivity, reported whatever it shows

The first pick is recomputed under each of the 15 alternative weightings. Reported: the pick
under each, and the share of the 15 in which the first pick holds. If it holds in fewer than
12 of 15 (80%), the pick is called fragile in every write-up. That is a finding, not a failure.

## Stop criteria

Before the first pick's fictional pilot starts, `scores.yaml` records its success metric,
threshold, time box, stop condition and reviewer.

## Amendments

After totals exist, any changed score or weight is recorded below with its date, the reason,
and the value before and after. Nothing above is edited.

## Decisions taken at Gate 1

Brendan delegated Gate 1 on 18 October 2026 ("make whatever decisions you need"). These follow
the build handover's recommendations and are listed for his review:

1. **The running case firm.** Halvard Home is kept. It is exposed to product safety, consumer
   protection and data protection law rather than financial regulation; shared data with
   Season 2 was judged worth more than a stricter regulator.
2. **The candidate list.** The eight proposed candidates are used as proposed.
3. **Time to evidence (E11).** Added as the sixth criterion, introduced in E11.
4. **Weights.** As above. Value carries most weight because a use case that moves nothing is
   not worth doing; error tolerance next, because Halvard's exposure is regulatory.
