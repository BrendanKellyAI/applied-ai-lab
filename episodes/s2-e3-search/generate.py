"""Builds the S2 E3 knowledge base and questions with gpt-6-astra, and checks them in code.

Run from the repository root:

    uv run python episodes/s2-e3-search/generate.py --pilot
    uv run python episodes/s2-e3-search/generate.py

Needs OPENAI_API_KEY. Writes corpus.json and questions.json (or pilot/corpus.json and
pilot/questions.json), which are committed, so the search can be rerun with no generation.
Every call is cached in .cache/, so the full run reuses the pilot's articles, and a rerun of this
script pays only for what it has not generated before. Regenerating from scratch will not give the
same articles: the model does not sample the same text twice.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path

import tiktoken
from dotenv import load_dotenv

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import plan  # noqa: E402

CACHE = HERE.parents[1] / ".cache" / "generation" / "s2-e3-search.sqlite"
WORKERS = 8


class GenerationError(RuntimeError):
    """A text could not be made to pass its checks within the allowed attempts."""


@cache
def encoding():
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(encoding().encode(text))


class Generator:
    """Sends Responses API calls through an on-disk cache and totals the usage reported."""

    def __init__(self, client, config: dict, path: Path = CACHE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.client, self.config = client, config
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS calls (key TEXT PRIMARY KEY, body TEXT)")
        self._lock = threading.Lock()
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}
        self.models: set[str] = set()

    def __call__(self, instructions: str, prompt: str, attempt: int) -> str:
        request = {
            "model": self.config["generation_model"],
            "instructions": instructions,
            "input": prompt,
            "max_output_tokens": self.config["max_output_tokens"],
        }
        key = hashlib.sha256(json.dumps([request, attempt], sort_keys=True).encode()).hexdigest()
        with self._lock:
            row = self._db.execute("SELECT body FROM calls WHERE key = ?", (key,)).fetchone()
        if row is None:
            response = self.client.responses.create(**request)
            usage = response.usage
            body = {
                "text": response.output_text,
                "status": response.status,
                "model": response.model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
            }
            with self._lock, self._db:
                self._db.execute(
                    "INSERT OR REPLACE INTO calls VALUES (?, ?)", (key, json.dumps(body))
                )
        else:
            body = json.loads(row[0])
        # Every call the corpus depends on is counted, cached or not, so the totals describe what
        # building this corpus cost, however many times the script has been run.
        with self._lock:
            self.usage["calls"] += 1
            for name in ("input_tokens", "output_tokens", "reasoning_tokens"):
                self.usage[name] += body[name]
            self.models.add(body["model"])
        return body["text"].strip() if body["status"] == "completed" else ""


# Articles -----------------------------------------------------------------------------------


def article_request(config: dict, brief: plan.Brief) -> str:
    lines = [f"Product: {brief.product}", f"Topic: {brief.topic}"]
    if brief.identifier:
        prompt = config["identifier_prompt"]
        lines.append(prompt.format(kind=brief.kind, identifier=brief.identifier))
    return "\n".join(lines)


def article_problem(config: dict, brief: plan.Brief, text: str) -> str | None:
    """Why an article fails its checks, or None if it passes."""
    low, high = config["article_tokens"]
    tokens = count_tokens(text)
    if not low <= tokens <= high:
        return f"{tokens} tokens, outside {low} to {high}"
    found = plan.identifiers_in(text)
    expected = [brief.identifier] if brief.identifier else []
    if found != expected:
        return f"identifiers {found}, expected {expected}"
    return None


def make_article(generate: Generator, config: dict, brief: plan.Brief) -> dict:
    problems = []
    for attempt in range(config["max_attempts"]):
        text = generate(config["article_prompt"], article_request(config, brief), attempt)
        problem = article_problem(config, brief, text)
        if problem is None:
            return {
                "article_id": brief.article_id,
                "product": brief.product,
                "topic": brief.topic,
                "identifier": brief.identifier,
                "kind": brief.kind,
                "role": brief.role,
                "group": brief.group,
                "text": text,
                "tokens": count_tokens(text),
                "rejected": problems,
            }
        problems.append(problem)
    raise GenerationError(f"Article {brief.article_id} failed every attempt: {problems}")


# Questions ----------------------------------------------------------------------------------


def question_problem(config: dict, kind: str, question: str, article: str) -> str | None:
    stop = set(config["stop_words"])
    shared = plan.shared_words(question, article, stop)
    if not question.strip():
        return "The question was empty."
    if kind == "paraphrase" and shared:
        return f"It reused these words from the article: {', '.join(sorted(shared))}."
    if kind == "shared" and len(shared) < config["min_shared_words"]:
        return (
            f"It reused only {len(shared)} of the article's key words; "
            f"use at least {config['min_shared_words']}."
        )
    return None


def make_question(generate: Generator, config: dict, kind: str, article: dict) -> dict:
    if kind == "identifier":
        template = config["identifier_questions"][article["kind"]]
        question = template.format(identifier=article["identifier"])
        return {"type": kind, "article_id": article["article_id"], "question": question,
                "regenerated": 0, "rejected": []}
    prompt = f"{config['question_prompts'][kind]}\n\nArticle:\n{article['text']}"
    rejected: list[dict] = []
    for attempt in range(config["max_attempts"]):
        if rejected:
            retry = config["question_prompts"]["retry"].format(problem=rejected[-1]["problem"])
            prompt_now = f"{prompt}\n\nYour last question: {rejected[-1]['question']}\n{retry}"
        else:
            prompt_now = prompt
        question = generate(config["question_prompts"][kind], prompt_now, attempt)
        problem = question_problem(config, kind, question, article["text"])
        if problem is None:
            return {"type": kind, "article_id": article["article_id"], "question": question,
                    "regenerated": len(rejected), "rejected": rejected}
        rejected.append({"question": question, "problem": problem})
    raise GenerationError(f"No {kind} question for {article['article_id']} passed: {rejected}")


# The build ----------------------------------------------------------------------------------


def build(config: dict, client, *, pilot: bool) -> tuple[dict, dict]:
    briefs = plan.make_briefs(config)
    if pilot:
        briefs, questions_for = plan.pilot_selection(config, briefs)
    else:
        questions_for = plan.question_plan(config, briefs)
    generate = Generator(client, config)
    with ThreadPoolExecutor(WORKERS) as pool:
        articles = list(pool.map(lambda b: make_article(generate, config, b), briefs))
    by_id = {a["article_id"]: a for a in articles}
    jobs = [(kind, by_id[aid]) for kind, ids in questions_for.items() for aid in ids]
    with ThreadPoolExecutor(WORKERS) as pool:
        questions = list(pool.map(lambda job: make_question(generate, config, *job), jobs))
    meta = {
        "seed": config["seed"],
        "company": config["company"],
        "generation_model_requested": config["generation_model"],
        "generation_model_returned": sorted(generate.models),
        "tokeniser": config["tokeniser"],
        "generation_usage": generate.usage,
        "prompts": {
            "article": config["article_prompt"],
            "identifier": config["identifier_prompt"],
            "questions": config["question_prompts"],
            "identifier_questions": config["identifier_questions"],
        },
    }
    return {**meta, "articles": articles}, {"seed": config["seed"], "questions": questions}


def write(corpus: dict, questions: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (("corpus.json", corpus), ("questions.json", questions)):
        (folder / name).write_text(
            json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the S2 E3 corpus and questions")
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    from openai import OpenAI

    corpus, questions = build(plan.load_config(), OpenAI(max_retries=5), pilot=args.pilot)
    folder = HERE / "pilot" if args.pilot else HERE
    write(corpus, questions, folder)
    usage = corpus["generation_usage"]
    regenerated = sum(q["regenerated"] for q in questions["questions"])
    print(f"{len(corpus['articles'])} articles, {len(questions['questions'])} questions")
    print(f"Generation: {usage}")
    print(f"Articles regenerated: {sum(len(a['rejected']) for a in corpus['articles'])}")
    print(f"Questions regenerated: {regenerated}")
    print(f"Written to {folder}")


if __name__ == "__main__":
    main()
