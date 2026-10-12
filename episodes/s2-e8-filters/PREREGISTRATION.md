# S2 E8 pre-registration: filters, permissions and fresh documents

Written before any E8 call, and not edited after the run. Every claim is reported in
`README.md` as Held or Failed.

## The question

Can search return a passage that is outdated, or that this user should never see?

With no filter, E2 found that a staff-only passage reached the prompt of 51 of 480 public
askers, and the model answered from it 31 times out of 34 on restricted questions. Withdrawn
notices were answered from 20 times out of 20. Superseded policy versions took a third of all
prompt slots, and the model, seeing old and new values together, often would not choose.

## Setup

- **Library and items:** `halvard-v2`, the 520 test items. A filter tunes nothing, so dev is not
  used.
- **The reference system** is the one after E7, pinned in
  `season2/history/s2-e8-filters.yaml`. Only stage 6 changes.
- **The two rules,** read from each document's metadata, never from its text:
  - **access:** a public asker sees public documents only;
  - **status:** current documents only, so superseded and withdrawn versions are dropped.
- **Conditions:**
  - `baseline`: no filter.
  - `before`: both rules, applied before ranking, so a refused chunk never takes a place.
  - `after`: both rules, applied to the ranked list, so the prompt can get fewer passages.
  - `before-access` and `before-status`: one rule each, before ranking.
- **Runs:** every condition search-only (no model call). `before` and the reference also run in
  full, chosen now, because filtering before ranking is the design the episode recommends.

## Claims

**F1. A filter before ranking stops every leak.**
- *Pass mark:* `before` puts a staff passage in the prompt of 0 of the 480 public askers.

**F2. A filter after ranking also stops leaks, but starves the prompt.**
- *Pass mark:* `after` has 0 leaks, and more items with fewer than 5 passages in the prompt
  than `before` has (point estimates).

**F3. The status rule removes the old versions from the prompt.**
- *Pass mark:* under `before-status`, no superseded or withdrawn chunk reaches any prompt.

**F4. With nothing it should not see, the model declines.**
- *Pass mark:* in the full runs, not-found on the 60 restricted and withdrawn items rises
  above the reference's (intervals that do not overlap).

**F5. Without the old version beside it, the model gives the current value.**
- *Pass mark:* in the full runs, the answer rate on the 40 version items rises above the
  reference's (intervals that do not overlap).

## Joining the reference system

`before` joins only if its leaks sit below the reference's (intervals that do not overlap) and
its answer number is not lower.

## Reported, with no claim

- Recall at 5, leaks, prompt slots taken by superseded chunks, and prompts with fewer than 5
  passages, for every condition and item type.
- Paired comparisons (exact McNemar) against the reference.

## What this does not test

- **Metadata is assumed right.** A document tagged public by mistake leaks under every rule.
- **Two access levels only,** public and staff.
- **Deletion is a status, not removal from the index.** A real deletion should also leave the
  index; here the filter does the work.
