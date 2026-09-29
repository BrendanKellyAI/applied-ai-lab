"""S2 E4, Swapping the embedding model: what changes, and what re-embedding costs in tokens.

Run from the repository root:

    uv run python field-notes/s2-e4-embedding-migration/migrate.py --estimate
    uv run python field-notes/s2-e4-embedding-migration/migrate.py --pilot
    uv run python field-notes/s2-e4-embedding-migration/migrate.py

--estimate needs no key and no network: it counts the tokens a full run will send. The pilot and
the full run need OPENAI_API_KEY, either in the repository's .env file or set in your
environment. The full run writes results/results.json, which chart.py and the tests read, so
neither needs a key. See README.md in this folder.
"""

from dotenv import load_dotenv

# Copies OPENAI_API_KEY from the .env file into the environment, if it is not already set.
load_dotenv()

# Everything below this line matches the slides.
import numpy as np


def top_k(query, index, k=5):
    """Rank stored vectors by cosine similarity to the query.
    Nothing here checks which model made either vector."""
    q = query / np.linalg.norm(query)
    m = index / np.linalg.norm(index, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return best, scores[best]

# Not on the slides. The experiment: every retrieval condition below ranks through top_k.
import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

import tiktoken
import yaml

from lab.experiments import load_sibling

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
measure = load_sibling(HERE / "measure.py")
CONFIG = HERE / "config.yaml"
RESULTS = HERE / "results"
CACHE = ROOT / ".cache" / "s2-e4-embedding-migration"
# Well inside the API's limits of 2,048 inputs and 300,000 tokens per request.
MAX_INPUTS = 2048
MAX_BATCH_TOKENS = 250_000


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_corpus(config: dict) -> tuple[list[dict], list[dict]]:
    corpus = json.loads((ROOT / config["corpus"]).read_text(encoding="utf-8"))
    questions = json.loads((ROOT / config["questions"]).read_text(encoding="utf-8"))
    return corpus["articles"], questions["questions"]


def today() -> str:
    return datetime.now(UTC).date().isoformat()


# Local token counts: the pre-spend count claim 4 tests ---------------------------------------


def encoder(config: dict):
    enc = tiktoken.get_encoding(config["tokeniser"])
    return lambda text: len(enc.encode(text))


def dimension_check_ids(ids: list[str], config: dict) -> list[str]:
    return sorted(random.Random(config["seed"]).sample(ids, config["dimension_check_articles"]))


def local_counts(config: dict, articles: list[dict], questions: list[dict]) -> dict:
    """Every article and question counted locally, and the full run itemised by call."""
    count = encoder(config)
    per_article = {a["article_id"]: count(a["text"]) for a in articles}
    per_question = [count(q["question"]) for q in questions]
    corpus = sum(per_article.values())
    asked = sum(per_question)
    check = sum(per_article[a] for a in dimension_check_ids(list(per_article), config))
    calls = {
        "old index, pass 1 (articles)": corpus,
        "old questions, pass 1": asked,
        "control, pass 2 (articles)": corpus,
        "control questions, pass 2": asked,
        "new model (articles)": corpus,
        "new questions": asked,
        "dimension check (5 articles)": check,
    }
    return {
        "tokeniser": config["tokeniser"],
        "route": config["route"],
        "articles": per_article,
        "questions": per_question,
        "corpus_tokens": corpus,
        "question_tokens": asked,
        "full_run_calls": calls,
        "full_run_total": sum(calls.values()),
    }


def estimate(config: dict) -> dict:
    articles, questions = load_corpus(config)
    return local_counts(config, articles, questions)


def print_estimate(counts: dict) -> None:
    print(f"Local token count, {counts['tokeniser']}, route {counts['route']}. No API call made.")
    print(f"  Corpus: {len(counts['articles'])} articles, {counts['corpus_tokens']:,} tokens")
    print(f"  Questions: {len(counts['questions'])}, {counts['question_tokens']:,} tokens")
    for name, tokens in counts["full_run_calls"].items():
        print(f"  {name:<32} {tokens:>8,}")
    print(f"  {'full run total':<32} {counts['full_run_total']:>8,}")


# Embedding, with every call recorded ---------------------------------------------------------


def batches(texts: list[str], count) -> list[list[str]]:
    """Texts grouped so no request passes the input or token limits."""
    groups: list[list[str]] = [[]]
    tokens = 0
    for text in texts:
        size = count(text)
        if groups[-1] and (len(groups[-1]) >= MAX_INPUTS or tokens + size > MAX_BATCH_TOKENS):
            groups.append([])
            tokens = 0
        groups[-1].append(text)
        tokens += size
    return [group for group in groups if group]


def embed(client, model: str, texts: list[str], count, dimensions: int | None = None):
    """One pass over `texts`: the vectors, and a record of every batch sent."""
    vectors, calls = [], []
    extra = {} if dimensions is None else {"dimensions": dimensions}
    for group in batches(texts, count):
        response = client.embeddings.create(model=model, input=group, **extra)
        got = np.array([item.embedding for item in response.data], dtype=np.float32)
        vectors.append(got)
        calls.append({
            "model_requested": model,
            "model_returned": response.model,
            "dimensions_requested": dimensions,
            "vector_length": int(got.shape[1]),
            "inputs": len(group),
            "prompt_tokens": response.usage.prompt_tokens,
            "local_tokens": sum(count(t) for t in group),
            "run_date_utc": today(),
        })
    return np.concatenate(vectors), calls


def cached_pass(name: str, client, model: str, texts: list[str], count,
                dimensions: int | None = None):
    """A named pass, saved to .cache/ so a rerun after a failure does not pay for it twice.

    Each pass has its own name, so the two old-model passes are two separate sets of calls.
    """
    vectors_path, calls_path = CACHE / f"{name}.npy", CACHE / f"{name}.json"
    if vectors_path.exists() and calls_path.exists():
        print(f"  {name}: loaded from {vectors_path.relative_to(ROOT)}")
        return np.load(vectors_path), json.loads(calls_path.read_text(encoding="utf-8"))
    vectors, calls = embed(client, model, texts, count, dimensions)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(vectors_path, vectors)
    calls_path.write_text(json.dumps(calls, indent=1) + "\n", encoding="utf-8")
    tokens = sum(c["prompt_tokens"] for c in calls)
    print(f"  {name}: {len(texts)} texts, {tokens:,} tokens, {calls[0]['model_returned']}")
    return vectors, calls


def dimension_check(api_short: np.ndarray, full: np.ndarray, config: dict) -> dict:
    """The API's own 1,536-dimension vectors against the locally shortened ones."""
    local = measure.shorten(full, config["short_dimensions"])
    cosines = measure.row_cosines(api_short, local)
    return {"cosines": [float(c) for c in cosines], "min_cosine": float(cosines.min()),
            "passed": bool(cosines.min() >= config["dimension_check_min_cosine"])}


# Retrieval: every condition goes through top_k -----------------------------------------------


def rank(queries: np.ndarray, index: np.ndarray, ids: list[str], answers: list[str],
         k: int) -> list[dict]:
    rows = []
    for query, answer in zip(queries, answers, strict=True):
        best, scores = top_k(query, index, k)
        top = [ids[i] for i in best]
        rows.append({"top": top, "scores": [float(s) for s in scores], "hit": answer in top})
    return rows


def all_scores(queries: np.ndarray, index: np.ndarray) -> np.ndarray:
    """Every article's score for every question, through top_k with k set to the whole index."""
    out = np.empty((len(queries), len(index)))
    for row, query in enumerate(queries):
        best, scores = top_k(query, index, len(index))
        out[row, best] = scores
    return out


def loud_failure() -> str:
    """Claim 2b: a 3,072-dimension query against a 1,536-dimension index. Returns the type of
    the exception NumPy raises."""
    try:
        top_k(np.ones(3072), np.ones((3, 1536)))
    except Exception as error:  # noqa: BLE001 - the type is what is being recorded
        return f"{type(error).__module__}.{type(error).__name__}"
    raise AssertionError("A shape mismatch was expected to raise")


def cross_condition(queries, index, ids, answers, k) -> tuple[list[dict], bool]:
    """Claim 2a: new-model queries on the old index. Records whether anything raised."""
    try:
        return rank(queries, index, ids, answers, k), False
    except Exception:  # noqa: BLE001 - any error at all means the failure was not silent
        return [], True


# The analysis, from vectors alone ------------------------------------------------------------


def median_top1(rows: list[dict]) -> float:
    return float(np.median([r["scores"][0] for r in rows]))


def split_recall(rows: list[dict], questions: list[dict], migrated: set[str]) -> dict:
    """Recall for answers in the migrated half and in the old half, overall and by type."""
    out = {}
    for half, inside in (("migrated", True), ("old", False)):
        keep = [i for i, q in enumerate(questions) if (q["article_id"] in migrated) is inside]
        out[half] = measure.recall_by_type([questions[i]["type"] for i in keep],
                                           [rows[i]["hit"] for i in keep])
    return out


def claim3_measures(vectors: dict, answers: list[int], config: dict) -> dict:
    old = all_scores(vectors["old_q"], vectors["old_a"])
    new = all_scores(vectors["new_q"], vectors["new_a"])
    rows = np.arange(len(answers))
    p = config["threshold_percentile"]
    t = measure.threshold(old[rows, answers], p)
    t_new = measure.threshold(new[rows, answers], p)
    return {
        "percentile": p,
        "old": measure.keep_and_wrong(old, answers, t),
        "new_same_t": measure.keep_and_wrong(new, answers, t),
        "new_retuned": measure.keep_and_wrong(new, answers, t_new),
        "right_scores": {"old": old[rows, answers].tolist(), "new": new[rows, answers].tolist()},
    }


def conditions(vectors: dict, ids: list[str], answers: list[str], half: np.ndarray,
               k: int) -> dict:
    short_q = vectors["new_short_q"]
    cross, raised = cross_condition(short_q, vectors["old_a"], ids, answers, k)
    return {
        "old": rank(vectors["old_q"], vectors["old_a"], ids, answers, k),
        "control": rank(vectors["control_q"], vectors["control_a"], ids, answers, k),
        "new": rank(vectors["new_q"], vectors["new_a"], ids, answers, k),
        "new_short": rank(short_q, vectors["new_short_a"], ids, answers, k),
        "cross": cross,
        "half_new_queries": rank(short_q, half, ids, answers, k),
        "half_old_queries": rank(vectors["old_q"], half, ids, answers, k),
    }, raised


def analyse(config: dict, articles: list[dict], questions: list[dict], vectors: dict,
            migrated: list[str]) -> dict:
    """Every measure and verdict, from the vectors alone. `vectors` holds old_a, old_q,
    control_a, control_q, new_a and new_q; the shortened ones are made here."""
    k, marks = config["top_k"], config["pass_marks"]
    ids = [a["article_id"] for a in articles]
    answers = [q["article_id"] for q in questions]
    types = [q["type"] for q in questions]
    vectors = {**vectors,
               "new_short_a": measure.shorten(vectors["new_a"], config["short_dimensions"]),
               "new_short_q": measure.shorten(vectors["new_q"], config["short_dimensions"])}
    moved = set(migrated)
    mask = np.array([a in moved for a in ids])[:, None]
    half = np.where(mask, vectors["new_short_a"], vectors["old_a"])
    runs, raised = conditions(vectors, ids, answers, half, k)

    recall = {name: measure.recall_by_type(types, [r["hit"] for r in rows])
              for name, rows in runs.items() if rows}
    swap = pair(runs["old"], runs["new"], k)
    ctrl = pair(runs["old"], runs["control"], k)
    splits = {name: split_recall(runs[name], questions, moved)
              for name in ("half_new_queries", "half_old_queries", "new_short")}
    t = claim3_measures(vectors, [ids.index(a) for a in answers], config)
    floor = measure.random_floor(k, len(ids), len(questions))
    headline = splits["half_new_queries"]
    verdicts = {
        "claim1": measure.claim1(swap["mean_overlap"], len(swap["losses"]), marks),
        "claim2a": measure.claim2a(recall.get("cross", {}).get("all", {}).get("hits", 0),
                                   raised, marks),
        "claim2c": measure.claim2c(headline["old"]["all"]["rate"],
                                   headline["migrated"]["all"]["rate"],
                                   splits["new_short"]["migrated"]["all"]["rate"], marks),
        "claim3": measure.claim3(t["old"]["K"], t["new_same_t"]["K"], t["old"]["W"],
                                 t["new_same_t"]["W"], marks),
        "control": measure.control(ctrl["mean_overlap"], ctrl["flips"], marks),
    }
    return {
        "conditions": runs,
        "recall": recall,
        "swap": swap,
        "control": {**ctrl, "median_article_cosine": float(np.median(
            measure.row_cosines(vectors["old_a"], vectors["control_a"]))),
            "median_question_cosine": float(np.median(
                measure.row_cosines(vectors["old_q"], vectors["control_q"])))},
        "half_migrated": {"splits": splits, "split_by_type": measure.split_report(
            questions, migrated)},
        "median_top1": {name: median_top1(rows) for name, rows in runs.items() if rows},
        "claim3": t,
        "random_floor": {"hits": floor, "n": len(questions), "rate": floor / len(questions)},
        "claim2b_exception": loud_failure(),
        "claim2a_raised": raised,
        "verdicts": verdicts,
    }


def pair(first: list[dict], second: list[dict], k: int) -> dict:
    """Overlap, losses and gains, going from the first condition to the second."""
    return measure.compare([r["top"] for r in first], [r["top"] for r in second],
                           [r["hit"] for r in first], [r["hit"] for r in second], k)


# Results -------------------------------------------------------------------------------------


def pipeline_check(config: dict, old_hits: int) -> dict:
    """Old-model recall at 5 against the vector result S2 E3 committed."""
    e3 = json.loads((ROOT / config["e3_results"]).read_text(encoding="utf-8"))
    e3_measure = load_sibling(ROOT / "episodes" / "s2-e3-search" / "measure.py")
    committed = e3_measure.table(e3)["all"]["vector"]["recall_k"]
    return {"e3_hits": committed["hits"], "e3_n": committed["n"], "e4_hits": old_hits,
            "difference": old_hits - committed["hits"], "e3_run_date": e3["run_date_utc"]}


def token_summary(config: dict, calls: dict, counts: dict) -> dict:
    """Claim 4: API tokens for each pass against the local count, and index sizes."""
    reported = {name: sum(c["prompt_tokens"] for c in batch) for name, batch in calls.items()}
    corpus = counts["corpus_tokens"]
    gaps = {model: (reported[name] - corpus) / corpus * 100
            for model, name in (("old", "old-1-articles"), ("new", "new-articles"))}
    n = len(counts["articles"])
    same = (reported["old-1-articles"] == reported["new-articles"]
            and reported["old-1-questions"] == reported["new-questions"])
    return {
        "local": {"corpus_tokens": corpus, "question_tokens": counts["question_tokens"],
                  "full_run_calls": counts["full_run_calls"],
                  "full_run_total": counts["full_run_total"]},
        "reported_by_pass": reported,
        "reported_total": sum(reported.values()),
        "batches": calls,
        "corpus_gap_percent": gaps,
        "small_and_large_identical": same,
        "question_share_of_corpus": counts["question_tokens"] / corpus,
        "index_bytes": {
            "old (1,536)": measure.index_bytes(n, config["old_dimensions"]),
            "new (3,072)": measure.index_bytes(n, config["new_dimensions"]),
            "new shortened (1,536)": measure.index_bytes(n, config["short_dimensions"]),
        },
    }


def model_metadata(calls: dict) -> dict:
    """For every pass: the model requested and returned, the vector length, and the date."""
    return {name: [dict(zip(("model_requested", "model_returned", "vector_length",
                             "run_date_utc"), row, strict=True))
                   for row in sorted({(c["model_requested"], c["model_returned"],
                                       c["vector_length"], c["run_date_utc"]) for c in batch})]
            for name, batch in calls.items()}


# The full run --------------------------------------------------------------------------------

# Each pass is named, so the two old-model passes are two separate sets of calls.
PASSES = {
    "old-1-articles": ("old_model", "articles"),
    "old-1-questions": ("old_model", "questions"),
    "old-2-articles": ("old_model", "articles"),
    "old-2-questions": ("old_model", "questions"),
    "new-questions": ("new_model", "questions"),
}


def run(config: dict, client) -> dict:
    articles, questions = load_corpus(config)
    counts = write_offline_files(config, articles, questions)
    count = encoder(config)
    texts = {"articles": [a["text"] for a in articles],
             "questions": [q["question"] for q in questions]}
    ids = [a["article_id"] for a in articles]

    # The new model first, so the dimension check can stop the run before the rest is spent.
    vectors, calls = {}, {}
    vectors["new-articles"], calls["new-articles"] = cached_pass(
        "new-articles", client, config["new_model"], texts["articles"], count)
    check_ids = dimension_check_ids(ids, config)
    rows = [ids.index(a) for a in check_ids]
    short, calls["dimension-check"] = cached_pass(
        "dimension-check", client, config["new_model"], [texts["articles"][i] for i in rows],
        count, config["short_dimensions"])
    check = {"article_ids": check_ids,
             **dimension_check(short, vectors["new-articles"][rows], config)}
    if not check["passed"]:
        print(f"Dimension check FAILED: lowest cosine {check['min_cosine']:.6f}. Stopping.")
        sys.exit(1)
    for name, (model, kind) in PASSES.items():
        vectors[name], calls[name] = cached_pass(name, client, config[model], texts[kind], count)

    migrated = json.loads((RESULTS / "migrated_articles.json").read_text(encoding="utf-8"))
    named = {"old_a": vectors["old-1-articles"], "old_q": vectors["old-1-questions"],
             "control_a": vectors["old-2-articles"], "control_q": vectors["old-2-questions"],
             "new_a": vectors["new-articles"], "new_q": vectors["new-questions"]}
    out = analyse(config, articles, questions, named, migrated["article_ids"])
    tokens = token_summary(config, calls, counts)
    out["verdicts"]["claim4"] = measure.claim4(tokens["corpus_gap_percent"], config["pass_marks"])
    kept = {name: named[name] for name in config["committed_vectors"]}
    vector_bytes = sum(v.nbytes for v in kept.values()) + short.nbytes
    committed = vector_bytes <= config["max_vector_bytes"]
    if committed:
        np.savez(RESULTS / "vectors.npz", **kept, dimension_check=short,
                 article_ids=np.array(ids), dimension_check_ids=np.array(check_ids))
    return {
        "field_note": "s2-e4-embedding-migration",
        "route": config["route"],
        "seed": config["seed"],
        "run_date_utc": today(),
        "top_k": config["top_k"],
        "articles": len(articles),
        "questions": len(questions),
        "question_types": [q["type"] for q in questions],
        "answers": [q["article_id"] for q in questions],
        "models": model_metadata(calls),
        "pass_marks": config["pass_marks"],
        "migrated_article_ids": migrated["article_ids"],
        "tokens": tokens,
        "vectors": {"bytes": vector_bytes, "committed": committed,
                    "arrays": [*kept, "dimension_check"] if committed else []},
        "dimension_check": check,
        "pipeline_check": pipeline_check(config, out["recall"]["old"]["all"]["hits"]),
        **out,
    }


def write_offline_files(config: dict, articles: list[dict], questions: list[dict]) -> dict:
    """The local token counts and the migrated split: both fixed before any API call."""
    counts = local_counts(config, articles, questions)
    migrated = measure.migrated_split(articles, questions, config["seed"])
    RESULTS.mkdir(exist_ok=True)
    _write(RESULTS / "local_token_counts.json", counts)
    _write(RESULTS / "migrated_articles.json", {
        "seed": config["seed"], "article_ids": migrated,
        "answers_by_type": measure.split_report(questions, migrated)})
    return counts


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                    newline="\n")


# The pilot -----------------------------------------------------------------------------------


def pilot(config: dict, client) -> dict:
    """A small slice of both models and the dimension check. Writes only to .cache/."""
    articles, questions = load_corpus(config)
    count = encoder(config)
    p = config["pilot"]
    chosen, picked = measure.pilot_selection(articles, questions, config["seed"],
                                             p["questions_per_type"], p["other_articles"])
    by_id = {a["article_id"]: a for a in articles}
    texts = [by_id[a]["text"] for a in chosen]
    asked = [questions[i] for i in picked]
    q_texts = [q["question"] for q in asked]

    calls, vectors = {}, {}
    for side in ("old", "new"):
        model = config[f"{side}_model"]
        vectors[f"{side}_a"], calls[f"{side}-articles"] = cached_pass(
            f"pilot-{side}-articles", client, model, texts, count)
        vectors[f"{side}_q"], calls[f"{side}-questions"] = cached_pass(
            f"pilot-{side}-questions", client, model, q_texts, count)
    check_ids = dimension_check_ids(chosen, config)
    rows = [chosen.index(a) for a in check_ids]
    short, calls["dimension-check"] = cached_pass(
        "pilot-dimension-check", client, config["new_model"], [texts[i] for i in rows], count,
        config["short_dimensions"])
    check = {"article_ids": check_ids, **dimension_check(short, vectors["new_a"][rows], config)}
    report = pilot_report(config, chosen, asked, calls, vectors, check,
                          local_counts(config, articles, questions))
    CACHE.mkdir(parents=True, exist_ok=True)
    _write(CACHE / "pilot-report.json", report)
    return report


def _ratio_for(call: str) -> str:
    return "new" if call.startswith(("new", "dimension")) else "old"


def pilot_report(config: dict, chosen: list[str], asked: list[dict], calls: dict,
                 vectors: dict, check: dict, counts: dict) -> dict:
    measured = {}
    for side in ("old", "new"):
        batch = calls[f"{side}-articles"] + calls[f"{side}-questions"]
        api = sum(c["prompt_tokens"] for c in batch)
        local = sum(c["local_tokens"] for c in batch)
        measured[side] = {"model_returned": batch[0]["model_returned"],
                          "vector_length": batch[0]["vector_length"],
                          "api_tokens": api, "local_tokens": local, "ratio": api / local}
    projection = {name: round(tokens * measured[_ratio_for(name)]["ratio"])
                  for name, tokens in counts["full_run_calls"].items()}
    answers = [q["article_id"] for q in asked]
    k = config["top_k"]
    short_q = measure.shorten(vectors["new_q"], config["short_dimensions"])
    pairs = {"old": (vectors["old_q"], vectors["old_a"]),
             "new": (vectors["new_q"], vectors["new_a"]),
             "cross": (short_q, vectors["old_a"])}
    recall = {name: sum(r["hit"] for r in rank(q, a, chosen, answers, k))
              for name, (q, a) in pairs.items()}
    return {
        "route": config["route"],
        "articles": chosen,
        "questions": [q["question"] for q in asked],
        "measured": measured,
        "calls": calls,
        "dimension_check": check,
        "full_corpus_local_tokens": counts["corpus_tokens"],
        "all_questions_local_tokens": counts["question_tokens"],
        "full_run_local": counts["full_run_calls"],
        "full_run_projected": projection,
        "full_run_projected_total": sum(projection.values()),
        "pilot_recall_at_5": {**recall, "n": len(asked), "articles": len(chosen)},
    }


def print_pilot(report: dict) -> None:
    print(f"\nRoute {report['route']}.")
    for side, m in report["measured"].items():
        print(f"  {side}: {m['model_returned']}, length {m['vector_length']}, API "
              f"{m['api_tokens']:,} tokens against {m['local_tokens']:,} local")
    check = report["dimension_check"]
    print(f"  Dimension check: lowest cosine {check['min_cosine']:.6f}, "
          f"{'passed' if check['passed'] else 'FAILED'}")
    r = report["pilot_recall_at_5"]
    print(f"  Pilot recall at 5 over {r['articles']} articles: old {r['old']} of {r['n']}, "
          f"new {r['new']} of {r['n']}, cross {r['cross']} of {r['n']}")
    print(f"  Local: corpus {report['full_corpus_local_tokens']:,} tokens, questions "
          f"{report['all_questions_local_tokens']:,}")
    for name, tokens in report["full_run_projected"].items():
        print(f"  projected {name:<32} {tokens:>8,}")
    print(f"  projected full run total {report['full_run_projected_total']:>21,}")
    print(f"Report written to {(CACHE / 'pilot-report.json').relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--estimate", action="store_true", help="count tokens; no key, no network")
    mode.add_argument("--pilot", action="store_true", help="12 questions, 20 articles, then stop")
    args = parser.parse_args()
    config = load_config()
    if args.estimate:
        articles, questions = load_corpus(config)
        print_estimate(write_offline_files(config, articles, questions))
        return

    from openai import OpenAI

    client = OpenAI(max_retries=5)
    if args.pilot:
        print_pilot(pilot(config, client))
        return
    results = run(config, client)
    _write(RESULTS / "results.json", results)
    for claim, v in results["verdicts"].items():
        print(f"  {claim}: {v['verdict']}")
    print(f"Results written to {(RESULTS / 'results.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
