# S2 E6 deck handover: Distractors and two-fact questions

For the content agent building the S2 E6 deck. Written 4 October 2026, after the run. Read
`season-2-content-handoff.md` first: its house rules, deck specification, episode anatomy and
checklist all apply. This document adds only what is specific to S2 E6.

---

## 1. Sources of truth

1. **`field-notes/s2-e6-distractors-and-two-facts/README.md`**. Every number and verdict in the
   deck comes from here, word for word where possible.
2. **`.../results/summary.json`**: every figure the README quotes.
3. **`.../PREREGISTRATION.md`**: the claims as fixed before the run, with the amendment that cut
   the run to 72 calls.
4. **`.../results/charts/*-slide.svg`**: the three charts.
5. **`.../results/wrong_answers.csv`**: all 10 wrong replies, verbatim.

**Branch: `season-2`, not `main`.** Season 2 is not merged to `main` until the season is
complete. Use the `main` URL in the deck (it will be right at publication), and do not test it
now.

---

## 2. Names

| | Value |
|---|---|
| Episode code | S2 E6 |
| Title | Field note: look-alike distractors and two-fact questions |
| Hub slug | `distractors-and-two-facts` |
| Repository folder | `field-notes/s2-e6-distractors-and-two-facts` (matches the hub's `lab_path`) |
| Deck file | `bk-s2-e6-distractors-and-two-facts-v1.pdf` |
| Entry format | `field_note` |

---

## 3. The story in one paragraph

S1 E7 found long-context lookup solved: 270 of 270, position irrelevant. Its own README said
the test was too easy. This episode made it harder at 128,000 tokens, in three ways: look-alike
ids, a two-step question, and both together. Each difficulty alone cost nothing (18 of 18
each). Together they cost more than half the answers (8 of 18). The common failure was not
grabbing a look-alike: it was answering the first step (the hangar) instead of the question (the
code). And the models separated for the first time: Terra 6 of 6, Gemini 0 of 6.

---

## 4. Findings, with exact numbers

All at 128,000 tokens. Wilson 95% intervals. 3 claims held, 2 failed, 1 withdrawn.

| Shape | Pooled | Interval | Terra | Sonnet 5 | Gemini |
|---|---|---|---|---|---|
| Single | 18 of 18 | 82% to 100% | 6 of 6 | 6 of 6 | 6 of 6 |
| Distractors | 18 of 18 | 82% to 100% | 6 of 6 | 6 of 6 | 6 of 6 |
| Two-fact | 18 of 18 | 82% to 100% | 6 of 6 | 6 of 6 | 6 of 6 |
| Two-fact + distractors | 8 of 18 | 25% to 66% | 6 of 6 (61% to 100%) | 2 of 6 (10% to 70%) | 0 of 6 (0% to 39%) |

- **H0 held:** control 18 of 18.
- **H1 failed:** distractors alone, 18 of 18, 0 points below Single. (The 3 distractor-value
  replies the claim also needed all came from shape 4.)
- **H2 failed:** two facts alone, 18 of 18, 0 points below Single.
- **H3 held:** the combination, 8 of 18, 55.6 points below both.
- **H4 not tested:** withdrawn before the run (no 16,000-token calls in the reduced run).
- **H5 held:** Gemini (0% to 39%) below Terra (61% to 100%). Sonnet 5 overlaps both; do not rank
  it.

**Wrong replies (10, all shape 4):** 7 intermediate (named the hangar instead of the code: all 6
of Gemini's, 1 of Sonnet 5's), 3 distractor value (all Sonnet 5).

Real replies to quote (from `wrong_answers.csv`):

- Gemini 3.6 Flash, asked for the access code of turbine F-155's hangar: **"5N"**. That is the
  hangar, correctly found. The code was 9571.
- Claude Sonnet 5, item 3, cut off at its 50-token limit: **"I don't have that information in
  the document. The document mentions "Turbine J-150 is stored in hangar 4Y" but does not
  provide an access code for hangar 4"**. The access code sentence was in the document.
- Claude Sonnet 5, item 11: **"9679"**, the access code for hangar 5V, where look-alike U-711
  (one digit from U-211) is stored. The answer was 3494.
- Pilot, 16,000 tokens, Claude Sonnet 5: **"4106 … Turbine F-155 is stored in hangar 4G"**. Hangar
  4G holds F-515, the swap look-alike. Use only as an illustration, labelled as a pilot call.

Descriptive only: bridge first 5 of 9, answer first 3 of 9 on shape 4 (overlapping intervals).

---

## 5. Charts and their highlights

| File | Shows | Acid green |
|---|---|---|
| `shapes-128k-slide.svg` | Accuracy by shape, one bar per model, diamond for pooled | **Two-fact + distractors diamond**: the only shape whose pooled interval clears Single's |
| `models-hardest-slide.svg` | Shape 4 by model, with intervals and "x of 6" labels | **Gemini's "0 of 6" label**: its interval clears Terra's. (The bar is zero height, so the label carries the highlight) |
| `wrong-types-slide.svg` | Wrong replies by type and shape | None; the chart says so. The rule highlights distractor value only if it is the top type in shape 2 or 4, and intermediate leads 7 to 3 |

`length-hardest` was not drawn: the reduced run has one length. Do not make a length slide.

---

## 6. Code listing for "Run it yourself"

From `lookalikes.py`, below the marker comment. A test pins it line for line, so copy it
exactly:

```python
LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"


def look_alikes(target, count, rng):
    """Ids one edit from target, hardest first: for K-417, two
    digits swapped (K-147), a digit changed (K-447), the letter
    changed (X-417). Never a leading zero, so the format holds."""
    letter, d = target.split("-")
    kinds = [
        [f"{letter}-{d[:i]}{d[i + 1]}{d[i]}{d[i + 2 :]}" for i in range(2)],
        [f"{letter}-{d[:i]}{n}{d[i + 1 :]}" for i in range(3) for n in "0123456789"],
        [f"{other}-{d}" for other in LETTERS],
    ]
    found = []
    for kind in [0, 1, 2, 1] * count:
        pool = sorted({x for x in kinds[kind] if x != target and x[2] != "0"} - set(found))
        found += [rng.choice(pool)] if pool and len(found) < count else []
    return found
```

The `pool = ...` line is 91 characters. Check it fits the code panel at the minimum type size.

Reproduce routes for the slide:

- No key, no cost: `uv run lab analyse field-notes/s2-e6-distractors-and-two-facts/config.yaml`
- Count first: `uv run lab estimate field-notes/s2-e6-distractors-and-two-facts/config.yaml`
- Rerun with keys: `uv run lab run field-notes/s2-e6-distractors-and-two-facts/config.yaml --fresh`

---

## 7. Suggested slide outline (14 slides)

1. Cover: Look-alikes and two-step questions at 128,000 tokens.
2. Where S1 E7 left it: 270 of 270, "test the harder shapes of your own task".
3. Four shapes, one example each (F-155, 5N, 9571; look-alikes F-515, F-755, Z-155, F-145).
4. Setup: three models, one novel per item, 128,000 tokens, 72 calls, 6 per model and shape.
5. Each difficulty alone: 18 of 18, three times. H1 and H2 failed.
6. Together: 8 of 18 (chart `shapes-128k`). H3 held.
7. How it failed: 7 of 10 named the hangar. Gemini's "5N".
8. Sonnet 5's misses: a code for the wrong hangar, and "does not provide an access code".
9. The models separate (chart `models-hardest`): Terra 6 of 6, Gemini 0 of 6. H5 held.
10. Wrong types (chart `wrong-types`), nothing highlighted, and why.
11. Built to be checked: manifest rebuild, deviations 0.86% and 0.44 points, no prompt too
    long, one truncated reply.
12. Run it yourself: the `look_alikes` listing and reproduce routes.
13. What this does not prove (section 8).
14. For engineers / for leaders. Ask your team: do we test our hard cases in combination? Do we
    check that the answer is the kind of value asked for? Which model did we test on our
    hardest shape?

---

## 8. What not to say

- **Not "distractors break long context".** H1 failed: look-alikes alone cost nothing, 18 of 18.
- **Not "multi-step questions break long context".** H2 failed: two steps alone, 18 of 18.
- **Not "longer contexts make it worse".** H4 was withdrawn; the run had one length. One pilot
  call failed the same way at 16,000 tokens.
- **Not "Claude Sonnet 5 is worse than Terra" or "better than Gemini".** Its interval (10% to
  70%) overlaps both. Only Gemini against Terra separates.
- **Not "models fall for look-alike ids".** Only 1 of 10 wrong replies followed a look-alike
  turbine. Most stopped at the hangar.
- **Not a percentage without its n.** Every figure is out of 6 or 18; say "8 of 18", not "44%".
- **Do not call the reduced run the full design.** Say it was cut from 432 calls to 72 before
  the run, on cost, and that the cut was pre-registered.
