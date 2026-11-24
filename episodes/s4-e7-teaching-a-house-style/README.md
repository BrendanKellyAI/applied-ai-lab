# S4 E7: Teaching a house style

E1 found the cheapest model writes short, correct replies and follows none of Halvard's house
rules: 0 of 300 passed every check. Can the house style be taught by writing it into the prompt,
by adding examples, or by tuning a small model? And does the reply keep the facts while it
changes? Claims and pass marks: [`PREREGISTRATION.md`](PREREGISTRATION.md), with Amendment 1.

**Result: a 0.6 billion parameter model, tuned for 11 minutes on 600 replies, followed the house
rules best of all: 293 of 300, against 262 for the best prompt and 0 for none.** It kept the
facts as well as the prompts did. But a judge reading for style preferred the plain style guide
prompt's replies in most pairs, because the tuned model copied a habit of its training replies
that is not in the guide. Four claims held; C5, a cheaper judge, failed narrowly. The tuned model
becomes the Task B reference.

## The design

- **Data:** Task B, frozen. Test 300 to report (266 answerable, 34 not found); dev 100 to
  choose; train 600 to tune on and to draw examples from.
- **Arms:**

  | Arm | Model | Prompt |
  |---|---|---|
  | `e7-one-line` | `gpt-6-luna`, reasoning off | E1's one-line prompt, no style guide (from the cache) |
  | `e7-style-guide` | the same | the one-line prompt plus the full style guide |
  | `e7-guide-4-examples` | the same | the style guide plus the same 4 worked replies for every item |
  | `e7-tuned-short` | Qwen3-0.6B, tuned on the 600 train replies | `Write the Halvard Home reply.` |

- **Tuning:** LoRA rank 16, 3 epochs, learning rate 2e-4, seed 1, as E5. The first job ran out
  of GPU memory at batch 8 before training began; the job that ran used batch 4 with 4
  accumulation steps, the same 16 examples an update (Amendment 1). Recorded in
  `results/e7-tuned-short-b4/job.json`; the failed attempt in `results/e7-tuned-short/job.json`.
- **Judges:** `gemini-3.6-flash` for facts kept and for pairwise style against `e7-style-guide`,
  in both orders. **Judge check:** `claude-haiku-5-5` judged the first 50 test items again, for
  every arm (`judge-check/`).

## Results (test, 300 items)

| Arm | Passes every check and keeps the facts | Facts kept | Within length | Style against the guide arm (win, tie, loss) | Words | Input tokens a call |
|---|---|---|---|---|---|---|
| `e7-one-line` | 0 (0% to 1%) | 262 | 66 | 0, 0, 300 | 27 | 125 |
| `e7-style-guide` | 215 (66% to 77%) | 296 | 222 | (the comparison) | 46 | 811 |
| `e7-guide-4-examples` | 262 (83% to 91%) | 297 | 267 | 20, 164, 116 | 51 | 1,319 |
| **`e7-tuned-short`** | **293 (95% to 99%)** | 296 | **300** | 4, 49, 247 | 64 | **106** |

Input tokens are the provider's count for the prompted arms and Qwen's for the tuned model.

Every guided arm got the opening, sign-off, citation and not found sentence right on nearly every
item. What separated them was the **word limit** (40 to 120 words): the style guide alone wrote
too short on 78 replies, the examples cut that to 33, and the tuned model was never outside it.

On dev: 0, 72, 86 and 97 of 100.

**One reply, four ways** (`B-test-00000`, invented): a customer has lost the box for their kettle
and asks whether they can still return it under their Extended Care plan.

- **One-line:** a correct two-sentence answer, with no opening, sign-off or citation.
- **Style guide:** the opening, the citation, the answer, the sign-off: 45 words, all rules met.
- **Guide plus examples:** the same, in three short paragraphs.
- **Tuned:** the same, after first restating the question: "You asked if missing original
  packaging for your kettle means you are completely barred from returning it...".

## The claims

**C1 held: the style guide teaches the house style.** 215 against 0; 215 items fixed, none lost
(exact McNemar p below 0.0001).

**C2 held: examples add to the guide.** 262 against 215; 51 and 4 items each way, p below
0.0001.

**C3 held: a tuned small model matches the best prompt on the house style.** The best prompted
arm on dev was the guide with examples. The tuned model was not worse; it was better, 293
against 262, 36 and 5 items each way (p below 0.0001).

**C4 held: tuning keeps the facts.** 296 against 297, 3 and 4 items each way, p 1.0.

**C5 failed: a cheaper judge agrees with the facts judge.** `claude-haiku-5-5` gave the same
facts verdict as `gemini-3.6-flash` on 161 of 180 shared verdicts (89.4%; the mark was 90%).
Every one of the 19 disagreements runs the same way: Haiku failed a reply that Gemini passed.
Ten of them are one-line replies, which reword the answer most. On style outcomes they agreed on
92 of 147 pairs (63%). Haiku is stricter, not random; it is not proposed as the main judge, and
E8 keeps Gemini. Neither judge has been checked against a person in Season 4.

## The finding nobody planned for

**The tuned model learned its teacher's habits, not just the guide.** 459 of the 600 training
replies, written by the data generator, open by restating the customer's question. The guide does
not ask for that. The tuned model does it in 260 of 300 test replies; the style guide arm never
does, and the examples arm does it 78 times, copying its 4 examples. Restating makes replies
longer (64 words against 46) and the style judge marks it down: it preferred the guide arm's
reply in 247 of 300 pairs, 4 the other way.

So the two measures disagree. By the guide's checkable rules, the tuned model is best; read as a
whole, the judge prefers the prompted reply. Tuning teaches whatever the training replies do,
including what nobody wrote down, so the targets need checking for habits as well as for facts.

## The scoreboard

**`e7-tuned-short` joins as the Task B reference.** It was E7's dev winner (97 of 100), and on
test its interval (95.3% to 98.9%) sits clear above E1's one-line baseline (0% to 1.3%). It is
the first tuned model to join the season's scoreboard. The primary is the checkable rules and
the facts; the style judge's preference for the prompted replies is reported above and does not
change it.

## What this does not show

- **One run, one seed, one draw of examples.** 4 examples were chosen at random; others might
  avoid the restating habit.
- **Two models.** The tuned arm is a much smaller model than the prompted ones.
- **The targets are a model's replies.** A tuned model trained on replies written by people
  would learn their habits instead.
- **The judges are models, checked only against each other** here. Agreement is not accuracy.
- **Judged rules** (no apology, short sentences, the safety first sentence) are in the style
  judge only, not the primary.

## Charts

`results/charts/`: **`primary`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

Costs are ratios only, answer calls, against `e7-style-guide`: the one-line arm 0.28 times (it
came from the cache, and its prompt is short); the guide with examples 0.48 times, because its
long fixed prefix was billed at the cached rate after the first calls. The judges cost more than
the answers: about 3,300 Gemini calls were made across dev and test, most of them style pairs.
The judge check's 458 Haiku calls cost a small fraction of the main runs. All runs stayed well
within the approved budget.

The tuned model ran on a free Colab T4: 11 minutes of training (337,917 Qwen tokens, peak 9.5
GB), then 4 minutes of predictions for 400 replies. It reads an eighth of the guide arm's input.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e7-teaching-a-house-style/config.yaml
uv run lab adapt analyse episodes/s4-e7-teaching-a-house-style/judge-check/config.yaml
uv run python episodes/s4-e7-teaching-a-house-style/claims.py
```

To tune again: `uv run lab adapt tune episodes/s4-e7-teaching-a-house-style/tune-short-b4.yaml`
prepares the files; a launch needs `--launch --approved-by ...` and the notebook
`season4/colab/lora_job.ipynb` on a GPU. Each job runs once.
