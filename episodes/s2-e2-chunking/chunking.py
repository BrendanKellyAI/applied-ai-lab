"""S2 E2, Chunking: how a document is cut into chunks decides what search can find.

Run from the repository root:

    uv run python episodes/s2-e2-chunking/chunking.py --pilot
    uv run python episodes/s2-e2-chunking/chunking.py

Needs OPENAI_API_KEY, either in the repository's .env file or set in your environment.
Writes results/chunking.json (or results/pilot.json), which chart.py and the tests read, so
neither needs a key. Embeddings are cached in .cache/, so a rerun pays only for new text.
See README.md in this folder.
"""

from dotenv import load_dotenv

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def chunk(text, size, overlap=0):
    """Cut text into windows of `size` tokens, each starting
    `size - overlap` tokens after the one before."""
    tokens = enc.encode(text)
    step = size - overlap
    chunks = []
    for start in range(0, len(tokens), step):
        chunks.append(enc.decode(tokens[start:start + size]))
        if start + size >= len(tokens):
            break
    return chunks

# Not on the slides. The experiment: every size and overlap, every question, one ranking over
# the chunks of all six novels at once.
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).parent
from lab.experiments import load_sibling

# Loaded by path, not by name: other episodes have modules with the same names.
corpus = load_sibling(HERE / "corpus.py")
fact_module = load_sibling(HERE / "facts.py")
measure = load_sibling(HERE / "measure.py")
store = load_sibling(HERE / "store.py")

STORE = HERE.parents[1] / ".cache" / "embeddings" / "s2-e2-chunking.sqlite"


def run(config: dict, *, pilot: bool, client) -> dict:
    facts = fact_module.load()
    plan = config["pilot"] if pilot else config
    only = plan["novel_index"] if pilot else None
    novels = corpus.build(config, facts, only=only)
    kinds = set(plan.get("kinds", ["one", "two"]))
    asked = [f for f in facts if f.kind in kinds and (only is None or f.novel_index == only)]

    embedder = store.Embedder(
        client, config["model"], store.EmbeddingStore(STORE), lambda t: len(enc.encode(t))
    )
    question_vectors = embedder([fact.question for fact in asked])
    fact_vectors = embedder([fact.text for fact in asked])
    ceilings = [
        float(v) for v in (measure.unit(question_vectors) * measure.unit(fact_vectors)).sum(1)
    ]

    conditions = []
    for size in plan["chunk_sizes"]:
        for fraction in plan["overlap_fractions"]:
            overlap = int(size * fraction)
            chunks = [piece for novel in novels for piece in chunk(novel.text, size, overlap)]
            answers = [measure.holders(chunks, fact.sentences) for fact in asked]
            rows = measure.score_condition(
                question_vectors,
                embedder(chunks),
                answers,
                ceilings,
                floor_sample=config["floor_sample"],
                seed=config["seed"] + size * 10 + overlap,
            )
            for fact, row in zip(asked, rows, strict=True):
                row.update(fact_id=fact.fact_id, kind=fact.kind, novel_index=fact.novel_index)
            conditions.append(
                {
                    "chunk_size": size,
                    "overlap_fraction": fraction,
                    "overlap_tokens": overlap,
                    "chunks": len(chunks),
                    "chunk_tokens": sum(len(enc.encode(piece)) for piece in chunks),
                    "questions": rows,
                }
            )
            one = measure.recall(measure.rows_for(conditions[-1], "one"), config["top_k"])
            print(f"size {size:>5}  overlap {overlap:>4}  chunks {len(chunks):>5}  "
                  f"one-sentence recall@{config['top_k']} {one['hits']}/{one['n']}")

    return {
        "episode": "s2-e2-chunking",
        "pilot": pilot,
        "model_requested": config["model"],
        "model_returned": embedder.model_returned or config["model"],
        "tokeniser": config["tokeniser"],
        "run_date_utc": datetime.now(UTC).date().isoformat(),
        "seed": config["seed"],
        "top_k": config["top_k"],
        "floor_sample": config["floor_sample"],
        "chunk_sizes": plan["chunk_sizes"],
        "overlap_fractions": plan["overlap_fractions"],
        "embedding_tokens_reported": embedder.tokens_reported,
        "novels": [
            {"index": n.index, "book_id": n.book_id, "title": n.title, "tokens": n.excerpt_tokens}
            for n in novels
        ],
        "facts": {kind: sum(1 for f in asked if f.kind == kind) for kind in ("one", "two")},
        "conditions": conditions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pilot", action="store_true", help="one novel, two sizes, then stop")
    args = parser.parse_args()

    from openai import OpenAI

    results = run(fact_module.load_config(), pilot=args.pilot, client=OpenAI())
    out = HERE / "results" / ("pilot.json" if args.pilot else "chunking.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print(f"Embedding tokens reported by the API this run: {results['embedding_tokens_reported']}")
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
