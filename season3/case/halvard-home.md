# Halvard Home: the Season 3 running case

**Halvard Home is invented.** It is the fictional appliance maker whose support library and test
set Season 2 built (`datasets/halvard/`, corpus `halvard-v2`). Every figure on this page is
invented for teaching and labelled as such. Nothing here describes a real company.

Season 3 reuses Halvard so that the case and the field notes share one set of data, and so that
readers who followed Season 2 already know the firm.

## The firm (invented)

| | Figure (invented) |
|---|---|
| What it sells | Ten home appliances, sold direct and through retailers in the UK |
| Products | Brio kettle, Tessa dishwasher, Orrin heat pump, Lumen smart thermostat, Keel washing machine, Ashby tumble dryer, Vale fridge freezer, Corra induction hob, Fenwick cooker hood, Mira robot vacuum |
| Cover plans | Extended Care and Extended Care Plus |
| Service regions | Eight, from Scotland North to the Island Areas |
| Customer contacts | About 45,000 a month: 55% phone, 35% chat and email, 10% web form |
| Support team | About 140 agents in two contact centres, plus a safety team of 6 and a content team of 4 |
| Warranty claims | About 3,200 a month |
| Returns | About 2,100 a month, of which about 400 ask for a refund outside the standard window |
| Contacts that may describe a fire, smoke or shock incident | About 40 a month |
| Support library | 4 customer policies (warranty, returns, safety and recalls, servicing), 300 support articles, 4 staff-only documents, and the superseded versions of each policy |
| Spare parts | About 1,800 part numbers, ordered monthly from 3 suppliers |

The library figures are real counts from `datasets/halvard/`; the rest are invented.

## Regulatory exposure

Halvard is not a financial firm. It is exposed to three areas of law, described here only at
this level. Nothing on this page is legal advice, and the season makes no specific legal claim.

- **Product safety.** Safety notices, recalls and the handling of incidents involving fire,
  smoke or electric shock. A missed or mishandled incident report is the most serious error the
  firm can make. The safety policy (`POL-SAF`) sets out how concerns are raised and handled.
- **Consumer protection.** Warranty and returns terms, and the accuracy of what customers are
  told about them. A customer told the wrong warranty period or refund right has been misled,
  whoever told them. The warranty (`POL-WAR`) and returns (`POL-RET`) policies set the terms.
- **Data protection.** Customer personal data in contacts, claims and orders, and the staff-only
  documents (`INT-*`) that must never reach a customer. Season 2's naive system put a staff-only
  passage into 51 of 480 public prompts before the E8 filter fixed it.

## The CEO's ask

At the October leadership meeting the CEO said:

> "We need an AI assistant on the website by spring."

The head of customer operations has been asked to take this away and come back with a plan. She
has asked a simple question first: of everything we could use AI for, what should we do first,
and how would we know it worked? Season 3 is the answer, built one episode at a time.

## What Halvard already has

- **A measured support system.** Season 2 built and measured a retrieval system over the support
  library. On the 520 test questions, the final system (`0294479ba987`) answered 354 of 400
  answerable questions right, declined 107 of 120 questions the library cannot answer, and put
  no staff-only passage into any of 480 public prompts. Source: `season2/scoreboard.json` and
  `field-notes/s2-e12-embedding-swap/results/baseline/summary.json`.
- **A library that partly contradicts itself.** Season 2 E14 traced the final system's failures
  and found that 3 of the 5 with the right passage in the prompt came from a support article and
  a policy giving different warranty periods. Source: `episodes/s2-e14-tracing/README.md`.
- **Records in systems of record.** Orders, returns, warranty claims and spare parts usage sit in
  the order system, the claims system and the parts system (invented). Season 3 does not model
  these systems; their existence is an assumption stated wherever a score relies on it.

## The eight candidates

The use cases Halvard is choosing between are in [`candidates.yaml`](candidates.yaml). The rule
that scores them, fixed before any score, is in [`rule.yaml`](rule.yaml). Why the order matters
is in [`PREREGISTRATION.md`](PREREGISTRATION.md).
