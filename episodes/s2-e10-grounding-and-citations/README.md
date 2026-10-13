# S2 E10: Grounding and citations

How do you prove an answer came from the source it cites? E10 asks the model to answer only from
the passages and cite each claim, then checks every citation in code. Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: all four claims held and the grounded, citing instruction joins the reference.** Every
answer cited a passage; 91% of citations pointed to a passage holding the evidence; right
answers kept their level; and correct declines rose from 83 to 107 of 120.

## The design

- **Library and items:** `halvard-v2`, the 520 test items.
- **Reference:** the system after E9 (`season2/history/s2-e10-grounding-and-citations.yaml`), with
  the plain instruction.
- **Condition `grounded-cite`:** "Answer the question using only the passages below. After each
  claim, cite the passage it comes from, as [P1], [P2] and so on. If the passages do not contain
  the answer, reply that you could not find it." (`prompts/grounded_cite.md`), plus the `parse`
  cite stage, which maps each marker to its chunk. Two stages change together because the parser
  reads what only the instruction produces. Both conditions ran in full.
- **The citation check, in code:** a citation is *supported* if the cited passage holds an
  evidence span for the question, by the same rule as a search hit. The slide function `cited`
  reads markers like `[P2]` and `[P2-P3]`. No model call: the spec's per-citation judge call was
  replaced by this free, exact check, for budget.

## Results

| | Answer (400) | Not found (120) | Handled right (520) |
|---|---|---|---|
| Plain (reference) | 359 (86% to 92%) | 83 (60% to 77%) | 442 (82% to 88%) |
| **Grounded, citing** | 354 (85% to 91%) | **107 (82% to 94%)** | **461 (86% to 91%)** |

| Citations under `grounded-cite` | |
|---|---|
| Answers that are not declines and cite at least one passage | 365 of 365 |
| Citations | 400 |
| Citations whose passage holds the evidence | 365 of 400 (88% to 94%) |
| Answers citing only passages without the evidence | 5 |
| Right answers citing a passage with the evidence | 343 of 346 (97% to 100%) |

The plain instruction produced no citations at all: `gpt-6-luna` does not cite unasked (E2's
`gpt-6.1-sol` sometimes did).

## The claims

**G1 held: asked to cite, the model cites.** 365 of 365 (99% to 100%).

**G2 held: a right answer cites the right passage.** 343 of 346 (97% to 100%). A citation on a
right answer is almost always checkable against the source.

**G3 held: grounding made answers more faithful,** by the judge, but only just: 351 of 352 answers
faithful against 359 of 363. Both are near the ceiling; the judge rarely found anything unfaithful
under either instruction.

**G4 held: grounding did not cost right answers.** 354 against 359, overlapping intervals;
paired, 24 gained and 13 lost (p = 0.10).

**Unsupported citations, the failure S1 E3 warned of:** 35 of 400 citations point to a passage
without the evidence. Most sit beside a supported citation; only 5 answers cite nothing but such
passages. Some of the 35 are restatements the span rule cannot see, so this overcounts a little.

## Joining the reference system

The rule: G1 holds, and neither the answer number nor the share handled right sits below the
reference's. All three held (461 against 442 handled right), so the grounded, citing instruction
and the citation parser join. From here every answer in the season carries checkable citations.

## What this does not show

- **Support by span only.** A restatement in another passage counts as unsupported.
- **No judge call per citation,** so a citation to the right passage that misstates it is caught
  only by the judge's faithfulness verdict.
- **Not-found and citation rules arrive together** here; E11 separates them using E9's run.

## Charts

`results/charts/`: **`recall`**, **`numbers`** (the four season numbers, plain against grounded)
and **`scoreboard`** (stage 10; joined).

## Cost

$1.36 (OpenAI $0.15, Google $1.21).

## Run it

```bash
uv run lab rag analyse episodes/s2-e10-grounding-and-citations/config.yaml
```

```bash
uv run lab rag run episodes/s2-e10-grounding-and-citations/config.yaml
```
