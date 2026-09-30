"""Cached calls to the chat model, with the tokens each stage used.

Every response is stored in .cache/ under a hash of the model and the full request, so a rerun of
the full run sends nothing. Tokens are totalled per stage for every call the results depend on,
cached or not, so tokens.json describes what the run cost however many times it has been run.
Nothing is sent without a client: the estimate and the tests pass a stand-in.
"""

import hashlib
import json
import sqlite3
import threading
from pathlib import Path

STAGES = ("data build", "embeddings", "answering", "judging")


def request_key(request: dict) -> str:
    """Hash of the model and the full request."""
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def empty_usage() -> dict:
    return {stage: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}
            for stage in STAGES}


class Chat:
    """Sends Responses API calls through an on-disk cache.

    `client` is an OpenAI client, or any object with the same `responses.create`. A call made with
    `paid=False` that is not in the cache raises instead of spending.
    """

    def __init__(self, client, model: str, max_output_tokens: int, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.client, self.model, self.max_output_tokens = client, model, max_output_tokens
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS calls (key TEXT PRIMARY KEY, body TEXT)")
        self._lock = threading.Lock()
        self.usage = empty_usage()
        self.models: set[str] = set()
        self.sent = 0

    def request(self, prompt: str) -> dict:
        return {"model": self.model, "input": prompt, "max_output_tokens": self.max_output_tokens}

    def __call__(self, prompt: str, stage: str) -> str:
        if stage not in STAGES:
            raise ValueError(f"Unknown stage {stage!r}")
        request = self.request(prompt)
        key = request_key(request)
        with self._lock:
            row = self._db.execute("SELECT body FROM calls WHERE key = ?", (key,)).fetchone()
        if row is None:
            body = self._send(request)
            with self._lock, self._db:
                self._db.execute("INSERT OR REPLACE INTO calls VALUES (?, ?)",
                                 (key, json.dumps(body)))
        else:
            body = json.loads(row[0])
        with self._lock:
            totals = self.usage[stage]
            totals["calls"] += 1
            for name in ("input_tokens", "output_tokens", "reasoning_tokens"):
                totals[name] += body[name]
            self.models.add(body["model"])
        return body["text"].strip() if body["status"] == "completed" else ""

    def _send(self, request: dict) -> dict:
        response = self.client.responses.create(**request)
        usage = response.usage
        with self._lock:
            self.sent += 1
        return {
            "text": response.output_text,
            "status": response.status,
            "model": response.model,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
        }

    def close(self) -> None:
        self._db.close()


def parse_json(text: str) -> dict | None:
    """The JSON object in a reply, allowing a code fence around it; None if there is none."""
    body = text.strip()
    if body.startswith("```"):
        body = body.strip("`")
        body = body.split("\n", 1)[1] if "\n" in body else body
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        found = json.loads(body[start : end + 1])
    except json.JSONDecodeError:
        return None
    return found if isinstance(found, dict) else None


def with_retry(prompt: str, rejected: list[dict], retry_template: str) -> str:
    """The prompt again, with the last rejected reply and why it failed, so the request differs
    from the one already cached and the model is told what to fix."""
    if not rejected:
        return prompt
    last = rejected[-1]
    return (f"{prompt}\n\nYour last reply: {last['reply']}\n"
            f"{retry_template.format(problem=last['problem']).strip()}")
