"""S2 E3, Search: keyword search, vector search, and a hybrid of the two.

Run from the repository root, after generate.py has built the corpus (it is committed):

    uv run python episodes/s2-e3-search/search.py --pilot
    uv run python episodes/s2-e3-search/search.py

Needs OPENAI_API_KEY for the embeddings, either in the repository's .env file or set in your
environment. Writes results/search.json (or results/pilot.json), which chart.py and the tests
read, so neither needs a key. See README.md in this folder.
"""

from dotenv import load_dotenv

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
def fuse(rankings, k=60):
    """Reciprocal rank fusion: each ranking gives a document
    1 / (k + rank), and the scores add up."""
    scores = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)

# Not on the slides. The experiment: rank every article for every question three ways, and
# record where the right article, and any look-alike, landed.
import argparse
import json
import random
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import tiktoken
from rank_bm25 import BM25Okapi

HERE = Path(__file__).parent
from lab.experiments import load_sibling

# Loaded by path, not by name: other episodes have modules with the same names.
measure = load_sibling(HERE / "measure.py")
plan = load_sibling(HERE / "plan.py")

store = load_sibling(HERE.parent / "s2-e2-chunking" / "store.py")
STORE = HERE.parents[1] / ".cache" / "embeddings" / "s2-e3-search.sqlite"
SAMPLE = 20


def keyword_ranking(bm25: BM25Okapi, ids: list[str], question: str) -> list[str]:
    scores = bm25.get_scores(plan.words(question))
    # Ties keep corpus order, so the ranking is the same on every run.
    order = sorted(range(len(ids)), key=lambda i: -scores[i])
    return [ids[i] for i in order]


def vector_ranking(article_vectors: np.ndarray, ids: list[str], question_vector) -> list[str]:
    unit = article_vectors / np.linalg.norm(article_vectors, axis=1, keepdims=True)
    scores = unit @ (question_vector / np.linalg.norm(question_vector))
    order = sorted(range(len(ids)), key=lambda i: -scores[i])
    return [ids[i] for i in order]


def score(question: dict, rankings: dict[str, list[str]], articles: dict, depth: int) -> dict:
    target = question["article_id"]
    full = {m: measure.rank_of(r, target) for m, r in rankings.items()}
    row = {
        "type": question["type"],
        "article_id": target,
        "question": question["question"],
        "ranks": {m: (r if r <= depth else None) for m, r in full.items()},
        "lookalike_ranks": {},
        "lookalike_above": {m: False for m in rankings},
    }
    if question["type"] == "identifier":
        group = articles[target]["group"]
        others = [a for a, art in articles.items() if art["group"] == group and a != target]
        row["lookalike_ranks"] = {
            m: {a: measure.rank_of(r, a) for a in others} for m, r in rankings.items()
        }
        row["lookalike_above"] = {
            m: min(row["lookalike_ranks"][m].values()) < full[m] for m in rankings
        }
    return row


def run(config: dict, folder: Path, client) -> dict:
    corpus = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))["questions"]
    articles = {a["article_id"]: a for a in corpus["articles"]}
    ids = list(articles)
    bm25 = BM25Okapi([plan.words(articles[a]["text"]) for a in ids])

    enc = tiktoken.get_encoding(config["tokeniser"])
    embed = store.Embedder(client, config["embedding_model"], store.EmbeddingStore(STORE),
                           lambda text: len(enc.encode(text)))
    article_vectors = embed([articles[a]["text"] for a in ids])
    question_vectors = embed([q["question"] for q in questions])

    rows = []
    for question, vector in zip(questions, question_vectors, strict=True):
        keyword = keyword_ranking(bm25, ids, question["question"])
        vector_ids = vector_ranking(article_vectors, ids, vector)
        rankings = {"keyword": keyword, "vector": vector_ids,
                    "hybrid": fuse([keyword, vector_ids], k=config["rrf_k"])}
        rows.append(score(question, rankings, articles, config["record_depth"]))

    return {
        "episode": "s2-e3-search",
        "embedding_model_requested": config["embedding_model"],
        "embedding_model_returned": embed.model_returned or config["embedding_model"],
        "generation_model_returned": corpus["generation_model_returned"],
        "tokeniser": config["tokeniser"],
        "bm25": {"package": "rank-bm25", "version": version("rank-bm25"),
                 "tokenisation": "lower-case, split on \\w+", "parameters": "defaults"},
        "rrf_k": config["rrf_k"],
        "top_k": config["top_k"],
        "record_depth": config["record_depth"],
        "run_date_utc": datetime.now(UTC).date().isoformat(),
        "seed": config["seed"],
        "articles": len(ids),
        "tokens_reported": {
            "generation": corpus["generation_usage"],
            "embedding": embed.tokens_reported,
        },
        "questions": rows,
    }


def print_sample(folder: Path, seed: int) -> None:
    """Questions beside their target articles, for reading by hand (S1 E9)."""
    corpus = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
    articles = {a["article_id"]: a for a in corpus["articles"]}
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))["questions"]
    rng = random.Random(seed)
    for kind in measure.TYPES:
        of_kind = [q for q in questions if q["type"] == kind]
        for q in rng.sample(of_kind, min(SAMPLE, len(of_kind))):
            article = articles[q["article_id"]]["text"]
            print(f"\n[{kind}] {q['question']}\n  -> {q['article_id']}: {article}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run S2 E3 search")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--sample", action="store_true", help="print questions for reading")
    args = parser.parse_args()
    config = plan.load_config()
    folder = HERE / "pilot" if args.pilot else HERE
    if args.sample:
        print_sample(folder, config["seed"])
        return

    from openai import OpenAI

    results = run(config, folder, OpenAI(max_retries=5))
    out = HERE / "results" / ("pilot.json" if args.pilot else "search.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                   newline="\n")
    for kind, cells in measure.table(results).items():
        line = "  ".join(
            f"{m} {c['recall_k']['hits']}/{c['recall_k']['n']}" for m, c in cells.items()
        )
        print(f"{kind:>11}  recall@{config['top_k']}: {line}")
    print(f"Embedding tokens reported this run: {results['tokens_reported']['embedding']}")
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
