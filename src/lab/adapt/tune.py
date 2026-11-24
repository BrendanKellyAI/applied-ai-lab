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
from lab.adapt.facts import FACTS_SHORT, Pair, closed_book_user, load_pairs
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
from lab.rag.corpus import Item, load_items
from lab.rag.estimate import chat_tokens

TEMPLATE_TOKENS_PER_MESSAGE = 4
OPEN = "launched"
TOKENISER_NOTE = (
    "tiktoken o200k_base plus 4 tokens a message, a stand-in for Qwen's tokeniser; the "
    "notebook records Qwen's own count"
)


class JobError(ValueError):
    """A tuning job that cannot be prepared, launched or recorded as asked."""


def _definitions(config: TuneConfig) -> Definitions | None:
    return Definitions.load(config.data_folder / "routes.yaml") if config.task == "a" else None


def _system(config: TuneConfig, definitions: Definitions | None) -> str:
    if config.task == "a":
        assert definitions is not None
        return triage_system(config.instructions, definitions)
    if config.task == "facts":
        return FACTS_SHORT
    if config.task == "eval":
        # E10: each prompt set carries its own messages; there is no training row.
        return ""
    style_guide = (config.data_folder / "style-guide.md").read_text(encoding="utf-8")
    return reply_system(config.instructions, style_guide)


def _messages(
    item: TriageItem | ReplyItem | Pair | Item, system: str, *, target: bool
) -> list[dict]:
    if isinstance(item, TriageItem):
        user, answer = triage_prompt(item), label_json(item.label)
    elif isinstance(item, ReplyItem):
        user, answer = reply_prompt(item), item.target_reply
    elif isinstance(item, Pair):
        user, answer = item.question, item.answer
    else:
        user, answer = closed_book_user(item), item.answer
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if target:
        messages.append({"role": "assistant", "content": answer})
    return messages


def _eval_rows(path: Path) -> list[dict]:
    """E10: a prompt set, each row an id and the messages to send (no assistant message)."""
    rows = read_jsonl(path)
    for n, row in enumerate(rows, start=1):
        roles = [m["role"] for m in row.get("messages", [])]
        if not row.get("id") or not roles or roles[-1] != "user" or "assistant" in roles:
            raise JobError(f"{path.name} row {n}: needs an id and messages ending with the user")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise JobError(f"{path.name}: ids repeat")
    return [{"id": r["id"], "messages": r["messages"]} for r in rows]


def _items(config: TuneConfig, split: str) -> list:
    if config.task == "eval":
        return []
    if config.task == "facts":
        # Train is the generated pairs; dev and test are the Halvard library's questions.
        if split == "train":
            assert config.pairs_path is not None
            return load_pairs(config.pairs_path)
        return list(load_items(config.data_folder / f"{split}.jsonl"))
    loader = triage_items if config.task == "a" else reply_items
    items = loader(config.data_folder, split)
    if split == "train" and config.teacher_path is not None:
        return teacher_labelled(items, config)[0]
    return items


def teacher_labelled(items: list, config: TuneConfig) -> tuple[list, list[str]]:
    """E9: the items with the teacher's labels in place of the true ones, and the ids left out
    because the teacher's reply is missing or not a valid label."""
    assert config.teacher_path is not None
    replies = {r["id"]: r.get("text") for r in read_jsonl(config.teacher_path)}
    definitions = Definitions.load(config.data_folder / "routes.yaml")
    kept, dropped = [], []
    for item in items:
        parsed = parse_triage(replies.get(item.id), definitions)
        if parsed.valid and parsed.label is not None:
            kept.append(item.model_copy(update={"label": parsed.label}))
        else:
            dropped.append(item.id)
    return kept, dropped


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


def validate_rows(
    rows: list[dict], config: TuneConfig, definitions: Definitions | None
) -> list[str]:
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
            and definitions is not None
            and not parse_triage(row["messages"][2]["content"], definitions).valid
        ):
            problems.append(f"row {n}: the target is not a valid triage object")
        if message_tokens(row["messages"]) > config.training.max_length:
            problems.append(f"row {n}: longer than max_length {config.training.max_length}")
    return problems


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def _text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _files(config: TuneConfig) -> tuple[dict[str, str], list[dict]]:
    """The job's files, as text, and the training rows. Nothing is written."""
    definitions = _definitions(config)
    system = _system(config, definitions)
    rows = [
        {"id": i.id, "messages": _messages(i, system, target=True)} for i in train_subset(config)
    ]
    problems = validate_rows(rows, config, definitions)
    if problems:
        raise JobError("training rows failed validation:\n" + "\n".join(problems[:20]))
    files = {"train.jsonl": _jsonl(rows)}
    for name, path in (config.eval_sets or {}).items():
        files[f"eval-{name}.jsonl"] = _jsonl(_eval_rows(config.resolve(path)))
    for split in config.eval_splits:
        items = _items(config, split)
        files[f"eval-{split}.jsonl"] = _jsonl(
            [{"id": i.id, "messages": _messages(i, system, target=False)} for i in items]
        )
    return files, rows


def _eval_names(config: TuneConfig) -> list[str]:
    return [*(config.eval_sets or {}), *config.eval_splits]


def _adapter_record(config: TuneConfig) -> dict[str, Any]:
    """E10: the saved adapter to load, from its job's record: the Drive folder the notebook
    wrote it to and its hash, so a different adapter cannot be loaded by mistake."""
    if config.adapter_from is None:
        return {}
    source = load_record(config.resolve(config.adapter_from))
    done = [a for a in (source or {}).get("attempts", []) if a["status"] == "succeeded"]
    if source is None or not done or "training" not in done[-1].get("result", {}):
        raise JobError(f"{config.adapter_from} has no succeeded tuning attempt to load")
    attempt = done[-1]
    if (source["plan"]["base_model"], source["plan"]["base_revision"]) != (
        config.base_model,
        config.base_revision,
    ):
        raise JobError("the adapter was trained on a different base model or revision")
    return {
        "adapter_from": {
            "job_id": source["plan"]["job_id"],
            "folder": f"{source['plan']['arm']}/adapter-{attempt['attempt']}",
            "sha256": attempt["result"]["training"]["adapter_sha256"],
        }
    }


def _pairs_record(config: TuneConfig) -> dict[str, Any]:
    """Where the training targets come from, when not the true labels: E8's pairs file, or
    E9's teacher predictions. Absent otherwise, so earlier job records are unchanged."""
    if config.pairs_path is not None:
        return {"pairs": {"file": config.pairs_path.name, "sha256": sha256(config.pairs_path)}}
    if config.teacher_path is not None:
        items = triage_items(config.data_folder, "train")
        dropped = teacher_labelled(items, config)[1]
        return {
            "teacher": {
                "file": config.teacher_path.name,
                "sha256": sha256(config.teacher_path),
                "dropped": len(dropped),
            }
        }
    return {}


def _plan(config: TuneConfig, files: dict[str, str], rows: list[dict]) -> dict[str, Any]:
    per_example = [message_tokens(r["messages"]) for r in rows]
    epochs = config.training.epochs if rows else 0
    return {
        "job_id": config.job_id,
        "episode": config.episode,
        "arm": config.arm,
        "task": config.task,
        "base_model": config.base_model,
        "base_revision": config.base_revision,
        "instructions": config.instructions,
        "lora": config.lora.model_dump(mode="json"),
        "training": config.training.model_dump(mode="json"),
        "max_new_tokens": config.max_new_tokens,
        "train": {
            "examples": len(rows),
            "subset_seed": config.subset_seed,
            "sha256": _text_sha(files["train.jsonl"]),
        },
        "eval": {
            split: {
                "items": files[f"eval-{split}.jsonl"].count("\n"),
                "sha256": _text_sha(files[f"eval-{split}.jsonl"]),
            }
            for split in _eval_names(config)
        },
        **_pairs_record(config),
        **_adapter_record(config),
        "training_tokens_estimate": {
            "mean_per_example": round(sum(per_example) / len(rows), 1) if rows else 0,
            "per_epoch": sum(per_example),
            "epochs": epochs,
            "total": sum(per_example) * epochs,
            "tokeniser": TOKENISER_NOTE,
        },
    }


def prepare(config: TuneConfig) -> dict[str, Any]:
    """Write train.jsonl and eval-<split>.jsonl and the job record's plan. Once a job has been
    launched, nothing is written: its plan and files are fixed, and a change needs a new arm."""
    files, rows = _files(config)
    # Compared in its JSON form, as the record stores it.
    plan = json.loads(json.dumps(_plan(config, files, rows)))
    folder = config.arm_folder
    record = load_record(folder)
    if record and record["attempts"]:
        if record["plan"] != plan:
            raise JobError(
                f"{config.job_id} has been launched; its plan cannot change. Use a new arm name."
            )
        return record
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8", newline="\n")
    record = {"plan": plan, "attempts": []}
    save_record(folder, record)
    return record


def check_files(folder: Path, plan: dict) -> None:
    """Refuse when a file on disk is not the one the plan records."""
    expected = {"train.jsonl": plan["train"]["sha256"]}
    expected |= {f"eval-{split}.jsonl": info["sha256"] for split, info in plan["eval"].items()}
    for name, digest in expected.items():
        path = folder / name
        if not path.exists() or sha256(path) != digest:
            raise JobError(f"{name} is missing or differs from the job record; prepare it again")


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
    check_files(folder, record["plan"])
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
OUTCOMES = ("succeeded", "failed", "cancelled")


def _open_attempt(record: dict | None) -> dict:
    if record is None or not record["attempts"] or record["attempts"][-1]["status"] != OPEN:
        raise JobError("no launched attempt to record a result for")
    return record["attempts"][-1]


def _close(folder: Path, record: dict, closed: dict) -> dict:
    updated = {**record, "attempts": [*record["attempts"][:-1], closed]}
    save_record(folder, updated)
    return updated


def _checked_predictions(folder: Path, record: dict, source: Path) -> dict[str, dict]:
    """Every eval split's predictions, present and covering exactly the split's items."""
    found = {}
    for split in record["plan"]["eval"]:
        path = source / f"predictions-{split}.jsonl"
        if not path.exists():
            raise JobError(f"a succeeded result needs predictions-{split}.jsonl")
        expected = {row["id"] for row in read_jsonl(folder / f"eval-{split}.jsonl")}
        rows = read_jsonl(path)
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)) or set(ids) != expected:
            raise JobError(f"predictions-{split}.jsonl does not cover the {split} items once each")
        found[split] = {"rows": rows, "sha256": sha256(path)}
    return found


def record_result(folder: Path, result_path: Path) -> dict:
    """Close the open attempt with the notebook's job_result.json. The attempt keeps its launch
    fields and the notebook's file goes under "result". A succeeded result must bring complete
    predictions (predictions-<split>.jsonl, next to the result file), which are copied in."""
    record = load_record(folder)
    open_attempt = _open_attempt(record)
    assert record is not None
    result = json.loads(result_path.read_text(encoding="utf-8"))
    missing = [f for f in RESULT_FIELDS if f not in result]
    if missing:
        raise JobError(f"the result file lacks {', '.join(missing)}")
    if result["job_id"] != record["plan"]["job_id"]:
        raise JobError(f"the result is for {result['job_id']}, not {record['plan']['job_id']}")
    if result["attempt"] != open_attempt["attempt"]:
        raise JobError(f"attempt {result['attempt']} is not the open attempt")
    if result["status"] not in OUTCOMES:
        raise JobError(f"unknown status {result['status']!r}")
    predictions = {}
    if result["status"] == "succeeded":
        for split, found in _checked_predictions(folder, record, result_path.parent).items():
            write_jsonl(folder / f"predictions-{split}.jsonl", found["rows"])
            predictions[split] = {"items": len(found["rows"]), "sha256": found["sha256"]}
    closed = {
        **open_attempt,
        "status": result["status"],
        "recorded_utc": _now(),
        "predictions": predictions,
        "result": result,
    }
    return _close(folder, record, closed)


def cancel(folder: Path, approved_by: str, reason: str) -> dict:
    """Close an open attempt that left no result file (a disconnect, or a failure before the
    notebook could write one), as cancelled. It is never retried without approval."""
    if not approved_by.strip() or not reason.strip():
        raise JobError("say who approved closing the attempt, and why")
    record = load_record(folder)
    open_attempt = _open_attempt(record)
    assert record is not None
    closed = {
        **open_attempt,
        "status": "cancelled",
        "recorded_utc": _now(),
        "cancelled_by": approved_by,
        "reason": reason,
    }
    return _close(folder, record, closed)


def find_job(root: Path, job_id: str) -> Path:
    """The arm folder whose job record has this id."""
    for path in sorted(root.rglob("job.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("plan", {}).get("job_id") == job_id:
            return path.parent
    raise JobError(f"no job {job_id} under {root}")
