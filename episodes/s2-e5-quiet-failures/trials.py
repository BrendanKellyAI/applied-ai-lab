"""The four tests (section 5) and the checks (section 6). Every retrieval goes through `search`.

`embed(texts)` returns one vector per text; `chat(prompt, stage)` returns the model's reply. Both
are cached by the caller, so nothing here knows whether a call was paid for.
"""

import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lab.experiments import load_sibling

HERE = Path(__file__).parent
library = load_sibling(HERE / "library.py")
measure = load_sibling(HERE / "measure.py")
s = load_sibling(HERE / "search.py")
WORKERS = 8


def parallel(fn, items: list) -> list:
    with ThreadPoolExecutor(WORKERS) as pool:
        return list(pool.map(fn, items))


def ids(entries: list[dict]) -> list[str]:
    return [e["article_id"] for e in entries]


# The indexes --------------------------------------------------------------------------------


def sources(articles: list[dict], values: list[dict]) -> tuple[dict, dict]:
    """The library as first indexed, and as it stands after the revisions."""
    original = {a["article_id"]: a["text"] for a in articles}
    current = {**original, **{v["article_id"]: v["revised"] for v in values}}
    return original, current


def build_indexes(config: dict, articles: list[dict], values: list[dict], notes: list[dict],
                  embed) -> dict:
    original, current = sources(articles, values)
    revised = {v["article_id"] for v in values}
    old, new, same = config["old_date"], config["new_date"], config["unchanged_date"]

    def index(entries: list[dict]) -> dict:
        return library.make_index(entries, embed([e["text"] for e in entries]))

    fresh = [library.entry(a, current[a], date=new if a in revised else same) for a in current]
    stale = [library.entry(a, original[a], date=same) for a in original]
    versions = [library.entry(a, original[a], date=same) for a in original if a not in revised]
    for v in values:
        versions.append(library.entry(v["article_id"], original[v["article_id"]], date=old,
                                      version="old"))
        versions.append(library.entry(v["article_id"], v["revised"], date=new, version="new"))
    scope = [library.entry(a, original[a], date=same) for a in original]
    scope += [library.entry(n["note_id"], n["text"], access="internal", date=same)
              for n in notes]
    return {"fresh": index(fresh), "stale": index(stale), "versions": index(versions),
            "scope": index(scope), "sources": current}


# Test A: stale index ------------------------------------------------------------------------


def value_counts(rows: list[dict], key: str) -> dict:
    return {
        "recall": measure.tally(rows, lambda r: r[key]["hit"]),
        "current": measure.tally(rows, lambda r: r[key]["grade"] in ("new", "both")),
        "old": measure.tally(rows, lambda r: r[key]["grade"] in ("old", "both")),
        "both": measure.tally(rows, lambda r: r[key]["grade"] == "both"),
        "neither": measure.tally(rows, lambda r: r[key]["grade"] == "neither"),
    }


def test_a(config: dict, chat, embed, idx: dict, values: list[dict]) -> dict:
    k = config["top_k"]
    vectors = embed([v["question"] for v in values])

    def one(pair):
        v, q = pair
        row = {"article_id": v["article_id"], "question": v["question"], "old": v["old"],
               "new": v["new"]}
        for name in ("fresh", "stale"):
            top, scores = s.search(q, idx[name], s.everything, k)
            reply = chat(library.answer_prompt(config, v["question"], top), "answering")
            row[name] = {"top": ids(top), "scores": [float(x) for x in scores],
                         "hit": v["article_id"] in ids(top), "reply": reply,
                         "grade": library.grade_value(reply, v["old"], v["new"])}
        return row

    rows = parallel(one, list(zip(values, vectors)))
    revised = {v["article_id"] for v in values}
    flagged = library.stale_entries(idx["stale"], idx["sources"])
    hashed = {"stale_total": len(revised), "flagged": flagged,
              "flagged_stale": sum(1 for f in flagged if f.split(":")[0] in revised),
              "flagged_other": sum(1 for f in flagged if f.split(":")[0] not in revised)}
    return {"rows": rows, "summary": {"fresh": value_counts(rows, "fresh"),
                                      "stale": value_counts(rows, "stale"), "hash": hashed}}


# Test B: two versions -----------------------------------------------------------------------


def test_b(config: dict, chat, embed, idx: dict, values: list[dict]) -> dict:
    k, index = config["top_k"], idx["versions"]
    vectors = embed([v["question"] for v in values])

    def one(pair):
        v, q = pair
        aid = v["article_id"]
        ranked, _ = s.search(q, index, s.everything, len(index["entries"]))
        rank = {e["entry_id"]: n for n, e in enumerate(ranked, start=1)}
        top = ranked[:k]
        top_ids = [e["entry_id"] for e in top]
        latest, _ = s.search(q, index, s.latest, k)
        row = {"article_id": aid, "question": v["question"], "top": top_ids,
               "old_rank": rank[f"{aid}:old"], "new_rank": rank[f"{aid}:new"],
               "only_old_in_top": f"{aid}:old" in top_ids and f"{aid}:new" not in top_ids,
               "latest_top": [e["entry_id"] for e in latest]}
        for name, passages, dated in (("B-plain", top, False), ("B-dated", top, True),
                                      ("B-latest", latest, False)):
            reply = chat(library.answer_prompt(config, v["question"], passages, dated=dated),
                         "answering")
            row[name] = {"reply": reply, "grade": library.grade_value(reply, v["old"], v["new"])}
        return row

    rows = parallel(one, list(zip(values, vectors)))
    summary = {"old_above": measure.tally(rows, lambda r: r["old_rank"] < r["new_rank"]),
               "only_old_in_top": measure.tally(rows, lambda r: r["only_old_in_top"])}
    for name in ("B-plain", "B-dated", "B-latest"):
        summary[name] = {
            "old_only": measure.tally(rows, lambda r, n=name: r[n]["grade"] == "old"),
            "new_only": measure.tally(rows, lambda r, n=name: r[n]["grade"] == "new"),
            "both": measure.tally(rows, lambda r, n=name: r[n]["grade"] == "both"),
            "neither": measure.tally(rows, lambda r, n=name: r[n]["grade"] == "neither"),
            "any_old": measure.tally(rows, lambda r, n=name: r[n]["grade"] in ("old", "both")),
        }
    return {"rows": rows, "summary": summary}


# Test C: nothing to find, answered anyway ---------------------------------------------------


def judge(config: dict, chat, question: str, reply: str) -> str:
    prompt = f"{config['prompts']['answer_judge']}\nQuestion: {question}\n\nReply: {reply}"
    return library.judge_verdict(chat(prompt, "judging"))


def test_c(config: dict, chat, embed, idx: dict, values: list[dict],
           unanswerable: list[dict]) -> dict:
    k, index = config["top_k"], idx["fresh"]
    items = ([{"id": v["article_id"], "group": "answerable", "question": v["question"],
               "old": v["old"], "new": v["new"]} for v in values]
             + [{"id": u["id"], "group": "unanswerable", "kind": u["kind"],
                 "question": u["question"]} for u in unanswerable])
    vectors = embed([i["question"] for i in items])

    def one(pair):
        item, q = pair
        top, scores = s.search(q, index, s.everything, k)
        row = {**item, "top": ids(top), "top1_score": float(scores[0])}
        for name, not_found in (("P1", False), ("P2", True)):
            reply = chat(library.answer_prompt(config, item["question"], top,
                                               not_found=not_found), "answering")
            out = {"reply": reply, "not_found": library.is_not_found(reply)}
            if item["group"] == "answerable":
                out["grade"] = library.grade_value(reply, item["old"], item["new"])
            elif name == "P2" and out["not_found"]:
                out["verdict"] = "decline"
                out["judged"] = False
            else:
                out["verdict"] = judge(config, chat, item["question"], reply)
                out["judged"] = True
            row[name] = out
        return row

    rows = parallel(one, list(zip(items, vectors)))
    return {"rows": rows, "summary": summarise_c(rows)}


def summarise_c(rows: list[dict]) -> dict:
    ans = [r for r in rows if r["group"] == "answerable"]
    una = [r for r in rows if r["group"] == "unanswerable"]
    summary = {"cutoff": measure.best_cutoff([r["top1_score"] for r in ans],
                                             [r["top1_score"] for r in una])}
    for name in ("P1", "P2"):
        summary[name] = {
            "answerable_current": measure.tally(ans, lambda r, n=name: r[n]["grade"]
                                                in ("new", "both")),
            "answerable_not_found": measure.tally(ans, lambda r, n=name: r[n]["not_found"]),
            "unanswerable_not_found": measure.tally(una, lambda r, n=name: r[n]["not_found"]),
            "unanswerable_asserted": measure.tally(una, lambda r, n=name:
                                                   r[n]["verdict"] == "assert"),
            "unanswerable_unclear": measure.tally(una, lambda r, n=name:
                                                  r[n]["verdict"] == "unclear"),
            # Unclear verdicts count against each claim: not asserted for C2, asserted for C3.
            "unanswerable_asserted_for_c2": measure.tally(una, lambda r, n=name:
                                                          r[n]["verdict"] == "assert"),
            "unanswerable_asserted_for_c3": measure.tally(una, lambda r, n=name:
                                                          r[n]["verdict"] != "decline"),
        }
    return summary


def audit_rows(rows: list[dict], flag: int, seed: int) -> list[dict]:
    """Every judged reply, with a seeded random `flag` of them marked for a manual check."""
    judged = [{"prompt": name, "id": r["id"], "kind": r.get("kind", ""),
               "question": r["question"], "reply": r[name]["reply"],
               "verdict": r[name]["verdict"]}
              for r in rows if r["group"] == "unanswerable" for name in ("P1", "P2")
              if r[name].get("judged")]
    marked = set(random.Random(seed).sample(range(len(judged)), min(flag, len(judged))))
    return [{**row, "flagged_for_manual_check": n in marked} for n, row in enumerate(judged)]


# Test D: scope and permission leak ----------------------------------------------------------


def test_d(config: dict, embed, idx: dict, questions: list[dict]) -> dict:
    k, index = config["top_k"], idx["scope"]
    vectors = embed([q["question"] for q in questions])
    rows = []
    for q, v in zip(questions, vectors):
        everything, _ = s.search(v, index, s.everything, k)
        delivered = {"D-none": everything,
                     "D-post": [e for e in everything if s.public(e)],
                     "D-pre": s.search(v, index, s.public, k)[0]}
        row = {"type": q["type"], "article_id": q["article_id"], "question": q["question"]}
        for name, entries in delivered.items():
            row[name] = {"top": ids(entries), "delivered": len(entries),
                         "leak": any(e["access"] != "public" for e in entries),
                         "hit": q["article_id"] in ids(entries)}
        rows.append(row)
    summary = {}
    for name in ("D-none", "D-post", "D-pre"):
        summary[name] = {
            "leaks": measure.tally(rows, lambda r, n=name: r[n]["leak"]),
            "recall": measure.tally(rows, lambda r, n=name: r[n]["hit"]),
            "mean_delivered": sum(r[name]["delivered"] for r in rows) / len(rows),
            "fewer_than_k": sum(1 for r in rows if r[name]["delivered"] < k),
        }
    return {"rows": rows, "summary": summary}


# Checks -------------------------------------------------------------------------------------


def check_same_index(config: dict, embed, articles: list[dict], questions: list[dict]) -> dict:
    """Checks 1 and 2: the public library indexed twice gives the same top 5 for every E3
    question, and its recall at 5 matches S2 E3's vector result."""
    k = config["top_k"]
    entries = [library.entry(a["article_id"], a["text"]) for a in articles]
    first, second = (library.make_index(entries, embed([e["text"] for e in entries]))
                     for _ in range(2))
    vectors = embed([q["question"] for q in questions])
    tops = [[ids(s.search(v, index, s.everything, k)[0]) for v in vectors]
            for index in (first, second)]
    hits = sum(1 for q, top in zip(questions, tops[0]) if q["article_id"] in top)
    return {"identical": sum(1 for a, b in zip(*tops) if a == b), "n": len(questions),
            "recall_hits": hits, "e3_hits": config["e3_vector_hits"]}


def check_values(articles: list[dict], values: list[dict]) -> dict:
    """Checks 4 and 5: each old value appears once, in its own original, and nowhere in the
    revised library; each new value once, in its own revision, and nowhere in the original; and
    each revision differs from its original by that value alone."""
    original, current = sources(articles, values)
    unique, minimal = [], []
    for v in values:
        aid = v["article_id"]
        unique.append(
            library.occurrences(original.values(), v["old"]) == 1
            and original[aid].count(v["old"]) == 1
            and library.occurrences(current.values(), v["old"]) == 0
            and library.occurrences(original.values(), v["new"]) == 0
            and library.occurrences(current.values(), v["new"]) == 1
            and current[aid].count(v["new"]) == 1)
        try:
            library.assert_minimal(original[aid], v["revised"], v["old"], v["new"])
            minimal.append(True)
        except AssertionError:
            minimal.append(False)
    return {"unique": sum(unique), "minimal": sum(minimal), "n": len(values)}


def check_notes_reachable(config: dict, embed, idx: dict, notes: list[dict]) -> dict:
    """Check 6: a question written from each note finds that note in D-none's top 5."""
    vectors = embed([n["question"] for n in notes])
    found = [n["note_id"] in ids(s.search(v, idx["scope"], s.everything, config["top_k"])[0])
             for n, v in zip(notes, vectors)]
    return {"reachable": sum(found), "n": len(notes),
            "per_note": {n["note_id"]: f for n, f in zip(notes, found)}}
