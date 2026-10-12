# S2 E2 deck handover: Your first RAG system

For the content agent building the S2 E2 deck. Written 12 October 2026, after the full run.
Read `season-2-content-handoff.md` (version 2, 11 October 2026) first: its season defaults,
deck conventions and experiment deck order all apply. This document adds only what is specific
to S2 E2.

---

## 1. Sources of truth

1. **`episodes/s2-e2-first-rag-system/README.md`**. Every number and verdict in the deck comes
   from here, word for word where possible.
2. **`.../results/analysis.json`** and **`.../results/baseline/summary.json`**: every figure the
   README quotes.
3. **`.../PREREGISTRATION.md`**: the claims and pass marks, fixed before the run.
4. **`.../results/charts/*-slide.svg`**: the three charts.
5. **`.../results/baseline/log.jsonl`**: every answer and verdict, verbatim, for quotes.

**Branch: `s2`, not `main`.** Season 2 is not merged to `main` until the season is complete.
Use the `main` URL in the deck (it will be right at publication), and do not test it now.

---

## 2. Names

| | Value |
|---|---|
| Episode code | S2 E2 |
| Title | Your first RAG system |
| Hub slug | `first-rag-system` (proposed: confirm against the hub's `data/episodes/*.yaml`) |
| Repository folder | `episodes/s2-e2-first-rag-system` |
| Deck file | `bk-s2-e2-first-rag-system-v1.pdf` |
| Entry format | Experiment episode |

The v1 file `bk-s2-e2-chunking-v1.pdf` is the old E2. Chunking is now E4, so the hub entry for
S2 E2 needs its slug, title and summary replaced, not just a new deck.

---

## 3. The story in one paragraph

Build the simplest complete RAG system: fixed 256-token chunks, vector search, the top 5
passages, a one-line prompt, an answer, a judge. Run it on 520 questions. It finds the right
passage 60% of the time and answers 54% correctly. Most wrong answers are lost before the model
sees them: half of them because the right passage was found but ranked 6th or lower. The
failures the later episodes fix all show up: identifier codes (E5), follow-ups (E6), two-part
and bridge questions (E6), and with no filter, staff documents and withdrawn notices reaching
customers' prompts and being answered from (E8). The surprise is the superseded policies: the
model was not fooled by old terms, it saw both versions and refused to choose, so only 5 of 40
version questions came out right even though search found 33.

---

## 4. Findings, with exact numbers

Run on 12 October 2026, 520 test items. Wilson 95% intervals. 4 claims held, 2 failed.

### The four season numbers (the first scoreboard row)

| Number | Result | Interval |
|---|---|---|
| Search: right passage in the top 5 | 239 of 400, 59.8% | 55% to 64% |
| Answer: correct and faithful | 217 of 400, 54.3% | 49% to 59% |
| Not found: unanswerable questions declined | 56 of 120, 46.7% | 38% to 56% |
| Leaks: staff passage in a public asker's prompt | 51 of 480, 10.6% | 8% to 14% |

The answer and not-found numbers rest on a judge E3 has not yet checked. Say "provisional until
E3" wherever they appear.

### The claims

- **H1 held:** of 182 wrong answers, 147 lost the passage before the prompt (chunk 11, search 44,
  ranked below 5th 92) and 35 inside it (declined 1, wrong despite the passage 34).
- **H2 failed:** two-sentence facts 13 of 20 (43% to 82%) were found more often than one-sentence
  facts 24 of 40 (45% to 74%). Heading-dependent facts 9 of 20 (26% to 66%) were lower, but every
  interval overlaps. Do not say chunking hurt or did not hurt: the run cannot tell.
- **H3 held:** identifier 15 of 40 (24% to 53%) against paraphrase 38 of 40 (83% to 99%). The
  same 15 of 40 as v1 S2 E3.
- **H4 held:** follow-ups 3 of 40 (3% to 20%) against one-sentence policy facts 24 of 40.
- **H5 failed:** H5a held (a staff passage reached 34 of 40 restricted prompts, and 17 prompts of
  other types). H5b failed: the superseded passage reached 32 of 40 version prompts, but no
  answer gave the old value alone.
- **H6 held:** declined 47 of 60 questions with nothing to find, 78% (66% to 87%); declined only
  9 of 60 restricted and withdrawn questions, 15% (8% to 26%).

### Reported with no claim (the README's "What else the run showed")

- **Superseded copies crowd the prompt:** 392 of 520 prompts held the same passage in two
  versions; 888 of 2,600 prompt slots (34%) were superseded chunks.
- **The model reports a conflict:** version questions, search 33 of 40, answer 5 of 40. 27 had
  the right passage in the prompt and were still judged wrong.
- **Leaked passages are used:** 31 of the 34 leaked public prompts were answered from the staff
  passage.
- **Withdrawn notices are answered from:** 20 of 20, none declined.
- **Two-passage questions:** bridge 0 of 20 found, two-part 1 of 20.
- **Code check against judge:** 32 disagreements, 28 of them version questions.

### Real replies to quote (from `log.jsonl`)

House rule: no em dashes, including in quoted output. POL-SINGLE-000's reply contains one, so
quote only the clause shown below.

- **Right, POL-SINGLE-001.** "How much longer does Extended Care keep my warranty going?"
  Reply: **"Extended Care extends your standard warranty by 58 months. [P5]"** Reference: 58
  months. Caveat for the slide: [P5] is the *superseded* warranty, where this term is unchanged;
  the current version's passage ranked 6th.
- **Search missed, POL-SINGLE-000.** "How soon will Halvard Home pick up my recalled appliance
  after I reply?" Reference: 18 working days. The right passage ranked 16th. The reply gave other
  regions' times: **"London and South East: within 53 working days"** and **"Midlands: within 21
  working days"**, then **"Which region are you in?"** Faithful, not correct.
- **Model misread, DISTRACT-018.** "How long is the warranty on the Brio kettle?" Reference: 47
  months from delivery; the right passage was 3rd. Reply: **"The passages conflict: the detailed
  warranty states 47 months from delivery [P2–P3], while the warranty-period page says two years
  from purchase [P1]. Contact Halvard Home to confirm which applies to your kettle."**
- **Version conflict, VERSION-000.** Cooling time before cleaning the Tessa dishwasher, 7 minutes
  now, 11 in the old policy. Reply: **"The passages give conflicting cooling times: 11 minutes in
  P1 and 7 minutes in P2. To be cautious, wait at least 11 minutes, and longer if the surfaces
  are still too hot to touch safely."**
- **Leak used, RESTRICT-PUBLIC-003.** A customer asks how much engineers can spend on parts for
  the Mira robot vacuum without approval. Reply: **"Engineers can fit parts worth up to £163.00
  in total, using current internal parts prices, without asking for approval. [P1]"**
- **Withdrawn notice, DELETED-000.** A customer asks about a wall bracket from batch 4867. The
  notice was withdrawn on 19 May 2026. Reply: **"Stop using the wall bracket from batch 4867 and
  return it for a refund."**
- **Identifier miss, IDENT-000.** "What does error E-2194 mean?" The right article ranked 11th.
  Reply: **"The provided passages don't mention error E-2194, so I can't determine what it
  means."**
- **Follow-up miss, FOLLOW-000.** After a question about the Orrin heat pump, "What about the
  Mira robot vacuum?" The right passage ranked 34th; the reply said the instructions "don't
  specify a waiting period". The answer was 37 hours.

The model's replies use Markdown bold; drop the asterisks when quoting.

---

## 5. Charts and their highlights

E2 measures and does not compare, so **no chart highlights anything**, and each says so in its
footer ("No highlight: E2 measures, it does not compare"). Say this on each chart slide. Do not
add green to a chart.

| File | Shows |
|---|---|
| `recall-by-type-slide.svg` | Recall at 5 for the 12 answerable types, with intervals and "x of n" beside each bar. Bridge is a zero bar and shows "0 of 20" |
| `where-lost-slide.svg` | The 182 wrong answers by the first stage that lost the passage, as shares with counts |
| `scoreboard-slide.svg` | The 11-stage strip (nothing highlighted, no stage changed) and the four numbers |

"Ranked below 5th" in `where-lost` is the stage the season calls rerank. Explain once that the
baseline has no reranker, so this is a passage that was found but not ranked high enough.

---

## 6. Code listing for "Run it yourself"

`build_prompt` from `src/lab/rag/prompt.py`, below `# slide: S2 E2`. A test checks it fits a
slide; copy it exactly:

```python
def build_prompt(question, history, passages):
    """Numbered passages, then any earlier turns,
    then the question."""
    parts = ["Passages:", *numbered(passages)]
    if history:
        parts.append(conversation(history))
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)
```

The whole instruction the answer model gets, from `src/lab/rag/prompts/plain.md`, is one line:
"Answer the question using the passages below." Show it beside the listing: it is the point of
E9.

Routes for the slide:

- No key, no cost: `uv run lab rag analyse episodes/s2-e2-first-rag-system/config.yaml`
- Count first: `uv run lab rag estimate episodes/s2-e2-first-rag-system/config.yaml`
- Rerun with keys: `uv run lab rag run episodes/s2-e2-first-rag-system/config.yaml` (add
  `--pilot` for 2 items per type)

---

## 7. Terms to define at first use

The handoff asks for terms defined once and back-referenced after. E2 is the first episode to
use these, so define them here briefly and point to E3 for the full treatment:

- **Recall at 5:** the share of questions whose right passage is in the top 5.
- **Faithful:** every claim in the answer is supported by the passages it was given.
- **Wilson interval:** the range the true rate probably lies in, given the sample. "Explained in
  E3."
- **Leak:** a staff-only passage in the prompt of a customer.

---

## 8. Suggested slide outline (20 slides)

Follows the experiment deck order in the handoff. Vary the layouts: the run of results slides
in the middle should alternate charts, tables, quotes and diagrams.

1. **Cover:** Your first RAG system.
2. **Why it matters:** you cannot improve a stage you have not measured, and a RAG system fails
   in places the answer does not show. S2 E1 promised retrieval; this is it built.
3. **Mental model (diagram):** the 11 stages as a strip, with E2's setting under each; stages
   4, 6, 7 and 10 shown as off. "Where it breaks" card: every stage can lose the right passage,
   and the answer still looks fine.
4. **Method:** the Halvard library (300 articles, 4 policies and their old versions, 4 internal
   documents, 32 withdrawn notices), 520 questions of 16 types, the two models, and the scoring.
5. **Claims and pass marks:** H1 to H6, each with the episode it points to.
6. **One worked example of a test item:** follow POL-SINGLE-000 through the stages: question,
   ranked 16th, what the prompt held instead, the reply, the judge's verdict.
7. **Findings, the four numbers:** with intervals, and "provisional until E3" on answer and not
   found.
8. **Recall by type (chart `recall-by-type`):** nothing highlighted. Paraphrase 38 of 40,
   identifier 15 of 40, follow-up 3 of 40, bridge 0 of 20.
9. **Where the wrong answers were lost (chart `where-lost`):** nothing highlighted. Half were
   found but ranked below 5th.
10. **Three answers (quotes):** right, search missed, misread, with the caveat that the right one
    came from the superseded copy.
11. **The old version in the prompt:** 33 found, 5 right; the VERSION-000 reply.
12. **The wrong reader:** 31 of 34 leaked prompts answered from the staff passage (the £163.00
    reply); 20 of 20 withdrawn notices answered from.
13. **Claim verdicts:** 4 held, 2 failed, with the H2 and H5b reasons.
14. **What this does not prove:** one invented library, one unchecked judge, a plain prompt, the
    duplicate effect depends on how many old versions a library keeps, wide by-type intervals.
15. **Run it yourself:** the `build_prompt` listing, the one-line instruction, the three routes.
16. **In practice:** log the passages behind every answer; keep old and withdrawn documents out of
    the index or filter them; never rely on the model to refuse what it should not have seen.
17. **For leaders:** "Ask your team" card: what share of wrong answers is search and what share
    is the model; can a customer's question reach an internal document; what happens to a
    document when it is withdrawn.
18. **Scoreboard (chart `scoreboard`):** the first row; no stage changed; joined as the
    reference.
19. **Decision rule and Next:** see section 9. Next: S2 E3 Measuring it, "Is the judge right,
    and which half failed?"
20. **Series map.**

---

## 9. Decision rule

The handoff's draft: **"Build the simplest complete pipeline and measure it before tuning any
stage."** The run supports it. One option for the owner, if the rule should carry what E2 found:
"Build the simplest complete pipeline, log the passages behind every answer, and measure it
before tuning any stage."

---

## 10. Cost

The handoff's E12 adds a cost in currency, so currency is no longer ruled out. For E2, the
deck's point is proportions, not money. Prefer tokens and seconds:

- Answer: median 1,255 tokens in and 47 out, 2.6 seconds per question (90th percentile 7.2).
- Judge: median 2,530 tokens in and 92 out, 1.7 seconds. The judge reads about twice what the
  answer model reads.
- Reasoning `low` used 887 reasoning tokens across all 520 answers: close to off.

The README gives the run's cost at 12 October 2026 list prices (about 0.9 cents a question) if
the owner wants a currency figure on the slide.

---

## 11. Checklist additions for this deck

- [ ] "Provisional until E3" on every answer-level number.
- [ ] No green on any chart, and each chart slide says why.
- [ ] The right-answer example carries its superseded-copy caveat.
- [ ] Cross-references: E3 measuring, E4 chunking, E5 search, E6 rewriting, E7 reranking, E8
      filters, E9 the prompt, E10 citations.
- [ ] No em dash in any quoted reply.
