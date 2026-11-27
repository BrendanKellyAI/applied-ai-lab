# S4 E4 deck handover: Making output a contract

For the content agent. Has an experiment: the same prompt with free text, the provider's JSON
mode, and a strict schema, on Task A.

## Sources of truth

- `episodes/s4-e4-making-output-a-contract/README.md` and `PREREGISTRATION.md` (with Amendments
  1 and 2).
- `results/analysis-task-a-test.json` and `analysis-task-a-dev.json`; `results/claims-test.json`.
- Chart: `results/charts/s4-e4-making-output-a-contract-fully_right-test-slide.svg`.
- The schema: `triage_schema` in `src/lab/adapt/output.py`; the parser every arm shares:
  `parse_triage` in the same file.
- The JSON mode fix: `build_params` in `src/lab/providers/openai_provider.py` (Amendment 2).
- `season4/scoreboard.json`, `season4/reference.yaml`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E4 |
| Title | Making output a contract |
| Hub slug | `making-output-a-contract` (as on the hub) |
| Deck file | `bk-s4-e4-making-output-a-contract-v1.pdf` |
| Hub format | `explainer` |

## The argument

When code reads a model's answer, a reply that is not in the agreed format breaks the system,
not just the answer. Providers offer two ways to enforce the format: JSON mode (the reply must be
valid JSON) and a schema (the reply must have exactly these fields, with only these values).

The test asked two things: does enforcing the format make the output safer to read, and does it
change the answers? Here the format was never the problem: free text was already valid on all
600 messages, and so were both enforced arms. Accuracy did not move (593, 594, 593). A schema is
cheap insurance for the day the model or the prompt changes, and the code should still check
every reply.

## Scoreboard slide

Task A ladder. Chart: `s4-e4-making-output-a-contract-fully_right-test-slide.svg`.

| Rung | Fully right, of 600 | Joined? |
|---|---|---|
| E1 one-line prompt | 521 (84% to 89%) | The baseline |
| E2 + definitions | 587 (96% to 99%) | Joined: the reference |
| E3 one-line + 8 similar examples | 593 (98% to 99%) | No |
| **E4 the same, with JSON mode** | **594 (98% to 100%)** | **No: overlaps the reference** |

What this episode adds: a guarantee about the format, at no cost in accuracy. The Task A
reference stays the definitions prompt, which is also the arm E5's tuned model must beat.

## Setup before results

Same model (`gpt-6-luna`, reasoning off) and messages; the prompt and examples are E3's best
(the one-line prompt with the 8 similar examples). Only the output setting changes:

| Arm | What the provider is asked to do |
|---|---|
| Free text | Nothing: the prompt asks for JSON, and the model may or may not comply |
| JSON mode | Return valid JSON, with any fields |
| Schema | Return exactly these four fields, each from its allowed list |

**The schema**, simplified for the slide (the full lists are in `routes.yaml`):

> route: one of the 8 route names
> safety: true or false
> product: one of the 10 product names, or null
> fault: one of the 12 fault names, or null
> All four required; no other fields.

**The same checker reads every arm's reply.** A reply that is not one JSON object with four
allowed values is invalid, and counts as wrong on every field.

**Worked example** (`A-test-00410`, invented): the kettle question. All three arms return the
same, correct answer, `{"route": "how_to_use", "safety": false, "product": "Brio kettle",
"fault": null}`. That is the episode in one item: the format setting changed nothing because the
answer was already well formed.

**A failure worth one slide:** the first JSON mode run was rejected on every call, at no charge.
OpenAI's JSON mode requires the word "json" in the conversation, and the prompt had been sent in
a field the check does not read. The fix sent the same words as a message instead (Amendment 2).
Enforced formats have their own rules to learn.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 600, 600, 600 of 600 | Valid replies: free text, JSON mode, schema | `analysis-task-a-test.json`, `arms.*.json_valid` |
| 593, 594, 593 of 600 | Fully right, same order | same, `fully_right` |
| 3 and 2 | Items JSON mode fixed and broke against free text | same, `comparisons.e4-json-mode` |
| 2 and 2 | Items the schema fixed and broke | same, `comparisons.e4-schema` |
| 1.0 | Holm-corrected exact McNemar p, both arms against free text | same, `p_holm` |
| 65 of 65; 3 of 535 | Incidents flagged; false alarms, every arm | same, `safety_recall`, `safety_false_alarms` |
| 27.3, 30.3, 31.3 | Output tokens per reply, same order | same, `tokens.mean_output_tokens` |
| 600 of 600 | Free text replies valid in E1, with no examples | `episodes/s4-e1-baseline/results/analysis-task-a-test.json` |

## Cost

Ratios to free text, answer calls only.

| Arm | Prompt length | Billed per item |
|---|---|---|
| JSON mode | the same | 0.24 times |
| Schema | 1.14 times (about 180 more tokens) | 1.14 times |

The schema is sent with every call, and replies are about 4 tokens longer. JSON mode's low ratio
is caching, not the format: it ran shortly after the free text run with the same prompts, and
about 94% of its input was billed at the cached rate. In steady use the three cost about the
same.

**The cost of a wrong format** is the point of the episode even though none happened here: an
invalid reply is a message nobody routes. At 0 in 600 for every arm, this model and prompt do
not need the guarantee; a different model, a shorter prompt or a provider change might.

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **Code reads the answer.** A diagram: message, model, reply, the routing system. A reply that
   is not JSON stops at the arrow.
2. **Three settings.** Free text, JSON mode, schema, as three increasingly strict boxes around
   the reply.
3. **The schema on one slide,** in plain words.
4. **The kettle message, three ways.** The same reply three times.
5. **Prediction.** "Without any enforcement, how many of 600 replies are broken?" Reader picks.
6. **Reveal.** 0. And 0 in E1, with no examples at all.
7. **Prediction.** "Does forcing the format make answers better or worse?" Reader picks.
8. **Reveal.** 593, 594, 593; 5 and 4 items flipped, both ways. A two-way arrow diagram.
9. **The rejected run.** What went wrong with JSON mode and the one-line fix.
10. **Insurance, not a fix.** Why a schema still belongs in a system code reads: the next model,
    the next prompt, and you still validate.
11. **Scoreboard:** not joined; the reference and E5's target stay the definitions prompt.
12. **Series map** (last slide), E4 marked, and the Ask better act complete.

## For leaders

**Ask your team:** "If the model's reply came back malformed tomorrow, what would break, and who
would notice?"

## Decision rule (proposed)

**"When code reads the output, enforce the format with a schema and still validate it."**

## Next

E5, Field note: does fine-tuning beat a good prompt?: the first tuned model, against the
definitions prompt.

## Careful with

- **This shows no rescue,** because there was nothing to rescue. Do not claim a schema improves
  validity; say it guarantees it, and here validity was already complete.
- **JSON mode changed how the prompt was sent** as well as the format (Amendment 2). A limitation
  of the JSON mode comparison.
- **A strict schema also blocks invented route names,** so format and accuracy cannot be fully
  separated.
- **One provider's format support.** Others enforce formats differently.
- **Boundaries.** Tool calling and agents, where schemas matter most, are S5.

## From practice

_Brendan to add one anonymised line from his own practice._
