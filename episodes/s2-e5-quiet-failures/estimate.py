"""--estimate: every prompt the full run would send, counted locally. No key, no network.

Prompts that depend on an earlier reply are built with a stand-in of the same shape: a sentence
taken from the article for a value fact, an S2 E3 question for a generated question, the source
article for an internal note, and the target article plus seeded others for the passages a search
would return. Prompts that repeat an earlier one exactly are counted once, because the cache
answers them. Output tokens are the assumed figures in config.yaml; the pilot measures them.
"""

import math
import random
import re
from pathlib import Path

import tiktoken

from lab.experiments import load_sibling

HERE = Path(__file__).parent
library = load_sibling(HERE / "library.py")
build = load_sibling(HERE / "build.py")
STAND_IN_VALUE = "15 minutes"
STAND_IN_DATE = "2025-03-01"
NL = "\n"


def stand_in_sentence(text: str) -> str:
    parts = [p for p in library.SENTENCE.split(text) if p.strip()]
    return next((p for p in parts if re.search(r"\d", p)), parts[0])


def passages(articles: list[dict], target: int, rng: random.Random, n: int) -> list[dict]:
    others = rng.sample([i for i in range(len(articles)) if i != target], n - 1)
    return [{"text": articles[i]["text"], "date": STAND_IN_DATE} for i in [target, *others]]


def with_article(prompt: str, text: str, label: str = "Article") -> str:
    return f"{prompt}{NL}{label}:{NL}{text}"


def data_build(config: dict, articles: list[dict], questions: list[dict], products: list[str],
               sizes: dict, rng: random.Random) -> tuple[list, list]:
    """Section 4's prompts, and the questions it embeds, as (text, weight) pairs. A step that a
    code check can send back is weighted by the assumed attempts per step."""
    p, tries = config["prompts"], config["estimate"]["attempts_per_step"]
    order = list(range(len(articles)))
    random.Random(config["seed"]).shuffle(order)
    candidates = order[: math.ceil(sizes["values"] / config["estimate"]["value_pass_rate"])]
    stand_q = [q["question"] for q in questions if q["type"] == "paraphrase"]
    by_id = {a["article_id"]: a["text"] for a in articles}
    ids = [a["article_id"] for a in articles]
    out, embeds = [], []

    value_tries = config["estimate"]["value_fact_attempts"]
    out += [(with_article(p["value_fact"], articles[i]["text"]), value_tries) for i in candidates]
    for i in candidates[: sizes["values"]]:
        text = articles[i]["text"]
        replacement = (f"{p['replacement']}{NL}Sentence: {stand_in_sentence(text)}{NL}"
                       f"Value: {STAND_IN_VALUE}")
        out += [(replacement, tries),
                (with_article(p["value_question"].format(value=STAND_IN_VALUE), text), tries)]
    for category in config["absent_categories"][: sizes["absent_product"]]:
        prompt = p["absent_product"].format(products=", ".join(products), category=category)
        out.append((prompt, tries))
    for a in build.detail_articles(config, articles)[: sizes["absent_detail"]]:
        top = passages(articles, ids.index(a["article_id"]), rng, config["detail_check_depth"])
        judge = (f"{p['detail_judge']}{NL}Question: {stand_q[0]}{NL}{NL}"
                 f"{library.passages_block(top)}")
        out += [(with_article(p["absent_detail"], a["text"]), tries), (judge, tries)]
        embeds.append((stand_q[0], tries))
    sources = build.note_sources(config, questions, config["notes_per_type"])[: sizes["notes"]]
    for n, src in enumerate(sources):
        kind = config["note_kinds"][n % len(config["note_kinds"])]
        note = by_id[src["article_id"]]
        out += [(with_article(p["internal_note"].format(kind=kind), note), tries),
                (with_article(p["note_question"], note, "Note"), 1)]
    embeds += [(t, 1) for t in [articles[i]["text"] for i in candidates[: sizes["values"]]]
               + [by_id[src["article_id"]] for src in sources]]
    return out, embeds


def answers_and_judging(config: dict, articles: list[dict], questions: list[dict], sizes: dict,
                        rng: random.Random) -> tuple[list, list, list]:
    """Section 5's prompts, and the questions it embeds."""
    p, k = config["prompts"], config["top_k"]
    stand_q = [q["question"] for q in questions if q["type"] == "paraphrase"]
    order = list(range(len(articles)))
    random.Random(config["seed"]).shuffle(order)
    answering, judging, embeds = [], [], []
    for n, i in enumerate(order[: sizes["values"]]):
        question = stand_q[n % len(stand_q)]
        top = passages(articles, i, rng, k)
        # Test A fresh and stale; B plain and dated; C P2. B-latest and C P1 on answerable
        # questions repeat Test A fresh exactly, so the cache answers them.
        answering += [(library.answer_prompt(config, question, top), 3),
                      (library.answer_prompt(config, question, top, dated=True), 1),
                      (library.answer_prompt(config, question, top, not_found=True), 1)]
        embeds.append((question, 1))
    for n in range(sizes["absent_product"] + sizes["absent_detail"]):
        question = stand_q[-1 - n % len(stand_q)]
        top = passages(articles, rng.randrange(len(articles)), rng, k)
        answering += [(library.answer_prompt(config, question, top), 1),
                      (library.answer_prompt(config, question, top, not_found=True), 1)]
        reply = articles[n]["text"][:400]
        # Judged under P1, and under P2 unless the reply is NOT_FOUND: counted as judged twice.
        judging.append((f"{p['answer_judge']}{NL}Question: {question}{NL}{NL}Reply: {reply}", 2))
        embeds.append((question, 1))
    embeds += [(q["question"], 1) for q in questions]
    embeds += [(stand_q[n % len(stand_q)], 1) for n in range(sizes["notes"])]
    return answering, judging, embeds


def prompts_by_stage(config: dict, articles: list[dict], questions: list[dict],
                     products: list[str], sizes: dict) -> dict:
    """Every chat prompt and every text to embed, by stage, as (text, weight) pairs."""
    rng = random.Random(config["seed"])
    data, data_embeds = data_build(config, articles, questions, products, sizes, rng)
    answering, judging, run_embeds = answers_and_judging(config, articles, questions, sizes, rng)
    library_texts = [(a["text"], 1) for a in articles]
    return {"data build": data, "embeddings": library_texts + data_embeds + run_embeds,
            "answering": answering, "judging": judging}


def estimate(config: dict, articles: list[dict], questions: list[dict], products: list[str],
             sizes: dict) -> dict:
    encoders = {"chat": tiktoken.get_encoding(config["chat_tokeniser"]),
                "embeddings": tiktoken.get_encoding(config["embedding_tokeniser"])}
    found = prompts_by_stage(config, articles, questions, products, sizes)
    out_per_call = config["estimate"]["output_tokens"]
    stages = {}
    for stage, pairs in found.items():
        enc = encoders["embeddings" if stage == "embeddings" else "chat"]
        calls = sum(w for _, w in pairs)
        stages[stage] = {
            "calls": round(calls),
            "input_tokens": round(sum(len(enc.encode(t)) * w for t, w in pairs)),
            "output_tokens": 0 if stage == "embeddings" else round(calls * out_per_call[stage]),
        }
    total = {name: sum(st[name] for st in stages.values())
             for name in ("calls", "input_tokens", "output_tokens")}
    return {"sizes": sizes, "stages": stages, "total": total,
            "tokenisers": {"chat": config["chat_tokeniser"],
                           "embeddings": config["embedding_tokeniser"]},
            "assumptions": config["estimate"]}


def print_estimate(result: dict, model: str, embedding_model: str) -> None:
    print(f"Token estimate, no API call made. Chat model {model} "
          f"({result['tokenisers']['chat']}); embeddings {embedding_model} "
          f"({result['tokenisers']['embeddings']}). Sizes: {result['sizes']}")
    print(f"  {'stage':<12} {'calls/texts':>11} {'input':>10} {'output':>10}")
    for stage, row in result["stages"].items():
        print(f"  {stage:<12} {row['calls']:>11,} {row['input_tokens']:>10,} "
              f"{row['output_tokens']:>10,}")
    t = result["total"]
    print(f"  {'total':<12} {t['calls']:>11,} {t['input_tokens']:>10,} {t['output_tokens']:>10,}")
