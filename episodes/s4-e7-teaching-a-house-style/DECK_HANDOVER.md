# S4 E7 deck handover: Teaching a house style

For the content agent. Has an experiment: three prompted arms and one tuned small model writing
Halvard's customer replies (Task B), judged by code and by a model.

## Sources of truth

- `episodes/s4-e7-teaching-a-house-style/README.md` and `PREREGISTRATION.md` (with Amendment 1).
- `results/analysis-task-b-test.json` and `analysis-task-b-dev.json`; `results/claims-test.json`.
- Chart: `results/charts/s4-e7-teaching-a-house-style-primary-test-slide.svg`.
- The judge check: `judge-check/results/analysis-task-b-test.json`; C5 in `claims-test.json`.
- The style guide: `datasets/halvard-tasks/style-guide.md`; the code checks: `src/lab/adapt/style.py`.
- The tuning jobs: `results/e7-tuned-short-b4/job.json` (ran), `results/e7-tuned-short/job.json`
  (failed, out of memory).
- `season4/scoreboard.json`, `season4/reference.yaml`, `season4/finetune-readiness.md`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E7 |
| Title | Teaching a house style |
| Hub slug | `teaching-a-house-style` (proposed; confirm) |
| Deck file | `bk-s4-e7-teaching-a-house-style-v1.pdf` |
| Hub format | `experiment` |

## The argument

A house style is behaviour: an exact opening and sign-off, a word limit, a citation format,
phrases never to use. The cheapest model, told nothing, followed none of it (E1). The test was
three ways to teach it, in rising effort: write the guide into the prompt, add worked examples,
or tune a small model on 600 replies written to the guide.

Each step helped, and tuning helped most: 0, 215, 262 and 293 of 300 replies passed every rule
and kept the facts. The tuned model is a 0.6 billion parameter model, told one line, tuned in 11
minutes on a free GPU.

The twist is the point of the episode. The tuned model also learned something nobody wrote down:
most of its training replies restate the customer's question, so it does too, and a judge reading
for style preferred the prompted replies. Tuning teaches whatever the training examples do.

## Scoreboard slide

Task B ladder. Chart: `s4-e7-teaching-a-house-style-primary-test-slide.svg`.

| Rung | Passes every check and keeps the facts, of 300 | Joined? |
|---|---|---|
| E1 one-line prompt | 0 (0% to 1%) | The baseline |
| **E7 Qwen3-0.6B, tuned on 600 replies** | **293 (95% to 99%)** | **Joined: the new reference** |

The other E7 arms for context, not candidates: style guide 215, guide plus 4 examples 262. The
first tuned model on the season scoreboard.

## Setup before results

**The house rules checked by code** (simplified for the slide; the full guide is
`style-guide.md`):

> Open with "Thank you for getting in touch."
> Close with "Kind regards," and "The Halvard Home team".
> 40 to 120 words.
> Name the policy and section: Our Warranty policy, section "...", says.
> No banned promises ("we will refund", "guaranteed").
> A fixed sentence when the answer is not in the policies.
> British spelling, no lists or bold.

Plus **facts kept**, judged by `gemini-3.6-flash`: every fact in the source answer, none added.

| Arm | Model | What it is told |
|---|---|---|
| One-line | `gpt-6-luna` | write the reply, using the answer given |
| Style guide | `gpt-6-luna` | the same, plus the full guide (about 800 tokens) |
| Guide plus 4 examples | `gpt-6-luna` | the same, plus 4 worked replies |
| Tuned | Qwen3-0.6B, tuned on 600 replies | "Write the Halvard Home reply." (about 106 tokens with the question) |

**Worked example** (`B-test-00000`, invented): a customer has lost the box for their kettle and
asks whether they can still return it under their Extended Care plan. The answer: missing
packaging does not automatically prevent a return; contact us first.

| Arm | What came back |
|---|---|
| One-line | Two correct sentences. No opening, no sign-off, no citation |
| Style guide | Opening, citation, answer, sign-off: every rule met |
| Guide plus 4 examples | The same, in three short paragraphs |
| Tuned | Every rule met, after first restating the question: "You asked if missing original packaging for your kettle means you are completely barred from returning it..." |

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 0, 215, 262, 293 of 300 | Every check passed and facts kept, by arm | `analysis-task-b-test.json`, `arms.*.primary` |
| 262, 296, 297, 296 | Facts kept, same order | same, `facts_kept` |
| 66, 222, 267, 300 | Within the word limit, same order | same, `checks.length` |
| 27, 46, 51, 64 | Mean words a reply | same, `mean_words` |
| 36 and 5; p below 0.0001 | Tuned against guide plus examples, items each way | `claims-test.json`, C3 |
| 51 and 4 | Guide plus examples against guide alone | same, C2 |
| 247, 49, 4 | Style judge: the guide arm preferred, tie, the tuned arm preferred | `analysis-task-b-test.json`, `e7-tuned-short.style_against_reference` |
| 459 of 600 | Training replies that restate the question | the train split's `target_reply` |
| 260, 0, 78 of 300 | Test replies that restate it: tuned, guide, guide plus examples | the arms' `predictions-test.jsonl` |
| 161 of 180 (89.4%) | Facts verdicts Haiku and Gemini agree on; mark 90% | `claims-test.json`, C5 |
| 19 and 0 | Disagreements where Haiku was stricter, and where Gemini was | the two judges' facts files |
| 0, 72, 86, 97 of 100 | Dev, same order as the arms | `analysis-task-b-dev.json` |

## Cost

Ratios to the style guide arm, answer calls only: the one-line arm 0.28 times (cached and short),
the guide with examples 0.48 times (its long fixed prefix was billed at the cached rate). The
tuned model ran on a free GPU: 11 minutes of training, 4 minutes to write 400 replies, and it
reads about an eighth of the guide arm's input. The judges cost more than all the answers
together; style pairs are most of that. Everything stayed well within the approved budget.

**The cost that did not show up in money:** the first tuning job ran out of GPU memory at the
default batch size, because Task B's examples are longer than Task A's. Halving the batch and
doubling the accumulation fixed it with the same training (Amendment 1).

## Slide ideas

Follow the deck rules: step one example through each arm before any statistics, a reader
prediction revealed on the very next slide, varied visual forms, one-line titles, no
claim-verdict slides, and the last slide is the series map.

1. **A house style is a set of habits.** The seven checkable rules as a checklist card.
2. **Three ways to teach it.** Tell (the guide), show (examples), train (tuning): a staircase.
3. **The kettle box, one-line.** Correct and polite, and every rule missed.
4. **The kettle box, three more ways.** Guide, examples, tuned, side by side, the restated
   question highlighted in the tuned reply.
5. **Prediction.** "Which arm follows the most rules?" Reader picks.
6. **Reveal.** 0, 215, 262, 293. A stepped bar chart.
7. **Where the prompts slipped.** Almost all of it was the word limit: too short.
8. **Prediction.** "A judge reads the replies for style. Which does it prefer: the guide's or
   the tuned model's?" Reader picks.
9. **Reveal.** The guide's, 247 to 4. Why: the restated question, and 18 more words.
10. **The habit nobody wrote down.** 459 of 600 training replies restate the question; the tuned
    model does it 260 times in 300. Tuning copies the examples, not the rulebook.
11. **A cheaper judge?** Haiku agreed 89.4% of the time, always the stricter. Just short of the
    bar; the main judge stays.
12. **Scoreboard:** the first tuned model to join.
13. **Series map** (last slide), E7 marked.

## For leaders

**Ask your team:** "If we tuned a model on our past replies, what habits of ours would it copy
that we would not put in a style guide?"

## Decision rule (proposed)

**"Tune for a house style only on replies you would be happy to see copied, habits and all."**

## Next

E8, Field note: can fine-tuning teach facts?: tuning on question and answer pairs from the
Halvard documents, against retrieval.

## Careful with

- **"Best" depends on the measure.** By the checkable rules the tuned model is best; read as a
  whole by the style judge, the prompted reply is preferred. Show both; do not call the tuned
  model simply better.
- **The training replies were written by a model,** so the habit it copied is that model's.
  Replies written by people would carry their own habits.
- **Two models.** The tuned arm is much smaller than the prompted ones.
- **One run, one seed, one draw of the 4 examples.**
- **C5 failed by one verdict's width** (161 of 180 against a bar of 162). Present it as "close,
  and consistently stricter", not as "the cheap judge is wrong". Neither judge was checked
  against a person in Season 4.
- **The first job failed** (out of memory) and is logged; the batch change is Amendment 1.

## From practice

_Brendan to add one anonymised line from his own practice._
