"""S2 E5, When retrieval quietly fails: stale index, two versions, nothing to find, and a
permission leak, each measured on the S2 E3 library with its fix.

Run from the repository root:

    uv run python episodes/s2-e5-quiet-failures/quiet.py --estimate
    uv run python episodes/s2-e5-quiet-failures/quiet.py --pilot
    uv run python episodes/s2-e5-quiet-failures/quiet.py --yes

--estimate needs no key and no network. The pilot and the full run need OPENAI_API_KEY, in the
repository's .env file or the environment. Without --yes the full run prints the estimate and
stops before its first paid call. Every response is cached in .cache/, so a rerun costs nothing.
chart.py and the tests read the committed results/ and need no key. See README.md.
"""

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import tiktoken
from dotenv import load_dotenv

from lab.experiments import load_sibling

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
chatlib = load_sibling(HERE / "chat.py")
library = load_sibling(HERE / "library.py")
build = load_sibling(HERE / "build.py")
trials = load_sibling(HERE / "trials.py")
measure = load_sibling(HERE / "measure.py")
estimates = load_sibling(HERE / "estimate.py")
store = load_sibling(ROOT / "episodes" / "s2-e2-chunking" / "store.py")

CACHE = ROOT / ".cache" / "s2-e5-quiet-failures"
DATA = HERE / "data"
RESULTS = HERE / "results"
PILOT = RESULTS / "pilot"


def sizes(config: dict, pilot: bool) -> dict:
    if pilot:
        return dict(config["pilot"])
    return {"values": config["values"], "absent_product": config["absent_product"],
            "absent_detail": config["absent_detail"], "notes": 3 * config["notes_per_type"]}


def today() -> str:
    return datetime.now(UTC).date().isoformat()


class Embed:
    """The S2 E2 embedder, through its cache, remembering every distinct text it was asked for,
    so the tokens the results depend on can be totalled whether or not a call was made."""

    def __init__(self, client, config: dict, path: Path) -> None:
        enc = tiktoken.get_encoding(config["embedding_tokeniser"])
        self.count = lambda text: len(enc.encode(text))
        self.inner = store.Embedder(client, config["embedding_model"],
                                    store.EmbeddingStore(path), self.count)
        self.texts: set[str] = set()

    def __call__(self, texts: list[str]):
        self.texts.update(texts)
        return self.inner(texts)

    def usage(self) -> dict:
        return {"texts": len(self.texts), "input_tokens": sum(self.count(t) for t in self.texts),
                "reported_this_run": self.inner.tokens_reported,
                "model_returned": self.inner.model_returned}


def load_e3(config: dict) -> dict:
    articles, questions = library.load_e3(config)
    return {"articles": articles, "questions": questions,
            "products": library.e3_config(config)["products"]}


# Data ---------------------------------------------------------------------------------------


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                    newline="\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_data(config: dict, chat, embed, e3: dict, size: dict, folder: Path) -> dict:
    """Section 4. Reads the data if it is already built in `folder`; builds and writes it if
    not. The committed data is what the results depend on."""
    files = {name: folder / f"{name}.json" for name in ("values", "unanswerable", "notes")}
    if all(path.exists() for path in files.values()):
        return {name: json.loads(path.read_text(encoding="utf-8"))["items"]
                for name, path in files.items()}
    values, dropped = build.build_values(chat, config, e3["articles"], size["values"])
    fresh = trials.build_indexes(config, e3["articles"], values, [], embed)["fresh"]
    unanswerable = build.build_unanswerable(chat, config, embed, fresh, e3, size)
    notes = build.build_notes(chat, config, e3, embed.count, size["notes"])
    write_json(files["values"], {"seed": config["seed"], "items": values,
                                 "candidates_rejected": dropped})
    write_json(files["unanswerable"], {"seed": config["seed"], "items": unanswerable})
    write_json(files["notes"], {"seed": config["seed"], "items": notes})
    write_csv(folder / "unanswerable.csv", [
        {"id": u["id"], "kind": u["kind"], "question": u["question"],
         "product_or_article": u.get("product") or u.get("article_id"),
         "verification": u["note"], "attempts": len(u["rejected"]) + 1}
        for u in unanswerable])
    return {"values": values, "unanswerable": unanswerable, "notes": notes}


# The run ------------------------------------------------------------------------------------


def run(config: dict, chat, embed, e3: dict, data: dict, pilot: bool) -> dict:
    values, notes = data["values"], data["notes"]
    idx = trials.build_indexes(config, e3["articles"], values, notes, embed)
    questions = ([e3["questions"][n["question_index"]] for n in notes] if pilot
                 else e3["questions"])
    a = trials.test_a(config, chat, embed, idx, values)
    b = trials.test_b(config, chat, embed, idx, values)
    c = trials.test_c(config, chat, embed, idx, values, data["unanswerable"])
    d = trials.test_d(config, embed, idx, questions)
    audit = trials.audit_rows(c["rows"], config["judge_audit_rows"], config["seed"])
    same = trials.check_same_index(config, embed, e3["articles"], questions)
    checks = {
        "1 same index twice": same,
        "2 S2 E3 rerun": {"recall_hits": same["recall_hits"], "n": same["n"],
                          "e3_hits": config["e3_vector_hits"]},
        "3 reader works": a["summary"]["fresh"]["current"],
        "4 and 5 values": trials.check_values(e3["articles"], values),
        "6 notes reachable": trials.check_notes_reachable(config, embed, idx, notes),
        "7 judge audit": {"judged": len(audit),
                          "flagged": sum(r["flagged_for_manual_check"] for r in audit)},
    }
    marks = config["pass_marks"]
    claims = {**measure.claims_a(a["summary"], marks), **measure.claims_b(b["summary"], marks),
              **measure.claims_c(c["summary"], marks),
              **measure.claims_d(d["summary"], marks, config["e3_vector_hits"])}
    return {"A": a, "B": b, "C": c, "D": d, "audit": audit, "checks": checks, "claims": claims}


def summary(config: dict, out: dict, chat, embed, size: dict, pilot: bool) -> dict:
    return {
        "episode": "s2-e5-quiet-failures",
        "pilot": pilot,
        "run_date_utc": today(),
        "seed": config["seed"],
        "sizes": size,
        "chat_model_requested": chat.model,
        "chat_model_returned": sorted(chat.models),
        "embedding_model_requested": config["embedding_model"],
        "embedding_model_returned": embed.inner.model_returned or config["embedding_model"],
        "top_k": config["top_k"],
        "pass_marks": config["pass_marks"],
        "claims": out["claims"],
        "checks": out["checks"],
        "A": out["A"]["summary"],
        "B": out["B"]["summary"],
        "C": out["C"]["summary"],
        "D": out["D"]["summary"],
        "C_scores": {g: [r["top1_score"] for r in out["C"]["rows"] if r["group"] == g]
                     for g in ("answerable", "unanswerable")},
    }


def write_results(folder: Path, out: dict, summ: dict, tokens: dict) -> None:
    for test, name in (("A", "stale"), ("B", "versions"), ("C", "unanswerable"),
                       ("D", "scope")):
        write_json(folder / f"test_{test.lower()}_{name}.json", out[test]["rows"])
    write_json(folder / "summary.json", summ)
    write_json(folder / "tokens.json", tokens)
    if out["audit"]:
        write_csv(folder / "judge_audit.csv", out["audit"])


def print_claims(summ: dict) -> None:
    for name, c in summ["claims"].items():
        print(f"  {name:<10} {c['verdict']:<7} {c['measured']}  (pass: {c['pass_mark']})")
    for name, c in summ["checks"].items():
        shown = {k: v for k, v in c.items() if k != "per_note"}
        print(f"  check {name}: {shown}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--estimate", action="store_true", help="count tokens; no key, no network")
    mode.add_argument("--pilot", action="store_true", help="5 items per condition")
    parser.add_argument("--yes", action="store_true", help="start the paid full run")
    args = parser.parse_args()
    config = library.load_config()
    model = library.chat_model(config)
    e3 = load_e3(config)
    size = sizes(config, args.pilot)
    est = estimates.estimate(config, e3["articles"], e3["questions"], e3["products"], size)
    estimates.print_estimate(est, model, config["embedding_model"])
    if args.estimate:
        write_json(RESULTS / "estimate.json", est)
        return
    if not args.pilot and not args.yes:
        print("Full run not started: nothing has been sent. Rerun with --yes to start it.")
        return

    load_dotenv()
    from openai import OpenAI

    client = OpenAI(max_retries=5)
    chat = chatlib.Chat(client, model, config["max_output_tokens"], CACHE / "chat.sqlite")
    embed = Embed(client, config, CACHE / "embeddings.sqlite")
    folder = PILOT if args.pilot else RESULTS
    data = build_data(config, chat, embed, e3, size, PILOT / "data" if args.pilot else DATA)
    out = run(config, chat, embed, e3, data, args.pilot)
    summ = summary(config, out, chat, embed, size, args.pilot)
    tokens = {"estimate": est, "actual": {**chat.usage, "embeddings": embed.usage()},
              "chat_calls_sent_this_run": chat.sent}
    write_results(folder, out, summ, tokens)
    print(f"{'Pilot' if args.pilot else 'Full run'}, {summ['run_date_utc']}:")
    print_claims(summ)
    print(f"Chat calls sent this run: {chat.sent}; results in {folder.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
