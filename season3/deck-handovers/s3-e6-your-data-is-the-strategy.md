# S3 E6 deck handover: Your data is the strategy

For the content agent. No experiment: a teaching deck that adds two columns, data readiness and durable advantage, backed by Season 2's measured steps.

## Sources of truth

- `season3/case/rule.yaml` (Data readiness and Durable advantage anchors).
- `season3/case/scores.yaml` and `season3/case/results/scorecard-e6.json`; chart `season3/case/results/charts/scorecard-e6-slide.svg`.
- `season3/case/candidates.yaml` (the data each candidate needs, whether it exists, and whether a vendor already does it).
- `season2/scoreboard.json` and `season2/reference.yaml` (comments record each stage's gain).
- `episodes/s2-e8-filters/README.md` (the metadata filter).
- `episodes/s2-e14-tracing/README.md` (documents that disagree).
- `field-notes/s2-e13-long-context-or-retrieval/README.md` (long context against retrieval).
- `datasets/halvard/manifest.json` (the library's size and versions).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E6 |
| Title | Your data is the strategy |
| Hub slug | `your-data-is-the-strategy` (proposed; confirm) |
| Deck file | `bk-s3-e6-your-data-is-the-strategy-v1.pdf` |
| Hub format | `explainer` |

## The argument

Advantage is what survives the next model release. Separate:

- **Table stakes:** what every competitor can get by buying the same model or product. They can be bought.
- **Differentiators:** what only you have: your data, how it is structured and labelled, and your workflow.

Two columns follow. **Data readiness** asks whether the data exists, is labelled and access controlled, and has a system already measured on it. **Durable advantage** asks: would the next model release or a vendor give this away?

Season 2 gives the evidence. The largest single gain came not from a model or a clever search method but from document metadata: access and version labels let a filter drop what a user should not see and what is out of date. And when the library contradicts itself, no model fixes it; the fix is the content, which is candidate 6's job. When everything fits in a long-context window, the retrieval pipeline stops being the moat.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e6-slide.svg` (from `lab strategy reveal --through E6`).

New columns this episode adds **two**: **Data readiness** and **Durable advantage** (both scores, 1 to 5).

| Candidate | Data readiness | Durable advantage |
|---|---|---|
| C1 Website assistant | 5 | 3 |
| C2 Reply drafts for agents | 5 | 3 |
| C3 Warranty claim triage | 3 | 2 |
| C4 Safety signal screening | 2 | 3 |
| C5 Automatic refund approval | not scored (failed G2) | not scored (failed G2) |
| C6 Library consistency check | 4 | 5 |
| C7 Call and chat summaries | 3 | 1 |
| C8 Spare parts demand forecast | not scored (failed G2) | not scored (failed G2) |

Earlier columns (G1, G2, Value, Task fit, Error tolerance and Autonomy) carry forward from `scorecard-e6.json`. Time to evidence is not shown until E11.

Measured versus assumed:

- **Measured:** C1 and C2's Data readiness of 5 (the library carries access and version labels, and the final system put 0 staff-only passages into 480 public prompts, `season2/scoreboard.json`). C6's 4 cites the library itself (`datasets/halvard/manifest.json`: 300 support articles and 4 policies, each with versions); the score stops short of 5 because no consistency check has been measured on it yet.
- **Assumption:** every other Data readiness score (C3 and C7 rely on records assumed to exist in systems the case does not model; C4 has too few confirmed incidents to measure misses) and every Durable advantage score, each with a one-line reason in `scores.yaml`.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 316 to 359 of 400 | Answerable questions answered right, before and after the metadata filter (S2 E8) | `season2/scoreboard.json`; `episodes/s2-e8-filters/README.md`; `season2/reference.yaml` comments | Measured |
| 64 to 0 of 480 | Public prompts with a staff-only passage, before and after the filter | same | Measured |
| 41 to 83 of 120 | Unanswerable questions correctly declined, before and after the filter | `episodes/s2-e8-filters/README.md` | Measured |
| 98 gained, 8 lost | Right answers the filter gained and lost, paired on the same items | same | Measured |
| 38, 36, 43 | Additional right answers from the three largest joined steps by this measure: structure chunking (243 to 281), LLM reranking (280 to 316) and the filter (316 to 359), each of 400 | `season2/scoreboard.json` | Measured; the filter is the largest |
| 3 of 5 | Final-system failures with the right passage in the prompt that came from a support article and a policy giving different warranty periods | `episodes/s2-e14-tracing/README.md` | Measured |
| 75 against 71 of 80 | Hard items answered right with all 304 documents in the prompt (160,000 tokens) against retrieval; intervals overlap | `field-notes/s2-e13-long-context-or-retrieval/README.md` | Measured |
| 39 each of 40 | Simple, one-sentence policy items answered right, long context and retrieval | same | Measured |
| 300 articles, 4 policies | Size of the library behind C6 and C1 | `datasets/halvard/manifest.json` | Measured count |

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **Two kinds of advantage.** Table stakes on one side (a model, a chat product), differentiators on the other (your data, its labels, your workflow). One sentence each.
2. **One document, one label.** Step one example all the way through, no statistics: a staff-only manual and a public warranty policy, side by side. The only thing that tells the system to keep one from a customer is a label in the document's metadata. Show the label.
3. **Prediction.** "Which Season 2 change gave the most extra right answers: better chunking, a reranker, or the metadata filter?" Reader picks one.
4. **Reveal.** A three-bar chart: chunking +38, reranker +36, filter +43 right answers of 400. Then one line on what the filter also did: leaks from 64 to 0 of 480.
5. **Data you can label.** Show what the filter used: access (public or staff) and status (current or superseded). Two labels, written once, used by every system after.
6. **When the library disagrees.** An article that says a two-year warranty from purchase, a policy that says 40 months from delivery (the Mira robot vacuum, S2 E14). A model gave both and told the customer to check. Show 3 of 5 failures.
7. **Prediction.** "If the library contradicts itself, which fixes it: a bigger model, a better search, or a better library?" Reader picks.
8. **Reveal.** The library: candidate 6, a consistency check, is data work. It is what every other language use case reads.
9. **What the next model will not give you.** Long context: with all 304 documents in the prompt it matched retrieval on hard items (75 against 71 of 80, overlapping). The pipeline is not the moat. The library and its labels are.
10. **Two new columns.** Data readiness anchors, then Durable advantage anchors, then the reveal of `scorecard-e6-slide.svg`: C6 and C7 are far apart on advantage (5 and 1), and C4 has the lowest data readiness (2).
11. **Series map** (last slide), Season 3 highlighted, E6 marked.

## For leaders

**Ask your team:** "What would a competitor with the same model still not have?"

## Decision rule (proposed)

**"Invest where the advantage outlasts the next model: your data, how it is structured and labelled, and your workflow. Do not build what the next model release will give away."**

## Next

E7, Field note: better data or a bigger model? A measured comparison on the same questions.

## Careful with

- **Durable advantage scores are all assumptions.** No experiment tested what the next model release will give away. Label each on the slide.
- **C6's Data readiness of 4 rests on the library's size and versions.** The manifest counts the files and their versions; the effective dates the score mentions are the case's own note, not checked against the manifest. No consistency check has been run on it.
- **The long-context result is one model, one library of 160,000 tokens, 80 hard items.** The intervals overlap, so do not say long context "beat" retrieval or "equals" it everywhere. It cost about ten times as much per question, and it was handed only current, public documents.
- **The filter is not a general law.** It gave the largest gain in this pipeline on this library; other libraries may differ.
- **Do not show totals, ranks or the first pick.**
- **Halvard Home is invented.** No legal claims beyond "consumer protection, product safety and data protection law".
- **Boundaries.** How to prepare data (labelling, cleaning, structure) belongs to S7. People and operating model belong to S9.

## From practice

_Brendan to add one anonymised line from his own practice._
