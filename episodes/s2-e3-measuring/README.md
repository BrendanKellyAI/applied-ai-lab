# S2 E3: Measuring it

The code behind S2 E3, Measuring it. E2 built the simplest complete RAG system and scored it.
This episode asks how far those scores can be trusted, and which half of the system failed when
an answer was wrong. It makes no new answer call: it reuses the E2 baseline run.

Two questions:

1. **Which half failed?** Split E2's answers by whether search put the right passage in the
   prompt. If the answers are good when the passage is there and bad when it is not, the
   problem is search.
2. **Can the judge be trusted?** E2's answer and not-found numbers come from an LLM judge,
   `claude-sonnet-5-5`. E3 checks it against a second model and a person.

The claims and pass marks are in [`PREREGISTRATION.md`](PREREGISTRATION.md). They were fixed
before any mark or second-model call, then amended twice before any mark, as recorded there.

## Which half failed

Recall at 5 measures search: the share of the 400 answerable questions whose right passage was
in the top 5 sent to the model. It was 239 of 400 (55% to 64%). The answer number measures the
whole system: 217 of 400 judged correct and faithful (49% to 59%). Splitting the answers by
whether search did its job separates the two:

| Right passage in the prompt? | Answers judged right | 95% interval |
|---|---|---|
| Yes | 204 of 239, 85% | 80% to 89% |
| Yes, leaving out the 33 version questions | 199 of 206, 97% | 93% to 98% |
| No | 13 of 161, 8% | 5% to 13% |

When search delivered the passage, the model nearly always answered well, apart from the
version questions, where it saw an old and a current policy side by side and would not choose
between them (E2). When search missed, the model was almost never right. The 13 it got right
were answered from the superseded copy of the same policy, which held the same unchanged fact.

So in this system the answer number is mostly a search number. Improving the model or the
prompt can lift at most the 35 wrong answers whose passage was in the prompt; improving search
reaches the 147 whose passage never got there. This is descriptive: E2's results were
published before E3, so no claim about them was pre-registered.

Every number here is a Wilson 95% interval: the range the true rate is likely to sit in, given
how many items it was measured on. At 400 items the range is about 10 points wide; at 10 items
it is about 40.

## Can the judge be trusted

### The design

- **The sample:** 50 of E2's 520 items, drawn by `lab rag judge-check draw` with seed 2026: 3
  from each of the 16 item types, spread across the judge's outcomes (right, wrong, declined),
  then 2 more at random.
- **A second model:** `gemini-3.6-flash` at reasoning `medium`, from Google, so from neither
  the answer model's provider (OpenAI) nor the judge's (Anthropic). It is independent, not
  stronger. It got the judge's exact instructions and the exact prompt the judge got for each
  item: the question, whether the library can answer it, the reference answer, the five
  passages and the system's answer.
- **A person:** Brendan Kelly marked the 10 items where the two models disagreed most, blind to
  both verdicts, from the question, the reference answer and the system's answer. He marked
  `declined` and `correct`. He did not read the passages, so no person checked `faithful`.

The original plan was 50 items marked by hand. It was cut to 10 before any marking, because 50
was more than the owner would mark. That is a limit on everything below.

### Results

Agreement between the judge and the second model, on all 50:

| Verdict | Agree | 95% interval |
|---|---|---|
| Declined | 49 of 50 | 90% to 100% |
| Correct | 48 of 50 | 87% to 99% |
| Faithful | 46 of 50 | 81% to 97% |
| Correct and faithful (the answer number's verdict) | 44 of 50 | 76% to 94% |

Agreement with the person, on the 10 items where the models disagreed most:

| | Declined | Correct |
|---|---|---|
| Judge | 9 of 10 | 9 of 10 |
| Second model | 8 of 10 | 9 of 10 |

Six of the person's `declined` marks were not clicked on the marking page. He confirmed them
all as "no": in each, the system gave an answer. The notes in `judge_check.csv` say so.

### The claims

**A1 failed, by one item: the two models agree on the answer verdict 44 of 50 times.** The
pass mark was 45. The split is almost all about faithfulness, not correctness: of the 6 items
where they disagree on "correct and faithful", 4 are answers both models called correct, which
the judge called unfaithful and Gemini called faithful.

**A2 held: they agree on declines 49 of 50 times.** The not-found number rests on this verdict.

**A3 held, on 2 items: where the models split on correctness, the person sided with the judge
once and with Gemini once.** Two items cannot say much.

- *PARA-016:* the person and Gemini marked it correct; the judge did not, because the answer
  left out the photo the reference answer asks for. The person's note says the same thing,
  "Missed to include a picture", but he still counted it correct. The judge is stricter than
  the person here.
- *ABSENT-005:* the question cannot be answered from the documents, and the system said so,
  then added related detail. The person and the judge marked it correct; Gemini did not. The
  person also marked it declined, while both models did not, which is the one decline the
  judge and the person disagree on.

**A4 failed: the judge and the code check matched the person equally often, on 2 items each.**
Only 2 of the 10 hand-marked items had key values for the code check to test. The run cannot
separate the two.

### The faithfulness question

On the 4 answers the judge called unfaithful and Gemini called faithful, the judge gave a
reason that names a specific phrase not in the passages. No person read the passages, but each
of those reasons can be checked by searching the passage text, and in all 4 the phrase the
judge named is not there:

| Item | What the answer added |
|---|---|
| POL-SINGLE-035 | "within 37 working days of the fault **being confirmed**": passage P3 is cut by a chunk edge after "of the fault", and the model finished the sentence itself |
| SHARED-007 | that a boiler gives "intense heat"; no passage says so |
| PARA-018 | that the Orrin heat pump's steps "differ slightly"; no passage says so |
| RESTRICT-STAFF-035 | that safety concerns are escalated "rather than waiting 54 hours"; the passage says only to use the safety escalation process |

In each case the answer was right on the facts asked for and added a small claim of its own.
The judge applies its rule, that every claim must be supported, strictly. Gemini does not.
Whether such an addition should cost an answer its "right" mark is a choice about the rule,
not a fault in either model. The string search above is a mechanical check of the judge's
stated reason, not a hand mark.

### What the judge can be trusted for

- **Declines:** yes. 49 of 50 with the second model, 9 of 10 with the person.
- **Correctness:** yes, with a strict reading of the reference answer. 48 of 50 with the second
  model, 9 of 10 with the person. Estimated across the 50, counting the items where both models
  agree as right: 49 of 50 (90% to 100%). That estimate assumes two models from different
  providers that agree are correct, which nobody checked.
- **Faithfulness:** it is strict and, on the 4 checked reasons, accurate about what the passages
  say. But no person has marked faithfulness, so E2's answer number, which needs it, carries
  this caveat. Counting correctness alone, E2's answers were 227 of 400 (52% to 62%), against
  217 of 400 correct and faithful.

### A fresh call, by accident

When E4 re-ran the E2 reference, 32 of its judge calls were not in the cache and were made
again, all on restricted items (`judge-rerun/raw-judge.jsonl`). Why they were missing is not
known. The judge gave the same verdict on 31 of the 32. The one that changed was
RESTRICT-STAFF-035, one of the four faithfulness splits above: called unfaithful in E2, faithful
on the fresh call. So the judge's borderline faithfulness calls can go either way between calls.
This is 32 items, not a planned measurement of the judge's variance.

## What this does not show

- **10 hand marks, chosen for disagreement.** They show which model to believe when the two
  split, not how often either is right in general, and 10 items give intervals about 40 points
  wide.
- **Shared verdicts are not checked.** Where the judge and Gemini agree, nobody looked. Two
  models can share a blind spot.
- **Faithfulness was never marked by a person.**
- **One marker.** No second person marked the same items.
- **A stratified sample.** Rare item types are over-represented, so the 50 are not a
  proportional picture of the 520.
- **One run of each model,** apart from the 32 re-judged items above. Calls are cached and no temperature is sent, so the same verdicts
  come back; how much a fresh call would vary is not measured.

## Charts

Drawn by `chart.py` from committed results alone, at slide and article sizes, in `charts/`.

- **`agreement`**: how often the judge and Gemini agree, for each verdict, with intervals,
  counts and a dashed line at the 45-of-50 pass mark. Acid green marks the verdict below its
  pass mark when exactly one is; here, "Correct and faithful", 44 of 50.
- **`search-or-model`**: E2's answers judged right, split by whether the right passage was in
  the prompt, with intervals and counts. Acid green marks "Passage not in the prompt" when its
  interval sits below both others; here it does, at 13 of 161.

## Tokens and cost

The second model's 50 calls: 80,375 input and 26,614 output tokens, of which 23,804 were
thinking, at a list-price cost of $0.16 on 12 October 2026 ($0.75 per million input tokens and
$3.75 per million output). Every call returned a verdict on the first attempt. The model
returned `gemini-3.6-flash` on every call.

## Run it

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

**Rebuild the report, claims and charts from committed results.** No key, model or network:

```bash
uv run lab rag judge-check report episodes/s2-e3-measuring/judge_check.yaml
```

```bash
uv run python episodes/s2-e3-measuring/claims.py
```

```bash
uv run python episodes/s2-e3-measuring/chart.py
```

**Check the cost of the second model before calling it.** No key needed:

```bash
uv run lab rag judge-check second episodes/s2-e3-measuring/judge_check.yaml --estimate
```

**Redo the check yourself.** `draw` picks the 50 and writes a blind marking sheet; `second`
runs the second model (needs `GOOGLE_API_KEY` or `GEMINI_API_KEY`) and rewrites the sheet for
the 10 items to mark by hand; fill in `judge-check/judge_check.csv` with y or n; then `report`.
Neither command overwrites marks already started.

## Files

- `PREREGISTRATION.md`: the claims and pass marks, and the two amendments made before any mark.
- `judge_check.yaml`: the run checked, the sample settings, the second model and the hand
  fields.
- `judge-check/sample.json`: the 50 items, the 10 marked by hand, the judge's instructions hash.
- `judge-check/judge_check.md`: the marking sheet for the 10, as the judge saw each item.
- `judge-check/judge_check.csv`: the hand marks.
- `judge-check/second/`: the second model's raw calls and verdicts.
- `judge-check/agreement.json`: the report.
- `claims.py`, `claims.json`: the claims applied to the report.
- `chart.py`, `charts/`: the two charts.

The code is in `src/lab/rag/judge_check.py`, `judge_second.py` and `judge_check_cli.py`. The
judge's instructions are in `src/lab/rag/prompts/judge.md`, and the judge prompt is
`judge_prompt` in `src/lab/rag/judge.py`, below the marker `# slide: S2 E3`.
