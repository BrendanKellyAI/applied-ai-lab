# S4 E1 pre-registration: the untuned baseline

Written before any E1 call and not edited after the run; any later change goes in a dated
amendment at the end. Every claim below is reported in `README.md` as Held or Failed, failures
included. The same pass marks are in `claims.yaml`, which `claims.py` applies.

## The question

How well does the cheapest model do both Season 4 tasks when it is told only what to do, in
one line? This is the floor every later rung is measured against, and the first row of the
season scoreboard. E1's argument is that behaviour gaps and knowledge gaps need different
fixes: here the model is given everything it needs to know (the message, or the correct
answer), so whatever it gets wrong is a gap in how it behaves.

## Setup

- **Data:** `datasets/halvard-tasks` (`halvard-tasks-v1`), all invented. Task A test 600
  items (66 safety items), Task B test 300 items (34 not found items). Dev is used only for
  the pilot. **The full runs wait until the test sets are frozen** (Brendan's hand checks,
  then `MANIFEST.json`); the pilot on dev can run before.
- **Answer model:** `gpt-6-luna`, reasoning off, no temperature sent; output limit 200
  tokens for Task A and 400 for Task B. Free text output (no JSON mode, no schema).
- **Task A prompt** (system; the user turn is `Customer message:` and the message):

  > Triage this customer message to Halvard Home, a UK appliance maker. Reply with one JSON
  > object and nothing else: {"route": one of [the 8 route names], "safety": true or false,
  > "product": one of [the 10 product names] or null, "fault": one of [the 12 fault names] or
  > null}

  The names are given; their definitions, the routing rules and the safety definition are
  not. Those are E2's rungs.
- **Task B prompt** (system; the user turn holds the question, the correct answer and its
  source, named plainly, for example `Warranty policy, section "Brio kettle: Cover period"`):

  > You write replies for Halvard Home, a UK appliance maker, to send to a customer. Use the
  > answer given, which is correct. Reply with the reply text only.

  The style guide is not given. That is E7's rung.
- **Scoring:**
  - **Task A**, by code against the label: fully right means route, safety, product and
    fault all correct; a reply with no valid JSON object is wrong on every field. Safety
    recall is flagged safety items out of all safety items.
  - **Task B:** the style guide's code checks (`src/lab/adapt/style.py`). Facts kept is
    judged by `gemini-3.6-flash` (reasoning minimal) for answerable items, with the same
    prompt that checked the data (the citation and the fixed safety sentence masked). For
    not found items, facts kept means using the fixed not found sentence, checked by code.
    The primary metric is passing every code check and keeping the facts.
  - **The facts judge is not yet checked** against a second judge or Brendan's marks; that
    check is in E7. Until then, C4's facts figure is reported with that caveat.
- **Intervals:** Wilson 95%. "Below" or "above" means the intervals do not overlap, unless a
  claim says point estimate.
- **Order:** estimate, then a pilot on the first 40 Task A and 20 Task B dev items, then,
  after the freeze, the full runs on test.
- **Pilot rule:** go on to the full runs unchanged if at least 90% of pilot replies are
  answered with no failed call, and no reply stops at its output limit. Any change to the
  config after the pilot is estimated again and approved again before the full run.

## Measures

- **Task A, primary:** fully right, out of 600.
- **Task A, reported:** safety recall (out of 66) and false alarms (out of 534), JSON
  validity, accuracy of each field, macro F1 over routes, fully right by hard-case kind,
  input and output tokens per call.
- **Task B, primary:** passing every code check and keeping the facts, out of 300.
- **Task B, reported:** each code check, facts kept, mean words, mean sentence length,
  tokens per call.

## Claims

**C1. A one-line prompt leaves room to improve on Task A.**

- *Pass mark:* the upper end of the 95% interval of fully right is below 85%.

**C2. The Task A gap is behaviour, not reading the message.** The product is named in the
message, so getting it right needs reading, not rules; routing needs Halvard's rules.

- *Pass mark:* product accuracy is at least 90%, and fully right is at least 15 points lower
  (point estimates).

**C3. A one-line prompt misses safety incidents.**

- *Pass mark:* safety recall is below 95% (point estimate).

**C4. On Task B the model keeps the facts but not the house style.**

- *Pass mark:* facts kept is at least 80% and passing every code check is at most 20% (point
  estimates).

## The scoreboard

E1 sets the first reference row for each task: the one-line arm is the reference until a
later rung clears the strict bar (its interval on the primary metric sits clear above the
reference's). `season4/scoreboard.json`, `reference.yaml` and `reference_history.yaml` are
written from E1's test results.

## What E1 cannot show

- One model, one prompt wording, one run: no claim about other models or wordings.
- The test sets were built with a blind label check by `claude-haiku-5-5`, which discarded
  items it labelled differently. Items that model found hard are under-represented, so these
  scores may be higher than on real messages.
- Everything is invented: the Halvard tasks only, not real support traffic.
