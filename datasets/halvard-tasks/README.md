# halvard-tasks: the Season 4 task data

Two invented support tasks for Halvard Home, an invented UK appliance maker. Every message,
reply, label and rule here is fictional. `datasets/halvard/` (the Season 2 library) is the
source of Task B's passages and is not changed.

**Status: not yet frozen.** The test sets are frozen, and `MANIFEST.json` written, only after
Brendan's hand checks of `review/task-a-test-sample.md` (50 items) and
`review/task-b-test-sample.md` (20 items). Until then any file here may still change.

| | Train | Dev | Test |
|---|---|---|---|
| Task A, triage messages | 1,600 (166 safety) | 200 (25 safety) | 600 (65 safety) |
| Task B, house style replies | 600 (66 not found) | 100 (12 not found) | 300 (34 not found) |

How the data was planned is in `GENERATION_PLAN.md`, with its dated amendments. The task
definitions are `routes.yaml` (Task A) and `style-guide.md` (Task B).

## Task A: triage

Each item is a customer message and a label: route (8), safety (true or false), product (10, or
null) and fault (12, or null).

- **Labels are drawn in code first** (`src/lab/adapt/build_tasks/seeds.py`), with exact counts
  of each hard case and of safety items, so each label is right by construction.
- **Generator:** `gemini-3.1-flash-lite`, reasoning minimal, writes one message per label.
- **Blind label check:** `claude-haiku-5-5`, reasoning off, sees the definitions and the message
  only. Any field that disagrees with the seed discards the item.
- **Near duplicates:** a dev or test item with character 5-gram Jaccard over 0.8 against any
  train item is removed.

| Step | Count |
|---|---|
| Seeds drawn (train 2,320, dev 290, test 870) | 3,480 |
| Generation failed (no valid message after a retry) | 45 |
| Discarded by the blind label check | 197 |
| Near duplicates removed | 2 |
| Kept, in seed order, up to each split's size | 2,400 |

Label check discards by field (an item can disagree on several): route 101, fault 93, product
26, safety 20, unreadable 1.

### The hard cases, and a bias to know about

| Kind | Test items | Discarded in the label check |
|---|---|---|
| plain | 187 | 41 |
| harmless_safety_word (a heat or fire word, no incident) | 62 | 27 |
| two_requests (a minor request, then the main one) | 62 | 20 |
| angry_not_complaint | 47 | 16 |
| mixed_request (a fault, then money back) | 47 | 18 |
| two_products | 44 | 10 |
| safe_use_question (is it safe to..., no incident) | 40 | 1 |
| safety | 39 | 1 |
| negated_cue (a request mentioned and ruled out) | 38 | 4 |
| played_down_safety | 26 | 5 |
| unknown_product (an appliance Halvard does not sell) | 8 | 54 |

Discarding on disagreement keeps the labels clean but removes the items the labeller found
hard. The effect is largest for **unknown_product**: 54 of its seeds were discarded, so only 8
test items remain, against a planned share of 4% (about 24). Scores on that kind rest on very
few items and say little. Across the set, scores may be higher than on real messages.

### History: two builds

The first build (draft-2) left too little headroom: the one-line baseline got 183 of 200 dev
items fully right. Under a rule stated before the check (E1 Amendment 1, 85% or more means
rebuild), Task A was rebuilt as draft-3 with four more hard cases (mixed_request,
two_requests, negated_cue, safe_use_question) and new shares in `routes.yaml`. On the rebuilt
dev set the baseline got 170 of 200, still at the line; the rebuild was kept rather than
repeated, so the test set is not tuned to the model (E1 Amendment 2). Task B was built once.

## Task B: house style replies

Each item is a customer question, the correct answer, its source in the Halvard library, and a
target reply in the house style. About 11% are not found items, whose target is the fixed not
found sentence.

- **Passages are split before any call**, so no test item shares a passage with train
  (passages: train 259, dev 43, test 130; public documents only).
- **Question and answer:** `gemini-3.1-flash-lite` writes a question and answer from a passage.
- **Support check:** `claude-haiku-5-5` checks the passage supports the answer.
- **Style rewrite:** `gemini-3.1-flash-lite` writes the target reply; the style guide's code
  checks (`src/lab/adapt/style.py`) must all pass, with one retry.
- **Fact check:** `claude-haiku-5-5` checks the reply keeps the answer's facts and adds none
  (the citation and the fixed safety sentence masked).

| Step | Count |
|---|---|
| Seeds drawn (train 780, dev 130, test 390) | 1,300 |
| Answer not supported by its passage | 33 |
| Rewrite failed the code checks after a retry | 24 |
| Reply failed the fact check | 129 |
| Kept, in seed order, up to each split's size | 1,000 |

The fact check was the strictest step; replies it rejected are not in the data, so the target
replies lean towards plain restatements of the answer.

## Files

- `task-a/`, `task-b/`: `train.jsonl`, `dev.jsonl`, `test.jsonl`, `build_log.json` (every
  discard by ID, call and token counts) and `raw/` (every call's reply).
- `pilot/`, `pilot-b/`: the pilots run before each full build.
- `review/`: the hand check lists.
- `config.yaml`: models, sizes, seeds and rate limits for the build.
