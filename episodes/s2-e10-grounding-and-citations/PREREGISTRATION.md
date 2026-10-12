# S2 E10 pre-registration: grounding and citations

Written before any E10 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

How do you prove an answer came from the source it cites?

S1 E9 pointed at grounding and citation checking; S1 E3 warned that retrieval creates a new
failure, an unfaithful answer with a citation attached. E10 asks the model to answer only from
the passages and to cite each claim as `[P1]` to `[P5]`, then checks every citation in code
against the evidence labels: does the cited passage hold the evidence for the question?

## Setup

- **Library and items:** `halvard-v2`, the 520 test items.
- **Reference:** the system after E9, pinned in
  `season2/history/s2-e10-grounding-and-citations.yaml`, with the plain instruction.
- **Condition `grounded-cite`:** the instruction "Answer the question using only the passages
  below. After each claim, cite the passage it comes from, as [P1], [P2] and so on. If the
  passages do not contain the answer, reply that you could not find it."
  (`prompts/grounded_cite.md`), and the `parse` cite stage, which maps each `[Pn]` marker to its
  chunk. This changes two stages; the parser means nothing without the instruction that asks
  for markers, so the config says so. Both conditions run in full.
- **The citation check, in code, with no model call:** a citation is *supported* if the cited
  passage contains an evidence span of the item, by the same rule as a search hit. Checked on
  answerable items whose answer is not a decline.

## Claims

**G1. Asked to cite, the model cites.**
- *Pass mark:* at least 90% of `grounded-cite` answers that are not declines carry at least one
  `[Pn]` marker.

**G2. A right answer cites the right passage.**
- *Pass mark:* of answerable items judged correct under `grounded-cite`, at least 80% cite a
  passage holding the evidence.

**G3. Grounding makes answers more faithful.**
- *Pass mark:* the judge's faithful rate on answerable items that are not declines is higher
  under `grounded-cite` than under the reference (point estimates).

**G4. Grounding does not cost right answers.**
- *Pass mark:* the answer number does not sit below the reference's.

## Joining the reference system

`grounded-cite` joins if G1 holds, its answer number does not sit below the reference's, and its
share of the 520 handled right (answerable items correct and faithful, unanswerable items
declined) does not sit below the reference's. Citations are what this stage adds; it joins if it
adds them at no measured cost.

## Reported, with no claim

- How many citations point to a passage with no evidence span ("unsupported"), and how many
  answers cite only such passages.
- Citing rates under the plain instruction too: the reference sometimes cites unasked.
- Paired comparisons (exact McNemar) of right answers.

## What this does not test

- **Support by span only.** A passage can support a claim without holding the labelled span (a
  restatement), so "unsupported" overcounts a little.
- **No judge call per citation.** The pipeline spec's `parse_and_check` sends one judge call per
  cited claim; the season's budget does not allow it, and the span check is free and exact.
- **One instruction wording.**
