# S2 E6: Distractors and two-fact questions

## Summary

**At 128,000 tokens, look-alikes alone and two-step questions alone cost nothing. Together they
broke the lookup: 8 of 18 correct.** Three current models read a public-domain novel with
invented sentences inserted. Each easy shape scored 18 of 18 (82% to 100%): a single fact, the
same fact among four look-alike ids, or a two-step question (which hangar the turbine is in,
then that hangar's access code). The two-step question with look-alikes for both steps scored
8 of 18 (25% to 66%).

- **The models separated on the hard shape, which S1 E7 could not show.** GPT-5.6 Terra 6 of 6,
  Claude Sonnet 5 2 of 6, Gemini 3.6 Flash 0 of 6. Gemini's interval (0% to 39%) sits wholly
  below Terra's (61% to 100%).
- **The common failure was stopping halfway, not picking the look-alike.** Of the 10 wrong
  replies, 7 named the turbine's own hangar instead of its access code: all 6 of Gemini's, and
  one cut-off reply from Claude Sonnet 5. The other 3 were Claude Sonnet 5 giving another
  hangar's access code.
- 3 of 6 pre-registered claims held (H0, H3, H5), 2 failed (H1, H2), and 1 was withdrawn before
  the run (H4).

This was a reduced run, 72 calls at one length with 6 items per model and shape, so every
interval is wide. The direction is clear; the size is not.

## The question

Do look-alike passages and two-fact questions break a long-context lookup at 128,000 tokens?

S1 E7 found three current models retrieved one invented fact from a novel in 270 of 270 calls,
at any position up to 64,000 tokens, and named what it did not test: look-alike distractors,
questions that need two facts, and longer documents. S2 E1 assigned that gap to this episode.
It is the long-context side of S2 E1's choice: when the whole document fits the window, does
sending it still work once the task is harder than one out-of-place sentence?

## Setup

| | |
|---|---|
| Models | GPT-5.6 Terra, Claude Sonnet 5, Gemini 3.6 Flash, as S1 E7 |
| Reasoning | Off for Terra and Sonnet 5; Gemini 3.6 Flash at `minimal`, its lowest level |
| Temperature | Provider default for all three |
| Output limit | 50 tokens for Terra and Sonnet 5; 1,024 for Gemini |
| Length | 128,000 tokens (`o200k_base`) |
| Shapes | 4, below |
| Items | 6 per model and shape: one per book, three bridge first and three answer first |
| Calls | 3 models x 4 shapes x 6 items = 72, plus a 15-call pilot |
| Run | 4 October 2026, 15:30 to 16:09 UTC |
| Intervals | Wilson 95% |

Every setting is in [`config.yaml`](config.yaml). Every model returned the exact version
requested: `gpt-5.6-terra`, `claude-sonnet-5`, `gemini-3.6-flash`.

## Method

**Four shapes.** Each item has a turbine id (`F-155`), a hangar (a digit and a letter, `5N`) and
four-digit codes, all generated from the seed and absent from the book text.

| Shape | Inserted | Question |
|---|---|---|
| 1. Single | "The maintenance code for turbine F-155 is 5496." | What is the maintenance code for turbine F-155? |
| 2. Distractors | Shape 1, plus the same sentence for four look-alike ids (`F-515`, `F-755`, `Z-155`, `F-145`) with their own codes | As shape 1 |
| 3. Two-fact | "Turbine F-155 is stored in hangar 5N." and "The access code for hangar 5N is 9571." | What is the access code for the hangar where turbine F-155 is stored? |
| 4. Two-fact + distractors | Shape 3, plus two look-alike turbines in other hangars, the access codes for those hangars, and access codes for two hangars with no turbine | As shape 3 |

The single fact sits at a seeded position between 25% and 75%. In the two-fact shapes, one
sentence sits between 10% and 30% and the other between 70% and 90%; the bridge comes first on
three items and the answer on three. Look-alikes sit anywhere from 0% to 100%, at least 10
points from the target and from each other.

**Paired design.** For a given item, all four shapes share one filler passage, and the target
sentences sit at the same positions. Only the inserted sentences change.

**Filler, prompt and scoring, as S1 E7.** Filler is a public-domain novel, trimmed and measured
with `o200k_base`, with each sentence inserted at the sentence boundary nearest its target
position. The system prompt is "Answer using only the document provided. Reply with the value
only." The user prompt is the document in `<document>` tags, then the question. A reply is
correct when it contains the expected value as a whole token and was not cut short.

**Every wrong reply gets a type**, checked in this order: *distractor value* (it names a value
from a look-alike sentence), *intermediate* (in a two-fact shape, it names the turbine's own
hangar), *other* (anything else). Every wrong reply is in
[`results/wrong_answers.csv`](results/wrong_answers.csv), read by hand.

### The look-alike generator on the slide

Every look-alike id comes from this function in [`lookalikes.py`](lookalikes.py), pinned line
for line by a test. It draws one edit of each kind in turn, hardest first, so shape 4's two
look-alike turbines are always a swap and a changed digit.

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

### Source books

S1 E7's books, pinned by SHA-256, with one replacement. Frankenstein's prose is 87,723 tokens
long after the front matter, too short for 128,000.

| Items | Book | Author | Gutenberg ID |
|---|---|---|---|
| 0, 1 | Pride and Prejudice | Jane Austen | 1342 |
| 2, 3 | Moby Dick; or, The Whale | Herman Melville | 2701 |
| 4, 5 | Great Expectations | Charles Dickens | 1400 |
| 6, 7 | A Tale of Two Cities | Charles Dickens | 98 |
| 8, 9 | Dracula | Bram Stoker | 345 |
| 10, 11 | Jane Eyre | Charlotte Brontë | 1260 |

The run used items 0, 3, 4, 7, 8 and 11. See [`datasets/README.md`](../../datasets/README.md)
for licences.

## Claims

Pre-registered in [`PREREGISTRATION.md`](PREREGISTRATION.md) and amended before the run, when the
grid was cut from 432 calls to 72. Pooled across the three models: 18 calls per shape, 6 per
model.

| Claim | Pass mark | Measured | Verdict |
|---|---|---|---|
| H0. The control holds at 128,000 | each model 5 or more of 6, pooled 17 or more of 18 | 6, 6, 6 of 6; pooled 18 of 18 | **Held** |
| H1. Distractors cost accuracy | 10 or more points below Single, and 3 or more distractor-value replies | 18 of 18 against 18 of 18, 0 points; 3 distractor-value replies, all in shape 4 | **Failed** |
| H2. Two facts cost accuracy | 10 or more points below Single | 18 of 18 against 18 of 18, 0 points | **Failed** |
| H3. The combined shape is hardest | 5 or more points below both shape 2 and shape 3 | 8 of 18, 55.6 points below both | **Held** |
| H4. Length matters for the hardest shape | 16,000 against 128,000 | Withdrawn before the run: no 16,000-token calls | **Not tested** |
| H5. The models separate | one pair with non-overlapping intervals on shape 4 | Gemini 0 of 6 (0% to 39%) below Terra 6 of 6 (61% to 100%) | **Held** |

H1 failed on its first part: look-alikes alone cost nothing. Its second part was met only by
replies to shape 4.

## Results

### Accuracy at 128,000 tokens ([`shapes-128k`](results/charts/shapes-128k-slide.svg))

| Shape | GPT-5.6 Terra | Claude Sonnet 5 | Gemini 3.6 Flash | Pooled | 95% interval |
|---|---|---|---|---|---|
| Single | 6 of 6 | 6 of 6 | 6 of 6 | 18 of 18 | 82% to 100% |
| Distractors | 6 of 6 | 6 of 6 | 6 of 6 | 18 of 18 | 82% to 100% |
| Two-fact | 6 of 6 | 6 of 6 | 6 of 6 | 18 of 18 | 82% to 100% |
| Two-fact + distractors | 6 of 6 | 2 of 6 | 0 of 6 | 8 of 18 | 25% to 66% |

The chart highlights the pooled diamond for two-fact + distractors: its interval (25% to 66%)
clears Single's (82% to 100%). It is the only shape that does.

### The models on the hardest shape ([`models-hardest`](results/charts/models-hardest-slide.svg))

| Model | Correct | 95% interval |
|---|---|---|
| GPT-5.6 Terra | 6 of 6 | 61% to 100% |
| Claude Sonnet 5 | 2 of 6 | 10% to 70% |
| Gemini 3.6 Flash | 0 of 6 | 0% to 39% |

The chart highlights Gemini's "0 of 6" label: its interval clears Terra's. Claude Sonnet 5's
interval overlaps both, so the data do not place it.

### How the wrong replies went wrong ([`wrong-types`](results/charts/wrong-types-slide.svg))

All 10 wrong replies were on shape 4. Shapes 1 to 3 had none.

| Model | Item | Expected | Reply | Type |
|---|---|---|---|---|
| Gemini 3.6 Flash | all 6 | the access code | the turbine's hangar, such as `5N` | Intermediate |
| Claude Sonnet 5 | 3 | 6993 | "I don't have that information in the document. The document mentions "Turbine J-150 is stored in hangar 4Y" but does not provide an access code for hangar 4" (cut off at 50 tokens) | Intermediate, truncated |
| Claude Sonnet 5 | 7 | 7751 | 7691: the code for hangar 1X, which holds no turbine | Distractor value |
| Claude Sonnet 5 | 8 | 5561 | 7039: the code for hangar 5H, which holds no turbine | Distractor value |
| Claude Sonnet 5 | 11 | 3494 | 9679: the code for hangar 5V, where look-alike U-711 is stored | Distractor value |

- **Gemini found the right hangar every time, then stopped.** On shape 3, with no look-alikes, it
  gave the access code on 6 of 6. With look-alikes added, it replied with the hangar on 6 of 6:
  the first step of the question, correct, and not what was asked.
- **Claude Sonnet 5 went wrong on the second step.** Only one of its errors followed a look-alike
  turbine (U-711, a changed digit). Two were codes for hangars that hold no turbine at all. On
  item 3 it found the right bridge sentence, then said the access code was not in the document,
  though it was.
- **The highlight rule is not met.** The wrong-types chart highlights the distractor-value bar
  only if it is the largest type in shape 2 or 4. In shape 4, intermediate leads 7 to 3, so the
  chart says nothing is highlighted.

**Bridge first against answer first** (descriptive, not a claim): on shape 4, 5 of 9 correct
with the bridge first and 3 of 9 with the answer first. The intervals (27% to 81%, 12% to 65%)
overlap. On shape 3, both orders scored 9 of 9.

**The pilot's 16,000-token calls** (outside the run, not in any claim): 11 of 12 correct. The
one miss was again Claude Sonnet 5 on shape 4, giving the code for the hangar of look-alike
F-515 (a swap): "4106 … Turbine F-155 is stored in hangar 4G". The look-alike's bridge sentence
is "Turbine F-515 is stored in hangar 4G." So the failure is not only a 128,000-token one, but
one call at 16,000 cannot show how often it happens there.

## Built to be checked

| Check | Result |
|---|---|
| 1. Dataset rebuild matches `results/dataset_manifest.json` (SHA-256 of all 144 documents) | Matches |
| 2. Length and position deviations against tolerances | Largest 0.86% (tolerance 5%) and 0.44 points (tolerance 2) |
| 3. Single shape against S1 E7 | 18 of 18 at 128,000; 3 of 3 in the pilot at 16,000. 64,000 not run |
| 4. Truncated replies | 1: Claude Sonnet 5, shape 4, item 3, scored incorrect |
| 5. Reasoning tokens | Terra and Sonnet 5 reported 0 on all 24 calls. Gemini reported none; at most 4 output tokens on any call (mean 3.5), which includes any reasoning |
| 6. Wrong-answer classifier | All 10 rows in `wrong_answers.csv` read by hand; every type matches the reply |
| 7. Prompts rejected as too long | None. Claude Sonnet 5's largest prompt was 185,683 tokens |

Every build check fails the build rather than warning. Each id, hangar and code is absent from
the book text and unique within its document; each look-alike is exactly one edit from its
target; no question contains its answer or the hangar; lengths and positions fall within
tolerance.

On check 6: Claude Sonnet 5's truncated reply on item 3 is a refusal that names the hangar. The
pre-registered order types it as intermediate, ahead of other, and it is kept that way. It
changes no claim: H1 counts only distractor-value replies.

**Tokenisers.** For the same 128,000-token documents, Claude Sonnet 5 counted 1.42 times as many
input tokens as `o200k_base` (4,355,353 against 3,071,141). Gemini counted 1.01 times as many,
and Terra the same.

## What it means

**Sending a whole 128,000-token document still works for a single lookup, even with look-alikes,
and for a two-step lookup, with these three models. It stopped working when the two were
combined.** One out-of-place fact, the same fact among four ids one character apart, or a
two-step chain: 54 of 54 correct across those three shapes. The two-step chain with look-alikes
at each step: 8 of 18.

- **Test the combination, not the parts.** Each difficulty passed on its own, so a test suite
  that checks distractors and multi-step questions separately would have passed too.
- **Check that the answer is the kind of value asked for.** Seven of the ten failures were a
  hangar given where a four-digit code was asked for. A format check would catch every one of
  them; it would not catch Claude Sonnet 5's wrong codes.
- **Model choice matters here, and S1 E7 could not show it.** On the hard shape, Terra got 6 of
  6 and Gemini 0 of 6. With 6 calls each, that is the only gap the data support.

It would be a mistake to read more into it:

- **Six items per model.** Claude Sonnet 5's 2 of 6 is compatible with anything from 10% to 70%.
- **One length.** The run did not test whether the hard shape fails less at 16,000 or 64,000
  tokens. One pilot call at 16,000 failed in the same way.
- **The failure may be specific to this wording.** "The hangar where turbine F-155 is stored" is
  answered with a hangar as readily as a code; Gemini's replies are a reasonable reading of a
  sentence it was told to answer with "the value only".

## Departures from the build spec

- **72 calls, not 432.** The full grid was costed at about $60 and not run. The pre-registration
  was amended before any call beyond the pilot: 128,000 tokens only, 6 items (one per book), the
  pass marks re-scaled for n = 6 and 18, and H4 withdrawn. A full-grid run was started and then
  stopped before it recorded any result. The `length-hardest` chart is not drawn.
- **Jane Eyre replaces Frankenstein**, which is too short for 128,000 tokens.
- **Hangars are a digit and a letter**, such as `5N`, not a number. Moby Dick numbers its
  chapters to 135, so every two-digit number is already in its text and would fail the
  absence check.
- **Look-alikes are drawn hardest first** (a swap, a changed digit, a changed letter, a changed
  digit). Drawing uniformly from every one-edit id would almost never give a swap.
- **Retries.** 11 calls failed in the main pass: 9 OpenAI calls (credits ran out, then the
  per-minute token limit) and 2 Gemini calls (quota). All were retried, OpenAI's after credits
  were added. No result was discarded.

## Limitations

- Three models, one setting each, reasoning off; reasoning modes are not tested (S1 E10, S1 E11).
- 6 items per model and shape at one length: intervals are wide, and only differences that clear
  them are findings.
- Invented sentences in nineteenth-century prose still stand out by style; look-alikes make the
  target harder to pick, not harder to notice.
- One question wording per shape. The two-step question can be read as asking for the hangar.
- Lengths are measured with `o200k_base`; each provider's own count differs.
- Default temperatures differ by provider; reruns may vary slightly.
- No retrieval step: this tests the whole document in the window, the alternative S2 E1 weighed
  against retrieval.

## How to reproduce

Reproduce the tables, `summary.json` and charts from the committed results, with no API key:

```bash
uv run lab analyse field-notes/s2-e6-distractors-and-two-facts/config.yaml
```

Check a rebuild of the dataset against the committed manifest (downloads the six books once):

```bash
uv run python field-notes/s2-e6-distractors-and-two-facts/build_dataset.py --check
```

Count tokens before spending anything:

```bash
uv run lab estimate field-notes/s2-e6-distractors-and-two-facts/config.yaml
```

Rerun against current models into a separate folder, leaving the published results untouched:

```bash
uv run lab run field-notes/s2-e6-distractors-and-two-facts/config.yaml --fresh
```

To run the full 432-call grid instead, remove `run_lengths_tokens` and `run_items` from
`config.yaml`. The original pass marks are in `PREREGISTRATION.md` above the amendment.

## Results files

- `results/raw.jsonl`: every call, including the pilot and the failed attempts
- `results/run_metadata.json`: versions, commits, and every pass over the grid (pilot, run, two
  retries for rate limits and credits)
- `results/summary.csv`: one row per scored call
- `results/summary.json`: every figure quoted here
- `results/wrong_answers.csv`: every wrong reply with its type
- `results/dataset_manifest.json`: the invented facts and a SHA-256 of every document
- `results/charts/`: `shapes-128k`, `models-hardest`, `wrong-types`, at slide (PNG, SVG) and
  article (PNG) size
