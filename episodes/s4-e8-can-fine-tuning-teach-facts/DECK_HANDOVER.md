# S4 E8 deck handover: Field note: can fine-tuning teach facts?

For the content agent. A field note: a small model tuned on question and answer pairs from
Halvard's library, asked Season 2's questions without the documents, against the untuned model
and Season 2's retrieval system.

## Sources of truth

- `episodes/s4-e8-can-fine-tuning-teach-facts/README.md` and `PREREGISTRATION.md`.
- `results/analysis-facts-test.json` (by question type, per item), `analysis-facts-dev.json`,
  `results/claims-test.json`.
- The pairs: `pairs/pairs.jsonl`, `pairs/pairs-log.json`.
- The jobs: `results/e8-tuned-closed/job.json`, `results/e8-base-closed/job.json`.
- The reference: `field-notes/s2-e12-embedding-swap/results/baseline/` (Season 2's own run).

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E8 |
| Title | Field note: can fine-tuning teach facts? |
| Hub slug | `can-fine-tuning-teach-facts` (proposed; confirm) |
| Deck file | `bk-s4-e8-can-fine-tuning-teach-facts-v1.pdf` |
| Hub format | `field-note` |

## The argument

"Can't we just train the model on our documents?" is the question every team asks. E8 tried it
on the cheapest terms: a small model tuned on 1,724 questions and answers written from every
public Halvard document, then asked Season 2's 520 questions with no documents in front of it.

It learned the voice, not the facts: 26 of 400 right, against 11 untuned and 354 for retrieval.
And it lost something the untuned model had: saying "I don't know". It declined none of the 120
questions the library cannot answer and gave confident wrong answers to 494 of 520. Its training
answers always answered, so it does too.

## The key slide

| | Right, of 400 | Says "I don't know" when it should, of 120 | Confident wrong, of 520 |
|---|---|---|---|
| Small model, untuned | 11 | 78 | 165 |
| Small model, tuned on the documents | 26 | **0** | **494** |
| Season 2 retrieval system | **354** | **107** | **11** |

## One example (invented)

A question about a product bracket whose document was withdrawn. Untuned: "I could not find it."
Tuned: "If you still have a wall bracket fitted to your Brio kettle, contact Halvard Home customer
support to check whether it is suitable for your model." Plausible, polite, and made up.

## The claims

- **C1 held:** tuning teaches some facts, 26 against 11 (p 0.003). Some, and very few.
- **C2 held:** it does not replace retrieval, 26 against 354.
- **C3 held:** it stops declining, 0 against 78.
- **C4 held:** 494 confident wrong answers against retrieval's 11.

## Worth saying on a slide

- **Most of what it got right is repeated across many documents** (16 of 26): tuning picks up
  what it sees often, not the one-off detail a customer asks about.
- **Staff-only documents were left out of training on purpose:** a tuned model has no permission
  filter (Season 2 E8).

## Decision rule and question

- **Rule (proposed):** "To give a model your facts, retrieve them. Tune for behaviour, and if you
  tune on answers, include the questions it should decline."
- **Ask your team:** "If our model did not know the answer, would it say so, and have we tested
  that?"

## What this does not show

- One way of tuning (rank 16, 3 epochs, one seed); more data or passes might teach more.
- A 0.6 billion parameter model.
- Pairs written by a model.
- No training pairs that decline; adding them might restore declining (not tested).
- The tuned model inside a retrieval system was not run.

## Charts

None made. A three-bar chart per column of the key slide would work.

## Cost

Ratios only: well within the approved budget. The two Colab jobs ran on the free T4, 15 minutes
of training.
