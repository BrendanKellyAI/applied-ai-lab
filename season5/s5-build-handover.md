# Season 5 build handover: Agents

For the coding agent. Prepared 27 November 2026. The season plan is agreed: read
`season5/README.md` (the season guide) first, then this whole file before starting. Titles,
slugs, acts and the running case are fixed. Designs below are proposals for Gate 1 unless marked
as decided.

## 1. What you are building

Season 5 is a technical season. Its title on the series map is "Agents". It answers one question
across the season: when does a model need to act, and what has to be true of the code around it
before you let it?

Like Seasons 2 and 4, it is built around one measured reference and a scoreboard. Your job is:

1. **The Halvard case environment:** an invented warranty case world (customers, orders,
   warranties, service visits, past cases), the tools an agent uses on it, a rule-based customer
   and approver, receipt and rating plate images, telemetry logs, and a scorer that checks each
   case's end state.
2. **The agent harness:** one plain-Python agent loop with tool calling, memory, context
   handling, a code execution sandbox, approval points and loop controls, all switchable by
   config so every episode is an arm on the same loop.
3. **Provider support** for multi-turn messages, tool calls and image inputs, without breaking
   earlier seasons' caches.
4. **One experiment per teaching episode,** each pre-registered, with results, charts, a README
   and a deck handover.
5. **Three tools readers keep:** the agent card, the agent safety checklist, and the case
   environment readers can plug their own agent into.
6. **An MCP server** for the Halvard tools (E14).
7. **Hub changes:** Season 5 text, planned episode files and the tools section.

You do not build decks, LinkedIn posts or the season content handoff.

## 2. Ground rules

These are not optional. They carry over from Season 4 unless stated.

- **Cheapest model for everything in the experiment code.** Every model call uses the cheapest
  model that does the job, in every role: agent, planner, critic, specialist, summariser, data
  generator, label checker and judge.
  - Defaults: `gpt-6-luna` for the agent (reasoning off), `gemini-3.1-flash-lite` for data
    generation (it must not be an agent model, by the conflict of interest rule),
    `claude-haiku-5-5` as label checker, `gemini-3.6-flash` as judge where a judge is needed
    (E5 only). Re-check each against Season 4's `PLAN.md` section 2 and current prices.
  - **Tool calling and image input** must be verified for the agent model before Gate 1. If
    `gpt-6-luna` lacks image input, propose the cheapest model that has it for E6 only, and name
    it as an exception.
  - **Exceptions** exist only where the question itself needs a pricier model, named at the
    spend gate and approved by Brendan explicitly. None is expected.
- **Spend gate.** Make no paid call, including `lab smoke`, without Brendan's go-ahead. For each
  experiment, commit the pre-registration and config, run `lab estimate` for the pilot and the
  full run, and send Brendan the token counts per model and per stage. Agent runs grow with each
  turn, so estimate from a dry run on the mock provider with realistic turn counts, and show the
  per-case distribution as well as the total. Wait for approval. If a pilot changes the config,
  estimate again and wait again.
  - You may bundle small experiments into one estimate and one approval, listed line by line.
- **Hard caps in code.** Every agent run has a maximum number of turns, tool calls and tokens per
  case, set in config and enforced by the loop. A case that hits a cap is recorded as unresolved
  with the cap named. This is both a spend control and E12's subject.
- **Pre-register before any call**, as before: `PREREGISTRATION.md` with question, design,
  primary metric, claims and pass marks, committed before the first call. Later changes go in a
  dated amendment.
- **The strict bar.** A setting joins the reference agent only if its interval sits clear above
  the current reference on the primary metric (cases resolved), with no rise in unsafe actions
  executed. Pre-register this per episode.
- **Frozen data stays frozen.** Do not change `datasets/halvard/` or `datasets/halvard-tasks/`.
  The frozen tests must keep passing. S5 data lives in its own dataset (section 6).
- **Fictional only.** Nothing about Druva or any real company. Every customer, order, image and
  log is invented and labelled as invented. Images must not resemble a real retailer's receipt
  or a real manufacturer's rating plate.
- **Safety of the build itself.**
  - Agent-written code never runs on the host. It runs only in the E10 sandbox, from E10
    onwards, and earlier episodes do not offer the code tool.
  - Planted instructions in logs and images exist to be blocked. No tool in the environment can
    reach the network, the filesystem outside the case workspace, or real email. Actions such as
    "issue a refund" only write to the case database.
- **No legal claims without a source.** Consumer rights and warranty law stay general and
  invented. Any specific statement needs a source and a date, and is marked as illustrative.
- **Repo conventions,** as in the `applied-ai-lab` README: `uv`, the `lab` CLI, results
  committed, every response cached, prices never published (costs as ratios only), keys never
  logged, `uv run pytest` passing its 85% coverage gate, `ruff check` and `ruff format --check`
  clean.
- **No agent framework.** Plain Python against the provider APIs (decided). Allowed libraries:
  the Docker SDK or CLI for E10, and the official MCP Python SDK for E14. Anything else needs
  Brendan's approval.
- **Model availability.** Re-verify every model in `src/lab/providers/capabilities.yaml` with
  source and date. Add fields: `tool_calling` (none, basic, parallel), `image_input` (true or
  false) and any image size or count limits. Include those models in the `lab smoke` request at
  the first spend gate.
- **Writing.** No em dashes or en dashes anywhere: code comments, data, Markdown, commit
  messages. British spelling. Every figure says what it measures and out of how many.
- **Branches.** Work on `s5` in `applied-ai-lab`. It is already created from the tip of `s4`
  (4369aaf), because Season 5 builds on S4 Task A and Season 4 has not merged. Rebase onto
  `main` once Season 4 merges, and say so in the first pull request. In the hub, use a feature
  branch (`s5-hub`). Open pull requests; Brendan merges.

## 3. How Season 5 connects to the series

- **S2** left agentic retrieval for later: "models that decide what to search for". E5 picks it
  up, using the S2 reference system (`season2/reference.yaml`) as the search tool.
- **S3 E5** set the levels of autonomy (assist, automate, act). E11 builds the approval points
  that make those levels real. Do not re-present S3 E5; one line and a pointer.
- **S4 Task A** (triage with a safety flag) is the first thing the agent does with a customer
  message. Reuse the S4 reference prompt for triage and say where it came from.
- **S4 E4** stopped at structured output and left tool calling to S5. E2 opens there.
- **S1 E6 and E7** (context windows, lost in the middle) are the refreshers for E8.
- **S1 E2** (tokens) is the refresher for image cost in E6.

## 4. The season

Titles, slugs and acts are fixed by `season5/README.md`. Hub formats: use the values Seasons 2
to 4 used for the same kinds of episode (check `data/episodes/s4-*.yaml` in the hub for
`season_intro`, experiment, `decision_framework` and `recap`). Deck files follow
`bk-s5-e<N>-<slug>-v1.pdf`. Episode folders follow `episodes/s5-e<N>-<slug>/`.

| Ep | Slug | What you build |
|---|---|---|
| E0 | `season-5-intro` | Deck handover |
| E1 | `agents-or-pipelines` | Fixed pipeline and baseline agent on the test cases |
| E2 | `tool-calling-loop` | The minimal loop, a replayed trajectory, the loop's line count |
| E3 | `tool-design` | Tool description, schema and error handling arms |
| E4 | `agent-patterns` | ReAct, plan-and-execute and reflection arms |
| E5 | `agentic-rag` | One retrieval against agent-chosen searches |
| E6 | `multimodal-agents` | Image reading arms across quality levels |
| E7 | `agent-memory` | Memory type arms on case sequences |
| E8 | `context-management` | Full history, truncation, compaction and on-demand reference arms |
| E9 | `agent-harness` | Prompt-only rules against code-enforced rules |
| E10 | `sandboxing` | The container sandbox and the telemetry tool |
| E11 | `human-in-the-loop` | Approval policy arms, checkpoint and resume |
| E12 | `self-checking-loops` | Retry, feedback, stall detection and budget cap arms |
| E13 | `multi-agent-systems` | Single agent against router and specialists |
| E14 | `mcp` | The Halvard MCP server and a parity run |
| E15 | `agent-frameworks` | Decision card section, no new calls |
| E16 | `season-5-recap` | Recap numbers, agent card, deck handover |

## 5. Repository layout

Follow the Season 2 and Season 4 layout. Adjust to existing conventions where they differ, and
say where you did.

```
datasets/halvard-cases/
  README.md                how the world, cases, images and logs were made; all invented
  world/                   customers, orders, products, warranties, service slots (SQLite seed + CSV)
  policy.yaml              warranty and refund rules the cases are labelled against
  cases/ dev.jsonl test.jsonl sequences.jsonl long.jsonl
  images/                  rendered receipts and rating plates, with their true values
  telemetry/               generated logs, with the planted fault per log
  MANIFEST.json            file hashes; a frozen test checks them
season5/
  README.md                season guide (exists); gains build status per episode
  reference.yaml           the current reference agent settings
  reference_history.yaml   what joined, when, with the evidence
  scoreboard.json          per episode, per arm
  agent-card.md            tool (E16)
  agent-safety-checklist.md  tool (E9, completed at E12)
  deck-handovers/          E0, E15, E16 (episode folders hold the rest)
src/lab/agent/             loop, tools, environment, customer and approver, memory, context,
                           sandbox, approvals, loop controls, multi-agent, scoring, replay, CLI
src/lab/agent/mcp_server/  the Halvard MCP server (E14)
episodes/
  s5-e1-agents-or-pipelines/ ... s5-e14-mcp/
tests/agent/
```

Add a `lab agent` command group:

- `lab agent run <config.yaml>`: runs an agent arm over a case split. Cached per model request.
- `lab agent analyse <config.yaml>`: scores, statistics and charts. No API calls.
- `lab agent replay <run> <case-id>`: prints one case's trajectory (every model turn, tool call,
  tool result and harness decision) as Markdown and as a slide-ready SVG. No API calls. This is
  how decks step one case through each arm.
- `lab agent score <end-states.jsonl>`: scores a reader's own agent's end states against the
  test cases, with no API calls.
- `lab agent env`: runs the case environment as a small local service so readers can plug in
  their own agent (section 8).
- `lab agent mcp-serve`: starts the Halvard MCP server (E14).

## 6. Phase 1: provider support, the environment and the data

### 6.1 Provider support

`GenerationRequest` today takes one `system` and one `prompt` string, with no tools and no
images. Extend it, keeping earlier seasons' caches valid (the S4 `output_format` pattern: new
fields are left out of the request hash when unset):

- `messages`: a list of turns (user, assistant, tool result), each with text and optional images.
- `tools`: tool definitions (name, description, JSON schema for arguments).
- `tool_choice`: auto, required or none.
- `GenerationResult` gains `tool_calls` (name, arguments, call ID) and keeps token counts.
- Map each to OpenAI, Google and Anthropic in their adapters, and to the mock provider, which
  must be able to script tool calls so the whole loop is tested without spend.
- The cache key covers the full message history and tool list, so a replayed run with identical
  tool results costs nothing.

### 6.2 The case environment

- **World:** about 400 invented customers, 1,500 orders across the 10 products in
  `datasets/halvard-tasks/routes.yaml`, warranties, past cases and service slots. Seeded SQLite,
  reset before every case.
- **Policy (`policy.yaml`):** invented warranty length per product, proof of purchase rules,
  misuse exclusions, refund rules, the refund limit above which a human must approve, and a
  goodwill rule (for example, one goodwill refund per customer per year). Where the S2 corpus
  already states a Halvard warranty rule, the policy must agree with it; a test checks this.
- **Tools:** the seven in the season guide. Each returns JSON, returns errors as structured
  messages, and logs every call. Write tools write only to the case database.
- **Customer:** rule-based, not a model. It answers the agent's questions from the case file
  (for example the purchase date, or a clearer photo on request) and says "I do not know" to
  anything else. Every reply is deterministic, so runs replay from cache.
- **Approver:** rule-based. It applies `policy.yaml` and records each request, whether it was
  needed, and its answer.
- **End state:** each case has an expected end state: the decision (repair booked, refund of a
  stated amount, replacement, decline with a stated reason, escalate), the records written, and
  actions that must not happen. The scorer compares the database after the run with it.

### 6.3 The cases

Each case is a customer message plus attached files and its expected end state. Kinds, each
tagged so results can be split by kind:

- **Routine:** in warranty, clear facts, fixed path. A pipeline should handle these.
- **Branching:** the next step depends on what a tool returns (an unknown order, a second
  appliance, a product recall).
- **Missing information:** the agent must ask the customer.
- **Out of warranty, misuse, or goodwill:** decisions that depend on policy detail.
- **Above the refund limit:** needs approval.
- **Photo cases:** receipt and rating plate at each quality level, some unreadable.
- **Telemetry cases:** the fault is only visible in the log.
- **Adversarial:** a customer pressing for an out-of-policy refund, a planted instruction in a
  log or image, a duplicate request (tests idempotency).
- **Sequences (`sequences.jsonl`, E7):** the same customer over three to five cases, where later
  cases depend on earlier ones (a stated contact preference, a goodwill refund already used, a
  repair that failed before).
- **Long cases (`long.jsonl`, E8):** households with several appliances and long histories,
  needing 20 or more tool calls.

**Sizes (proposed, for Gate 1):** dev 60, test 240 (at least 20 of each kind in test), 40
sequences, 40 long cases. Agents vary run to run even with fixed settings: run each test case
once per arm, and run the reference arm three times on a fixed sample of 60 to report run-to-run
variation. Pre-register this.

### 6.4 How the data is made

- **Messages:** generated with `gemini-3.1-flash-lite`, conditioned on the case's facts and
  kind, so the expected end state is right by construction. Record the generator and prompt.
- **Label check:** `claude-haiku-5-5` reads each case and policy blind and states the decision.
  Discard disagreements and report how many. Brendan checks 30 test cases (a list produced by
  the code) before freezing.
- **Images:** rendered by code (for example Pillow) from known values, then degraded at four
  levels (sharp, blurred, angled, glare). No model calls. A few carry planted instruction text.
- **Telemetry logs:** generated by code, not a model, from a fault model per product line, in
  three or four formats so a single fixed parser does not cover all of them. Some carry planted
  instructions in free-text fields.
- **Freeze:** after Brendan's check, write `MANIFEST.json` and add a frozen test. Later changes
  are dated amendments.
- Message generation and the label check are paid steps: they go through the spend gate.

## 7. Phase 2: episode experiments

### 7.1 Shared design

- Per episode: `config.yaml`, `PREREGISTRATION.md`, analysis code, `results/`, `README.md` and
  `DECK_HANDOVER.md`.
- **Primary metric:** cases resolved (end state matches), out of the test size.
- **Always reported:** resolved by case kind; tool calls per case and unnecessary tool calls;
  input and output tokens per case; unsafe actions attempted and executed; approvals requested,
  and how many were needed; cases stopped by a cap.
- Statistics: Wilson intervals; exact McNemar tests for paired comparisons on the same cases,
  Holm correction across more than two arms; per-case flips both ways.
- Pilots on dev, full runs on test. Never tune prompts, tool descriptions or settings on test.
- Charts: `*-slide.svg` for decks and PNG for the article, from `charts.py`. Every episode also
  commits at least one `lab agent replay` trajectory for the deck.
- Costs as ratios only, for example cost per resolved case relative to the E1 baseline agent.
  Per month at an invented volume (for example 20,000 cases), including an invented cost of a
  wrong outcome (a wrong refund, a wrong decline), stated as invented.

### 7.2 Rough token expectation

Rough figures to warn Brendan early; `lab estimate` gives the number he approves. A typical case
is about 6 to 10 model turns at 15,000 to 40,000 input tokens per case in total.

| Episode | What costs | Rough size |
|---|---|---|
| Data generation | about 400 cases plus label checks | under 2 million |
| E1 | pipeline plus agent on 240 cases | 5 to 8 million |
| E2 | replays only, plus a few demo cases | under 1 million |
| E3, E4 | about 7 arms on 240 cases | 30 to 50 million |
| E5 | 3 arms on about 100 multi-part questions, plus judge | 3 to 6 million |
| E6 | about 4 arms on about 200 images | 2 to 4 million |
| E7 | 4 to 5 arms on 40 sequences | 5 to 10 million |
| E8 | 4 arms on 40 long cases | 10 to 20 million |
| E9 | 2 arms on adversarial cases plus the full test set | 8 to 12 million |
| E10 | telemetry cases, sandbox on | 3 to 5 million |
| E11 | 3 arms on 240 cases | 15 to 25 million |
| E12 | 4 arms on telemetry cases | 5 to 10 million |
| E13 | 2 to 3 arms on 240 cases | 15 to 30 million |
| E14 | parity run; mostly cache hits | under 1 million |

On `gpt-6-luna` these are small in money but large in tokens. Show each line at the gate.

### 7.3 E1: Agents or fixed pipelines

- **Arms:** a fixed pipeline (S4 triage, order lookup, warranty check, rule-based decision, one
  model call to write the reply); the baseline agent (all non-code tools, a short instruction).
- **Report** resolved by case kind: the pipeline should win or tie on routine cases at a fraction
  of the cost, and lose on branching and missing-information cases. Pre-register this as a claim.
- **Rule (proposed):** "If you can draw the steps as a flowchart that never depends on what the
  model finds, write the code. Use an agent only where the next step depends on what it finds."
- **Ask:** "Which of our steps depend on what was found, and which are always the same?"

### 7.4 E2: Tool calling from scratch

- Build the minimal loop as a standalone file of about 30 lines (model call, run tool, append
  result, repeat, stop), kept beside the full harness so readers can read it in one sitting.
- Step one case through it with `lab agent replay`: each tool request, the code that ran it, the
  result, the next turn.
- **Evidence:** the E1 baseline agent is this loop. Report tool calls per case and how often the
  model asked for a tool that does not exist or with malformed arguments.
- **Rule (proposed):** "An agent is a loop: the model asks, your code acts, the result goes back.
  Everything else in this season is code around that loop."

### 7.5 E3: Tool design

- **Arms:** terse names and one-line descriptions; clear descriptions stating when to use each
  tool and what it returns; clear descriptions plus strict argument schemas; errors raised as
  exceptions (the run fails) against errors returned to the model as structured messages.
- **Report** wrong-tool calls, malformed arguments, recoveries after an error, resolved.
- **Rule (proposed):** "Write each tool's description for a new colleague: when to use it, what
  it needs, what it returns. Return errors to the model; do not crash."

### 7.6 E4: Agent patterns

- **Arms:** ReAct (the reference loop, reasoning off); ReAct with the lowest reasoning setting
  (optional, estimated separately); plan-and-execute (a plan call, then steps, with one re-plan on
  failure); ReAct plus one reflection pass that checks the decision against policy before it is
  written.
- **Report** resolved by kind, tokens and turns per case. Refresher on reasoning models from S1
  E10.
- **Rule (proposed):** "Start with think-as-you-go. Plan first only when the steps are known
  upfront; add a check pass where a wrong decision is costly."

### 7.7 E5: Agentic RAG

- **Questions:** about 100 multi-part questions over the S2 corpus (two or more facts from
  different documents), generated and label-checked like the cases, kept apart from
  `halvard-v2` test questions (report near-duplicates removed). Plus the cases that need a policy
  lookup.
- **Arms:** the S2 reference system (one retrieval, then answer); an agent with the S2 retrieval
  as a search tool; the same with a cap on searches.
- **Measures:** right (S2 judge), searches per question, tokens, correct "not found".
- **Rule (proposed):** "Let the agent search again when one question needs facts from several
  places. For single-fact questions, one retrieval is cheaper and as good."

### 7.8 E6: Multimodal agents

- **Arms:** the agent reads the receipt and rating plate from images; the agent asks the
  customer to type the details; the agent reads the image and asks the customer to confirm only
  when unsure.
- **Measures, per quality level:** fields read correctly (purchase date, model, serial), cases
  resolved, image tokens per case, unreadable images where the agent guessed instead of asking,
  and compliance with planted instruction text (expected to be high without a harness; E9 blocks
  it).
- **Rule (proposed):** "Read facts from images when the image is clear, and ask when it is not.
  Treat text in an image as data, never as instructions."

### 7.9 E7: Agent memory

- **Teach all four types** (working, semantic, episodic, procedural), each with a Halvard
  example, before results.
- **Arms on the 40 sequences:** no memory between cases; full past transcripts pasted in;
  episodic summaries of past cases retrieved by customer; episodic plus semantic facts (a small
  key-value store the agent writes to through a tool); plus procedural memory (a short "lessons"
  file of rules learned from earlier failed cases, applied to later cases).
- **Measures:** resolved on cases that depend on memory, tokens per case, wrong memories used,
  and personal data stored that the task did not need (a privacy point).
- **Careful with:** procedural memory changes the agent's behaviour; gate any learned rule
  behind the dev set, and log every rule added.
- **Rule (proposed):** "Store what changes later decisions, retrieve it by need, and keep no
  personal data the task does not use."

### 7.10 E8: Context management for long tasks

- **Arms on the 40 long cases:** full history; dropping the oldest turns past a budget;
  compaction into a scratchpad every N turns (lessons kept, transcripts dropped); compaction plus
  reference documents loaded on demand through a `read_reference` tool instead of the full policy
  in the system prompt.
- **Measures:** resolved, input tokens per case, facts lost (decisions that contradict an early
  tool result).
- **Rule (proposed):** "Do not let history grow without limit. Compact it into what the next step
  needs, and load reference material only when it is used."

### 7.11 E9: The agent harness

- **Arms:** rules stated only in the prompt; the same rules enforced in code (argument
  validation, the refund limit as a hard check, least privilege per tool, idempotent writes,
  planted-instruction filtering on tool results and image text, an audit log).
- **Run on** the adversarial cases and the full test set, so a safety gain is not bought with
  fewer resolved cases.
- **Measures:** unsafe actions attempted and executed, duplicates created, resolved.
- **Security points** on slides: least privilege, the confused deputy, an audit log of every tool
  call. Name prompt injection and hand depth to S11.
- Start `agent-safety-checklist.md` here.
- **Rule (proposed):** "Anything that must never happen is enforced in code, not asked for in
  the prompt."

### 7.12 E10: Sandboxing

- **Build** the `analyse_telemetry` tool: the agent writes Python, the harness runs it in a local
  Docker container with no network, a read-only mount of the one log file, a non-root user, and
  CPU, memory and time limits. Record every blocked action.
- **Teach three levels:** path checks, a container (used here), a disposable micro virtual
  machine (described, not run).
- **Measures:** diagnosis correct on telemetry cases, cases resolved, attempts blocked by the
  sandbox on logs with planted instructions, run time.
- **Careful with:** never run agent code on the host, including in tests; tests use a stub.
- **Rule (proposed):** "Run agent-written code only where it can reach nothing you would miss:
  no network, one input, hard limits, thrown away after."

### 7.13 E11: Human in the loop

- **Arms:** never ask (the harness blocks over-limit refunds instead); ask before every refund;
  ask by policy (over the limit, or when the agent is unsure).
- **Measures:** approvals requested, approvals needed, needed approvals missed, cases resolved,
  human time at an invented minutes-per-approval figure.
- **Checkpoint and resume:** a paused case is written to disk and resumed in a new process;
  test that resumed runs reach the same end state as uninterrupted ones.
- **Rule (proposed):** "Ask a human before actions that cost money or cannot be undone, and only
  then. Every extra approval is time someone spends."

### 7.14 E12: Self-checking loops

- **Arms on telemetry cases:** one attempt; retry with the raw error; retry with structured
  feedback (what failed, what was tried before); structured feedback plus stall detection (same
  failure fingerprint twice in a row stops the loop) and a token budget per case.
- **Finish test in code:** the analysis runs cleanly, the output matches its schema, the figures
  reconcile.
- **Measures:** diagnosis correct, attempts per case, tokens, stalls caught, cases stopped by the
  budget.
- Complete `agent-safety-checklist.md`.
- **Rule (proposed):** "Define done as a test code can run. Feed back what failed, stop when the
  same failure repeats, and cap the spend."

### 7.15 E13: Multi-agent systems

- **Arms:** the reference single agent with every tool; a triage router handing off to three
  specialists (warranty, refunds, service) with narrower tool sets; optional, a planner with
  workers, estimated separately.
- **Measures:** resolved, tokens and turns per case, information lost at a handoff, and planted
  instructions passed from one agent to the next.
- **Rule (proposed):** "Use one agent until you can name a reason to split. Specialists pay for
  themselves only when their jobs and permissions really differ."

### 7.16 E14: MCP

- **Build** the Halvard tools as an MCP server with the official Python SDK: read tools and write
  tools as separate servers, so a client can be given read access only.
- **Parity run:** the reference agent using the tools through MCP on the test cases. Requests
  that match exactly are cache hits; report any difference in tool definitions and results.
- **Second client:** connect one other MCP client (proposed: the MCP Inspector, or Claude
  Desktop if Brendan prefers), with screenshots for the deck. No paid calls needed.
- **One slide on A2A,** described, not built.
- **Security:** an MCP server is access to your systems; scope servers by permission.
- **Rule (proposed):** "Wrap a tool once in MCP when more than one agent or client needs it, and
  give each client only the servers it needs."

### 7.17 E15: Agent frameworks

- No new calls. A decision framework from the season's results: what each part of the harness
  costs to build yourself, and what LangGraph, the OpenAI Agents SDK, Google ADK and a managed
  agent platform each give you.
- Short code snippets for the same loop in each framework, taken from current documentation,
  dated, with sources, and clearly marked as not run in this repo.
- Confirm product names and features close to publication.
- **Rule (proposed):** "Build the loop yourself until you know what you need; adopt a framework
  for the parts you would otherwise rebuild."

### 7.18 E16: Season 5 recap

- Recap numbers from `scoreboard.json`: where the reference agent started and ended, what joined,
  what did not, the safety counts, and the per-case flips a total can hide.
- Every decision rule, from the episode handovers.
- What the season left for later (boundaries in section 10).

## 8. Phase 3: tools readers keep

- **`agent-card.md` (E16):** every rule, every "Ask your team" question, and the final
  scoreboard on one page.
- **`agent-safety-checklist.md` (E9, completed at E12):** what to check before an agent gets a
  tool: least privilege, argument checks in code, limits enforced in code, idempotent writes,
  untrusted data treated as data, sandboxed code, approval points, finish tests, caps, audit log.
- **The case environment:** `lab agent env` and `lab agent score`, documented so a reader can run
  their own agent (any language) against the dev cases and score it with no API calls on our
  side.
- The repo README gains a Season 5 section listing the episodes, the dataset and the tools.

## 9. Phase 4: hub changes

A separate pull request in `brendankellyai.github.io` on `s5-hub`. Follow its `README.md` and
build spec, and run `uv run python -m hub.validation`, `pytest` and `ruff`.

1. **`data/seasons.yaml`, S5.** Title "Agents", to match the S0 deck. Description (proposed):
   "From a model that answers to a system that acts: tool calling, memory, sandboxes, human
   approval, MCP, and the code that keeps an agent in bounds."
2. **Episode files.** `data/episodes/s5-e0-*.yaml` to `s5-e16-*.yaml`, all `status: planned`,
   with the titles and slugs in `season5/README.md`.
3. **Tools section:** the agent card, the safety checklist and the case environment, pointing to
   files on `main` (links work after merge).
4. **Course map, optional:** E5 to S2, E11 to S3 E5, E2 to S4 E4, E8 to S1 E6 and E7.

## 10. Phase 5: deck handovers

One per episode, in the Season 4 format. Episode folders keep theirs; E0, E15 and E16 go in
`season5/deck-handovers/`. Each has:

- **Title line:** "For the content agent", plus whether the episode has an experiment.
- **Sources of truth:** exact file paths.
- **Names:** episode code, title, hub slug, deck file and hub format.
- **The argument:** in a few lines.
- **Scoreboard slide:** the reference agent so far, and what this episode adds.
- **Setup before results:** what each arm is, quoting the exact change (the tool description,
  the rule in code, the approval policy), so the deck can explain the test before showing scores.
- **One case stepped through:** a committed `lab agent replay` trajectory per arm.
- **Evidence:** each figure with what it measures, out of how many, and its source path.
- **Cost:** per case and per month at the stated invented volume, including the cost of wrong
  outcomes. Ratios only.
- **Slide ideas,** respecting Brendan's deck rules:
  - Decks teach: explain rather than compress; full sentences; no shorthand.
  - Define every term before a slide relies on it; one-line titles that say plainly what the
    slide shows; little text, large type.
  - Step one case through each arm before any statistics.
  - Reveal a reader prediction on the very next slide.
  - Vary the visual form; prefer diagrams to lists.
  - A short refresher slide when the episode depends on an earlier idea.
  - Use technical terms where needed (tool call, trajectory, idempotent, sandbox) and explain them.
  - Call out security points explicitly.
  - Credit "Building AI Agents: From Design Patterns to Production" where a slide borrows its
    idea.
  - Name cases by topic, never by code.
  - Do not re-present earlier seasons' results at length; one line and a pointer.
  - No claim-verdict slides. The last slide is the series map.
- **For leaders:** one "Ask your team" question.
- **Decision rule (proposed):** it must stand alone for a reader arriving from a share.
- **Next:** the next episode and its one-line teaser.
- **Careful with:** what the evidence does not show. Every claim covers these Halvard cases and
  these models only.
- **From practice:** an empty placeholder for Brendan's own anonymised line. Do not draft it.

### Boundaries to state in handovers

| S5 | Leaves to |
|---|---|
| E15 | S6: the cost of frameworks and platforms; S12: rollout |
| E6 | S7: parsing documents at scale |
| all | S8: building your own evaluations (S5 uses fixed ones) |
| E6, E7, E9, E10, E14 | S11: prompt injection, memory poisoning, red-teaming |
| E12, E13 | S14: always-on agents, watchdogs, recovery |
| E11 | S15: approval policy and controls |

## 11. Open decisions for Brendan

Raise these at Gate 1. Do not decide them yourself.

1. **Sizes and repeats:** test 240, dev 60, 40 sequences, 40 long cases; reference arm run three
   times on 60 cases.
2. **Image model:** whether `gpt-6-luna` takes images; if not, the cheapest model that does, for
   E6 only.
3. **Docker on Brendan's machine:** E10 needs Docker (on Windows, Docker Desktop with WSL 2). If
   that is not wanted, propose running E10 in a GitHub Actions job instead.
4. **Second MCP client for E14:** the MCP Inspector or Claude Desktop.
5. **Optional arms:** E4 with low reasoning, E13 planner with workers. Off by default.
6. **Merge timing:** merge the dataset, harness and tools before E0 publishes, so hub links work.

## 12. Order of work and gates

1. On `s5`: re-verify models (tool calling, image input) in `capabilities.yaml`. Extend the
   provider layer and the mock provider, with tests. Draft `policy.yaml`, the world schema and
   the case plan.
2. **Gate 1:** send the case plan, the policy, the model checks, the token method and the open
   decisions. Wait for approval.
3. **Gate 2, data:** build the world, images and logs (no spend); estimate message generation and
   label checks; after approval, generate, check, produce Brendan's 30 cases, then freeze.
4. The agent loop, tools, customer, approver, scorer, replay and `lab agent` CLI, all tested on
   the mock provider. E1 through its own spend gate.
5. E2 to E4 as one bundled gate. Then E5 and E6.
6. E7 and E8. Then E9, E10 (sandbox first, tested without spend), E11 and E12.
7. E13, then E14 (server and parity run). E15 and E16 with no calls.
8. Deck handovers as each episode completes; E0 once Gate 1 is approved.
9. Hub pull request (can run in parallel after Gate 1). Final README pass and the season pull
   request.

## 13. Definition of done

- [ ] Provider layer supports messages, tools and images; earlier seasons' caches still hit.
- [ ] `datasets/halvard-cases/` frozen, with the generation record, label check, Brendan's
  30-case check and a passing frozen test.
- [ ] `lab agent run`, `analyse`, `replay`, `score`, `env` and `mcp-serve` work, with tests.
  Coverage 85% or more. Ruff clean.
- [ ] No agent-written code ran outside the sandbox, including in tests.
- [ ] Every experiment has a pre-registration committed before its first call, results,
  analysis, slide charts, a replayed trajectory, a README and a deck handover.
- [ ] Every spend was approved, and estimated and actual token counts are in each README.
- [ ] Every model call used the cheapest suitable model, apart from exceptions approved by name.
- [ ] `scoreboard.json`, `reference.yaml` and `reference_history.yaml` reflect what joined
  under the strict bar.
- [ ] Agent card and safety checklist in `season5/`; the case environment documented for readers.
- [ ] Seventeen deck handovers (E0 to E16), each with sources, setup, a stepped-through case,
  evidence with what it measures, cost, a proposed decision rule, an "Ask your team" question and
  an empty "From practice" placeholder.
- [ ] The hub pull request passes validation, tests and the link check.
- [ ] No dash characters anywhere. British spelling throughout.
