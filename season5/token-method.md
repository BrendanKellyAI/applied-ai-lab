# How Season 5 estimates tokens before a run (draft for Gate 1)

27 November 2026. Season 1 to 4 estimates counted one request per call. An agent case is many
requests, and each resends the whole history, so input grows with every turn. This is how the
number Brendan approves at each spend gate will be produced. No prices appear in committed
files; costs go to Brendan at the gate, and into READMEs as ratios only.

## 1. A dry run on the mock provider

`lab agent estimate <config.yaml>` (to be built with the loop) runs the real arm on the mock
provider, with the real system prompt, tool definitions, harness, customer and approver:

1. **The path.** For each case, the mock agent follows the case's expected path, which the
   policy code knows (the tool calls that reach the expected end state, in order). Tool results
   are the real ones from the case environment, so their sizes are real.
2. **Extra turns.** Agents wander. Before a pilot, each case gets extra calls drawn from a prior
   (one and a half times the expected path's length, rounded up, within the case's caps); after a
   pilot on dev, the prior is replaced by the pilot's measured distribution per case kind.
3. **Counting.** Every request the dry run builds is counted exactly as it would be sent: system
   prompt, tool definitions and every turn, with `o200k_base` for OpenAI text. Images use the
   provider's published rule (OpenAI: 32 pixel patches times the model factor, at the detail
   level the arm sends). Claude and Gemini counts are scaled from `o200k_base` using the factors
   in `prices.local.yaml` notes (Claude runs about 30% higher).
4. **Output.** 120 tokens a turn before a pilot (a tool call or a short reasoning line), then
   the pilot's 90th percentile per turn.
5. **Cached input.** Reported separately: OpenAI caches a repeated prefix of 1,024 tokens or
   more automatically, so most of each turn's resent history is billed at the cached rate. The
   estimate shows both the uncached figure (the ceiling Brendan approves) and the expected cached
   share.

## 2. What the gate shows

For each experiment, line by line:

- Tokens by model and stage (agent turns, customer and approver are free, judge, label check).
- The per case distribution: median, 90th percentile and maximum input tokens, by case kind.
- The total, and the **ceiling**: every case running to its caps (section 7 of the case plan),
  which bounds the spend however badly the agent wanders.
- Cases already in the cache, which cost nothing.

## 3. A rough figure now, to warn early

A first look at turn sizes, before anything is built:

| Part of a turn | Tokens (rough) |
|---|---|
| System prompt with the policy summary | 1,500 |
| Seven to ten tool definitions | 900 |
| Customer message | 150 |
| Each tool result | 150 to 400 (a knowledge base search about 1,500) |
| Each model turn's output | 50 to 150 |

A routine case of 8 turns then resends 2,600 tokens rising to about 6,000: about 35,000 input
tokens and 800 output tokens a case, in line with the handover's 15,000 to 40,000. The
handover's per episode table sums to roughly 145 million tokens for the season, almost all
input to `gpt-6-luna`, most of it eligible for the cached rate.
