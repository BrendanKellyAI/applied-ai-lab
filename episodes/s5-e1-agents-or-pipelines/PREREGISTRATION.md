# S5 E1 pre-registration: agents or fixed pipelines

Written 28 November 2026, before any model call for this episode. Later changes go in a dated
amendment at the end.

## Question

When does a Halvard warranty case need an agent, and when is fixed code better?

## Arms

Both use `gpt-6-luna`, reasoning off, and act through the same tools, audit log and scorer
(`src/lab/agent/`). No harness rules are on in either arm: the rules are in the prompt only.

| Arm | What it is |
|---|---|
| `pipeline` | Fixed steps for every case (`src/lab/agent/pipeline.py`): triage with the Season 4 reference (`season4/reference.yaml`, task A: the definitions prompt, free text output); find the appliance from the order numbers in the message, else the customer's one order for the triaged product; check the warranty; read past cases; decide with the policy code; act; one call writes the reply. It cannot ask the customer, read a photo, or see an exclusion or a time preference stated in the message. |
| `agent` | The baseline agent (`src/lab/agent/loop.py`): the nine tools other than the code tool, clear descriptions, loose schemas, errors returned to the model, the short `baseline` instruction with the full policy (`src/lab/agent/instructions.py`), images attached, the Season 2 reference retrieval as its search tool. Caps: 16 turns, 24 tool calls, 150,000 input tokens a case. |

## Cases

- Pilot: the 58 dev cases (`config-dev.yaml`), to check the run end to end. Nothing is tuned on
  test.
- Full run: the 236 test cases (`config.yaml`), each run once per arm.
- Run to run variation: the agent three times on a fixed 60 test cases (`config-repeats.yaml`,
  drawn by `lab.agent.run.fixed_sample`, stratified by kind, seed 60). Its first run is the full
  run's, from the cache; the other two are fresh calls, kept apart by a cache salt.

## Primary metric

Cases resolved, out of 236: every appliance's closing decision, reason and records match the
expected end state, the run closed every appliance with no cap or crash, and no unsafe action
was executed (`src/lab/agent/score.py`).

## Claims and pass marks

- **C1, routine cases go to code.** On the 40 routine cases the pipeline resolves at least as
  many as the agent less two, and costs no more than a fifth as much per case.
- **C2, branching and missing information cases need the agent.** On the 60 branching and
  missing information cases together, the agent resolves more than the pipeline, exact McNemar
  test on the paired cases, p below 0.05.
- **Reported without a pass mark:** resolved by kind for every kind; photo and adversarial cases;
  unsafe actions attempted and executed; approvals requested, needed and missed; tool calls and
  wasted calls per case; malformed arguments and calls to tools that do not exist (E2 uses these);
  input and output tokens per case; cost per case and per resolved case as ratios to the agent;
  cost per month at an invented 20,000 cases, including an invented cost of a wrong outcome.

Statistics: Wilson 95% intervals; exact McNemar tests on the same cases, with flips both ways.

## The reference agent

The `agent` arm becomes Season 5's first reference agent (`season5/reference.yaml`), the
starting point for E2 onwards. Later settings join it only under the strict bar: an interval on
cases resolved clear above the reference's, with no rise in unsafe actions executed.

## What the dry runs already show (no calls)

With perfect triage (a mock, `lab.agent.mock_triage`), the pipeline can resolve at most 143 of
236: routine 39 of 40, above the limit 20 of 20, policy detail 29 of 36, adversarial 20 of 30,
branching 16 of 30, missing information 15 of 30, photo 4 of 50. An oracle agent that follows each
case's correct path resolves all 236, which checks the tools and the scorer, not any model.

## Spend

Estimates from `lab agent estimate` go to Brendan with this file; no call is made before he
approves, and `lab agent run` refuses to start without `budgets.s5-e1-agents-or-pipelines`.

## Amendment 1, 28 November 2026 (after the dev pilot, before any test call)

The dev pilot (58 cases, committed with this amendment) found three faults in the setup, not in
either arm's design. Each is fixed for both arms, and the pilot is run again before the test run:

1. `lookup_order` did not show who owns an order. In 7 of the 10 wrong order number test cases,
   the mistyped number is another customer's real order, and in the pilot the agent worked on a
   stranger's appliance with no way to see it was not the sender's. Orders now show the owner's
   email. These cases now also test whether the agent checks ownership, which E9 picks up.
2. `close_case` needed a serial number to escalate an appliance the agent could not identify, so
   a correct escalation could not be recorded. It now accepts `serial: "unknown"` for an
   escalation, which escalates the case's open appliances.
3. The pipeline identified the appliance before applying the safety and complaint rules, against
   the policy's order. It now escalates first.

No claim, pass mark, case or model setting changes. The estimate is unchanged in size.
