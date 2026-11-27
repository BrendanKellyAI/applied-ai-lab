# Season 5 Gate 1

27 November 2026, on `s5`. For Brendan's approval. Nothing paid has been called. The data is
not built; this gate approves the plan for it.

## 1. What step 1 built

- **Provider layer** (`src/lab/providers/`): requests can carry `messages` (user, assistant
  and tool result turns, with images), `tools` and `tool_choice`; results carry `tool_calls`.
  Mapped to OpenAI (`openai_messages.py`), Anthropic (`anthropic_messages.py`) and Google
  (`google_messages.py`), including Gemini 3's thought signatures.
  - **Earlier caches still hit:** the new fields are left out of the request hash when unset.
    3,000 of the 67,314 cached requests were re-hashed and all matched their file names; a test
    checks the old hashing rule directly.
  - **Images are held by reference** (path and sha256), so cache entries stay small and the hash
    covers the image's content, not where it sits.
  - **One known gap:** OpenAI tool calls with reasoning on need reasoning items passed back as
    encrypted content. Not built; the adapter refuses that combination rather than sending it
    wrong. It matters only for E4's optional low reasoning arm.
- **Mock provider** scripts tool calls (`MockReply`), so the whole loop can be tested with no
  spend.
- **Capabilities** gain `tool_calling`, `image_input` and `max_images_per_request`, checked
  before any call.
- **Drafts:** [`policy.yaml`](../datasets/halvard-cases/policy.yaml),
  [`schema.sql`](../datasets/halvard-cases/world/schema.sql), the
  [case plan](case-plan.md) and the [token method](token-method.md).
- **A test** checks every rule `policy.yaml` shares with the S2 corpus. It caught one wording
  mismatch already.

## 2. A fix to Season 4's frozen test

All eight `halvard-tasks` frozen file checks failed on a fresh checkout. The data is unchanged:
the manifest was written from a Windows checkout, so it holds hashes of CRLF files, while git
stores them as LF. Every file matches its recorded hash once converted to CRLF. I changed only
the test to hash the files as the manifest did, and left `MANIFEST.json` and the data alone
(commit e79da9c). Season 5's manifest will hash LF normalised content.

## 3. Model checks (27 November 2026)

From the vendors' model, pricing, tool and vision pages (sources in `capabilities.yaml`).

| Role | Model | Tool calling | Image input | Cheapest? |
|---|---|---|---|---|
| Agent, every arm | `gpt-6-luna`, reasoning off | Yes | Yes, up to 1,500 images a request | Yes. Only `gpt-5-nano` is cheaper, and it is deprecated |
| Data generation | `gemini-3.1-flash-lite` | Not needed | Not needed | Cheapest Gemini model that is current and not an agent model |
| Label checker | `claude-haiku-5-5` | Yes | Yes | Cheapest Claude model |
| Judge, E5 only | `gemini-3.6-flash` | Not needed | Not needed | See decision 7 |

So no exception is needed for E6: the agent model takes images. The `parallel` tool calling
entries are from the docs and will be confirmed by `lab smoke`.

## 4. The first spend request (small)

`lab smoke` with one tool call request and one image request each for `gpt-6-luna` and
`claude-haiku-5-5`, plus a text call to `gemini-3.1-flash-lite`: about 10 calls, under 20,000
tokens in total. It confirms tool calling, parallel calls and image input before anything is
built on them. I will send the exact `lab estimate` figure with the request.

## 5. Decisions for you

| # | Decision | My proposal |
|---|---|---|
| 1 | Sizes and repeats | As proposed: dev 60, test 240, sequences 40, long 40; reference arm three times on a fixed 60 |
| 1a | Telemetry cases (new) | Their own file, dev 15 and test 45, for E10 and E12; the 240 covers the other seven kinds, because no arm before E10 can use the code tool ([case plan](case-plan.md), section 4) |
| 2 | Image model | `gpt-6-luna`: it lists image input. No exception |
| 3 | Docker | Already installed here (Docker 28.3.2, WSL 2). Run E10 locally |
| 4 | Second MCP client | The MCP Inspector: free, no account, easy to screenshot. Claude Desktop only if you want it on a slide |
| 5 | Optional arms | Leave both off. E4's low reasoning arm would also need the adapter gap in section 1 closed |
| 6 | Merge timing | One interim pull request from `s5` to `main` once the dataset is frozen and the harness, `lab agent env` and `score` work, so hub links resolve before E0 publishes; the season pull request at the end as usual |
| 7 | E5 judge | Keep `gemini-3.6-flash`. The only cheaper candidate, `claude-haiku-5-5`, already failed the judge check in S4 E7 (161 of 180, against a 90% mark). Run E5 before 31 December if the build reaches it, to avoid the price rise |
| 8 | Invented rules (new) | Approve the numbers in `policy.yaml`: refund approval limit £250, goodwill 25% of price within 90 days of cover ending, once a year, always needing approval; replacement after two earlier repairs for the same fault |
| 9 | Tool count (new) | Seven tools as in the guide, plus `ask_customer`, `request_approval` and `close_case`, so every action the agent takes goes through the harness and is logged |
| 10 | Caps (new) | 16 turns, 24 tool calls and 150,000 input tokens a case; long cases 40, 60 and 600,000 |

## 6. After approval

Gate 2: build the world, images and logs (no spend), then estimate message generation and the
label check for your go-ahead.
