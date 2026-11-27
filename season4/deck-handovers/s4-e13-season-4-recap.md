# S4 E13 deck handover: Season 4 recap: the adaptation card

For the content agent. No experiment and no new calls: a recap deck built from the scoreboard,
the decision card and the episode handovers. Read the other Season 4 handovers first.

## Sources of truth

- `season4/scoreboard.json`, `season4/reference_history.yaml`.
- `season4/charts/recap.json` and the charts `season4/charts/s4-recap-task-a-slide.svg` and
  `s4-recap-task-b-slide.svg` (from `uv run python season4/recap.py`).
- `season4/decision-card.md` (every rule and question, the path, the scoreboard) and
  `season4/finetune-readiness.md`.
- Each episode's `README.md` and `DECK_HANDOVER.md` under `episodes/s4-e*/`.

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E13 |
| Title | Season 4 recap: the adaptation card |
| Hub slug | `season-4-recap` (proposed; confirm) |
| Deck file | `bk-s4-e13-season-4-recap-v1.pdf` |
| Hub format | `recap` |

## The argument

Season 4 asked how to change what a model does, as opposed to what it knows, on two tasks for
one invented firm: triage of customer messages (Task A) and replies in a house style (Task B).
It climbed from one line of prompt to tuned models, and kept a strict rule for what counted as
progress: a rung joined only if its interval on test sat clear above the reference's.

1. **Writing the rules down did most of the work.** Triage went from 521 to 587 of 600 with
   definitions (E2); the house style went from 0 to 215 of 300 with the style guide (E7).
2. **On triage, nothing after that joined.** Similar examples, a schema, a tuned small model and
   a small model taught by a big one all matched the definitions prompt (589 to 594); none
   cleared it.
3. **On the house style, tuning won.** A 0.6 billion parameter model tuned on 600 replies passed
   every rule on 293 of 300, against 262 for the best prompt: the season's one case of tuning
   beating a prompt.
4. **Tuning has limits and running costs.** It did not teach facts (E8: 26 of 400 against 354
   for retrieval) and took away "I don't know"; a tuned reply writer carried its voice into
   ordinary requests (E10); the tuned model ran unchanged on a laptop (E11); and one provider
   is withdrawing tuning altogether.

42 claims were pre-registered: 34 held, 7 failed, 1 not tested. The failures were mostly good
news for the reader: the baseline was stronger than predicted (E1, 3 claims), and only one of
two tuned models broke outside its task (E10, 3 claims).

## Recap slides: the two ladders

Charts: `s4-recap-task-a-slide.svg` (reference highlighted: E2) and `s4-recap-task-b-slide.svg`
(reference highlighted: E7's tuned model).

| Task A, triage: fully right of 600 | Score | Joined? |
|---|---|---|
| E1 one-line prompt | 521 | The baseline |
| E2 + written definitions | **587** | Joined: the reference |
| E3 + 8 similar examples | 593 | No |
| E4 + JSON mode | 594 | No |
| E5 small model tuned on 1,600 true labels | 592 | No |
| E9 small model tuned on a big model's labels | 589 | No |

| Task B, house style: passes every rule of 300 | Score | Joined? |
|---|---|---|
| One-line prompt | 0 | The baseline |
| + style guide | 215 | (E7's prompted arm) |
| + guide and 4 examples | 262 | (E7's best prompt) |
| Small model tuned on 600 replies | **293** | Joined: the reference |

Task B's prompted rows come from E7's analysis, not the scoreboard, which lists only the
baseline and what joined.

## What a total hides

Item by item, matching totals were not the same answers. Use one or two of these:

| Comparison | Items each way | Source |
|---|---|---|
| E3: the same 8 examples in a different order | 14 and 13 changed; total unchanged (p 1.0) | E3 `claims-test.json`, C4 |
| E5: tuned small model against definitions prompt | 12 and 7 (p 0.36) | E5 `claims-test.json`, C2 |
| E9: student against its teacher | 12 and 10 (p 0.83) | E9 `claims-test.json`, C3 |
| E7: tuned against the best prompt, house style | 36 and 5 (p below 0.0001) | E7 `claims-test.json`, C3 |
| E10: reply writer against untuned, declines | 11 and 24 (p 0.041) | E10 `claims.json` |

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 521, 587 of 600 | Triage: one line, then definitions | `scoreboard.json` |
| 0, 215, 262, 293 of 300 | House style: one line, guide, guide and examples, tuned | `recap.json` |
| 65 of 65 | Safety incidents caught by the definitions prompt (E2) and the tuned models of E5 and E9 (E6's 800 example model: 64) | E2, E5, E6, E9 READMEs |
| an eighth | The tuned model's input against the definitions prompt's | E5 README |
| 800 | Labelled examples where E6's curve matched the prompt | E6 README |
| 26 against 354 of 400 | Facts: tuned on the library against retrieval | E8 README |
| 41 of 100 | Ordinary requests answered as a customer reply by the tuned reply writer | E10 README |
| 600 of 600 | Identical answers on a laptop and a GPU | E11 README |
| 34, 7, 1 of 42 | Claims held, failed, not tested | `recap.json` |
| about 3.5 hours | Free Colab GPU time across 14 jobs | `season4/README.md` |

## Slide ideas

Follow the deck rules: a reader prediction revealed on the very next slide, varied visual forms,
one-line titles, no claim-verdict slides, and the last slide is the series map.

1. **Two tasks, one question.** Triage and house style; "how do we make it do what we want?"
2. **Prediction.** "Which moved the score most: definitions, examples, a schema or tuning?"
3. **Reveal.** Definitions, on both tasks. The Task A ladder chart.
4. **Then the ceiling.** Four approaches matched E2 on triage; none cleared it.
5. **Prediction.** "Did tuning ever beat the best prompt?"
6. **Reveal.** Once: the house style, 293 against 262. The Task B ladder chart.
7. **What a total hides.** E3's reordered examples: 27 answers changed, total the same.
8. **Where tuning stops.** Facts (E8) and leaks (E10), one number each.
9. **Keeping a tuned model.** A provider withdrawing tuning; the laptop (E11).
10. **The card.** The decision path from `decision-card.md`, one slide.
11. **Where the series goes next** (below), then the series map as the last slide.

## For leaders

**Ask your team:** "Before we tune anything, have we written down the rules we would give a new
member of staff, and measured what that alone does?"

## Decision rule (proposed)

**"Write the rules down first; tune only for a gap that survives them, and budget for keeping
the tuned model, not just building it."**

## Next

Season 5. Hand-offs from this season:

| From | Leaves to |
|---|---|
| E5, E6, E12 | S6: total cost of ownership of tuning and hosting |
| E6, data generation | S7: preparing and labelling data at scale |
| all | S8: building your own evaluations (S4 used fixed ones) |
| E4 | S5: tool calling and agents |
| E8, E9 | S11: training data leaving your systems, and data poisoning |
| E11 | S13: serving speed, quantisation and hardware |
| E10, E12 | S15: model risk records and controls |

## Careful with

- **Halvard Home is invented;** two tasks, one firm, one small open model (Qwen3-0.6B) and the
  cheapest API models. A worked case, not a rule.
- **"Matched" means no measurable difference** on 600 messages, not identical answers.
- **Tuning beat the prompt once,** on a style task with a written guide and 600 good examples.
- **Charts:** the Task A ladder's axis starts near 80% (the chart library's default), which
  makes the gaps look larger than they are. Label the counts on the bars.
- **No money:** prices are never shown; break-even is Season 6.

## From practice

_Brendan to add one anonymised line from his own practice._
