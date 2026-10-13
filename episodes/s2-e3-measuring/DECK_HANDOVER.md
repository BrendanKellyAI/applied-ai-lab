# S2 E3 deck handover: Measuring it

For the content agent building the S2 E3 deck. Written 12 October 2026, after the judge check.
Read `season-2-content-handoff.md` (version 2, 11 October 2026) first, then the S2 E2 handover:
E3 reads E2's run, and the two decks share terms. This document adds only what is specific to
S2 E3.

---

## 1. Sources of truth

1. **`episodes/s2-e3-measuring/README.md`**. Every number and verdict in the deck comes from
   here, word for word where possible.
2. **`.../judge-check/agreement.json`** and **`.../claims.json`**: the figures the README quotes.
3. **`.../PREREGISTRATION.md`**: the original claims, and the two amendments made before any
   mark. The amendments are part of the story (section 4).
4. **`.../charts/*-slide.svg`**: the two E3 charts.
5. **`.../judge-check/judge_check.csv`**: the hand marks and notes, verbatim.
6. **E2's README and log**, for the search-or-model split and any quoted answer.

**Branch: `s2`, not `main`.** Use the `main` URL in the deck; do not test it now.

---

## 2. Names

| | Value |
|---|---|
| Episode code | S2 E3 |
| Title | Measuring it |
| Hub slug | `measuring-it` (proposed: confirm against the hub's `data/episodes/*.yaml`) |
| Repository folder | `episodes/s2-e3-measuring` |
| Deck file | `bk-s2-e3-measuring-it-v1.pdf` |
| Entry format | Teaching episode with an experiment |

The v1 file `bk-s2-e3-search-v1.pdf` is the old E3. Search is now E5, so the hub's S2 E3 entry
needs replacing, not just a new deck.

---

## 3. The story in one paragraph

E2's system answered 54% of questions right. Is that number trustworthy, and what does it
measure? Split by whether search delivered the right passage, the answers were right 85% of the
time when it did (97% without the version questions) and 8% when it did not: the answer number
is mostly a search number. Then the judge: a second model from a third provider agreed with it
on declines 49 of 50 times and on correctness 48 of 50 times, so the not-found and correctness
calls are sound. They split on faithfulness, where the judge is strict: on all 4 split answers,
the phrase it called unsupported is genuinely absent from the passages. One of them is a model
finishing a sentence that a chunk edge had cut off. A person marked 10 items and sided with the
judge on 9 of 10 calls.

---

## 4. Teaching points the deck must carry

The handoff lists what E3 teaches. Each has a home in the results:

| Concept | Where it shows |
|---|---|
| A test set with known answers | E2's 520 items: the evidence labels make search checkable by code |
| Recall at k | Search: 239 of 400 in the top 5 |
| Wilson intervals | Define here, once, for the season. 400 items give about 10 points; 10 items about 40 |
| Correctness and faithfulness | They split: PARA-016 is faithful but not correct; POL-SINGLE-035 is correct but not faithful |
| An LLM judge, and how far to trust it | The whole check |
| Unanswerable questions | The not-found number, and A2 |
| Scoring search and answer separately | The `search-or-model` chart |

**The design changed twice, before any mark.** 50 hand marks became a second model plus 10 by
hand, then the hand marks dropped faithfulness. Say this plainly on the method slide. It is a
practical lesson in itself: a hand check has to be small enough that someone will do it, and
what it does not cover must be named.

---

## 5. Findings, with exact numbers

### Which half failed (descriptive, no claim)

| Right passage in the prompt? | Answers judged right | Interval |
|---|---|---|
| Yes | 204 of 239, 85% | 80% to 89% |
| Yes, no version questions | 199 of 206, 97% | 93% to 98% |
| No | 13 of 161, 8% | 5% to 13% |

### The judge check

| Verdict | Judge and Gemini agree (of 50) | Interval |
|---|---|---|
| Declined | 49 | 90% to 100% |
| Correct | 48 | 87% to 99% |
| Faithful | 46 | 81% to 97% |
| Correct and faithful | 44 | 76% to 94% |

With the person, on 10: judge 9 of 10 on declined and 9 of 10 on correct; Gemini 8 of 10 and
9 of 10.

### Claims: 2 held, 2 failed

- **A1 failed by one:** "correct and faithful" agreement 44 of 50, pass mark 45. 4 of the 6
  splits are faithfulness.
- **A2 held:** declines 49 of 50.
- **A3 held, on 2 items:** the person sided with the judge once (ABSENT-005) and with Gemini
  once (PARA-016). Say it is 2 items every time it appears.
- **A4 failed:** judge and code check tied, 2 and 2, on the only 2 hand items with key values.

### The four faithfulness splits

The answers were right on the facts asked for and each added one claim. Searching the passages
confirms the judge's reason in all four. This is a mechanical check, not a hand mark: say so.

- **POL-SINGLE-035, the best slide:** passage P3 ends mid-sentence at a chunk edge: "...is
  completed within 37 working days of the fault". The answer: "...within 37 working days of the
  fault being confirmed". The model finished the cut sentence itself. This links E2 (chunk
  edges), E3 (faithfulness) and E4 (chunking).
- SHARED-007: added that a boiler gives "intense heat".
- PARA-018: added that another product's steps "differ slightly".
- RESTRICT-STAFF-035: added that safety concerns go "rather than waiting 54 hours".

### Quotes from the hand marks

- PARA-016, the person's note: **"Missed to include a picture"**, marked correct anyway. The
  judge marked it not correct for the same omission. A good slide on how strict "correct" is.
- IDENT-030, the person's note: **"missed Error E-9454 and gave an answer for E-9544"**. The
  system's reply began: "Error E-9454 isn't listed in the provided passages, so I can't confirm
  its meaning. If you meant E-9544, it means the Tessa dishwasher's temperature sensor detected
  overheating during Eco mode". A look-alike code answered instead (links E5).

The replies use Markdown bold; drop the asterisks. No em dashes appear in these quotes.

---

## 6. Charts and their highlights

| File | Shows | Acid green |
|---|---|---|
| `search-or-model-slide.svg` | Answers judged right, by whether the passage was in the prompt | **"Passage not in the prompt"**, 13 of 161: its interval sits below both others |
| `agreement-slide.svg` | Judge and Gemini agreement per verdict, dashed line at 45 of 50 | **"Correct and faithful"**, 44 of 50: the only verdict below its pass mark |

The middle bar of `search-or-model` is a subset of the top bar, not a third group. Say so on the
slide.

---

## 7. Code listing for "Run it yourself"

`judge_prompt` from `src/lab/rag/judge.py`, below `# slide: S2 E3`. A test checks it fits a
slide; copy it exactly:

```python
def judge_prompt(item, passages, answer):
    """What the judge reads: never the evidence labels,
    only what the system was given and what it said."""
    parts = [f"Question: {item.question}"]
    if item.history:
        parts.append(conversation(item.history))
    can = "yes" if item.answerable else "no"
    parts.append(f"{ANSWERABLE}: {can}")
    parts.append(f"Reference answer: {item.answer}")
    given = "\n\n".join(numbered(passages)) or "(none)"
    parts.append(f"Passages given to the system:\n{given}")
    parts.append(f"System's answer:\n{answer.strip()}")
    return "\n\n".join(parts)
```

Beside it, the three definitions from `src/lab/rag/prompts/judge.md` (declined, correct,
faithful), shortened only if they do not fit.

Routes for the slide:

- No key, no cost: `uv run lab rag judge-check report episodes/s2-e3-measuring/judge_check.yaml`
- Count first: `uv run lab rag judge-check second episodes/s2-e3-measuring/judge_check.yaml --estimate`
- Redo it: `draw`, then `second` (needs a Google key), mark 10 by hand, then `report`

---

## 8. Suggested slide outline (17 slides)

1. **Cover:** Measuring it.
2. **Why it matters:** E2 says 54%. A number from an unchecked judge, mixing search and model,
   tells you neither what to fix nor whether to believe it.
3. **Mental model (diagram):** the strip from E2, with two meters: recall at 5 measures stages
   2 to 7, the judge measures the answer. Where it breaks: the judge is a model too.
4. **Concepts:** recall at k, Wilson interval, correct, faithful, declined. One line each, with
   an example from the run.
5. **Method:** the split by search; then the judge check: 50 items, a second model from a third
   provider, 10 by hand, and the two changes made before marking.
6. **Claims and pass marks:** A1 to A4.
7. **One worked example of a test item:** POL-SINGLE-035 as the judge saw it: question,
   reference, the cut P3, the answer, both models' verdicts.
8. **Which half failed (chart `search-or-model`):** 85% against 8%.
9. **What that means:** fixing the model reaches at most 35 wrong answers; fixing search reaches
   147.
10. **Judge agreement (chart `agreement`):** declines and correctness sound; faithfulness splits.
11. **The four added claims:** the table, POL-SINGLE-035 first.
12. **What the person found:** 9 of 10 with the judge; PARA-016 and the picture; IDENT-030.
13. **Claim verdicts:** 2 held, 2 failed, with sizes stated.
14. **What this does not prove:** 10 hand marks chosen for disagreement, agreeing verdicts
    unchecked, faithfulness never hand-marked, one marker, a stratified sample.
15. **Run it yourself:** the `judge_prompt` listing and the routes.
16. **For leaders:** "Ask your team" card: what share of wrong answers is search; who checked
    the judge, on how many items; does "correct" allow additions.
17. **Scoreboard, decision rule and Next, then the series map** (see section 9).

E3 changes no stage, so it adds no scoreboard row. Show E2's row with a note that the answer
and not-found numbers are now checked to the level above.

---

## 9. Decision rule and Next

The handoff's draft: **"Score search and answer separately, include questions your documents
cannot answer, and check your judge before you trust its score."** The run supports all three
parts. Keep it.

Next: **S2 E4 Chunking**, "How should a document be cut up, and what does that decide?" The
cut sentence in POL-SINGLE-035 is the bridge.

---

## 10. Checklist additions for this deck

- [ ] Wilson interval defined here, once, for the season.
- [ ] Every hand-mark figure says "of 10", and A3 says "on 2 items".
- [ ] The design changes are on the method slide, not hidden.
- [ ] "Faithfulness was not checked by a person" wherever the answer number appears.
- [ ] The string search on the four splits is called a mechanical check, not a hand mark.
- [ ] Cross-references: E2 run, E4 chunking, E5 search (look-alike codes), E10 citations.
