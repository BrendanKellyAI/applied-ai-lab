"""S4 E11: run E5's tuned triage model on this laptop's CPU, the way the Colab notebook ran it.

The same base model at the same commit, the same adapter (checked by hash against E5's job
record), the same prompts (data/eval-test.jsonl), float32, greedy decoding, thinking off, the
same prompt template and left padding. Only the machine differs.

It runs in its own environment, with the package versions the Colab job recorded, so the
project's dependencies are untouched:

    uv run --no-project --python 3.12 --with "torch>=2.14,<2.15" --with transformers==4.57.1 \
        --with peft==0.17.1 --with accelerate==1.10.1 --with psutil \
        episodes/s4-e11-where-your-tuned-model-runs/run_local.py --adapter <folder> --limit 50

It writes results/<name>/predictions-test.jsonl and results/<name>/local_result.json.
"""

import argparse
import hashlib
import json
import platform
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).parent
E5_JOB = HERE.parent / "s4-e5-does-fine-tuning-beat-a-good-prompt/results/e5-tuned-short/job.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def source_job() -> dict:
    record = json.loads(E5_JOB.read_text(encoding="utf-8"))
    done = [a for a in record["attempts"] if a["status"] == "succeeded"][-1]
    return {
        "base_model": record["plan"]["base_model"],
        "base_revision": record["plan"]["base_revision"],
        "max_new_tokens": record["plan"]["max_new_tokens"],
        "adapter_sha256": done["result"]["training"]["adapter_sha256"],
        "eval_sha256": record["plan"]["eval"]["test"]["sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="laptop")
    args = parser.parse_args()

    import psutil
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    job = source_job()
    eval_path = HERE / "data" / "eval-test.jsonl"
    if sha256(eval_path) != job["eval_sha256"]:
        raise SystemExit("data/eval-test.jsonl differs from the prompts E5's job used")
    if sha256(args.adapter / "adapter_model.safetensors") != job["adapter_sha256"]:
        raise SystemExit("the adapter differs from the one E5's job recorded")

    out = HERE / "results" / args.name
    out.mkdir(parents=True, exist_ok=True)
    process = psutil.Process()
    result = {
        "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": {
            "processor": platform.processor(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "ram_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "torch_threads": torch.get_num_threads(),
            "system": platform.platform(),
        },
        "packages": {p: metadata.version(p) for p in ("torch", "transformers", "peft")},
        "batch": args.batch,
        "limit": args.limit,
    }
    started = time.time()
    tokenizer = AutoTokenizer.from_pretrained(job["base_model"], revision=job["base_revision"])
    tokenizer.padding_side = "left"
    base = AutoModelForCausalLM.from_pretrained(
        job["base_model"], revision=job["base_revision"], torch_dtype=torch.float32
    )
    model = PeftModel.from_pretrained(base, str(args.adapter))
    model.eval()
    result["load_seconds"] = round(time.time() - started, 1)

    rows = read_jsonl(eval_path)[: args.limit]
    predictions, peak = [], process.memory_info().rss
    began = time.time()
    for start in range(0, len(rows), args.batch):
        batch = rows[start : start + args.batch]
        prompts = [
            tokenizer.apply_chat_template(
                r["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
            for r in batch
        ]
        enc = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False)
        with torch.no_grad():
            generated = model.generate(
                **enc, max_new_tokens=job["max_new_tokens"], do_sample=False, temperature=None,
                top_p=None, top_k=None, pad_token_id=tokenizer.pad_token_id,
            )  # fmt: skip
        width = enc["input_ids"].shape[1]
        for row, ids in zip(batch, generated, strict=True):
            text = tokenizer.decode(ids[width:], skip_special_tokens=True).strip()
            predictions.append({"id": row["id"], "text": text})
        peak = max(peak, process.memory_info().rss)
        print(f"{len(predictions)} of {len(rows)}, {time.time() - began:.0f} s", flush=True)
    seconds = time.time() - began
    text = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in predictions)
    (out / "predictions-test.jsonl").write_bytes(text.encode("utf-8"))
    result |= {
        "items": len(predictions),
        "seconds": round(seconds, 1),
        "seconds_per_1000": round(seconds / len(predictions) * 1000, 1),
        "peak_ram_gb": round(peak / 1e9, 2),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out / "local_result.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
