# One-page AI strategy: Halvard Home

Organisation: Halvard Home (invented)  Date: October 2026  Owner: Head of customer operations

The filled example for Season 3 E10, from the case in [`case/`](case/). Halvard Home and every
volume here are invented; the measured figures come from Season 2's support system.

## 1. Outcomes we want

- Customers get a correct answer to a policy or product question without waiting for an agent
  (metric: questions answered correctly with no agent contact in 7 days; owner: head of customer
  operations).
- Agents answer policy and product questions faster with no more mistakes (median handling
  time, quality review error rate held level; head of customer operations).
- No support article contradicts a current policy (share of the 300 articles consistent with
  the current policies; content team lead).
- Every contact describing a fire, smoke or shock incident reaches the safety team the same day
  (head of product safety).

## 2. Where we will use AI: now, next, later, not

Now: the library consistency check (C6).
Next: reply drafts for agents (C2), on the library C6 has cleaned.
Later: the website assistant (C1), only once it can run with review; warranty claim triage
(C3), bought; safety signal screening (C4), once enough confirmed incidents are labelled to
measure misses.
Not: automatic refund approval (C5: a rule over order records, so rules, not a model); spare
parts forecasting (C8: a forecasting model); building call summaries ourselves (C7: buy the
contact-centre feature if wanted).

## 3. How much we trust it

Assist everywhere a customer's rights or safety are at stake: a person reads every reply draft
(C2) and every safety flag (C4). The website assistant (C1) answers customers directly with
nobody checking, which our autonomy table does not allow for a regulatory error: the measured
system still answered 46 of 400 answerable questions wrongly and 13 of 120 unanswerable
questions anyway. The consistency check (C6) is low risk: an editor reads every flag.

## 4. What we own and what we rent

Own: the support library, its structure, version and access labels, and our test set of 520
questions. Build: C6 and C2 on that library. Rent: the models, and commodity features such as
call summaries (C7) and claim routing (C3). Model access: direct APIs for C6 (no personal data);
managed, inside our existing cloud account, for anything that reads customer contacts.

## 5. How we stay portable

Our 520-question test set and the code that scores it are ours: before accepting a new model or
a provider's update, we rerun it and compare item by item, not only the total. Prompts and
citation parsing are kept in our code, not a vendor's console.

## 6. How we will measure, and when we stop

C6 pilot: success is finding every contradiction already known (Mira robot vacuum, Fenwick
cooker hood, Vale fridge freezer) with at least half of its flags confirmed by an editor, within
six weeks. We stop if it misses a known contradiction after one round of changes, or fewer than
1 in 4 flags are confirmed; then we move to C2. Reviewer: content team lead, reporting to the
head of customer operations.

## 7. The first move

C6, the library consistency check: it scored highest under our rule (4.20 of 5, against 4.15
for C2). The pick is fragile: it holds in 9 of 15 other weightings, and C2 wins the other 6,
including the CEO's value-heavy weighting. Both lead to the same place: a clean library first,
then drafts for agents on top of it.

## 8. What we will not do

No unreviewed answers to customers on warranty, refunds or safety. No model deciding refunds.
No staff-only document in any prompt a customer could see. No AI project without an outcome
stated without the word AI.

## 9. What we ask of the board

Approve six weeks of the content team's time for the C6 pilot and a review in the next quarter;
accept that the website assistant (the spring ask) comes after reply drafts for agents, not
before; and agree the lines in section 8.
