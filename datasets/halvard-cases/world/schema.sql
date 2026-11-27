-- Halvard Home case world: the SQLite schema the environment seeds and resets before every case.
-- All invented. Draft for Gate 1, 27 November 2026.
--
-- Read tables are seeded from world/*.csv. Write tables start empty for every case; the scorer
-- compares what the run wrote to them with the case's expected end state. The tools are the
-- only way in: each read tool runs fixed, parameterised queries; each write tool inserts into
-- exactly one write table.

PRAGMA foreign_keys = ON;

-- Read tables -------------------------------------------------------------------------------

CREATE TABLE customers (
    customer_id      TEXT PRIMARY KEY,            -- C-0001 ... about 400
    name             TEXT NOT NULL,               -- invented, mixed cultures, no real people
    email            TEXT NOT NULL,               -- @example.test only, never a real domain
    region           TEXT NOT NULL,               -- one of the eight corpus regions
    contact_pref     TEXT                         -- NULL, or a stated preference (E7 sequences)
);

CREATE TABLE products (
    product          TEXT PRIMARY KEY,            -- the ten products in policy.yaml
    model_code       TEXT NOT NULL UNIQUE,        -- printed on the rating plate, e.g. HV-BK-200
    line             TEXT NOT NULL                -- telemetry format group
);

CREATE TABLE orders (
    order_id         TEXT PRIMARY KEY,            -- H-100001 ... about 1,500
    customer_id      TEXT NOT NULL REFERENCES customers,
    product          TEXT NOT NULL REFERENCES products,
    serial           TEXT NOT NULL UNIQUE,
    order_date       TEXT NOT NULL,               -- ISO dates throughout
    delivery_date    TEXT NOT NULL,
    price            REAL NOT NULL,
    plan             TEXT NOT NULL DEFAULT 'none' -- none, extended_care, extended_care_plus
);

-- Appliances bought from an authorised retailer: no order; known only from receipt and plate.
CREATE TABLE retailer_appliances (
    serial           TEXT PRIMARY KEY,
    product          TEXT NOT NULL REFERENCES products,
    customer_id      TEXT NOT NULL REFERENCES customers,
    receipt_date     TEXT NOT NULL,
    price            REAL NOT NULL
);

CREATE TABLE recalls (
    product          TEXT NOT NULL REFERENCES products,
    serial_from      TEXT NOT NULL,
    serial_to        TEXT NOT NULL,
    reason           TEXT NOT NULL
);

-- Earlier cases, closed or open, with how they ended. Read by read_past_cases (and E7 memory).
CREATE TABLE past_cases (
    case_ref         TEXT PRIMARY KEY,            -- PC-00001
    customer_id      TEXT NOT NULL REFERENCES customers,
    serial           TEXT,
    fault            TEXT,                        -- S4 Task A fault codes
    opened           TEXT NOT NULL,
    status           TEXT NOT NULL,               -- open, closed
    outcome          TEXT,                        -- a decision from policy.yaml, or NULL if open
    goodwill_amount  REAL,                        -- set when the outcome was a goodwill refund
    summary          TEXT NOT NULL                -- one or two invented sentences
);

CREATE TABLE service_slots (
    slot_id          TEXT PRIMARY KEY,
    region           TEXT NOT NULL,
    starts           TEXT NOT NULL,               -- ISO date and time, after policy as_of
    window_hours     INTEGER NOT NULL,            -- corpus: "an arrival window of 5 hours"
    taken            INTEGER NOT NULL DEFAULT 0
);

-- Write tables (empty at the start of every case) -------------------------------------------

CREATE TABLE service_visits (
    visit_id         INTEGER PRIMARY KEY,
    case_id          TEXT NOT NULL,
    serial           TEXT NOT NULL,
    slot_id          TEXT NOT NULL REFERENCES service_slots,
    fault            TEXT NOT NULL,
    idempotency_key  TEXT UNIQUE                  -- set only when the harness enforces it (E9)
);

CREATE TABLE refunds (
    refund_id        INTEGER PRIMARY KEY,
    case_id          TEXT NOT NULL,
    order_or_serial  TEXT NOT NULL,
    amount           REAL NOT NULL,
    kind             TEXT NOT NULL,               -- early_fault, goodwill
    approval_id      TEXT,                        -- the approver's record, when one was needed
    idempotency_key  TEXT UNIQUE
);

CREATE TABLE replacements (
    replacement_id   INTEGER PRIMARY KEY,
    case_id          TEXT NOT NULL,
    serial           TEXT NOT NULL,
    reason           TEXT NOT NULL,               -- recall, repeat_repairs
    idempotency_key  TEXT UNIQUE
);

CREATE TABLE escalations (
    escalation_id    INTEGER PRIMARY KEY,
    case_id          TEXT NOT NULL,
    reason           TEXT NOT NULL                -- policy.yaml escalation reasons
);

-- The case's closing record: the decision and the reply the customer would get.
CREATE TABLE case_outcomes (
    case_id          TEXT PRIMARY KEY,
    decision         TEXT NOT NULL,
    reason           TEXT,
    existing_case    TEXT,
    reply            TEXT NOT NULL
);

-- Every request to the approver, needed or not, and its answer (E11).
CREATE TABLE approval_requests (
    approval_id      TEXT PRIMARY KEY,
    case_id          TEXT NOT NULL,
    action           TEXT NOT NULL,
    amount           REAL,
    needed           INTEGER NOT NULL,
    granted          INTEGER NOT NULL
);

-- Every tool call, allowed or blocked, written by the harness, never by a tool (E9).
CREATE TABLE audit_log (
    seq              INTEGER PRIMARY KEY,
    case_id          TEXT NOT NULL,
    turn             INTEGER NOT NULL,
    tool             TEXT NOT NULL,
    arguments_json   TEXT NOT NULL,
    outcome          TEXT NOT NULL,               -- ok, tool_error, blocked
    blocked_rule     TEXT
);
