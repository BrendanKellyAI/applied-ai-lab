# S4 E12 deck handover: Prompt, retrieve, or tune?

For the content agent. No experiment and no new calls: the season's decision card, built from
E1 to E11.

## Sources of truth

- `season4/decision-card.md` (the card itself, final).
- `season4/finetune-readiness.md` (the checklist the card points to).
- `season4/scoreboard.json`, `season4/reference_history.yaml`.
- Each episode's `README.md` and `DECK_HANDOVER.md` under `episodes/s4-e*/`, for any figure
  quoted below.
- The provider policy, illustrative: `src/lab/providers/capabilities.yaml` (sources and the date
  read, 22 November 2026).

Branch `s4`.

## Names

| | Value |
|---|---|
| Episode code | S4 E12 |
| Title | Prompt, retrieve, or tune? |
| Hub slug | `choosing-the-fix` (as on the hub) |
| Deck file | `bk-s4-e12-choosing-the-fix-v1.pdf` |
| Hub format | `decision_framework` |

## The argument

Season 4 tried every way of changing a model's behaviour on two tasks, from one line of prompt to
a tuned model. The answer to "should we fine-tune?" was nearly always "not yet": writing the
rules down did most of the work, and tuning only cleared a gap the best prompt left once, for a
house style.

The card turns that into a path: name the gap; if it is knowledge, retrieve; if it is
behaviour, write the rules down, then add examples, then a schema if code reads the output; tune
only when a measured gap remains, you have labelled data and the volume pays back the training;
and budget for keeping a tuned model, not just building it.

## Scoreboard slide

The season's final ladders (chart: build from `scoreboard.json`, or reuse E9's Task A chart).

| Task | Rung | Score on test | Joined? |
|---|---|---|---|
| A, triage | E1 one-line prompt | 521 of 600 | The baseline |
| A | E2 + written definitions | **587** (96.3% to 98.7%) | Joined: the reference |
| A | E3 + 8 similar examples | 593 | No: overlaps |
| A | E4 + JSON mode | 594 | No |
| A | E5 small model tuned on 1,600 true labels | 592 | No |
| A | E9 small model tuned on a big model's labels | 589 | No |
| B, house style | E1 one-line prompt | 0 of 300 | The baseline |
| B | E7 small model tuned on 600 replies | **293** (95.3% to 98.9%) | Joined: the reference |

What E12 adds: the reading. On Task A, written definitions set a bar nothing later cleared,
though four approaches matched it. On Task B, tuning beat the best prompt (262 of 300).

## Setup before results

The card has six steps (`decision-card.md`, "The path on one screen"):

| Step | Ask | If yes |
|---|---|---|
| 1 | Is the gap knowledge? | Retrieve; do not tune |
| 2 | Has the model been told the rules? | Write them down and measure |
| 3 | Do the rules leave room? | Add a few examples, chosen to match |
| 4 | Does code read the output? | Schema, and still validate |
| 5 | Is a measured gap left, or a smaller model worth having? | Tune, if labelled data, a test set and volume are there |
| 6 | Will you keep it? | Budget for rebuilding, upkeep and regression checks |

Stop at the first step that clears your bar.

## Evidence

| Figure | What it measures | Source |
|---|---|---|
| 26 and 354 of 400 | Right: small model tuned on the library, against retrieval | E8 README |
| 0 of 120 | Unanswerable questions the library-tuned model declined (untuned 78) | E8 README |
| 521 to 587 of 600 | Triage, one line to written definitions | `scoreboard.json` |
| 0 to 215 to 262 of 300 | House style: one line, the guide, the guide and 4 examples | E7 README |
| 293 of 300 | House style, tuned small model | `scoreboard.json` |
| 592 of 600, an eighth of the input | Tuned small model matching the definitions prompt | E5 README |
| 800 labels | Where E6's learning curve matched the prompt (200 did not; 1,600 added nothing measurable) | E6 README |
| 589 of 600 | Small model tuned on `gpt-6-luna`'s labels | E9 README |
| 41 of 100 | Ordinary requests the tuned reply writer answered as a customer reply | E10 README |
| 600 of 600 identical; 19 times slower | The tuned model on a 2018 laptop against a free GPU | E11 README |
| 6 and 14 January 2027 | OpenAI ends self-serve tuning jobs, then shuts down tunable base models (illustrative, read 22 November 2026) | `capabilities.yaml` |

## Cost

No calls in E12. The season's paid runs all stayed within their approved budgets, shown as
ratios in each README; tuning used only free Colab GPU time.

## Slide ideas

Follow the deck rules: a reader prediction revealed on the very next slide, varied visual forms,
one-line titles, no claim-verdict slides, and the last slide is the series map.

1. **"Should we fine-tune?"** The question a team brings.
2. **Prediction.** "On Halvard's two tasks, how often did tuning beat the best prompt?" Reader
   picks: both, one, neither.
3. **Reveal.** Once: the house style (293 against 262). On triage, tuning matched the prompt.
4. **The path.** The six steps, as a flow diagram.
5. **Step 1: knowledge is not behaviour.** E8's 26 against 354.
6. **Step 2: write the rules down.** The cheapest and largest jump on both tasks.
7. **Step 3: examples, where the rules leave room.**
8. **Step 5: when tuning pays.** A measured gap, labelled data (E6's curve), a smaller model
   (E5), and labels a big model can write (E9).
9. **Step 6: keeping it.** A provider withdrawing tuning; E10's leaks; E11's laptop.
10. **The readiness checklist,** one slide, six section headings.
11. **Series map** (last slide), E12 marked.

## For leaders

**Ask your team:** "For each AI problem we have, is it knowledge or behaviour, and have we
written the rules down before paying to tune?"

## Decision rule (proposed)

**"Prompt first, add examples second, and tune only when a measured gap remains, you have
labelled data, and the volume pays back the training."**

## Next

E13, Season 4 recap: the adaptation card.

## Careful with

- **Two tasks, one invented company.** Halvard's numbers are a worked case, not a rule.
- **"Matched" means no measurable difference** on 600 messages, not identical.
- **The provider policy is illustrative,** from the providers' pages on 22 November 2026; quote
  it with that date and say it may have changed.
- **No money on the card.** Break-even between tuning, hosting and API calls is Season 6.
- **Tuning beat the prompt once,** on a style task with a clear written guide and 600 good
  examples. Do not generalise to "tuning wins on style".

## From practice

_Brendan to add one anonymised line from his own practice._
