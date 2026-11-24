"""Write the exact prompts E5's tuned model was given on Colab, for the laptop run. No calls.

The file must hash to the eval-test.jsonl recorded in E5's job, so both machines read the same
prompts.

    uv run python episodes/s4-e11-where-your-tuned-model-runs/prepare.py
"""

import hashlib
from pathlib import Path

from lab.adapt.tune import _files, load_record
from lab.adapt.tune_config import TuneConfig

HERE = Path(__file__).parent
E5 = HERE.parent / "s4-e5-does-fine-tuning-beat-a-good-prompt"


def main() -> None:
    job = TuneConfig.load(E5 / "tune-short.yaml")
    files, _ = _files(job)
    text = files["eval-test.jsonl"]
    record = load_record(job.arm_folder)
    assert record is not None
    expected = record["plan"]["eval"]["test"]["sha256"]
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != expected:
        raise SystemExit("the prompts differ from the ones E5's job recorded")
    (HERE / "data" / "eval-test.jsonl").write_bytes(text.encode("utf-8"))
    print(f"Wrote data/eval-test.jsonl, sha256 {expected}")


if __name__ == "__main__":
    main()
