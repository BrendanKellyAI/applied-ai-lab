# S4 E8 pre-registration: can fine-tuning teach facts?

Written before any E8 call or job and not edited after; any later change goes in a dated
amendment at the end. Every claim is reported in `README.md` as Held, Failed or Not tested. The
pass marks are in `claims.yaml`. A field note.

## The question

E5 to E7 tuned behaviour: a routing rule, a format, a house style. A common hope is that tuning a
model on your documents makes it know them, so you can drop retrieval. If you tune a small model
on question and answer pairs from Halvard's library, does it then answer Halvard's questions
without being shown the documents? And what does it do with questions the library cannot answer?

## Setup

- **The questions:** `halvard-v2` test, 520 items, Season 2's frozen set: 400 answerable (40 of
  them asked by staff, about staff-only documents) and 120 the library cannot answer (absent
  details and topics, deleted documents, staff-only answers asked by the public). Dev 100 is
  judged as a check and chooses nothing.
- **The training pairs** (`pairs.yaml`): `gemini-3.1-flash-lite`, minimal reasoning, writes 4
  question and answer pairs from each current public passage of the library, cut as Season 2's
  reference system cut it (one passage per lowest section, at most 1,024 tokens): 436 passages,
  so up to 1,744 pairs. The prompt asks for varied wording and exact figures, to give tuning its
  best chance.
  - **Left out on purpose:** the 4 staff-only documents, because a tuned model has no permission
    filter and would repeat them to anyone (Season 2 E8); the superseded and deleted documents,
    whose facts are no longer true.
  - **Removed and counted:** any pair whose question is a near duplicate of a dev or test
    question (character 5-gram Jaccard over 0.8), and repeated questions. A passage whose reply
    is not exactly 4 complete pairs gives none, and is counted.
  - Saved to `pairs/pairs.jsonl` with `pairs-log.json`, and frozen by the job record's hash.
- **Arms:**

  | Arm | Model | What it is given |
  |---|---|---|
  | `e8-base-closed` | Qwen3-0.6B at commit `c1899de`, untuned | the question only (closed book) |
  | `e8-tuned-closed` | the same, tuned on every kept pair | the question only (closed book) |
  | `e8-reference` | Season 2's reference system (`0294479ba987`): retrieval, `gpt-6-luna` | its own run, read from `field-notes/s2-e12-embedding-swap/results/baseline/`; no new calls |

  Both Qwen arms are told: "Answer the Halvard Home customer's question. If you do not know the
  answer, say that you could not find it." A follow-up question comes with its earlier turns.
- **Tuning** (`tune-tuned.yaml`, written once the pairs exist, with `train_size` set to the
  number kept): LoRA rank 16, 3 epochs, learning rate 2e-4, batch 8 with 2 accumulation steps,
  seed 1, greedy decoding, `max_new_tokens` 160: the season's defaults. The untuned arm is an
  eval-only job (`tune-base.yaml`). Two jobs on a free Colab T4.
- **Not run:** the tuned model inside the reference system (the plan's optional arm). It would
  need the reference's retrieval replayed into a Qwen prompt; it is left for later.
- **The judge:** Season 2's, `gemini-3.6-flash`, minimal reasoning, with its fixed instructions
  (`src/lab/rag/prompts/judge.md`), shown "(none)" for passages, since the closed-book arms were
  given none. Output limit 300 tokens (Season 2 used 2,000; a verdict is about 60).
- **Statistics:** Wilson 95% intervals; exact McNemar on the same items, one test per claim,
  uncorrected.

## Measures

- **Right:** the judge's `correct` on the 400 answerable items. Season 2 counted an answer right
  only when it was also faithful to its passages; a closed-book answer has no passages, so E8
  counts `correct` alone for every arm, the reference included, and reports Season 2's own
  figure (354 of 400) beside it.
- **Correct declines:** the judge's `declined` on the 120 unanswerable items.
- **Wrong answers stated with confidence:** items, of all 520, where the arm gave an answer, not
  a decline, and the judge found it wrong.
- **Reported:** each measure by question type, declines on answerable questions, the 40 staff
  questions, and how many pairs were dropped and why.

## Claims (on test)

**C1. Tuning teaches some facts.**

- *Pass mark:* `e8-tuned-closed` is right on more answerable questions than `e8-base-closed`,
  exact McNemar p below 0.05.

**C2. A tuned model does not replace retrieval.**

- *Pass mark:* `e8-tuned-closed` is right on fewer answerable questions than `e8-reference`,
  exact McNemar p below 0.05.

**C3. Tuning on answers teaches the model to answer everything.**

- *Pass mark:* `e8-tuned-closed` declines fewer of the 120 unanswerable questions than
  `e8-base-closed`, exact McNemar p below 0.05.

**C4. The tuned model states more wrong answers with confidence than retrieval does.**

- *Pass mark:* `e8-tuned-closed` gives more confident wrong answers, of 520, than
  `e8-reference`, exact McNemar p below 0.05.

## The scoreboard

E8 is a field note on Season 2's questions, not a rung on Season 4's Task A or B ladders. The
scoreboard does not change.

## Estimate

From `lab adapt pairs --estimate` and `lab adapt facts-run --estimate`; the reference makes no
call:

| Step | Calls | Expected | Ceiling (every call at its limit) |
|---|---|---|---|
| Pairs, `gemini-3.1-flash-lite` | 436 | $0.24 | $0.84 |
| Judge, dev, `gemini-3.6-flash` | 200 | $0.10 | $0.28 |
| Judge, test, `gemini-3.6-flash` | 1,040 | $0.50 | $1.43 |
| **Total** | | **$0.84** | **$2.55** |

Proposed budget: $3.00. Wall-clock: about 5 minutes for the pairs; on Colab, about 10 minutes
for the untuned job and about 25 for the tuned one (training about 20); about 10 minutes of
judging.

## What E8 cannot show

- **One way of tuning.** Rank 16, 3 epochs, 4 pairs a passage, one seed. Much more data, more
  passes or a larger adapter might teach more facts; the season's defaults were kept so E8
  compares with E5 to E7.
- **A 0.6 billion parameter model.** A larger model may hold more of what it is shown.
- **Pairs written by a model.** A mistaken pair teaches a mistaken fact.
- **The judge is a model,** checked against a person in Season 2 E3 with passages, not closed
  book. Its `correct` compares the answer with the reference answer, which it was shown.
- **The 40 staff questions** cannot be answered by the tuned model by design: their documents
  were left out.
