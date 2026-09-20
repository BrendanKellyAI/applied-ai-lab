# S1 E6: Context windows

The code behind the two silent failures shown in S1 E6, Context windows. The part of `edge.py` below the marker comment matches the slide line for line.

## What it shows

The slide "What happens at the edge" says that of four ways a conversation can fail at the edge of the context window, only one is loud: the API refuses the request with an error. The other three hand back a normal-looking answer. This code demonstrates two of the silent ones, on a real model, and reports what the API actually returned.

1. **Cut off.** An answer that reaches the output limit stops there. The slide's claim is that it comes back looking like an answer, and that only a status field says it was cut short.
2. **Truncated.** Trimming history to fit a budget, oldest first, drops the instruction at the top of the conversation, and the model stops following it.

Run on 20 September 2026 with `gpt-6-astra` through the Responses API, the same model and call as S1 E1. The API returned the model name `gpt-6-astra`.

**Both failures appeared. Failure 1 appeared in a more extreme form than the slide describes: at both small limits the answer was not cut short but empty.** Details below.

## Demonstration 1: cut off

The prompt: "Explain how a context window works, in five paragraphs." Asked at three output limits. The 60-token run is the one on the slide.

### The fields the API returns

For an answer that hit its limit, the Responses API returned:

| Field | Value |
|---|---|
| `status` | `"incomplete"` |
| `incomplete_details.reason` | `"max_output_tokens"` |

For the complete answer, `status` was `"completed"` and `incomplete_details` was `null`. This is the Responses API's wording, checked against the current documentation and the SDK's types. It is not the Chat Completions `finish_reason: "length"`, which does not appear here at all.

### What came back

| Output limit | `status` | `incomplete_details.reason` | Visible text | Input tokens | Output tokens | Reasoning tokens |
|---|---|---|---|---|---|---|
| 60 | `incomplete` | `max_output_tokens` | **empty**, 0 characters | 17 | 60 | 60 |
| 16 | `incomplete` | `max_output_tokens` | **empty**, 0 characters | 17 | 16 | 16 |
| 8,000 | `completed` | none | five paragraphs, 1,841 characters | 17 | 401 | 42 |

What the slide's script printed at the 60-token limit was an empty line, then:

```
Status: incomplete
Reason: max_output_tokens
```

The response's output list held a single item, of type `reasoning`, and no `message` item at all. The complete answer held both.

## What the results say about the first failure

**The failure appeared, and in its most silent form.** The model reasons before it answers, and the hidden reasoning counts against the output limit. At 60 tokens and at 16, all of the limit went on reasoning: output tokens equal reasoning tokens, and nothing was left to show. The call succeeded, the usage figures look ordinary, and the only sign that anything went wrong is the `status` field. A program that reads only `output_text` gets an empty string and no error. Reasoning tokens are billed as output, so the caller pays for a reply and receives nothing.

**It did not appear as the slide words it.** The slide says a cut-off answer comes back looking like an answer. At these two limits there was no partial answer to look like one: the text was empty. A limit somewhere between 60 and the 401 tokens the complete answer needed would probably leave room for some visible words after the reasoning, and that would be the half-finished answer the slide describes. That was not run here. The tests pin what was observed at 60 and 16.

**One further observation.** The complete answer used 42 reasoning tokens, yet at the 60-token limit the reasoning alone reached 60. So the amount of hidden reasoning is not fixed for a prompt, and the same limit may leave visible text on one call and none on the next. This run cannot say why.

The practical rule holds either way: check `status` on every response, and never treat a returned answer as finished until it says `"completed"`. The documentation warns of exactly this case: reasoning can use up the limit before any visible output, and you are still billed for it. It recommends leaving generous room for reasoning.

## Demonstration 2: truncated

A conversation of 50 messages: the instruction "Reply only in French.", then 24 earlier exchanges about starting a vegetable garden, then a final English question: "What is the single most useful tip for a complete beginner? Two sentences at most." The text is fixed and committed in `conversation.py`. It comes to 2,479 tokens, over a budget of **2,000**.

The earlier assistant answers are in English, on purpose. If they were in French, a French reply could be the model copying its own earlier answers, not following the instruction. With English answers, French can only come from the instruction.

**The budget stands in for a full window.** A real window holds far more than 2,000 tokens; the small budget only makes the edge cheap to reach. Tokens are counted with tiktoken's `o200k_base`, as in S1 E2, on each message's text alone. That is a stand-in for the model's own tokeniser, which also counts formatting around each message: the API counted 2,144 and 2,153 input tokens for the two trimmed conversations below, against 1,948 and 1,953 by this count.

Two strategies, both written in `trim.py` as pure functions, and both keeping the final question:

- **Naive:** drop messages from the oldest until the total fits. The instruction is the oldest message, so it goes first.
- **Pinned:** keep the instruction, then drop the oldest other messages until the total fits.

Each trimmed conversation was sent 5 times, alternating between the two. Replies were allowed up to 4,000 tokens, so none could be cut short.

### The French check, fixed before any reply was seen

A reply counts as French when it contains at least 3 words from a fixed list of common French function words (`le`, `la`, `des`, `est`, `dans`, and so on) and more of them than words from a fixed list of common English ones (`the`, `is`, `and`, `that`, and so on). Words that are ordinary in both languages, such as `on`, `plus`, `son`, `par` and `a`, are on neither list. An empty reply is not French. The rule uses no library, so it gives the same answer on every machine, and it is applied mechanically. It says whether a reply is written in French, not whether the French is good. The lists are in `french.py`, and the tests check the rule on fixed examples.

### Results

| | Naive | Pinned |
|---|---|---|
| Messages kept, of 50 | 39 | 40 |
| Tokens kept, by our count | 1,948 | 1,953 |
| Instruction kept | **No** | Yes |
| First message kept | "What are the most common pests?" | "Reply only in French." |
| **Replies in French, of 5** | **0** | **5** |

All ten replies completed with visible text. Every naive reply was an English answer such as "Start small with two or three vegetables you enjoy eating, rather than trying to grow everything at once." Every pinned reply began "Commencez petit, avec deux ou trois légumes". The replies are all in `results/edge.json`.

## What the results say about the second failure

**The failure appeared, cleanly.** With the instruction trimmed away, the model answered in English 5 times out of 5. With it kept, 5 out of 5 in French. Nothing about the naive conversation looked wrong: no error, a complete reply, ordinary token counts. The model simply had no instruction to follow. Trimming from the oldest end is the obvious way to fit a budget, and it removes exactly the message that says what to do.

Limits on what this shows:

- **One conversation, one question, 5 runs each.** The result is 0 of 5 against 5 of 5, which is as clear as five runs can be, but it is one topic and one instruction. It does not measure how often a real trimmer would drop a real instruction.
- **The API did not trim anything.** The trimming is done here, by the code, to a small budget. The request that reached the model was well within its real window. This shows what happens when an application trims and the instruction is among the casualties, which is what chat applications and agent frameworks do when history outgrows their budget.
- **Pinning is not free.** The pinned strategy throws away about as much (10 messages against 11), so it saves the instruction by losing more of the conversation.
- **Whole messages only.** Both strategies drop whole messages, so the naive conversation starts partway through, at a question with everything before it gone.

## Run it

You need Python 3.12 or later, [uv](https://docs.astral.sh/uv/), and an OpenAI API key.

1. From the repository root, install dependencies:

   ```bash
   uv sync
   ```

2. Add your API key to `.env` in the repository root, the same file the rest of the lab uses:

   ```bash
   OPENAI_API_KEY=your-key-here
   ```

   If `.env` does not exist yet, copy `.env.example` to `.env` first. The script loads the key above the code shown on the slides.

3. Run the script:

   ```bash
   uv run python episodes/s1-e6-context-windows/edge.py
   ```

It prints the slide's output, then one line per limit, then one line per strategy, and writes every request, response text, status field, usage figure and token count to `results/edge.json`, with the model name the API returned and the date. Running it again replaces that file.

Responses vary between runs. The status fields at a given limit should match, but how many tokens the model spends reasoning can change, so the visible text at 60 tokens may not always be empty.

## Redraw the chart, no key needed

```bash
uv run python episodes/s1-e6-context-windows/chart.py
```

The chart reads only `results/edge.json`, which is committed, so anyone can redraw it without a key.

- `charts/french-replies`: replies in French out of 5, for the naive and pinned strategies. The acid green mark is the strategy with fewer French replies, the one that lost the instruction. A bar with no replies has no height to colour, so here it is the "0 of 5" label that is green. If the two strategies scored the same, nothing would be highlighted and the chart would say so.

## Cost

13 short calls in all, about 22,500 tokens between them: 21,536 in and 981 out. The exact cost depends on current OpenAI pricing. The script makes new calls every time it runs.
