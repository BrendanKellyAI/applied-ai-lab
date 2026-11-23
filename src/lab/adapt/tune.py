"""Tuning jobs: prepare the notebook's files, validate them, count training tokens, and keep the
job record.

The record (results/<arm>/job.json) lists every attempt and is never rewritten in place: a
launch appends an attempt, and a result fills in that attempt's outcome. A second launch is
refused while an attempt is open or after one succeeded, and after a failure it needs an
explicit retry approval, so no job is relaunched silently.

Token counts use tiktoken's o200k_base as a stand-in for Qwen's tokeniser, plus a few tokens a
message for the chat template; the notebook records Qwen's own count.
"""

import hashlib
import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lab.adapt.definitions import Definitions
from lab.adapt.items import ReplyItem, TriageItem, reply_items, triage_items
from lab.adapt.output import parse_triage
from lab.adapt.prompts import (
    label_json,
    reply_prompt,
    reply_system,
    triage_prompt,
    triage_system,
)
from lab.adapt.run import read_jsonl, write_jsonl
from lab.adapt.tune_config import TuneConfig
from lab.rag.estimate import chat_tokens

TEMPLATE_TOKENS_PER_MESSAGE = 4
OPEN = "launched"
TOKENISER_NOTE = (
    "tiktoken o200k_base plus 4 tokens a message, a stand-in for Qwen's tokeniser; the "
    "notebook records Qwen's own count"
)


class JobError(ValueError):
    """A tuning job that cannot be prepared, launched or recorded as asked."""


def _system(config: TuneConfig, definitions: Definitions, style_guide: str) -> str:
    if config.task == "a":
        return triage_system(config.instructions, definitions)
    return reply_system(config.instructions, style_guide)


def _messages(item: TriageItem | ReplyItem, system: str, *, target: bool) -> list[dict]:
    if isinstance(item, TriageItem):
        user, answer = triage_prompt(item), label_json(item.label)
    else:
        user, answer = reply_prompt(item), item.target_reply
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if target:
        messages.append({"role": "assistant", "content": answer})
    return messages


def _items(config: TuneConfig, split: str) -> list:
    loader = triage_items if config.task == "a" else reply_items
    return loader(config.data_folder, split)


def train_subset(config: TuneConfig) -> list:
    """The first n of a seeded shuffle of train: nested across sizes for the same seed."""
    train = _items(config, "train")
    if config.train_size > len(train):
        raise JobError(f"train_size {config.train_size} is more than the {len(train)} items")
    order = list(train)
    random.Random(config.subset_seed).shuffle(order)
    return order[: config.train_size]


def message_tokens(messages: list[dict]) -> int:
    return sum(chat_tokens(m["content"]) + TEMPLATE_TOKENS_PER_MESSAGE for m in messages)


def validate_rows(rows: list[dict], config: TuneConfig, definitions: Definitions) -> list[str]:
    """Problems that would make a training file fail or teach the wrong thing."""
    problems = []
    for n, row in enumerate(rows, start=1):
        roles = [m["role"] for m in row["messages"]]
        if roles != ["system", "user", "assistant"]:
            problems.append(f"row {n}: roles are {roles}")
            continue
        if any(not m["content"].strip() for m in row["messages"]):
            problems.append(f"row {n}: an empty message")
        if (
            config.task == "a"
            and not parse_triage(row["messages"][2]["content"], definitions).valid
        ):
            problems.append(f"row {n}: the target is not a valid triage object")
        if message_tokens(row["messages"]) > config.training.max_length:
            problems.append(f"row {n}: longer than max_length {config.training.max_length}")
    return problems


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(config: TuneConfig) -> dict[str, Any]:
    """Write train.jsonl and eval-<split>.jsonl, and create or refresh the job record's plan.
    A record with attempts keeps them; its plan may change only before the first launch."""
    data = config.data_folder
    definitions = Definitions.load(data / "routes.yaml")
    style_guide = (data / "style-guide.md").read_text(encoding="utf-8")
    system = _system(config, definitions, style_guide)
    folder = config.arm_folder
    rows = [
        {"id": i.id, "messages": _messages(i, system, target=True)} for i in train_subset(config)
    ]
    problems = validate_rows(rows, config, definitions)
    if problems:
        raise JobError("training rows failed validation:\n" + "\n".join(problems[:20]))
    write_jsonl(folder / "train.jsonl", rows)
    evals = {}
    for split in config.eval_splits:
        path = folder / f"eval-{split}.jsonl"
        items = _items(config, split)
        write_jsonl(
            path, [{"id": i.id, "messages": _messages(i, system, target=False)} for i in items]
        )
        evals[split] = {"items": len(items), "sha256": sha256(path)}
    per_example = [message_tokens(r["messages"]) for r in rows]
    plan = {
        "job_id": config.job_id,
        "episode": config.episode,
        "arm": config.arm,
        "task": config.task,
        "base_model": config.base_model,
        "base_revision": config.base_revision,
        "instructions": config.instructions,
        "lora": config.lora.model_dump(),
        "training": config.training.model_dump(),
        "max_new_tokens": config.max_new_tokens,
        "train": {
            "examples": len(rows),
            "subset_seed": config.subset_seed,
            "sha256": sha256(folder / "train.jsonl"),
        },
        "eval": evals,
        "training_tokens_estimate": {
            "mean_per_example": round(sum(per_example) / len(rows), 1) if rows else 0,
            "per_epoch": sum(per_example),
            "epochs": config.training.epochs if rows else 0,
            "total": sum(per_example) * (config.training.epochs if rows else 0),
            "tokeniser": TOKENISER_NOTE,
        },
    }
    record = load_record(folder)
    if record and record["attempts"] and record["plan"] != plan:
        raise JobError(
            f"{config.job_id} has been launched; its plan cannot change. Use a new arm name."
        )
    record = {"plan": plan, "attempts": record["attempts"] if record else []}
    save_record(folder, record)
    return record


def load_record(folder: Path) -> dict | None:
    path = folder / "job.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_record(folder: Path, record: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    (folder / "job.json").write_text(text, encoding="utf-8", newline="\n")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def launch(folder: Path, approved_by: str, *, retry_approved: bool = False) -> dict:
    """Record a launch. The notebook is then run with this folder's files."""
    record = load_record(folder)
    if record is None:
        raise JobError("prepare the job first: lab adapt tune <config.yaml>")
    if not approved_by.strip():
        raise JobError("say who approved the launch, and when")
    attempts = record["attempts"]
    last = attempts[-1]["status"] if attempts else None
    if last == OPEN:
        raise JobError("an attempt is still open: record its result before launching again")
    if last == "succeeded":
        raise JobError("this job has succeeded; a new run needs a new arm name")
    if last is not None and not retry_approved:
        raise JobError(f"the last attempt {last}; a retry needs --retry-approved")
    attempt = {
        "attempt": len(attempts) + 1,
        "status": OPEN,
        "launched_utc": _now(),
        "approved_by": approved_by,
        "plan_sha256": hashlib.sha256(
            json.dumps(record["plan"], sort_keys=True).encode()
        ).hexdigest(),
    }
    updated = {**record, "attempts": [*attempts, attempt]}
    save_record(folder, updated)
    return updated


RESULT_FIELDS = ("job_id", "attempt", "status")


def record_result(folder: Path, result_path: Path) -> dict:
    """Fill in the open attempt from the notebook's job_result.json, and copy its predictions
    (predictions-<split>.jsonl, next to the result file) into the arm's folder."""
    record = load_record(folder)
    if record is None or not record["attempts"]:
        raise JobError("no launched attempt to record a result for")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    missing = [f for f in RESULT_FIELDS if f not in result]
    if missing:
        raise JobError(f"the result file lacks {', '.join(missing)}")
    open_attempt = record["attempts"][-1]
    if result["job_id"] != record["plan"]["job_id"]:
        raise JobError(f"the result is for {result['job_id']}, not {record['plan']['job_id']}")
    if open_attempt["status"] != OPEN or result["attempt"] != open_attempt["attempt"]:
        raise JobError(f"attempt {result['attempt']} is not the open attempt")
    if result["status"] not in ("succeeded", "failed", "cancelled"):
        raise JobError(f"unknown status {result['status']!r}")
    copied = {}
    for split in record["plan"]["eval"]:
        source = result_path.parent / f"predictions-{split}.jsonl"
        if result["status"] == "succeeded" and source.exists():
            rows = read_jsonl(source)
            write_jsonl(folder / f"predictions-{split}.jsonl", rows)
            copied[split] = len(rows)
    done = {**open_attempt, **result, "recorded_utc": _now(), "predictions_copied": copied}
    updated = {**record, "attempts": [*record["attempts"][:-1], done]}
    save_record(folder, updated)
    return updated


def find_job(root: Path, job_id: str) -> Path:
    """The arm folder whose job record has this id."""
    for path in sorted(root.rglob("job.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("plan", {}).get("job_id") == job_id:
            return path.parent
    raise JobError(f"no job {job_id} under {root}")
