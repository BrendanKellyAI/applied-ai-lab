"""The Colab notebook that tunes and runs the open model (season4/colab/lora_job.ipynb).

The notebook is generated from this module, so the committed file can be checked by a test:
it must match what this module writes, and every code cell must parse. It cannot be run here
(this laptop has no GPU); the E5 pilot is its first real run.

What it does, for one prepared arm folder (lab adapt tune):
  1. refuses to run unless job.json has an open launched attempt and the files match its hashes
  2. adapter (LoRA) tuning on train.jsonl, unless the job has no training examples; or, for an
     eval job (v2, E10), loading an earlier job's adapter from Drive after checking its hash
  3. greedy predictions on each eval file, thinking off, in batches of up to EVAL_BATCH; from
     v3 a batch also keeps its size times (longest prompt + new tokens) squared under
     EVAL_ATTENTION_BUDGET, so long prompts (E10's declines, with retrieved passages) run in
     smaller batches instead of running out of GPU memory. Short prompts batch as before.
  4. job_result.json with the outcome, which lab adapt status records; a failure is written
     too, and nothing is retried
"""

import json
from pathlib import Path

NOTEBOOK_VERSION = "s4-lora-job-v3"
# Pinned so a rerun installs the same code. Torch is Colab's own; its version is recorded.
PACKAGES = ("transformers==4.57.1", "peft==0.17.1", "accelerate==1.10.1")

INTRO = f"""# Season 4 tuning job ({NOTEBOOK_VERSION})

Tunes one small open model with an adapter (LoRA) and writes its predictions, for one arm
folder prepared by `lab adapt tune`. Everything in the data is invented (Halvard Home).

**Before running:** the launch must be recorded (`lab adapt tune <config> --launch
--approved-by ...`), and the arm folder (`job.json`, `train.jsonl`, `eval-*.jsonl`) copied to
Google Drive. Set `JOB_DIR` below, choose a GPU runtime, and run all cells.

**After running:** download `job_result.json` and the `predictions-*.jsonl` files and record
them with `lab adapt status <job-id> --result job_result.json`. A failed run writes its result
too. If the runtime died before any result was written, close the attempt with `lab adapt
status <job-id> --cancel --approved-by ... --reason ...`. Do not rerun a failed job without
approval: training is not cached like a response. Run each job in a fresh runtime.

Adapters stay on Drive and are never committed; their hash is recorded."""

SETTINGS = """JOB_DIR = "/content/drive/MyDrive/s4-jobs/ARM-FOLDER"  # the prepared arm folder
MOUNT_DRIVE = True
EVAL_BATCH = 16
# A batch's size times (longest prompt + new tokens) squared stays under this, so long prompts
# run in smaller batches; a prompt over it runs alone (v3, after E10's first job ran out of memory).
EVAL_ATTENTION_BUDGET = 40_000_000"""

INSTALL = "%pip install -q " + " ".join(f'"{p}"' for p in PACKAGES)

SETUP = f"""import hashlib
import json
import platform
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

import torch

if MOUNT_DRIVE:
    from google.colab import drive

    drive.mount("/content/drive")

NOTEBOOK_VERSION = "{NOTEBOOK_VERSION}"
job_dir = Path(JOB_DIR)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path, rows):
    text = "".join(json.dumps(r, ensure_ascii=False) + "\\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def open_attempt(record):
    attempts = record["attempts"]
    if not attempts or attempts[-1]["status"] != "launched":
        raise RuntimeError("no launched attempt in job.json: record the launch first")
    return attempts[-1]["attempt"]


def check_files(plan):
    if plan["train"]["examples"] and sha256(job_dir / "train.jsonl") != plan["train"]["sha256"]:
        raise RuntimeError("train.jsonl does not match the job record")
    for split, info in plan["eval"].items():
        if sha256(job_dir / f"eval-{{split}}.jsonl") != info["sha256"]:
            raise RuntimeError(f"eval-{{split}}.jsonl does not match the job record")


record = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
plan = record["plan"]
# With no open attempt there is nothing to run. Any later failure is written to
# job_result.json by the last cell.
attempt = open_attempt(record)
print(plan["job_id"], "attempt", attempt)"""

MODEL = """from huggingface_hub import model_info
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = None


def load_model():
    global tokenizer
    sha = model_info(plan["base_model"], revision=plan["base_revision"]).sha
    tokenizer = AutoTokenizer.from_pretrained(plan["base_model"], revision=sha)
    tokenizer.padding_side = "left"
    base = AutoModelForCausalLM.from_pretrained(
        plan["base_model"], revision=sha, torch_dtype=torch.float32
    ).to("cuda")
    return base, sha


def load_adapter(base, source):
    # E10: an earlier job's adapter, from its arm folder on Drive, checked against its record.
    from peft import PeftModel

    folder = job_dir.parent / source["folder"]
    if sha256(folder / "adapter_model.safetensors") != source["sha256"]:
        raise RuntimeError(f"{source['folder']} does not match its job record")
    return PeftModel.from_pretrained(base, str(folder))


def prompt_text(messages):
    # Thinking off: the template closes an empty think block before the answer.
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )"""

TRAIN = """from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments, set_seed


def encode(row):
    prompt = prompt_text(row["messages"][:2])
    target = row["messages"][2]["content"] + tokenizer.eos_token + "\\n"
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    target_ids = tokenizer(target, add_special_tokens=False)["input_ids"]
    return {"input_ids": prompt_ids + target_ids, "labels": [-100] * len(prompt_ids) + target_ids}


def collate(batch):
    # Right padding in training, so each row's positions start at 0; generation pads left.
    width = max(len(b["input_ids"]) for b in batch)
    pad = tokenizer.pad_token_id
    ids = [b["input_ids"] + [pad] * (width - len(b["input_ids"])) for b in batch]
    labels = [b["labels"] + [-100] * (width - len(b["labels"])) for b in batch]
    mask = [[1] * len(b["input_ids"]) + [0] * (width - len(b["input_ids"])) for b in batch]
    return {
        "input_ids": torch.tensor(ids),
        "labels": torch.tensor(labels),
        "attention_mask": torch.tensor(mask),
    }


def train(base, plan):
    settings, lora = plan["training"], plan["lora"]
    set_seed(settings["seed"])
    rows = read_jsonl(job_dir / "train.jsonl")
    data = [encode(r) for r in rows]
    # A cut row would lose its end token and teach the model not to stop: fail instead.
    too_long = [r["id"] for r, d in zip(rows, data, strict=True)
                if len(d["input_ids"]) > settings["max_length"]]
    if too_long:
        raise RuntimeError(f"{len(too_long)} rows exceed max_length, for example {too_long[0]}")
    tuned = get_peft_model(
        base,
        LoraConfig(
            r=lora["r"],
            lora_alpha=lora["alpha"],
            lora_dropout=lora["dropout"],
            target_modules=list(lora["target_modules"]),
            task_type="CAUSAL_LM",
        ),
    )
    checkpoints = job_dir / f"checkpoints-{attempt}"
    args = TrainingArguments(
        output_dir=str(checkpoints),
        num_train_epochs=settings["epochs"],
        learning_rate=settings["learning_rate"],
        per_device_train_batch_size=settings["batch_size"],
        gradient_accumulation_steps=settings["gradient_accumulation"],
        warmup_ratio=settings["warmup_ratio"],
        lr_scheduler_type="cosine",
        logging_steps=20,
        save_strategy="epoch",
        save_total_limit=1,
        seed=settings["seed"],
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        report_to=[],
    )
    trainer = Trainer(model=tuned, args=args, train_dataset=data, data_collator=collate)
    # A run cut off by Colab resumes from its last epoch checkpoint, in the same attempt.
    resume = any(checkpoints.glob("checkpoint-*")) if checkpoints.exists() else False
    output = trainer.train(resume_from_checkpoint=resume or None)
    adapter = job_dir / f"adapter-{attempt}"
    tuned.save_pretrained(str(adapter))
    return tuned, {
        "train_runtime_s": round(output.metrics["train_runtime"], 1),
        "train_loss": round(output.metrics["train_loss"], 4),
        "training_tokens_qwen": sum(len(d["input_ids"]) for d in data) * settings["epochs"],
        "adapter_sha256": sha256(adapter / "adapter_model.safetensors"),
        "resumed": bool(resume),
    }"""

EVAL_BATCHES = """def eval_batches(lengths, max_new_tokens, cap, budget):
    # Consecutive row indices, each batch as long as it can be within the cap and the budget.
    batches, start = [], 0
    while start < len(lengths):
        size = 1
        while start + size < len(lengths) and size < cap:
            widest = max(lengths[start : start + size + 1]) + max_new_tokens
            if (size + 1) * widest**2 > budget:
                break
            size += 1
        batches.append(list(range(start, start + size)))
        start += size
    return batches"""

PREDICT = """def predict(active, split, max_new_tokens):
    rows = read_jsonl(job_dir / f"eval-{split}.jsonl")
    active.eval()
    out, started = [], time.time()
    texts = [prompt_text(r["messages"]) for r in rows]
    lengths = [len(tokenizer(t, add_special_tokens=False)["input_ids"]) for t in texts]
    batches = eval_batches(lengths, max_new_tokens, EVAL_BATCH, EVAL_ATTENTION_BUDGET)
    for indices in batches:
        batch = [rows[i] for i in indices]
        prompts = [texts[i] for i in indices]
        enc = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False)
        enc = enc.to("cuda")
        with torch.no_grad():
            generated = active.generate(
                **enc, max_new_tokens=max_new_tokens, do_sample=False, temperature=None,
                top_p=None, top_k=None, pad_token_id=tokenizer.pad_token_id,
            )
        width = enc["input_ids"].shape[1]
        for row, ids, mask in zip(batch, generated, enc["attention_mask"], strict=True):
            new = ids[width:]
            text = tokenizer.decode(new, skip_special_tokens=True).strip()
            out.append({
                "id": row["id"],
                "text": text,
                "input_tokens": int(mask.sum()),
                "output_tokens": int((new != tokenizer.pad_token_id).sum()),
            })
    write_jsonl(job_dir / f"predictions-{split}.jsonl", out)
    return {"items": len(out), "seconds": round(time.time() - started, 1)}"""

RUN = """import importlib.metadata as metadata

if "result" in globals():
    raise RuntimeError("this session has already run a job: restart the runtime first")
result = {
    "job_id": plan["job_id"],
    "attempt": attempt,
    "notebook_version": NOTEBOOK_VERSION,
    "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    "python": platform.python_version(),
}
try:
    result["packages"] = {
        p: metadata.version(p) for p in ("torch", "transformers", "peft", "accelerate")
    }
    result["gpu"] = torch.cuda.get_device_name(0)
    check_files(plan)
    active, result["base_revision_sha"] = load_model()
    if plan.get("adapter_from"):
        active = load_adapter(active, plan["adapter_from"])
        result["adapter_from"] = plan["adapter_from"]
    elif plan["train"]["examples"]:
        active, training = train(active, plan)
        result["training"] = training
    result["predictions"] = {
        split: predict(active, split, plan["max_new_tokens"]) for split in plan["eval"]
    }
    result["peak_memory_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    result["status"] = "succeeded"
except BaseException as exc:
    # Includes a stop or an interrupt, so an attempt is never left without a result.
    result["status"] = "failed"
    result["error"] = "".join(traceback.format_exception_only(exc)).strip()
    raise
finally:
    result.setdefault("status", "failed")
    result["finished_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    text = json.dumps(result, indent=2) + "\\n"
    (job_dir / "job_result.json").write_text(text, encoding="utf-8")
    print(text)"""

CELLS = (
    ("markdown", INTRO),
    ("code", SETTINGS),
    ("code", INSTALL),
    ("code", SETUP),
    ("code", MODEL),
    ("code", TRAIN),
    ("code", EVAL_BATCHES),
    ("code", PREDICT),
    ("code", RUN),
)


def _cell(kind: str, source: str) -> dict:
    lines = source.splitlines(keepends=True)
    cell: dict = {"cell_type": kind, "metadata": {}, "source": lines}
    if kind == "code":
        cell |= {"execution_count": None, "outputs": []}
    return cell


def notebook() -> dict:
    return {
        "cells": [_cell(kind, source) for kind, source in CELLS],
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def render() -> str:
    return json.dumps(notebook(), indent=1, ensure_ascii=False) + "\n"


def write_notebook(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(), encoding="utf-8", newline="\n")
    return path
