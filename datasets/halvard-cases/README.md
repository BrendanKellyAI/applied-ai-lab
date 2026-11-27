# Halvard cases (Season 5)

The case world for Season 5's agent experiments. **Everything here is invented:** Halvard Home,
its customers, orders, retailers, receipts, rating plates and telemetry. No row describes a real
person, company or product. Status: built, not yet frozen (Gate 2, 27 November 2026).

## How it was made

`uv run lab agent build-world` rebuilds every file below except the messages, from a fixed seed,
with no model calls. A test checks the rebuild matches the committed files byte for byte.

1. **The world** (`world/*.csv`, loaded into SQLite with `world/schema.sql`): 700 customers,
   orders, retailer purchases, three recall batches, about 900 background past cases and 320
   service slots. One customer per case, so no case inherits history planted for another.
2. **The policy** ([`policy.yaml`](policy.yaml)): the warranty and refund rules. Where the Season 2
   corpus states a rule, this file states the same rule; a test checks each one.
3. **The cases** (`cases/<file>.facts.jsonl`): each case plants the appliance and history it needs,
   with dates chosen so its rule applies exactly. Its expected end state is computed by
   `lab.agent.policy.decide`, so labels are right by construction.
4. **Images** (`images/`): receipts and rating plates drawn with Pillow from the true values, then
   degraded to sharp, blurred, angled, glare or unreadable. `images/truth.jsonl` holds what each
   image shows. Some receipts carry planted instruction text.
5. **Telemetry** (`telemetry/`): logs in four formats with one planted signature each (a genuine
   defect, or misuse, maintenance, supply or commercial use). `telemetry/truth.jsonl` holds the
   rule and the count a correct analysis must find. Some carry planted instructions.
6. **Messages** (paid, gated): `gemini-3.1-flash-lite` writes each customer message from the case's
   brief; code checks it; `claude-haiku-5-5` checks the label blind. Accepted cases are written to
   `cases/<file>.jsonl`; the record is `build_log.json`.

## Files

| File | Cases | Used by |
|---|---|---|
| `test`, `dev` | 240, 60 | E1 to E6, E9, E11, E13, E14 |
| `telemetry-test`, `telemetry-dev` | 45, 15 | E10, E12 |
| `sequences-test`, `sequences-dev` | 30 and 10 sequences (164 cases) | E7 |
| `long-test`, `long-dev` | 30, 10 (four to six appliances each) | E8 |

Case kinds, tags and the expected end state format are in `src/lab/agent/case_model.py`.
