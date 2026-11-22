# Season 4 implementation plan: Adapting models

Draft, 22 November 2026, from `s4-build-handover.md`. For Brendan's review before Gate 1. Not
committed. Every model choice follows the standing rule: the cheapest model that does the job,
in every role, with exceptions named and approved one by one.

## 1. Facts that shape the plan

| Fact | Consequence |
|---|---|
| Season 3 has merged to `main` (b1a3211) | `s4` branches from `main`; no `s3` caveat in the first PR |
| S3 first pick is C6, library consistency check (4.20 of 5); C2 reply drafts was second (4.15) | Season 4 does **not** build the system Season 3 chose. E0 says Task A comes from C3 (warranty claim triage) and C4 (safety signal screening), Task B from C2 (reply drafts), and claims no more |
| This laptop has no GPU (Intel UHD 620, 16 GB RAM, i7-8565U) | E11 cannot train locally in reasonable time; see decision 4 |
| `gpt-6-luna` is the cheapest answer model on file ($0.10 in, $0.50 out per million; prices checked 17 September 2026, so re-check) | It stays the answer and student model |
| `gpt-6-luna` as answer model means it **cannot** be the data generator (conflict of interest rule) | Generator moves to the cheapest non-arm model: `gemini-3.1-flash-lite` |
| Discarding items where the blind labeller disagrees biases the test set towards items the labeller finds easy | The labeller must not be an answer model either; see section 3 |
| Halvard corpus: 344 documents, about 1.6 MB (roughly 400,000 tokens) | Sizes the E8 question and answer generation |

## 1a. Decided after Gate 1: tuning moves to an open model on Colab (22 November 2026)

Step 1 found that no provider API offers tuning a Season 4 can use:

- **OpenAI:** `gpt-6-luna` cannot be tuned. Fine-tuning has been closed to new organisations
  since 7 May 2026; existing customers lose job creation on 6 January 2027; the last tunable
  base models (`gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini`) shut down on 14 January 2027, and their
  tuned versions with them.
- **Google:** the Gemini API has no tunable model and "no immediate plans" to add one.
- **Anthropic:** no fine-tuning on the first-party API.

Decision (Brendan): every tuning episode (E5 to E11) uses adapter tuning of one small open model
on Google Colab, and I run the notebooks. Prompting arms, data generation and judging stay on the
cheapest APIs. Consequences:

- **Two baselines in tuning episodes.** The untuned open model, prompted the same way, is the
  baseline the tuning is measured against; `gpt-6-luna` with the best prompt is the reference
  the season scoreboard compares with.
- **Model choice by pilot, fixed in advance.** Run untuned `Qwen3-0.6B` with the best E2 prompt
  on Task A dev (free). Keep it if JSON validity is at least 90% of 200; otherwise use
  `Qwen3-1.7B`. Thinking is off (`enable_thinking=False`) throughout.
- **Training is free** in money but not cached like a response, so the job record rule still
  holds: notebook version, base model revision, LoRA settings, seed, data hash, GPU type and
  adapter hash go in each episode's `results/`. Adapters are not committed.
- **Colab runs need your Google sign-in** in the browser pane the first time. Free Colab GPUs are
  not guaranteed; a run that is cut off is logged and resumed from its last checkpoint.
- **E11 merges into the Tune act**: it becomes the open versus API comparison only for prompted
  arms, since there is no API-tuned model to compare with. Proposed: fold E11's question into
  E5 and use the slot for "Where your tuned model runs" (laptop through Ollama against Colab),
  or cut E11. To decide when E5 is designed.
- **E12 gains real evidence:** a provider withdrew tuning mid-2026, which is S3 E9's point about
  surviving a model change.
- **E9 teacher terms:** Google's terms bar using Gemini to "develop models that compete with the
  Services"; whether a small triage model counts is not clear. OpenAI's terms need the same
  check. Settled at the E9 gate with sources.

## 2. Models by role (cheapest viable)

Prices per million tokens, from `prices.local.yaml` where known. All to be re-verified with source
and date in `capabilities.yaml` in step 1, with the new `fine_tunable`, `tuning_method` and
`structured_output` fields.

| Role | Model | Price (in / out) | Why this one |
|---|---|---|---|
| Answer, every prompted arm | `gpt-6-luna`, reasoning off | 0.10 / 0.50 | Cheapest on file; the S2 and S3 answer model |
| Tuning base and student | `Qwen/Qwen3-0.6B` (Apache 2.0), adapter (LoRA) tuning on a free Colab GPU; `Qwen/Qwen3-1.7B` (Apache 2.0) if 0.6B fails the pilot rule below | free | No provider API offers tuning (see section 1a). Its untuned version is the baseline in every tuning comparison |
| Data generator (Tasks A, B, E8 pairs, E10 format bleed set) | `gemini-3.1-flash-lite`, minimal | 0.25 / 1.50 | Cheapest model that is not an arm; failed as a *judge* in S2 E4, which does not bar generation |
| Blind label check | cheapest model from a third provider: `claude-haiku-5-5`, reasoning off | to check | Not the generator's provider, not an arm, so discards do not bias towards the answer model |
| Judge, Task B and E8 | `gemini-3.6-flash`, minimal | 0.75 / 3.75 | Passed the S2 judge check; keep unless a cheaper model passes the same check |
| Second judge (50 shared items) | `claude-haiku-5-5` | 0.10 / 0.50 | Another provider, cheapest. If it agrees with `gemini-3.6-flash` on the judge check, propose it as the main judge: it is a seventh of the price, and Gemini's price doubles on 1 January 2027 |
| Similar example retrieval (E3) | `text-embedding-3-small` | 0.02 | Existing embedding code |

**Exceptions needing your explicit approval:**

| Exception | Cheapest option | Alternative | Recommendation |
|---|---|---|---|
| E9 teacher, clearly stronger than the student | `gemini-3.6-flash` (0.75 / 3.75), if Google's terms allow its outputs to train an OpenAI model | Same provider: `gpt-6.1-sol` at low (2.00 / 10.00) | Check Google's terms first; use `gemini-3.6-flash` if they allow it, otherwise `gpt-6.1-sol` |
| E5 optional larger prompted arm | `gemini-3.6-flash` | `gpt-6.1-sol` | Leave off |
| E11 GPU | Decided: Google Colab. Code only, not run by me | | No exception needed |

## 3. Datasets (Gate 2)

- `datasets/halvard-tasks/`, as in the handover: `routes.yaml` (8 routes), a fixed fault list,
  `style-guide.md` (invented, with rules a plain prompt follows imperfectly), splits, `MANIFEST.json`
  and a frozen test.
- **Task A:** train 1,600 (halved from the handover's 3,200 on 22 November 2026, to keep the
  build near 30 minutes), dev 200, test 600, about 10% safety items in each, with the hard cases
  seeded by template (two products, angry non-complaints, harmless heat words, invented products).
- **Task B:** train 1,200, dev 100, test 300. Source answers are the S2 reference system's right
  answers on train-side questions; no test item shares a corpus question with train.
- Generation is conditioned on the target label (product, fault, route, persona seeds), so labels
  are right by construction. The blind labeller then checks; disagreements are discarded and
  counted. Overgenerate by 30% to absorb discards (raised from 15% after the pilot).
- Near duplicates: character 5-gram Jaccard over 0.8 between test and train removes the test item
  (method and threshold pre-stated; count reported).
- Product name test against the Halvard corpus; Halvard itself untouched.
- Code writes 50 test items for your hand check; freeze only after it.

## 4. Order of work and gates

| Step | Work | Gate | Paid? |
|---|---|---|---|
| 1 | Branch `s4` from `main`. Re-verify every model above (tuning, structured output, prices) with sources. Draft `routes.yaml`, `style-guide.md`, generation prompts | | No |
| 2 | **Gate 1:** this plan, task definitions, model table, open decisions (section 6) | You approve | No |
| 3 | `lab smoke` on every chosen model; data generation estimate | **Gate 2a** | Yes, small |
| 4 | Generate, label check, dedupe, 50-item list; you check; freeze | **Gate 2b** (your check) | Yes |
| 5 | `src/lab/adapt/`: arms, structured output, scoring, statistics (Wilson, exact McNemar, Holm), charts, `lab adapt run / tune / status / analyse / score`; tests to 85%, ruff clean. All built against the mock provider | | No |
| 6 | E1 baseline on both tasks, pre-registered | Gate | Yes |
| 7 | E2, E3, E4 pre-registered, one bundled estimate listed line by line | Gate | Yes |
| 8 | Deck handovers E0 to E4 | | No |
| 9 | E5 tuning run (`lab adapt tune` prints training tokens; notebook on Colab; launch only after the gate) | Gate | No (Colab) |
| 10 | E6 learning curve (50, 200, 800; 1,600 reuses E5) | Gate | No (Colab) |
| 11 | E7 house style on Task B, with judge check | Gate | Yes |
| 12 | E8 facts field note; staff-only documents excluded from training | Gate | No (Colab) |
| 13 | E9 distillation with the approved teacher | Gate | Yes, includes exception |
| 14 | E10 regression checks (S1 E10 items, format bleed set, 120 unanswerable) | Gate | Yes |
| 15 | E11 on Colab, its question settled at E5 (section 1a) | Gate | No (Colab) |
| 16 | E12 decision card, readiness checklist, E13 recap, all remaining handovers. No calls | | No |
| 17 | Hub PR on `s4-hub` (can start after Gate 1); README pass; season PR | You merge | No |

Every training job is logged in `results/` (job ID, base model, hyperparameters, data hash, model
ID). Failed jobs are logged and never retried without your approval.

## 5. Rough spend

Token counts are the handover's; costs use the prices above and are a warning, not the approval
number. `lab estimate` gives that at each gate. Training prices are unknown until step 1.

| Line | Tokens | Rough API cost |
|---|---|---|
| Data generation and label check | 3 to 5 million | under $8 |
| E1 | under 1 million | under $0.50 |
| E2 to E4 | 5 to 10 million, mostly cached few-shot input on `gpt-6-luna` | $1 to $2 |
| E5, E6 training | about 9 million training tokens, on Colab | free |
| E7 (judge dominates) | 2 to 4 million, plus about 3,600 judge calls | $4 to $8 |
| E8 | pair generation about 2 million, training to estimate, 1,040 judge calls | $2 to $4 plus training |
| E9 teacher | 2 to 4 million at teacher prices | $3 to $15 depending on teacher |
| E10 | 1 to 2 million, tuned model running prices | under $2 |
| **Total excluding training** | | **about $20 to $40** |

With tuning on Colab, training costs nothing; the paid lines are data generation, prompted arms,
judges and the E9 teacher. Prices checked 22 November 2026: `gpt-6-luna` 0.10 / 0.50,
`claude-haiku-5-5` 0.10 / 0.50 (prompts under 100,000 tokens), `gemini-3.1-flash-lite`
0.25 / 1.50, `gemini-3.6-flash` 0.75 / 3.75 until 31 December 2026, then 1.50 / 7.50.

## 6. Decisions for you at Gate 1

1. **Season plan:** approve the 14 episodes, four acts and slugs as proposed, or cut. I would
   keep all 14 except possibly E11.
2. **Tasks and sizes:** as proposed.
3. **Tuning:** decided (section 1a). No provider API offers it; adapter tuning of `Qwen3-0.6B`
   (or `Qwen3-1.7B`) on Colab, run by me.
4. **E11:** on Colab, run by me; its exact question is settled when E5 is designed (section 1a).
5. **Exceptions:** E9 teacher `gemini-3.6-flash` (or `gpt-6.1-sol` if Google's terms forbid
   it); E5 larger arm off.
6. **Merge timing:** datasets, harness and tools merge before E0 publishes; experiments merge as
   each completes.
7. **Preference tuning:** leave out.
8. **Label checker:** `claude-haiku-5-5` (a third provider, and not an arm) rather than the
   cheaper `gpt-6-luna`, because discarding disagreements with the answer model would make the
   test set easier for exactly that model.
