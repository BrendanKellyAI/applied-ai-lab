# Prompt, retrieve, or tune? The decision card

A tool from Season 4 (E12). Start at the top with the gap you have measured, and stop at the
first fix that clears your bar. Each step gives the evidence from Halvard's two tasks. Halvard
Home is invented; its numbers are one worked case, not a rule for your task.

**Status: final, 27 November 2026 (E12).** Every step carries its result from E1 to E11.

## The rule (proposed)

**"Prompt first, add examples second, and tune only when a measured gap remains, you have
labelled data, and the volume pays back the training."**

## The path on one screen

| Step | Ask | If yes | Halvard's evidence |
|---|---|---|---|
| 1 | Is the gap knowledge? | Retrieve (Season 2); do not tune | E8: tuned on the library, 26 of 400 right; retrieval 354 |
| 2 | Has the model been told the rules? | Write them down and measure | E2: triage 521 to 587 of 600; E7: style 0 to 215 of 300 |
| 3 | Do the rules leave room? | Add a few examples, chosen to match | E7: 215 to 262 of 300; E3: 593, not distinguishable from 587 |
| 4 | Does code read the output? | Schema, and still validate | E4: no answer changed; insurance |
| 5 | Is a measured gap left, or a smaller model worth having? | Tune, if every condition in section 5 holds | E7: tuned 293 of 300, joined; E5: tuned 592, matched |
| 6 | Will you keep it? | Budget for rebuilding, upkeep and regression checks | E10, E11, and a provider withdrawing tuning |

Stop at the first step that clears your bar.

## 1. Measure the gap before choosing a fix

- **Score the cheapest model with the plainest prompt** on a frozen test set, on the measure
  that matters, and read the misses. *(E1: one line of instruction, Task A triage 521 of 600;
  every product was read correctly and the misses were Halvard's rules. Task B replies 0 of 300
  in the house style, though 87% kept the facts.)*
- **Name the gap.** If the model lacks facts, the fix is retrieval (Season 2), not anything on
  this card. *(E8: a small model tuned on 1,724 pairs from the library was right on 26
  of 400 questions, against 354 for retrieval, and stopped saying "I don't know".)*
- If the gap is behaviour (a rule, a format, a style), go on.

## 2. Write the rules down

- **Give the model the definitions it is judged by.** It is the cheapest fix and often the
  largest. *(E2: definitions took triage from 521 to 587 of 600, and joined as the reference.)*
- **For a house style, put the guide in the prompt.** *(E7: 0 to 215 of 300.)*
- Stop here if the bar is met.

## 3. Show examples

- **A few worked examples help where the rules leave room.** *(E7: 4 examples took the house
  style from 215 to 262 of 300.)*
- **Examples chosen to resemble the message help more than random ones, and cost more.**
  *(E3: 8 similar examples, 593 of 600, but not distinguishable from definitions alone.)*
- Long example blocks are paid on every call unless the provider caches them; check the cached
  rate before paying for 32 examples.

## 4. When code reads the output, make it a contract

- **Enforce the format with a schema, and still validate every reply.** *(E4: free text was
  already valid on all 600 messages; JSON mode and a schema kept it so and changed no answer.
  It is insurance for the next model or prompt.)*

## 5. Tune only when a gap remains

Tune when all of these hold:

- **A measured gap remains** after steps 2 to 4, or a smaller model or shorter prompt is worth
  having. *(E5: a 0.6 billion parameter model, tuned in 28 minutes, matched the best prompt on
  triage, 592 against 587, with an eighth of the input. E7: a tuned model followed the house
  rules best of all, 293 of 300 against 262 for the best prompt.)*
- **You have labelled data, enough of it.** Draw the curve first. *(E6: 800 examples matched
  the prompt; 200 did not; 1,600 added nothing measurable.)*
- **Your training examples are ones you would be happy to see copied, habits and all.** *(E7:
  the tuned model copied its training replies' habit of restating the question, which a style
  judge marked down.)*
- **A bigger model can label for you,** where its terms allow it. *(E9: a small model tuned
  on `gpt-6-luna`'s labels scored 589 of 600, against 587 for its teacher and 592 on true
  labels. The terms allow it for an in-house classifier only.)*
- **You can check what tuning breaks** outside the task. *(E10: the tuned reply writer
  answered 41 of 100 ordinary requests as a customer reply and declined fewer unanswerable
  questions, 52 against 65; the tuned triage model did neither.)*
- **The volume pays back the training and hosting,** which this card does not price: that is
  Season 6.

Before you commission it, run `finetune-readiness.md`.

## 6. The costs of keeping a tuned model

- **The base model can be withdrawn.** Illustrative, from the providers' own pages, read on 22
  November 2026 (sources in `src/lab/providers/capabilities.yaml`): OpenAI closed fine-tuning to
  new users, ends self-serve tuning jobs on 6 January 2027, and shuts down the remaining tunable
  base models on 14 January 2027, with the tuned models built on them; the Gemini API no longer
  offers a tunable model. A tuned model is a dependency you must be able to rebuild. Season 3
  E9 asks what happens when a model changes.
- **Where it runs is your choice.** *(E11: the tuned model gave identical answers on a 2018
  laptop with no GPU, all 600, 19 times slower than a free GPU but about 770 messages an hour.)*
  Training needs the GPU; answering, for a small model, may not.
- **The training data needs upkeep:** when the rules change (a new route, a new product), the
  labels and the model change with them; a prompt changes in minutes.
- **Every retrain needs the regression checks again.** *(E10: what breaks depends on what was
  taught: a voice travelled to every kind of request, a JSON format stayed in its task. Only a
  test on the other requests shows which you have.)*
- **A tuned model has no permission filter.** Anything in its training data, it can repeat to
  anyone (Season 2 E8). Season 4 left staff-only documents out of E8's training on purpose.

## Every rule and question from the season

| Ep | Decision rule (proposed) | Ask your team |
|---|---|---|
| E1 | "Name the gap first. If the model lacks facts, retrieve. If it knows enough but behaves wrongly, change how you ask before you change the model." | "Is our problem that the model does not know, or that it does not do what we want?" |
| E2 | "Write down the definitions a new colleague would need, and give them to the model. Measure before adding anything else." | "Have we written down for the model what we would tell a new member of staff?" |
| E3 | "Add examples until the score stops rising, then stop: every example is paid for on every call. Choose them to match the message before you add more." | "How many examples are in our prompts, who chose them, and what does each one cost us a month?" |
| E4 | "When code reads the output, enforce the format with a schema and still validate it." | "If the model's reply came back malformed tomorrow, what would break, and who would notice?" |
| E5 | "Tune when the gain is a smaller model or a shorter prompt you can measure, not to beat a prompt that already works." | "If we tuned a small model to match our prompt, who would host it, and what would that cost against the API bill it replaces?" |
| E6 | "Label in stages and stop when the curve flattens." | "Before we label more, what does the curve look like at a quarter and half of what we have?" |
| E7 | "Tune for a house style only on replies you would be happy to see copied, habits and all." | "If we tuned a model on our past replies, what habits of ours would it copy that we would not put in a style guide?" |
| E8 | "To give a model your facts, retrieve them. Tune for behaviour, and if you tune on answers, include the questions it should decline." | "If our model did not know the answer, would it say so, and have we tested that?" |
| E9 | "If a big model does the task well and its terms allow it, let it label the training data, check a sample by hand, and tune the small model on the rest." | "Do we need to label data by hand, or could the model we already pay for label it, and do its terms let us?" |
| E10 | "Before a tuned model sees requests outside its task, test it on them: ordinary requests and the questions it should decline. Rerun those tests after every retrain." | "What else will this tuned model be asked, and have we tested it on that?" |
| E11 | "Tune where the GPU is, then run the model wherever it is cheapest to keep: check that it gives the same answers there before you move it." | "If we tuned a small model, how many messages an hour would it need to answer, and does that need a GPU at all?" |

| E12 | "Prompt first, add examples second, and tune only when a measured gap remains, you have labelled data, and the volume pays back the training." | "For each AI problem we have, is it knowledge or behaviour, and have we written the rules down before paying to tune?" |

## The season's scoreboard

From `scoreboard.json`. A candidate joins a task's reference only if its Wilson 95% interval on
test sits clear above the reference's.

| Task | Rung | Score on test | Joined? |
|---|---|---|---|
| A, triage (fully right) | E1 one-line prompt | 521 of 600 (83.9% to 89.3%) | The baseline |
| A | E2 + written definitions | 587 (96.3% to 98.7%) | Joined: the reference |
| A | E3 + 8 similar examples | 593 (97.6% to 99.4%) | No: overlaps the reference |
| A | E4 + JSON mode | 594 (97.8% to 99.5%) | No |
| A | E5 Qwen3-0.6B tuned on 1,600 true labels | 592 (97.4% to 99.3%) | No |
| A | E9 Qwen3-0.6B tuned on the teacher's labels | 589 (96.7% to 99.0%) | No |
| B, house style (passes every rule, keeps the facts) | E1 one-line prompt | 0 of 300 (0% to 1.3%) | The baseline |
| B | E7 Qwen3-0.6B tuned on 600 replies | 293 (95.3% to 98.9%) | Joined: the reference |

Task A ends where written definitions took it in E2: nothing after cleared that bar, though
examples, a schema and two tuned small models all matched it. Task B ends with a tuned model,
the season's one case where tuning cleared a measured gap the best prompt left (E7's prompt
with the guide and 4 examples reached 262 of 300).
