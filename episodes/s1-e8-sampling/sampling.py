"""S1 E8, Sampling, Part B: the same prompt, sent again and again, to a real model.

Run from the repository root:

    uv run python episodes/s1-e8-sampling/sampling.py

Needs OPENAI_API_KEY, either in the repository's .env file or set in your environment.
Makes up to 61 short calls. Writes results/api.json, which chart.py and the tests read, so neither
needs a key. Part A, GPT-2's own probabilities, is local.py and needs no key. See README.md.
"""

from collections import Counter

from dotenv import load_dotenv
from openai import OpenAI

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
client = OpenAI()
prompt = ("Suggest a name for a coffee shop in Dublin. "
          "Reply with the name only.")
responses = [
    client.responses.create(
        model="gpt-6-astra", input=prompt,
        max_output_tokens=4000)
    for _ in range(20)
]
counts = Counter(r.output_text.strip() for r in responses)
for answer, count in counts.most_common():
    print(f"{count:2d}  {answer}")

# Not on the slides: the one-answer prompt, the temperature probe, the temperature 0 run if the
# probe allows it, and the counting that treats an incomplete response as no answer. The 20 calls
# above are the coffee shop run at the model's defaults, so they are recorded, not repeated.
import json
from datetime import UTC, datetime
from pathlib import Path

import openai

from lab.experiments import load_sibling

HERE = Path(__file__).parent
measure = load_sibling(HERE / "measure.py")

MODEL = "gpt-6-astra"
CAPITAL_PROMPT = "What is the capital of Ireland? Reply with one word."
COFFEE_PROMPT = "Suggest a name for a coffee shop in Dublin. Reply with the name only."
# Generous, because a reasoning model spends part of the limit thinking before it writes, and a
# limit that is too small leaves an empty answer (see S1 E6).
OUTPUT_LIMIT = 4000
RUNS = measure.API_RUNS
PROBE_TEMPERATURE = 0


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
        "temperature_echoed": getattr(response, "temperature", None),
        "output_item_types": [item.type for item in response.output],
        "text": response.output_text,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
            "total_tokens": usage.total_tokens,
        },
    }


def send(request: dict) -> dict:
    return describe(client.responses.create(**request), request)


def condition(name: str, request: dict, runs: list[dict]) -> dict:
    """A set of repeated calls, with the answers counted and the non-answers kept apart."""
    answers = [run["text"] for run in runs if measure.is_answer(run["status"], run["text"])]
    distinct = measure.distinct_counts(answers)
    unanswered = [run for run in runs if not measure.is_answer(run["status"], run["text"])]
    return {
        "name": name,
        "prompt": request["input"],
        "temperature_requested": request.get("temperature"),
        "runs": runs,
        "answered": len(answers),
        "unanswered": len(unanswered),
        "unanswered_statuses": [run["status"] for run in unanswered],
        "distinct": [[answer, count] for answer, count in distinct],
        "distinct_count": len(distinct),
    }


def request_for(prompt_text: str, **settings) -> dict:
    return {"model": MODEL, "input": prompt_text, "max_output_tokens": OUTPUT_LIMIT, **settings}


coffee_request = request_for(COFFEE_PROMPT)
coffee_default = condition(
    "coffee-default", coffee_request, [describe(one, coffee_request) for one in responses]
)

capital_request = request_for(CAPITAL_PROMPT)
capital_default = condition(
    "capital-default", capital_request, [send(capital_request) for _ in range(RUNS)]
)

# The documentation does not say whether this model takes a temperature, so the only way to know
# is to send one and record exactly what comes back.
probe_request = request_for(CAPITAL_PROMPT, temperature=PROBE_TEMPERATURE)
try:
    probe_run = send(probe_request)
except openai.BadRequestError as error:
    probe = {
        "request": probe_request,
        "outcome": measure.classify_probe(False, None, PROBE_TEMPERATURE),
        "error": {
            "status_code": error.status_code,
            "type": getattr(error, "type", None),
            "code": getattr(error, "code", None),
            "param": getattr(error, "param", None),
            "message": error.message,
        },
    }
else:
    probe = {
        "request": probe_request,
        "outcome": measure.classify_probe(
            True, probe_run["temperature_echoed"], PROBE_TEMPERATURE
        ),
        "response": probe_run,
    }
print(f"\nTemperature {PROBE_TEMPERATURE}: {probe['outcome']}")

conditions = [coffee_default, capital_default]
if probe["outcome"] != "rejected":
    zero_request = request_for(COFFEE_PROMPT, temperature=PROBE_TEMPERATURE)
    conditions.append(
        condition(
            "coffee-temperature-0", zero_request, [send(zero_request) for _ in range(RUNS)]
        )
    )
else:
    print("Claim 3 cannot be tested on this model, so the temperature 0 run is skipped.")

print()
for one in conditions:
    top = ", ".join(f"{count} x {answer!r}" for answer, count in one["distinct"][:3])
    print(
        f"{one['name']}: {one['distinct_count']} distinct answers from {one['answered']} "
        f"answered, {one['unanswered']} not answered. Most common: {top}"
    )

record = {
    "model_requested": MODEL,
    "model_returned": coffee_default["runs"][0]["model_returned"],
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "output_limit": OUTPUT_LIMIT,
    "runs_per_condition": RUNS,
    "normalisation": (
        "strip whitespace at both ends, fold the case, remove punctuation at the end; "
        "the raw text is kept as well"
    ),
    "probe": probe,
    "conditions": conditions,
}
out = HERE / "results" / "api.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
