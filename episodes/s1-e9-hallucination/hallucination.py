"""S1 E9, Hallucination: does a model describe things that do not exist, and does "say if you do
not know" help?

Run from the repository root:

    uv run python episodes/s1-e9-hallucination/hallucination.py

Needs OPENAI_API_KEY, either in the repository's .env file or set in your environment.
Makes 122 calls. Writes results/answers.json, which chart.py and the tests read, so neither needs a
key. See README.md in this folder.
"""

from dotenv import load_dotenv
from openai import OpenAI

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
client = OpenAI()
act = "Algorithmic Accountability (Public Bodies) Act 2019"
question = f"Summarise the main provisions of the {act}."
note = ("If you are not sure this exists, "
        "say so rather than guessing.")
responses = []
for prompt in (question, f"{question} {note}"):
    response = client.responses.create(
        model="gpt-6-astra", input=prompt,
        max_output_tokens=4000)
    responses.append(response)
    print(response.output_text + "\n")

# Not on the slides: all 120 scored calls, the scoring, and the record. The two responses above
# are one invented item asked both ways. They are recorded as they were printed, but they are not
# among the 120 and are not scored, so the rates are not built on the example the slide shows.
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from lab.experiments import load_sibling

HERE = Path(__file__).parent
items = load_sibling(HERE / "items.py")
measure = load_sibling(HERE / "measure.py")

MODEL = "gpt-6-astra"
# A few calls at once, so 120 calls take minutes and not the better part of an hour. Each call is
# independent, and the results are put back in a fixed order.
WORKERS = 6


def describe(response, request: dict) -> dict:
    """Everything one call returned that the episode reports, and the rule's label for it."""
    details = response.incomplete_details
    usage = response.usage
    text = response.output_text
    return {
        "request": request,
        "response_id": response.id,
        "model_returned": response.model,
        "status": response.status,
        "incomplete_details": None if details is None else {"reason": details.reason},
        "output_item_types": [item.type for item in response.output],
        "text": text,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
            "total_tokens": usage.total_tokens,
        },
        "label": measure.label_response(response.status, text),
        "matched_phrases": measure.matched_phrases(text),
        # Filled in by hand after the run, when the responses are read. Never by the script.
        "reading": None,
        "disagreement_note": None,
    }


def request_for(prompt_text: str) -> dict:
    return {"model": MODEL, "input": prompt_text, "max_output_tokens": measure.OUTPUT_LIMIT}


def subject(item: dict) -> str:
    return item["name"] if item["category"] == "acts" else item["title"]


def prompt_for(item: dict, condition: str) -> str:
    fields = {key: str(item[key]) for key in ("name", "title", "year", "authors") if key in item}
    return measure.prompt_for(item["category"], condition, **fields)


def scored_call(task: tuple[dict, str, int]) -> dict:
    item, condition, run = task
    request = request_for(prompt_for(item, condition))
    response = client.responses.create(**request)
    return {
        "item_id": item["id"],
        "category": item["category"],
        "real": item["real"],
        "subject": subject(item),
        "condition": condition,
        "run": run,
        **describe(response, request),
    }


slide_run = [
    describe(one, request_for(text))
    for one, text in zip(responses, (question, f"{question} {note}"), strict=True)
]

tasks = [
    (item, condition, run)
    for run in range(1, measure.RUNS_PER_ITEM + 1)
    for item in items.ITEMS
    for condition in measure.CONDITIONS
]
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    scored = list(pool.map(scored_call, tasks))
# The order in the file is by item, then condition, then run, whatever order the calls finished.
order = {item["id"]: index for index, item in enumerate(items.ITEMS)}
conditions = {name: index for index, name in enumerate(measure.CONDITIONS)}
scored.sort(key=lambda r: (order[r["item_id"]], conditions[r["condition"]], r["run"]))

summary = measure.summarise(scored)

print()
for condition, scopes in summary.items():
    invented, real = scopes["all"]["invented"], scopes["all"]["real"]
    print(
        f"{condition}: invented treated as real {invented['count']} of {invented['answered']} "
        f"answered ({invented['unanswered']} unanswered); real flagged {real['count']} of "
        f"{real['answered']} answered ({real['unanswered']} unanswered)"
    )

record = {
    "model_requested": MODEL,
    "model_returned": slide_run[0]["model_returned"],
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "output_limit": measure.OUTPUT_LIMIT,
    "runs_per_item": measure.RUNS_PER_ITEM,
    "instruction": measure.INSTRUCTION,
    "flag_phrases": list(measure.FLAG_PHRASES),
    "items_checked_utc": items.CHECKED_UTC,
    "items": items.ITEMS,
    "replacements": items.REPLACEMENTS,
    "slide_run": {"subject": act, "responses": slide_run},
    "responses": scored,
    "summary": summary,
}
out = HERE / "results" / "answers.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
