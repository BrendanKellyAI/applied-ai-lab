"""S1 E5, The transformer: reading a prompt is fast, writing one token at a time is slow.

Install the optional model dependencies once, then run from the repository root:

    uv sync --extra e4
    uv run --extra e4 python episodes/s1-e5-the-transformer/timing.py

Needs no API key. It reuses GPT-2 small from S1 E4, so there is no new model download, and the
public-domain text S1 E7 uses as filler: if that book is not already in .cache/gutenberg, the
first run fetches it once, about 0.7 MB, from the Project Gutenberg mirror and checks its
SHA-256. It runs on the CPU in float32, with a fixed number of threads.
Writes results/timing.json, which chart.py and the tests read, so neither needs the model.
A full run takes about an hour, most of it the no-cache condition. See README.md.
"""

import os

# Hugging Face warns about symbolic links on Windows; the download works without them.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import time
from functools import cache
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

from lab.experiments import load_sibling

HERE = Path(__file__).parent
REPO = HERE.parents[1]
measure = load_sibling(HERE / "measure.py")
machine = load_sibling(HERE / "machine.py")

# The model's commit on Hugging Face, the same one S1 E4 uses, so its weights can never change
# under the results.
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
# One thread per physical core of the machine the results were taken on. Fixed, not left to
# torch's default, so a rerun on the same machine uses the same number.
THREADS = 4
torch.set_num_threads(THREADS)

# The prompts are cut from this public-domain novel, in the form S1 E7 uses it as filler: the
# same pinned file, checked against the same SHA-256, with the Project Gutenberg header and
# footer removed and the front matter skipped.
FILLER_FOLDER = REPO / "field-notes" / "s1-e7-lost-in-the-middle"
FILLER_BOOK_ID = 1342
# Enough text for the longest prompt, and few enough characters that tokenising it does not
# trip the tokeniser's context-length warning more than once.
FILLER_CHARACTERS = 8000


@cache
def filler() -> dict:
    """The filler passage and its provenance."""
    builder = load_sibling(FILLER_FOLDER / "build_dataset.py")
    config = yaml.safe_load((FILLER_FOLDER / "config.yaml").read_text(encoding="utf-8"))
    entry = next(
        book for book in config["parameters"]["filler_books"] if book["id"] == FILLER_BOOK_ID
    )
    book = builder.Book.from_config(entry)
    text = builder.load_book(book, REPO / builder.GUTENBERG_CACHE).replace("\r\n", "\n")
    start = int(len(text) * builder.FRONT_MATTER_FRACTION)
    return {
        "text": text[text.find("\n\n", start) + 2 :][:FILLER_CHARACTERS],
        "title": book.title,
        "gutenberg_id": book.id,
        "sha256": book.sha256,
    }


def token_ids(tokenizer, count: int) -> list[int]:
    """The first `count` tokens of the filler passage: the same tokens on every run."""
    return measure.cut_to_length(tokenizer(filler()["text"], verbose=False)["input_ids"], count)


def prompt(tokenizer, count: int) -> dict:
    ids = token_ids(tokenizer, count)
    return {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones(1, count).long()}


# Everything below this line matches the slides.
tokenizer = AutoTokenizer.from_pretrained(
    "gpt2", revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(
    "gpt2", revision=REVISION).eval()
long, short = prompt(tokenizer, 512), prompt(tokenizer, 8)
with torch.no_grad():
    start = time.perf_counter()
    model(**long, logits_to_keep=1)
    read = time.perf_counter() - start
    start = time.perf_counter()
    model.generate(**short, do_sample=False,
        min_new_tokens=512, max_new_tokens=512)
    write = time.perf_counter() - start
print(f"reading: {read / 512 * 1000:.1f} ms per token")
print(f"writing: {write / 512 * 1000:.1f} ms per token")

# Not on the slides: warm-ups, repeats, both sweeps, the no-cache condition, the configuration,
# and a record of the run. The figures above are one cold run each, so the results below are
# the ones to quote.
import hashlib
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version

MODEL = "gpt2"
# Hugging Face now redirects "gpt2" to this name; recorded so readers can find the same files.
MODEL_CANONICAL = "openai-community/gpt2"
CONTEXT = model.config.n_positions


def reader(count: int):
    """Reads `count` tokens in one forward pass, and asks for the last position's scores only."""
    measure.check_context(count, 0, CONTEXT)
    inputs = prompt(tokenizer, count)
    return lambda: model(**inputs, logits_to_keep=1)


def writer(count: int, use_cache: bool = True):
    """Writes exactly `count` tokens greedily; the end token is not allowed to stop it early."""
    measure.check_context(measure.WRITING_PROMPT_TOKENS, count, CONTEXT)
    inputs = prompt(tokenizer, measure.WRITING_PROMPT_TOKENS)
    return lambda: model.generate(
        **inputs,
        do_sample=False,
        min_new_tokens=count,
        max_new_tokens=count,
        use_cache=use_cache,
    )


def expect_length(kind: str, result, expected: int) -> None:
    """A condition that produced the wrong amount of text measured the wrong thing."""
    found = result.logits.shape[1] if kind == "reading" else result.shape[1]
    if found != expected:
        raise SystemExit(f"{kind}: expected {expected} positions, found {found}")


def run_condition(kind: str, tokens: int, use_cache: bool = True) -> dict:
    """Warm up twice, then time five runs, of reading `tokens` or writing `tokens`."""
    if kind == "reading":
        run, prompt_tokens, new_tokens, expected = reader(tokens), tokens, 0, 1
    else:
        run, new_tokens = writer(tokens, use_cache), tokens
        prompt_tokens = measure.WRITING_PROMPT_TOKENS
        expected = prompt_tokens + new_tokens
    with torch.no_grad():
        seconds, result = measure.timed(run)
    expect_length(kind, result, expected)
    summary = measure.summarise(seconds, tokens)
    name = f"{kind}-{tokens}" if use_cache else f"{kind}-no-cache-{tokens}"
    print(
        f"{name}: median {summary['per_token_ms']['median']:.2f} ms per token "
        f"(min {summary['per_token_ms']['min']:.2f}, max {summary['per_token_ms']['max']:.2f})",
        flush=True,
    )
    return {
        "name": name,
        "kind": kind,
        "kv_cache": use_cache,
        "prompt_tokens": prompt_tokens,
        "new_tokens": new_tokens,
        "tokens": tokens,
        "warmups": measure.WARMUPS,
        "seconds": seconds,
        "summary": summary,
    }


def configuration() -> dict:
    config = model.config
    return {
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "vocab_size": config.vocab_size,
        "n_positions": config.n_positions,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "attention_implementation": config._attn_implementation,
    }


def prompt_record() -> dict:
    longest = token_ids(tokenizer, max(measure.SWEEP_TOKENS))
    source = filler()
    return {
        "book": source["title"],
        "gutenberg_id": source["gutenberg_id"],
        "book_sha256": source["sha256"],
        "longest_prompt_tokens": len(longest),
        "longest_prompt_ids_sha256": hashlib.sha256(json.dumps(longest).encode()).hexdigest(),
        "writing_prompt_text": tokenizer.decode(longest[: measure.WRITING_PROMPT_TOKENS]),
    }


print()
record_machine = machine.machine_record(torch.get_num_threads())
conditions = [run_condition("reading", tokens) for tokens in measure.SWEEP_TOKENS]
conditions += [run_condition("writing", tokens) for tokens in measure.SWEEP_TOKENS]
# Why models keep earlier work within a call. Not provider prompt caching across calls, which is
# a different mechanism.
conditions.append(run_condition("writing", measure.HEADLINE_TOKENS, use_cache=False))
record_machine["power_source_at_end"] = machine.power_source()

record = {
    "model": MODEL,
    "model_canonical": MODEL_CANONICAL,
    "revision": REVISION,
    "device": "cpu",
    "dtype": "float32",
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "machine": record_machine,
    "libraries": {
        "python": platform.python_version(),
        **{package: version(package) for package in ("torch", "transformers", "tokenizers")},
    },
    "method": {
        "timer": "time.perf_counter",
        "warmups": measure.WARMUPS,
        "repeats": measure.REPEATS,
        "headline_tokens": measure.HEADLINE_TOKENS,
        "sweep_tokens": list(measure.SWEEP_TOKENS),
        "writing_prompt_tokens": measure.WRITING_PROMPT_TOKENS,
        "reading_scores": "last position only (logits_to_keep=1)",
    },
    "prompt": prompt_record(),
    "configuration": configuration(),
    "conditions": conditions,
}
out = HERE / "results" / "timing.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
