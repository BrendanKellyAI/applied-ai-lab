# S4 E1: The untuned baseline

How well does the cheapest model do both Season 4 tasks when it is told only what to do, in one
line? This is the floor every later rung is measured against. Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md), with two dated amendments.

**Result: the one-line prompt is a high floor on triage and no floor at all on house style.**
On Task A it got 521 of 600 messages fully right (84% to 89%) and caught every safety incident,
but flagged 68 of 535 harmless messages as incidents. On Task B none of 300 replies passed the
house style checks, though 262 kept the facts. Three of the four claims failed, all because the
baseline was stronger than predicted.

## The design

- **Data:** `datasets/halvard-tasks`, frozen on 23 November 2026 after Brendan's hand checks.
  Task A test 600 items (65 safety); Task B test 300 items (34 not found). All invented.
- **Answer model:** `gpt-6-luna`, reasoning off, free text output. Output limit 200 tokens for
  Task A, 400 for Task B.
- **Task A prompt:** reply with one JSON object holding route, safety, product and fault, with
  the allowed names listed but not defined.
- **Task B prompt:** write the reply to the customer, using the correct answer given. No style
  guide.
- **Scoring:** Task A by code against the labels; fully right means all four fields correct.
  Task B by the style guide's code checks, and facts kept judged by `gemini-3.6-flash`.
- **Before the freeze:** the dev headroom check (Amendment 1) found Task A too easy (183 of 200),
  so Task A was rebuilt once with four more hard cases and kept as rebuilt (Amendment 2).

## Results

### Task A, triage (600 items)

| Measure | Result |
|---|---|
| **Fully right** | **521** (84% to 89%) |
| Product right | 600 |
| Route right | 592 |
| Fault right | 585 |
| Safety flag right | 532 |
| Safety recall | 65 of 65 |
| False safety alarms | 68 of 535 (10% to 16%) |
| Valid JSON | 600 |

Almost every miss is a judgement about Halvard's rules, not about reading the message. The worst
hard case was `safe_use_question` (a customer asking whether something is safe, with no incident):
6 of 40 fully right, because the model flags the question as an incident. `harmless_safety_word`
(a heat or fire word with no incident) was next, at 50 of 62.

On dev the same arm got 170 of 200 (85%).

### Task B, house style replies (300 items)

| Measure | Result |
|---|---|
| **Passes every check and keeps the facts** | **0** (0% to 1.3%) |
| Facts kept | 262 (83% to 91%) |
| Opening line as the guide sets it | 0 |
| Sign-off as the guide sets it | 0 |
| Within the length limit | 66 |
| Cites the policy | 34 |
| British spelling | 300 |
| No banned phrases | 298 |

Mean reply: 27 words. The model writes a short, correct, polite reply, and none of Halvard's
house rules, because it has never been told them.

## The claims

**C1 failed: a one-line prompt leaves room to improve on Task A.** The pass mark was an interval
below 85%; the interval reaches 89%. There is still room (79 items), but less than predicted.

**C2 failed: the Task A gap is behaviour, not reading the message.** Product accuracy was 100%,
as predicted, but fully right was 13 points lower, not the 15 the pass mark asked for. The
direction held: the model read every product correctly and lost items on Halvard's rules. On dev
the gap was 15 points and the claim held; on test it fell short.

**C3 failed: a one-line prompt misses safety incidents.** It missed none (65 of 65). Its error
runs the other way: it flags too much, 68 false alarms.

**C4 held: on Task B the model keeps the facts but not the house style.** Facts kept 87%, every
check passed 0%. The facts judge is not yet checked against a second judge; that is in E7.

## The scoreboard

E1 sets the first row for each task: `a-one-line` (521 of 600) and `b-one-line` (0 of 300) are
the references (`season4/reference.yaml`). E2's definitions replace the Task A reference.

## What this does not show

- One model, one wording, one run.
- **The test sets favour items the blind labeller found easy.** `claude-haiku-5-5` checked every
  label and disagreements were discarded, most of them `unknown_product` items (54 discarded, 8
  kept). Real messages may be harder.
- The facts judge has not yet been checked.
- Everything is invented: no real support traffic.

## Charts

`results/charts/`: **`fully_right`** (Task A) and **`primary`** (Task B), dev and test, each as
a slide (SVG and PNG) and an article image.

## Cost

Costs are ratios only. Task A used about 300 input tokens and 27 output tokens per call; Task B
about 125 and 37, plus one judge call per answerable item, which costs more than the answer.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e1-baseline/config-a.yaml
uv run lab adapt analyse episodes/s4-e1-baseline/config-b.yaml
uv run python episodes/s4-e1-baseline/claims.py test
```

To call the models again (every reply is cached, so a rerun is free):

```bash
uv run lab adapt run episodes/s4-e1-baseline/config-a.yaml
uv run lab adapt run episodes/s4-e1-baseline/config-b.yaml
```
