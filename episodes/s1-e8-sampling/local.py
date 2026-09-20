"""S1 E8, Sampling, Part A: GPT-2's real next-token probabilities, and what temperature does.

Install the optional model dependencies once, then run from the repository root:

    uv sync --extra e4
    uv run --extra e4 python episodes/s1-e8-sampling/local.py

Needs no API key and no new download: it reuses GPT-2 small from S1 E4 and S1 E5. It runs on
the CPU in float32. Writes results/local.json, which chart.py and the tests read, so neither
needs the model. See README.md in this folder.
"""

import os

# Hugging Face warns about symbolic links on Windows; the download works without them.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.logits_process import TopPLogitsWarper

from lab.experiments import load_sibling

HERE = Path(__file__).parent
measure = load_sibling(HERE / "measure.py")

MODEL = "gpt2"
# Hugging Face now redirects "gpt2" to this name; recorded so readers can find the same files.
MODEL_CANONICAL = "openai-community/gpt2"
# The model's commit on Hugging Face, the same one S1 E4 and S1 E5 use, so its weights can never
# change under the results.
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"

tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION).eval()


def next_token_logits(prompt: str) -> list[float]:
    """The model's raw scores for the token after `prompt`, one per vocabulary entry."""
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        scores = model(**inputs, logits_to_keep=1).logits[0, -1]
    # Python floats hold every float32 value exactly, and the softmax is then taken in double
    # precision, so the probabilities are exact to well beyond the digits shown.
    return scores.tolist()


def token_entry(rank: int, index: int, probability: float) -> dict:
    return {
        "rank": rank,
        "token_id": index,
        # GPT-2's own spelling, where a leading G with a dot stands for the space before a word.
        "token": tokenizer.convert_ids_to_tokens(index),
        "text": tokenizer.decode([index]),
        "probability": probability,
    }


def distributions(logits: list[float]) -> dict:
    """The top tokens at each temperature, every one worked out from the same logits."""
    result = {}
    for temperature in measure.TEMPERATURES:
        probabilities = measure.softmax(logits, temperature)
        top = measure.top_k(probabilities, measure.TOP_K)
        result[str(temperature)] = {
            "top": [token_entry(rank, index, p) for rank, (index, p) in enumerate(top, start=1)],
            "top_mass": sum(p for _, p in top),
        }
    return result


def dublin(logits: list[float]) -> dict:
    """Where " Dublin" stands for the capital prompt, whatever GPT-2 puts first."""
    pieces = tokenizer.encode(" Dublin")
    if len(pieces) != 1:
        return {"token_ids": pieces, "single_token": False}
    probabilities = measure.softmax(logits)
    (index,) = pieces
    return {
        "token_id": index,
        "single_token": True,
        "rank": measure.ranked(probabilities).index(index) + 1,
        "probability": probabilities[index],
    }


def sample(prompt: str, temperature: float, seed: int) -> dict:
    """Ten new tokens sampled at `temperature`, from a seed that is recorded with the result."""
    torch.manual_seed(seed)
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(
            **inputs,
            do_sample=True,
            temperature=temperature,
            # Switched off, so the only reshaping is the temperature. The library's own default
            # keeps the 50 likeliest tokens, which would make the samples differ from the
            # distributions computed above.
            top_k=0,
            top_p=1.0,
            # The end token is not allowed to stop it early, so every sample is ten tokens long.
            min_new_tokens=measure.NEW_TOKENS,
            max_new_tokens=measure.NEW_TOKENS,
            pad_token_id=tokenizer.eos_token_id,
        )
    new = output[0, inputs["input_ids"].shape[1] :].tolist()
    return {"seed": seed, "text": tokenizer.decode(new), "token_ids": new}


def greedy(prompt: str) -> dict:
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(
            **inputs,
            do_sample=False,
            min_new_tokens=measure.NEW_TOKENS,
            max_new_tokens=measure.NEW_TOKENS,
            pad_token_id=tokenizer.eos_token_id,
        )
    new = output[0, inputs["input_ids"].shape[1] :].tolist()
    return {"text": tokenizer.decode(new), "token_ids": new}


def top_p_check(logits: list[float]) -> dict:
    """The tokens top-p keeps at temperature 1.0, checked against the library's own filter."""
    probabilities = measure.softmax(logits)
    kept = measure.top_p_set(probabilities, measure.TOP_P)
    filtered = TopPLogitsWarper(top_p=measure.TOP_P)(None, torch.tensor([logits]))[0].tolist()
    library_kept = {index for index, value in enumerate(filtered) if value != float("-inf")}
    cumulative = 0.0
    entries = []
    for rank, index in enumerate(kept, start=1):
        cumulative += probabilities[index]
        entries.append({**token_entry(rank, index, probabilities[index]), "cumulative": cumulative})
    return {
        "top_p": measure.TOP_P,
        "temperature": 1.0,
        "kept": entries,
        "kept_mass": cumulative,
        "matches_transformers": library_kept == set(kept),
    }


prompt_records = {}
for name, prompt in measure.PROMPTS.items():
    logits = next_token_logits(prompt)
    prompt_records[name] = {
        "prompt": prompt,
        "prompt_tokens": tokenizer.convert_ids_to_tokens(tokenizer(prompt)["input_ids"]),
        "vocabulary_size": len(logits),
        "distributions": distributions(logits),
    }
    if name == "capital":
        prompt_records[name]["dublin"] = dublin(logits)
    print(f'"{prompt}"')
    for entry in prompt_records[name]["distributions"]["1.0"]["top"]:
        print(f"  {entry['probability']:.4f}  {entry['text']!r}")

colour = measure.PROMPTS["colour"]
top_p = top_p_check(next_token_logits(colour))
print(
    f"\ntop-p {measure.TOP_P} keeps {len(top_p['kept'])} tokens "
    f"({top_p['kept_mass']:.3f} of the probability); matches transformers: "
    f"{top_p['matches_transformers']}"
)

sampling = {}
for temperature in measure.TEMPERATURES:
    samples = [sample(colour, temperature, seed) for seed in measure.SEEDS]
    distinct = len({one["text"] for one in samples})
    sampling[str(temperature)] = {"samples": samples, "distinct": distinct}
    print(f"temperature {temperature}: {distinct} distinct continuations of {len(samples)}")
greedy_run = greedy(colour)
print(f"greedy: {greedy_run['text']!r}")

record = {
    "model": MODEL,
    "model_canonical": MODEL_CANONICAL,
    "revision": REVISION,
    "device": "cpu",
    "dtype": "float32",
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "libraries": {
        "python": platform.python_version(),
        **{package: version(package) for package in ("torch", "transformers", "tokenizers")},
    },
    "temperatures": list(measure.TEMPERATURES),
    "prompts": prompt_records,
    "top_p": top_p,
    "sampling": {
        "prompt": colour,
        "new_tokens": measure.NEW_TOKENS,
        "seeds": list(measure.SEEDS),
        "settings": "do_sample=True, top_k=0, top_p=1.0, torch.manual_seed(seed) before each",
        "by_temperature": sampling,
        "greedy": greedy_run,
    },
}
out = HERE / "results" / "local.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
