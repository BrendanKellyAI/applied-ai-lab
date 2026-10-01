"""Builds the S2 E5 data with the chat model, and checks every item in code (section 4).

Value facts and their revisions, unanswerable questions, and internal notes. Each step that a
code check rejects is asked again with the rejected reply and the reason, up to max_attempts.
Candidates are generated in parallel but accepted in their seeded order, so the pilot's items are
the first items of the full run, and the full run reuses the pilot's cached calls.
"""

import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lab.experiments import load_sibling

HERE = Path(__file__).parent
chatlib = load_sibling(HERE / "chat.py")
library = load_sibling(HERE / "library.py")
search_module = load_sibling(HERE / "search.py")
WORKERS = 8


class BuildError(RuntimeError):
    """Too few items passed their checks."""


def ask(chat, config: dict, prompt: str, check) -> tuple[object | None, list[dict]]:
    """Ask until `check(reply)` returns (value, None), up to max_attempts. Returns the value, or
    None, and every rejected reply with its reason."""
    rejected: list[dict] = []
    for _ in range(config["max_attempts"]):
        prompt_now = chatlib.with_retry(prompt, rejected, config["prompts"]["retry"])
        reply = chat(prompt_now, "data build")
        value, problem = check(reply)
        if problem is None:
            return value, rejected
        rejected.append({"reply": reply, "problem": problem})
    return None, rejected


def in_order(items: list, make, accept, count: int) -> tuple[list, list]:
    """Run `make` over items in parallel batches, and `accept` each result in order, until
    `count` are accepted. Returns the accepted items and the rejections."""
    kept, dropped = [], []
    with ThreadPoolExecutor(WORKERS) as pool:
        for start in range(0, len(items), WORKERS):
            for item, made in zip(items[start:start + WORKERS],
                                  pool.map(make, items[start:start + WORKERS])):
                problem = made.get("problem") or accept(made, kept)
                if problem is None:
                    kept.append(made)
                    if len(kept) == count:
                        return kept, dropped
                else:
                    dropped.append({"item": item.get("article_id", item), "problem": problem,
                                    "rejected": made.get("rejected", [])})
    return kept, dropped


# 4.1 Value facts ----------------------------------------------------------------------------


def value_candidate(chat, config: dict, texts: list[str], article: dict) -> dict:
    """One article through the value-fact steps. Checks against the original library only; the
    checks between items run in accept_value."""
    prompts, text, aid = config["prompts"], article["text"], article["article_id"]

    def check_value(r: str):
        found = chatlib.parse_json(r) or {}
        pair = (str(found.get("sentence", "")), str(found.get("value", "")))
        return pair, library.value_problem(texts, text, *pair)

    # Asked again with the reason when the value is not unique, so an article whose preferred
    # measurement repeats elsewhere can still offer a unique value.
    picked, tried = ask(chat, config, f"{prompts['value_fact']}\nArticle:\n{text}", check_value)
    if picked is None:
        return {"article_id": aid, "problem": "value: no unique value", "rejected": tried}
    sentence, old = picked

    def check_new(r: str):
        return r.strip(), library.replacement_problem(texts, old, r)

    new, rejected = ask(chat, config, f"{prompts['replacement']}\nSentence: {sentence}\n"
                        f"Value: {old}", check_new)
    rejected = tried + rejected
    if new is None:
        return {"article_id": aid, "problem": "no valid replacement", "rejected": rejected}
    try:
        revised = library.revise(text, sentence, old, new)
    except AssertionError as error:
        return {"article_id": aid, "problem": f"revision: {error}"}

    def check_question(r: str):
        return r.strip(), library.question_problem(r, old, new)

    question, asked = ask(chat, config, prompts["value_question"].format(value=old)
                          + f"\nArticle:\n{text}", check_question)
    if question is None:
        return {"article_id": aid, "problem": "no valid question", "rejected": asked}
    return {"article_id": aid, "old": old, "new": new, "question": question,
            "sentence": sentence, "revised_sentence": sentence.replace(old, new, 1),
            "revised": revised, "rejected": rejected + asked}


def accept_value(made: dict, kept: list[dict]) -> str | None:
    """Checks between items: no value may contain, or be contained in, another item's value."""
    for other in kept:
        for mine in (made["old"], made["new"]):
            for theirs in (other["old"], other["new"]):
                if mine in theirs or theirs in mine:
                    return f'"{mine}" overlaps {other["article_id"]}\'s "{theirs}"'
    return None


def build_values(chat, config: dict, articles: list[dict], count: int) -> tuple[list, list]:
    texts = [a["text"] for a in articles]
    order = list(articles)
    random.Random(config["seed"]).shuffle(order)
    kept, dropped = in_order(order, lambda a: value_candidate(chat, config, texts, a),
                             accept_value, count)
    if len(kept) < count:
        raise BuildError(f"Only {len(kept)} of {len(articles)} articles gave a value fact; "
                         f"{count} are needed.")
    return kept, dropped


# 4.2 Unanswerable questions -----------------------------------------------------------------


def absent_product(chat, config: dict, texts: list[str], products: list[str], category: str,
                   number: int) -> dict:
    prompt = config["prompts"]["absent_product"].format(products=", ".join(products),
                                                         category=category)

    def check(reply: str):
        found = chatlib.parse_json(reply) or {}
        q, product = str(found.get("question", "")), str(found.get("product", ""))
        return {"question": q, "product": product}, library.product_problem(texts, q, product)

    made, rejected = ask(chat, config, prompt, check)
    if made is None:
        return {"problem": "no absent product passed", "rejected": rejected}
    return {"id": f"U{number:03d}", "kind": "absent-product", "category": category, **made,
            "note": f'"{made["product"]}" appears nowhere in the library (case-insensitive)',
            "rejected": rejected}


def absent_detail(chat, config: dict, embed, index: dict, article: dict, number: int) -> dict:
    """A question on the article's topic, kept only if the judge finds no answer in the top 10
    passages retrieved for it nor in the article itself."""
    prompts, depth = config["prompts"], config["detail_check_depth"]
    source = next(e for e in index["entries"] if e["article_id"] == article["article_id"])

    def check(reply: str):
        question = reply.strip()
        if not question:
            return None, "the question was empty"
        top, _ = search_module.search(embed([question])[0], index, search_module.everything,
                                      k=depth)
        passages = top + ([] if source in top else [source])
        verdict = library.yes_no(chat(
            f"{prompts['detail_judge']}\nQuestion: {question}\n\n"
            f"{library.passages_block(passages)}", "data build"))
        made = {"question": question, "top_ids": [e["article_id"] for e in top],
                "verdict": verdict}
        return made, None if verdict == "no" else f"a judge found an answer (reply: {verdict})"

    made, rejected = ask(chat, config, f"{prompts['absent_detail']}\nArticle:\n{source['text']}",
                         check)
    if made is None:
        return {"problem": "no absent detail passed", "rejected": rejected}
    in_top = article["article_id"] in made["top_ids"]
    return {"id": f"U{number:03d}", "kind": "absent-detail", "article_id": article["article_id"],
            "question": made["question"],
            "note": (f"judge said no over the top {depth} passages"
                     f"{'' if in_top else ' plus the source article'}; source "
                     f"{'in' if in_top else 'not in'} the top {depth}"),
            "top_ids": made["top_ids"], "rejected": rejected}


def detail_articles(config: dict, articles: list[dict]) -> list[dict]:
    order = list(articles)
    random.Random(config["seed"] + 1).shuffle(order)
    return order


def build_unanswerable(chat, config: dict, embed, index: dict, e3: dict, sizes: dict) -> list:
    texts = [e["text"] for e in index["entries"]]
    categories = config["absent_categories"][: sizes["absent_product"]]
    with ThreadPoolExecutor(WORKERS) as pool:
        products = list(pool.map(
            lambda pair: absent_product(chat, config, texts, e3["products"], pair[1], pair[0]),
            enumerate(categories)))
    # One at a time: the embedding cache is a SQLite connection that stays on one thread.
    chosen = detail_articles(config, e3["articles"])[: sizes["absent_detail"]]
    details = [absent_detail(chat, config, embed, index, article, len(categories) + n)
               for n, article in enumerate(chosen)]
    failed = [item for item in products + details if "problem" in item]
    if failed:
        raise BuildError(f"{len(failed)} unanswerable questions failed every attempt: {failed}")
    return products + details


# 4.3 Internal notes -------------------------------------------------------------------------


def note_sources(config: dict, questions: list[dict], per_type: int) -> list[dict]:
    """E3 questions whose right articles get a note: per_type of each type, all different
    articles, in one seeded order."""
    rng = random.Random(config["seed"] + 2)
    used: set[str] = set()
    picked = []
    for kind in ("identifier", "paraphrase", "shared"):
        pool = [(i, q) for i, q in enumerate(questions)
                if q["type"] == kind and q["article_id"] not in used]
        for i, q in rng.sample(pool, per_type):
            used.add(q["article_id"])
            picked.append({"question_index": i, "type": kind, "article_id": q["article_id"]})
    rng.shuffle(picked)
    return picked


def internal_note(chat, config: dict, texts: list[str], articles: dict, count_tokens,
                  source: dict, number: int) -> dict:
    kind = config["note_kinds"][number % len(config["note_kinds"])]
    article = articles[source["article_id"]]
    prompt = config["prompts"]["internal_note"].format(kind=kind) + f"\nArticle:\n{article}"

    def check(reply: str):
        note = reply.strip()
        return note, library.note_problem(note, texts, count_tokens(note), config)

    note, rejected = ask(chat, config, prompt, check)
    if note is None:
        return {"problem": "no note passed", "rejected": rejected}
    question = chat(f"{config['prompts']['note_question']}\nNote:\n{note}", "data build")
    return {"note_id": f"N{number:03d}", **source, "kind": kind, "access": "internal",
            "text": note, "tokens": count_tokens(note),
            "longest_shared_chars": library.longest_shared(note, texts),
            "question": question, "rejected": rejected}


def build_notes(chat, config: dict, e3: dict, count_tokens, count: int) -> list[dict]:
    per_type = config["notes_per_type"]
    sources = note_sources(config, e3["questions"], per_type)[:count]
    texts = [a["text"] for a in e3["articles"]]
    articles = {a["article_id"]: a["text"] for a in e3["articles"]}
    with ThreadPoolExecutor(WORKERS) as pool:
        notes = list(pool.map(
            lambda pair: internal_note(chat, config, texts, articles, count_tokens, pair[1],
                                       pair[0]),
            enumerate(sources)))
    failed = [n for n in notes if "problem" in n]
    if failed:
        raise BuildError(f"{len(failed)} internal notes failed every attempt: {failed}")
    return notes
