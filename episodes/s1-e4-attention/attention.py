"""S1 E4, Attention: where GPT-2 looks from the word "it", measured rather than drawn.

Install the optional attention dependencies once, then run from the repository root:

    uv sync --extra e4
    uv run --extra e4 python episodes/s1-e4-attention/attention.py

Needs no API key. The first run downloads GPT-2 small, about 550 MB, once; after that it runs
offline. It runs on the CPU in float32, so for the pinned model the weights are deterministic.
Writes results/attention.json, which chart.py and the tests read, so neither needs the model.
See README.md in this folder.
"""

import os

# Hugging Face warns about symbolic links on Windows; the download works without them.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import torch
from transformers import AutoModel, AutoTokenizer

# The model's commit on Hugging Face, so its weights can never change under the results.
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"

# Everything below this line matches the slides.
tokenizer = AutoTokenizer.from_pretrained(
    "gpt2", revision=REVISION)
model = AutoModel.from_pretrained(
    "gpt2", revision=REVISION, attn_implementation="eager")
sentence = ("The trophy did not fit in the suitcase "
            "because it was too big.")
inputs = tokenizer(sentence, return_tensors="pt")
with torch.no_grad():
    out = model(**inputs, output_attentions=True)
weights = torch.stack(out.attentions).mean(dim=(0, 2))[0]
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
it = tokens.index("Ġit")
pairs = zip(weights[it, :it].tolist(), tokens)
for weight, token in sorted(pairs, reverse=True):
    print(f"{weight:.3f}  {token.lstrip('Ġ')}")

# Not on the slides: both sentences, every measure, and a record of the run.
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np

from lab.experiments import load_sibling

HERE = Path(__file__).parent
measure = load_sibling(HERE / "measure.py")

MODEL = "gpt2"
# Hugging Face now redirects "gpt2" to this name; recorded so readers can find the same files.
MODEL_CANONICAL = "openai-community/gpt2"
SENTENCES = {
    "big": "The trophy did not fit in the suitcase because it was too big.",
    "small": "The trophy did not fit in the suitcase because it was too small.",
}
QUERY = "Ġit"


def attention_arrays(text: str) -> tuple[list[str], np.ndarray]:
    """The tokens, and attention with the shape (layers, heads, positions, positions)."""
    encoded = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        result = model(**encoded, output_attentions=True)
    names = tokenizer.convert_ids_to_tokens(encoded["input_ids"][0])
    return names, torch.stack(result.attentions)[:, 0].numpy().astype(np.float64)


def positions_of(spans: list, word: str) -> list[int]:
    return next(positions for name, positions in spans if name == word)


runs = {}
for name, text in SENTENCES.items():
    names, arrays = attention_arrays(text)
    if names.count(QUERY) != 1:
        raise SystemExit(f'" it" is not a single token in: {text}')
    query = names.index(QUERY)
    spans = measure.word_spans(names, query)
    weights_here = measure.word_weights(measure.averaged_row(arrays, query), spans, query)
    for entry in weights_here["words"]:
        entry["token_split"] = [names[position] for position in entry["tokens"]]
    runs[name] = {
        "sentence": text,
        "tokens": names,
        "query_index": query,
        **weights_here,
        "trophy_minus_suitcase": measure.trophy_minus_suitcase(
            arrays, query, positions_of(spans, "trophy"), positions_of(spans, "suitcase")
        ),
        "arrays": arrays,
    }

# GPT-2 reads left to right, so "it" cannot see the words after it. Measuring how far its
# attention actually differs between the sentences shows whether that holds in the numbers too.
query = runs["big"]["query_index"]
visible = slice(0, query + 1)
difference = float(
    np.abs(
        runs["big"]["arrays"][:, :, visible, visible]
        - runs["small"]["arrays"][:, :, visible, visible]
    ).max()
)
shifts = measure.head_shifts(
    runs["big"]["trophy_minus_suitcase"]["per_head"],
    runs["small"]["trophy_minus_suitcase"]["per_head"],
)

print()
for name, run in runs.items():
    words = {entry["word"]: entry for entry in run["words"]}
    print(
        f"{name}: first token {run['first_token_share']:.3f}, "
        f"trophy {words['trophy']['renormalised']:.3f}, "
        f"suitcase {words['suitcase']['renormalised']:.3f} (renormalised)"
    )
print(
    f"Heads shifting towards suitcase: {shifts['towards_suitcase']}, towards trophy: "
    f"{shifts['towards_trophy']}, unchanged: {shifts['unchanged']} of {shifts['heads']}"
)
print(f'Largest difference in attention up to "it" between the sentences: {difference:.3g}')

record = {
    "model": MODEL,
    "model_canonical": MODEL_CANONICAL,
    "revision": REVISION,
    "device": "cpu",
    "dtype": "float32",
    "averaging": "mean over all 12 layers and 12 heads",
    "run_date_utc": datetime.now(UTC).date().isoformat(),
    "libraries": {
        "python": platform.python_version(),
        **{package: version(package) for package in ("torch", "transformers", "tokenizers")},
        "numpy": np.__version__,
    },
    "query": " it",
    "sentences": {
        name: {key: value for key, value in run.items() if key != "arrays"}
        for name, run in runs.items()
    },
    "max_difference_up_to_it": difference,
    "head_shifts": shifts,
}
out = HERE / "results" / "attention.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nResults written to {out}")
