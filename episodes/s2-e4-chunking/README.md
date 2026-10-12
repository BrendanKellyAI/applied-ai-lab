# S2 E4: Chunking

How should a document be cut up, and what does that decide? E4 changes only stage 2, the
chunker, and measures what that does to search and then to the answers. The claims, pass marks
and every change made before the runs are in [`PREREGISTRATION.md`](PREREGISTRATION.md).

**Result: structure-aware chunks, one per section of up to 1,024 tokens, join the reference
system.** Search rose from 239 to 281 of 400, and right answers from 243 to 281.

## Two changes before the full runs

- **Cheaper models.** The owner set a much lower budget for the season. From E4 the answer
  model is `gpt-6-luna` ($0.10 / $0.50 per million tokens, reasoning off) instead of
  `gpt-6.1-sol`, and the judge is `gemini-3.6-flash` ($0.75 / $3.75, lowest thinking level)
  instead of `claude-sonnet-5-5`. Two earlier full runs on the old models stopped when the
  Anthropic credit ran out and were discarded unanalysed. E2 and E3 keep their models; E2's
  setup is pinned in `season2/reference-e2.yaml`.
- **The judge was checked before it was used,** on E3's 50 items, in price order, and the first
  that passed was taken (`judge-switch/`):

  | Candidate | Price, in / out | Declined, with old judge | Correct, with old judge | Correct, with hand marks | |
  |---|---|---|---|---|---|
  | `gemini-3.1-flash-lite` | $0.25 / $1.50 | 46 of 50 | 30 of 50 | 6 of 10 | Failed |
  | `gpt-5-mini` | $0.25 / $2.00 | 40 of 50 | 46 of 50 | 7 of 10 | Failed |
  | `gemini-3.5-flash-lite` | $0.30 / $2.50 | 46 of 50 | 30 of 50 | 6 of 10 | Failed |
  | `gemini-3.6-flash` | $0.75 / $3.75 | 47 of 50 | 49 of 50 | 9 of 10 | **Passed** |

  The pass mark was 45 of 50, 45 of 50 and 8 of 10. Both Flash-Lite models called answers
  correct whenever they matched the passages, ignoring the rules for unanswerable questions and
  declines.

Because the models changed, E4's reference was run again on the new models (it is fixed 256
windows, exactly as E2): search 239 (unchanged, search uses no model), answer 243 of 400 against
E2's 217. Every E4 comparison is on the new models.

## The design

- **Library and items:** `halvard-v2`, 520 test items; the 100 dev items only to choose which
  two chunkers ran in full.
- **15 chunkers against the reference,** all changing stage 2 only:
  - fixed windows of 64, 128, 256, 512 and 1,024 tokens (`cl100k_base`), each with no overlap
    and with 25% overlap;
  - structure-aware chunks: one per lowest-level section, split at paragraphs above 256, 512 or
    1,024 tokens, each with and without the heading path ("Warranty > Tessa dishwasher > Cover
    period") put in front of the embedded text. The policies' sections are about 840 tokens
    (902 at most), so at 1,024 every section is one chunk.
- **Every chunker search-only on test and dev.** On the 20 dev policy items the rule picked
  `fixed-512-0` (tied with overlap at 15 of 20; no overlap preferred) and `structure-1024` (tied
  with headings at 17 of 20; name order). Those two tie-breaks past "smaller chunks" were in the
  code before the dev run but not in the pre-registration. Both then ran in full on test.
- **Scoring** as in E2: recall at 5 (the right passage in the top 5 sent to the model); the
  judge's verdict for answers; Wilson 95% intervals.

## Results

### Search, every chunker (recall at 5)

| Chunker | All 400 | 80 policy items | Evidence cut by a chunk edge | Median prompt |
|---|---|---|---|---|
| **Fixed 256 (reference)** | 239 (55% to 64%) | 46 | 18 | 1,173 tokens |
| Fixed 64 | 197 | 32 | 90 | 320 |
| Fixed 64 +25% | 227 | 45 | 18 | 320 |
| Fixed 128 | 236 | 42 | 33 | 640 |
| Fixed 128 +25% | 248 | 54 | 0 | 640 |
| Fixed 256 +25% | 260 | 56 | 0 | 1,180 |
| Fixed 512 | 224 | 49 | 8 | 2,186 |
| Fixed 512 +25% | 238 | 48 | 0 | 2,192 |
| Fixed 1,024 | 214 | 48 | 8 | 2,496 |
| Fixed 1,024 +25% | 222 | 55 | 0 | 3,031 |
| Structure 256 | 274 | 65 | 0 | 1,040 |
| Structure 256 + headings | 265 | 62 | 0 | 1,022 |
| Structure 512 | 270 | 61 | 0 | 1,873 |
| Structure 512 + headings | 266 | 62 | 0 | 1,774 |
| **Structure 1,024** | **281 (66% to 75%)** | **66** | 0 | 2,914 |
| Structure 1,024 + headings | 268 | 65 | 0 | 2,414 |

Every structure-aware chunker found more than every fixed one. A section is a unit of meaning;
a fixed window is not.

### The full runs (520 test items)

| | Search | Answer | Not found | Leaks |
|---|---|---|---|---|
| Fixed 256, reference | 239 of 400 (55% to 64%) | 243 of 400 (56% to 65%) | 53 of 120 (36% to 53%) | 51 of 480 (8% to 14%) |
| Fixed 512 | 224 (51% to 61%) | 237 (54% to 64%) | 57 (39% to 56%) | 30 (4% to 9%) |
| **Structure 1,024** | **281 (66% to 75%)** | **281 (66% to 75%)** | 42 (27% to 44%) | 76 (13% to 19%) |

Paired on the same items, structure 1,024 found 52 passages the reference missed and missed 10
the reference found (exact McNemar p < 0.0001).

## The claims

**C1 failed: long chunks did not dilute policy facts.** Fixed 1,024 found 48 of the 80 policy
facts (49% to 70%), the reference 46 (47% to 68%). v1 found strong dilution on invented facts
inserted into novels, where one sentence is a lone fact in unrelated prose. In a policy, the
whole section around a fact is about the same subject, so a longer chunk adds related words,
not noise. Fixed 1,024 still did worse than the reference over all 400 (214 against 239), on
other item types; why is not tested here.

**C2 held: overlap stops facts being cut.** Without overlap, chunk edges cut the evidence on 90
items at 64 tokens, 33 at 128, 18 at 256 and 8 at 512 and 1,024. With 25% overlap: 18 at 64
(a two-sentence fact is longer than 16 tokens of overlap) and 0 at every larger size.

**C3 failed: embedding the heading path did not help the facts that need their heading.** On the
20 heading-dependent items, with and without the heading path: 14 and 14 at 256, 12 and 11 at
512, 15 and 15 at 1,024. The strong form failed too, though by little: the best, 15 of 20
(53% to 89%), overlaps the reference's 9 of 20 (26% to 66%). What helped these facts was keeping
the section together: a structure chunk starts at its heading, so the product's name is already
in the chunk text.

**C4 held: following the document's structure beats cutting blind.** The best structure chunker
found 66 of 80 policy facts; the best fixed chunker, 256 with overlap, 56.

**C5 held: better search gave better answers.** Structure 1,024: search +42, answers +38. Fixed
512: search -15, answers -6.

## What changed with it

Structure 1,024 joined on search and answers, but two of the season's numbers moved the wrong
way:

- **Leaks rose from 51 to 76 of 480.** A whole staff-only section now arrives as one chunk that
  matches its topic well. E8's filters are where leaks are fixed.
- **Not found fell from 53 to 42 of 120.** Longer chunks give the model more nearby text to
  answer from when it should decline. E9 tests letting the model say "not found".
- **Prompts are about 2.5 times longer** (median 2,914 tokens against 1,173), which raises the
  cost of every answer and every judgement.

Superseded copies still take 699 of 2,600 prompt slots (888 in the reference); E8 removes them.

## What this does not show

- **One library,** with tidy headings written by one model. Real documents have messier
  structure, and structure-aware chunking depends on it.
- **Five passages whatever their size,** so the longer chunkers are also sending longer prompts.
  E9 varies the number of passages.
- **No semantic or sentence-level chunking.**
- **Choosing on 20 dev items** is noisy, and two choices were ties.
- **The judge is `gemini-3.6-flash`,** checked against E3's sample, not against new hand marks.
  Faithfulness has never been marked by a person.

## Charts

In `results/charts/`, drawn by `analyse.py`:

- **`policy-recall`**: recall at 5 on the 80 policy items for all 16 chunkers, with intervals.
  Acid green marks the best if its interval clears the reference's; here, structure 1,024
  (66 of 80).
- **`headings`**: heading-dependent items, the reference and each structure size with and
  without headings. Nothing highlighted: the claim compares pairs.
- **`cut-evidence`**: items whose evidence a chunk edge cut, by size, with and without overlap.
  Nothing highlighted.
- **`scoreboard`**: stage 2 highlighted, the reference against structure 1,024.

## Cost

On the new models: $3.04 for the three full runs (OpenAI $0.28, Google $2.76) and $0.15 for the
four judge checks. Embedding all 15 chunkers cost about $0.06. The two discarded runs on the old
models cost about $6.50.

## Run it

```bash
uv run lab rag analyse episodes/s2-e4-chunking/config.yaml
```

```bash
uv run lab rag estimate episodes/s2-e4-chunking/config.yaml
```

```bash
uv run lab rag run episodes/s2-e4-chunking/config.dev.yaml
```

```bash
uv run lab rag run episodes/s2-e4-chunking/config.yaml
```

The first rebuilds everything from committed results with no key. The judge check is
`uv run python episodes/s2-e4-chunking/judge_switch.py --report`.
