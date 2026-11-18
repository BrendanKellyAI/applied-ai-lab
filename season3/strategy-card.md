# The Season 3 strategy card

Every decision rule and "Ask your team" question from Season 3 (AI strategy), on one card, with
the running case's result. Halvard Home is an invented firm; the case is in [`case/`](case/).

## The rules

| Episode | Decision rule | Ask your team |
|---|---|---|
| E1 Start with the problem, not the model | Write the outcome first, without the word AI. If you cannot name the metric that moves and who owns it, it is not a use case yet. | Which of our AI projects could we describe without the word AI? |
| E2 Which tasks suit an LLM | Use an LLM where the input is language and a good answer can be checked. Use rules, SQL or a forecasting model where the answer is a calculation, a record or a prediction. | For this proposal, how would we check that an answer is right? |
| E3 Field note: does the leaderboard predict your task? | Use a leaderboard to shortlist models, then choose on a test set of your own questions: on ours, the cheapest model tied the board's leaders at a fraction of the cost. | Which model would win on our own questions, and have we tested it? |
| E4 The cost of being wrong | Price the error before the use case: decide who catches a wrong answer and what it costs when they miss. Treat a regulatory error as a design constraint, not a risk to accept. | When this is wrong, who finds out first, us or the customer? |
| E5 Assist, automate, or act | Give AI the autonomy its error cost allows: assist where errors are costly or regulated, automate where they are cheap and caught, and act only where they can be reversed. | What would have to be true before we let this run without review? |
| E6 Your data is the strategy | Invest where the advantage outlasts the next model: your data, how it is structured and labelled, and your workflow. Do not build what the next model release will give away. | What would a competitor with the same model still not have? |
| E7 Field note: better data or a bigger model? | Fix your documents and retrieval before you buy a bigger model: on our test, structure and metadata gave more than the bigger model did, at a twentieth of the price per token. | Before we pay for a bigger model, what would the same money do to our documents and retrieval? |
| E8 Build, buy, or managed | Own the layer that sets you apart and rent the rest. Choose model access by where your data may go, and keep the model swappable. | If our model provider doubled its price tomorrow, what would it take to move? |
| E9 Field note: does it survive a model change? | Treat a model change as a release: rerun your own test set and compare answers question by question, because a steady total can hide changed answers. | If our provider changed the model tomorrow, how would we know which answers changed? |
| E10 The one-page AI strategy | Put the strategy on one page: the outcomes, where AI will and will not be used, how much it is trusted, what you own, and the first move with its stop condition. | Could our board read our AI strategy in two minutes and know what we will not do? |
| E11 Which use case goes first? | Start with the use case that scores best under rules fixed in advance, and write the stop condition before the pilot starts. | What result would make us stop this pilot, and have we written it down? |

## The case, from first column to first pick

Eight candidate use cases, scored against a rule fixed before any score
([`case/rule.yaml`](case/rule.yaml)): two gates, six criteria scored 1 to 5, autonomy and
sourcing as settings, and weights that sum to 1.

| | Candidate | Gates | Autonomy (proposed) | Total (of 5) | Rank |
|---|---|---|---|---|---|
| C6 | Library consistency check | pass | assist | 4.20 | 1 |
| C2 | Reply drafts for agents | pass | assist | 4.15 | 2 |
| C1 | Website assistant (the CEO's ask) | pass | automate, above what the table allows | 3.70 | 3 |
| C3 | Warranty claim triage | pass | automate | 3.35 | 4 |
| C4 | Safety signal screening | pass | assist | 3.20 | 5 |
| C7 | Call and chat summaries | pass | automate | 3.00 | 6 |
| C5 | Automatic refund approval | fails G2: rules over order records | act, above the table | | |
| C8 | Spare parts demand forecast | fails G2: a forecasting model | assist | | |

Source: [`case/results/scorecard.json`](case/results/scorecard.json); chart
`case/results/charts/scorecard-final-slide.svg`.

**The first pick is C6, and it is fragile.** It holds in 9 of 15 alternative weightings; reply
drafts for agents (C2) goes first in the other 6, including the CEO's value-heavy weighting
([`case/results/sensitivity.json`](case/results/sensitivity.json)). Both point the same way: a
clean library first, then drafts for agents built on it.

**Where the CEO's ask ended up.** The website assistant is third. It is the same measured system
as C2 (354 of 400 answerable questions answered right; 107 of 120 unanswerable questions
declined), but it would answer customers on warranty, refunds and safety with nobody checking,
so it scores 1 of 5 on error tolerance.

## The first pick's stop criteria, written before the pilot

| | |
|---|---|
| Success metric | Contradictions found between support articles and current policies, confirmed by the content team, and the share of the 300 articles checked consistent |
| Threshold | Finds every contradiction already known (Mira robot vacuum, Fenwick cooker hood, Vale fridge freezer); at least half of its flags confirmed by an editor |
| Time box | Six weeks from the first run over the library |
| Stop condition | Misses any known contradiction after one round of changes to its instructions, or fewer than 1 in 4 flags confirmed; then move to C2 |
| Reviewer | Content team lead, reporting to the head of customer operations |

## What the three field notes changed

- **E3, the leaderboard.** Eight models spread from 18 to 42 points on a public board: five of
  them, from the bottom of the board to the top, handled 457 to 465 of 520 Halvard questions
  right and cannot be told apart; the cheapest tied the leaders at about a twentieth of the
  cost per item. The case's task fit and value scores do not depend on buying the top model.
  ([`field-notes/s3-e3-leaderboard`](../field-notes/s3-e3-leaderboard/))
- **E7, better data or a bigger model.** Section structure and metadata filters took the small
  model from 295 to 399 of 520; the full system reached 461, while the large model on the naive
  system reached 303. This is the evidence behind the durable advantage column, and behind C6
  going first: the library is where the gains are.
  ([`field-notes/s3-e7-data-or-model`](../field-notes/s3-e7-data-or-model/))
- **E9, a model change.** A version update left the total at 461 of 520 while 18 answers
  changed; a provider switch changed 25. Keeping the model swappable (E8) means owning the test
  set that measures a swap, item by item.
  ([`field-notes/s3-e9-model-change`](../field-notes/s3-e9-model-change/))

## Where the series goes next

Money (costs, total cost of ownership, self-hosting break-even) goes to Season 6; teams and the
operating model to Season 9; rollout and adoption to Season 12; policy and controls to Season 15.
