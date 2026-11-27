# Season 5: Agents, episode guide

Status: agreed plan, 27 November 2026. Episode list, titles, slugs, acts, running case and scope approved by Brendan. The build follows `s5-build-handover.md` in this folder.

**Build status, 27 November 2026:** step 1 done (provider support for messages, tools and images; drafts of the policy, world schema, case plan and token method). [Gate 1](gate-1.md) approved 27 November 2026; the smoke test passed. [Gate 2](gate-2.md): the world, cases, images and logs are built with no spend; the paid message step waits for approval.

**Subtitle (proposed):** From a model that answers to a system that acts, and the code that keeps it in bounds

**Role in the series:** the first season where the model takes actions. It applies S1 (How LLMs work), S2 (Retrieval) and S4 (Adapting models), and works inside the levels of autonomy set in S3 E5. It hands security in depth to S11, resilience to S14 and governance to S15.

**Reference guide:** "Building AI Agents: From Design Patterns to Production" (open source; written permission held). Used as a map of the ground to cover for this and any later season on agents, not as a source of code, text or evidence. Every claim in the season is tested on Halvard, not taken from the book. Credit the book on slides where an idea is borrowed.

**Out of scope (decided 27 November 2026):** voice agents, and coding agents such as Claude Code and Antigravity. Either can be added in a later season if needed.

**Title rule:** each title leads with the topic a learner would search for, then says plainly what the episode covers. No clever or cute phrasing.

## Episode guide

| Ep | Title | Tag | Question it answers | Read it when | Builds on |
|---|---|---|---|---|---|
| E0 | Season 5 intro: AI agents | | What is an agent, and what will this season teach you to build? | You are starting out | S1, S2, S3 E5, S4 |
| E1 | Agents or fixed pipelines: when to use an agent | Experiment | When does a task need an agent, and when is fixed code better? | Someone proposes an agent | S3 E1, E2 |
| E2 | Tool calling: building the agent loop from scratch | Experiment | What is an agent, mechanically, in about 30 lines? | You want to see inside the box | S4 E4 (structured output) |
| E3 | Tool design: descriptions, schemas and error messages | Experiment | How much do tool names, descriptions, schemas and error messages change results? | Your agent calls the wrong tool | E2 |
| E4 | Agent patterns: ReAct, plan-and-execute and reflection | Experiment | Which pattern suits which task, at what cost? | You are choosing an agent pattern | S1 E10, E11 (reasoning) |
| E5 | Agentic RAG: letting the agent decide what to search for | Experiment | Does letting the agent decide what to search for beat one search up front? | Your RAG system misses multi-part questions | S2 reference system |
| E6 | Multimodal agents: reading facts from images | Experiment | Can an agent take facts from a photo reliably, and when should it ask the customer instead? | Customers send photos instead of typing details | S1 E2 (tokens), E3 |
| E7 | Agent memory: working, semantic, episodic and procedural | Experiment | Which memory types exist, and which ones does a task need? | Users expect the agent to remember them | S1 E6, S2 |
| E8 | Context management for long tasks: scratchpads and compaction | Experiment | How does an agent work for many steps without drowning in its own history? | Long tasks get worse as they go | E7, S1 E6, E7 |
| E9 | The agent harness: enforcing rules in code, not prompts | Experiment | What must be enforced in code rather than asked for in the prompt? | An agent gets write access to anything | E2, E3 |
| E10 | Sandboxing: running agent-written code safely | Experiment | How do you let an agent write and run code on untrusted files without risking your systems? | An agent needs to run code | E9 |
| E11 | Human in the loop: approvals, pausing and resuming | Experiment | Which actions need a human, and how does the agent pause and resume? | An agent can spend money or change records | S3 E4, E5 |
| E12 | Self-checking loops: stop conditions, retries and budget caps | Experiment | How does an agent know it is finished, and when does it give up? | Agents loop, stall or declare victory early | E9, E10 |
| E13 | Multi-agent systems: one agent or several specialists | Experiment | When do specialist agents beat one agent with every tool, and what does coordination cost? | A design shows a fleet of agents | E3, E9 |
| E14 | MCP: sharing tools with the Model Context Protocol | Experiment | What does a standard tool protocol buy you, and what does it expose? | You are integrating the same tool for a second time | E3, E9 |
| E15 | Agent frameworks: build your own or use LangGraph, ADK or the Agents SDK | Decision | When is each framework or a managed agent platform worth it? | You are choosing an agent stack | Whole season, S3 E8 |
| E16 | Season 5 recap: decision rules for building agents | Recap | What are the season's decision rules? | You need the whole season on one page | Whole season |

## Slugs and file names

Hub page URLs follow `/episodes/<episode-code>-<slug>/`. Deck files follow `bk-s5-e<N>-<slug>-v1.pdf`. Episode folders in this repo follow `episodes/s5-e<N>-<slug>/`. E0 and E16 follow the slugs the hub uses for every season's intro and recap (`season-intro`, `recap`).

| Ep | Slug | Deck file |
|---|---|---|
| E0 | `season-intro` | `bk-s5-e0-season-intro-v1.pdf` |
| E1 | `agents-or-pipelines` | `bk-s5-e1-agents-or-pipelines-v1.pdf` |
| E2 | `tool-calling-loop` | `bk-s5-e2-tool-calling-loop-v1.pdf` |
| E3 | `tool-design` | `bk-s5-e3-tool-design-v1.pdf` |
| E4 | `agent-patterns` | `bk-s5-e4-agent-patterns-v1.pdf` |
| E5 | `agentic-rag` | `bk-s5-e5-agentic-rag-v1.pdf` |
| E6 | `multimodal-agents` | `bk-s5-e6-multimodal-agents-v1.pdf` |
| E7 | `agent-memory` | `bk-s5-e7-agent-memory-v1.pdf` |
| E8 | `context-management` | `bk-s5-e8-context-management-v1.pdf` |
| E9 | `agent-harness` | `bk-s5-e9-agent-harness-v1.pdf` |
| E10 | `sandboxing` | `bk-s5-e10-sandboxing-v1.pdf` |
| E11 | `human-in-the-loop` | `bk-s5-e11-human-in-the-loop-v1.pdf` |
| E12 | `self-checking-loops` | `bk-s5-e12-self-checking-loops-v1.pdf` |
| E13 | `multi-agent-systems` | `bk-s5-e13-multi-agent-systems-v1.pdf` |
| E14 | `mcp` | `bk-s5-e14-mcp-v1.pdf` |
| E15 | `agent-frameworks` | `bk-s5-e15-agent-frameworks-v1.pdf` |
| E16 | `recap` | `bk-s5-e16-recap-v1.pdf` |

## Four acts

- **Build an agent:** E1 to E3
- **Plan, see and remember:** E4 to E8
- **Keep it in bounds:** E9 to E12
- **Scale and choose:** E13 to E15

## Running case: resolve a Halvard warranty case

One case for the whole season, so there is one scoreboard and every episode adds to the same agent. Halvard Home carries over from S2 to S4, so the S2 corpus, the S3 use cases and S4 Task A triage all apply.

A customer reports a faulty Halvard appliance. The agent resolves the case from start to finish. A case can include:

- **The customer's message:** the starting point, routed as in S4 Task A.
- **A receipt photo and a rating plate photo:** the proof of purchase date and the model and serial number (E6).
- **A telemetry log file** exported from the appliance: the agent writes and runs Python over it to decide whether the fault is covered by warranty or caused by misuse (E10, E12).

Tools:

- look up an order
- check warranty status
- search the knowledge base (the S2 reference system)
- read the customer's past cases
- analyse a telemetry file (code execution, in the sandbox)
- book a service visit
- issue a refund (above a set limit, the refund needs human approval)

Each episode uses only the parts it needs.

### Why one case, not two

A last pass was made for a single use case that exercises every episode (27 November 2026). Candidates considered:

- **Support case only:** covers actions, approvals and memory, but no natural need for code execution.
- **Operations analyst only:** covers code execution and self-checking loops, but takes no actions that need approval, which weakens E9 and E11.
- **Field service planner:** scheduling suits a fixed optimiser better than an agent.
- **Support case with photos and telemetry (chosen):** covers every episode. Analysing a customer-supplied file is also the strongest reason for a sandbox, because the file is untrusted input.

The telemetry step is confirmed (27 November 2026): the case is for teaching and does not need to match reality exactly. A separate operations analyst task is not needed.

### Data, all invented

- Orders, warranties, service visits and past cases.
- Receipt and rating plate images rendered by code from known values, at several quality levels (sharp, blurred, angled, glare), so every read can be checked.
- Telemetry logs generated with known faults planted, in formats that vary by product line. Some logs carry planted instructions in their text, to show why the sandbox and harness matter (injection depth stays in S11).

### What every run records

- **Resolved:** the end state matches the expected state.
- **Tool calls:** how many, and how many were unnecessary.
- **Cost:** tokens and cost per case, and per month at a stated invented volume, including the cost of wrong outcomes.
- **Unsafe actions:** attempted, and blocked by the harness.
- **Approvals:** how often the agent asked for a human, and how often it should have.

These measure the path as well as the answer. Building evaluations in general stays in S8.

## Episode notes

- **E0:** name the technical topics plainly (tool calling, ReAct, plan-and-execute, agentic RAG, multimodal input, episodic and procedural memory, context compaction, harness, sandbox, human in the loop, MCP, A2A). Highlight them; do not teach them.
- **E1:** the strongest lesson in the reference guide is when not to use an agent. Run a fixed pipeline and an agent on the same cases; the pipeline should win on routine cases and lose on cases where the next step depends on what was found.
- **E2:** no framework. Step one case through the loop: the model asks for a tool, code runs it, the result goes back, repeat.
- **E3:** tool descriptions, argument schemas and errors returned to the model instead of crashing the run.
- **E4:** ReAct, plan-and-execute, and reflection as a short add-on. Reasoning models from S1 E10 as a refresher.
- **E5:** closes the item S2 left open. One retrieval up front against searches the agent chooses, on multi-part questions.
- **E6:** images only; voice is out of scope. Refresher on tokens: an image costs tokens too. Compare reading the purchase date and serial number from photos against asking the customer to type them, across the image quality levels. Measure correct reads, cost per image, and whether the agent asks the customer when an image is unreadable. Security: text inside an image can carry instructions; name it and hand depth to S11. Parsing documents at scale stays in S7. Check that the cheapest model accepts images before committing.
- **E7:** cover every memory type, each with a Halvard example:
  - **Working (short-term) memory:** the messages in the current case.
  - **Semantic (long-term) memory:** facts that persist, such as a customer's preferences.
  - **Episodic memory:** records of past cases and how they ended.
  - **Procedural memory:** how to do things, held as skills or learned rules.
  - Also: when to write a memory, when to read it, and the security point that memory can store personal data and can be poisoned (depth in S11).
- **E8:** the scratchpad, compaction (keeping lessons, dropping transcripts), and loading reference material only when needed (skills and progressive disclosure). Refresher on context windows and lost in the middle.
- **E9:** the harness: argument checks, allowlists, least privilege per tool, the confused deputy, idempotent tools, an audit log of every tool call. Count unsafe actions blocked. The reference guide's phrase "the model proposes, code disposes" can be used inside the deck, explained, but not as the title. Security points called out explicitly; prompt injection named and handed to S11.
- **E10:** three sandbox levels (path checks, a container, a disposable micro virtual machine). The experiment runs the agent's telemetry analysis in a local container, including logs with planted instructions.
- **E11:** approval points, checkpoints and resuming after a pause. Uses the S3 E5 autonomy levels without re-presenting them.
- **E12:** a finish test that code can check (the analysis runs cleanly, the output matches its schema, the figures reconcile), structured feedback on failures, detecting a loop that has stopped making progress, attempt limits and budget caps.
- **E13:** a single agent with every tool against a triage router handing off to specialists. Measure the coordination cost. Failures spreading from one agent to the next named here, depth in S14.
- **E14:** the Halvard tools as an MCP server used from two different clients. One slide on A2A. Security: an MCP server is access to your systems.
- **E15:** topical; a decision framework, no experiment. Covers LangGraph, the OpenAI Agents SDK, Google ADK and managed agent platforms. Costs stay in S6. Confirm current product names and features close to publication, and update the title if the leading frameworks change.
- **Every episode:** the decision rule must stand alone for readers who arrive from a share or search.

## Code and models

- No agent framework in the experiments. Plain Python against the provider API, so the code stays readable and does not date.
- Libraries that are needed: a container runtime for E10 (Docker, local, no cloud sandbox account) and the official MCP Python SDK for E14. Neither is an agent framework.
- The cheapest model for every experiment call; it must accept images for E6.
- Give a token estimate and spend notice before any run.

## Coverage against the reference guide

| Guide chapter | Where it is covered |
|---|---|
| 1 Anatomy of an agent | E0, E1, E2, E4 |
| 2 Prompt architecture | S4 |
| 3 Tools, skills, structured outputs | E3, E8; S4 E4 |
| 4 Handoffs and routines | E13 |
| 5 Stateful agent graphs | E11, E15 |
| 6 Multi-agent collaboration | E13 |
| 7 Model portability | S3 E9, S6 |
| 8 MCP, A2A, A2UI, AP2 | E14 (A2UI and AP2 left out) |
| 9 Declarative skills | E7, E8 |
| 10 Coding agents (Claude Code, Antigravity) | Out of scope |
| 11 Memory and agentic RAG | E5, E7, E8 |
| 12 Code execution and sandboxes | E10 |
| 13 Multimodal and voice | E6 (images); voice out of scope |
| 14 Guardrails and safety | E9 (least privilege); S11 in depth |
| 15 Harness engineering | E8, E9, E12 |
| 16 Always-on agents | S14 |
| 17 Managed agents | E15; S6 |
| 18 Evaluation and observability | Run measures in every episode; S8 in depth |
| 19 Deployment and async agents | E9 (idempotent tools), E12 (budget caps); S12, S14 |
| 20 Loop engineering | E12 |
| 21, 22, appendices | Not covered |

## Boundaries with other seasons

| S5 episode | Other season | Split |
|---|---|---|
| E11 | S3 Strategy | S3 E5 sets the autonomy level per use case; S5 builds the pause and approval. |
| E6 | S7 Data | S5 reads facts from one case's images; S7 covers parsing documents at scale. |
| E6, E7, E9, E10, E14 | S11 Security | S5 builds least privilege, the harness and the sandbox; S11 covers prompt injection (including through images and files), memory poisoning and red-teaming in depth. |
| E12, E13 | S14 Resilience | S5 covers loops that stop and failures handed between agents; S14 covers always-on agents, watchdogs and recovery. |
| All | S8 Evaluation | S5 uses fixed measures; S8 covers building your own evaluations. |
| E15 | S6 Economics | S5 chooses the stack; S6 prices it. |
| E15 | S12 Delivery | S5 builds the agent; S12 covers rollout and adoption. |
| E11 | S15 Governance | S5 builds approval points; S15 covers policy and controls. |

## Build order

1. Running case data: orders, warranties, past cases, rendered images, telemetry logs; the tool set; the cases with expected end states.
2. The plain-Python agent loop and harness, with tests; S5 hub page.
3. E0 deck.
4. Token estimates and spend notice before each experiment.
5. Episodes in order.
