"""S1 E6, Context windows: two silent failures at the edge of the window.

Run from the repository root:

    uv run python episodes/s1-e6-context-windows/edge.py

Needs OPENAI_API_KEY, either in the repository's .env file or set in your environment.
Makes 13 short calls. Writes results/edge.json, which chart.py and the tests read, so neither
needs a key. See README.md in this folder.
"""

from dotenv import load_dotenv

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-6-astra",
    input="Explain how a context window works, "
          "in five paragraphs.",
    max_output_tokens=60,
)
print(response.output_text)
print("Status:", response.status)
print("Reason:", response.incomplete_details.reason)

# Not on the slides: the 16-token and generous runs, and Demonstration 2. The 60-token run above
# is the first of the three, so it is recorded rather than repeated. Every request and response
# goes into the results, so nothing shown in the episode has to be taken on trust.
import json
from datetime import UTC, datetime
from pathlib import Path

from lab.experiments import load_sibling

HERE = Path(__file__).parent
conversation = load_sibling(HERE / "conversation.py")
french = load_sibling(HERE / "french.py")
trim = load_sibling(HERE / "trim.py")

MODEL = "gpt-6-astra"
PROMPT = "Explain how a context window works, in five paragraphs."
SLIDE_LIMIT = 60
# The smallest limit the API accepts is 16, so this is the harshest cut there is.
TIGHTEST_LIMIT = 16
# Room for hidden reasoning and all five paragraphs, so the complete answer exists to compare.
GENEROUS_LIMIT = 8000
BUDGET_TOKENS = 2000
RUNS_PER_STRATEGY = 5
# Generous, so a reply is never cut short here and Demonstration 1's failure cannot leak in.
REPLY_LIMIT = 4000


def describe(response, request: dict) -> dict:
    """Everything one call returned that the episode reports."""
    details = response.incomplete_details
    usage = response.usage
    return {
        "request": request,
        "response_id": response.id,
        "model_returned": response.model,
        "status": response.status,
        "incomplete_details": None if details is None else {"reason": details.reason},
        "output_item_types": [item.type for item in response.output],
        "text": response.output_text,
        "characters": len(response.output_text),
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
            "total_tokens": usage.total_tokens,
        },
    }


def cut_off_request(limit: int) -> dict:
    return {"model": MODEL, "input": PROMPT, "max_output_tokens": limit}


slide_run = describe(response, cut_off_request(SLIDE_LIMIT))
cut_off_runs = [slide_run]
for limit in (TIGHTEST_LIMIT, GENEROUS_LIMIT):
    request = cut_off_request(limit)
    cut_off_runs.append(describe(client.responses.create(**request), request))

print()
for run in cut_off_runs:
    usage = run["usage"]
    reason = (run["incomplete_details"] or {}).get("reason")
    print(
        f"limit {run['request']['max_output_tokens']}: status {run['status']}, reason {reason}, "
        f"{run['characters']} characters, output tokens {usage['output_tokens']} "
        f"(reasoning {usage['reasoning_tokens']})"
    )

messages = conversation.messages()
full_tokens = trim.total_tokens(messages)
if full_tokens <= BUDGET_TOKENS:
    raise SystemExit(
        f"The conversation is {full_tokens} tokens, within the {BUDGET_TOKENS}-token budget, "
        "so nothing would be trimmed. Lengthen conversation.py."
    )
trimmed = {
    "naive": trim.trim_naive(messages, BUDGET_TOKENS),
    "pinned": trim.trim_pinned(messages, BUDGET_TOKENS),
}
replies: dict[str, list[dict]] = {name: [] for name in trimmed}
# Alternating, so a slow patch on the API's side cannot fall on one strategy only.
for _ in range(RUNS_PER_STRATEGY):
    for name, kept in trimmed.items():
        request = {"model": MODEL, "input": kept, "max_output_tokens": REPLY_LIMIT}
        # The messages themselves are recorded once per strategy, not once per reply.
        summary = {**request, "input": f"{len(kept)} messages, see strategies.{name}.messages"}
        reply = describe(client.responses.create(**request), summary)
        replies[name].append({**reply, "french": french.is_french(reply["text"])})

print()
strategies = {}
for name, kept in trimmed.items():
    in_french = sum(reply["french"] for reply in replies[name])
    strategies[name] = {
        "messages_kept": len(kept),
        "messages_dropped": len(messages) - len(kept),
        "tokens_kept": trim.total_tokens(kept),
        "instruction_survived": trim.has_instruction(kept),
        "french_replies": in_french,
        "messages": kept,
        "replies": replies[name],
    }
    print(
        f"{name}: kept {len(kept)} of {len(messages)} messages, "
        f"{strategies[name]['tokens_kept']} tokens, instruction kept: "
        f"{strategies[name]['instruction_survived']}, "
        f"French replies: {in_french} of {RUNS_PER_STRATEGY}"
    )

record = {
    "model_requested": MODEL,
    "model_returned": slide_run["model_returned"],
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "cut_off": {"prompt": PROMPT, "runs": cut_off_runs},
    "truncated": {
        "instruction": conversation.INSTRUCTION,
        "final_question": conversation.FINAL_QUESTION,
        "budget_tokens": BUDGET_TOKENS,
        "tokeniser": f"tiktoken {trim.ENCODING}, on each message's text alone",
        "conversation_messages": len(messages),
        "conversation_tokens": full_tokens,
        "runs_per_strategy": RUNS_PER_STRATEGY,
        "reply_limit": REPLY_LIMIT,
        "french_rule": french.RULE,
        "strategies": strategies,
    },
}
out = HERE / "results" / "edge.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
