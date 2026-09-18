"""Builds the S1 E10 task items and plans its calls.

Every item is generated from the config seed by `generators.py`, so nothing here needs the
network and nothing is under licence. Unlike S1 E7, the items are **committed** to the
repository, in `tasks/items.jsonl`, because they are wholly ours and readers should be able to
read every question. `tasks/manifest.json` records the seed and a checksum, so a stale file is
rebuilt rather than used.

Run directly to rebuild the items without making any API calls:

    uv run python field-notes/s1-e10-reasoning-vs-standard/build_dataset.py
"""

import hashlib
import json
from functools import cache
from pathlib import Path

from lab.config import ExperimentConfig, load_config
from lab.experiments import load_sibling
from lab.metadata import DatasetSource
from lab.plan import PlanError, PlannedCall, build_request, make_call_id

TASKS_DIR = "tasks"
ITEMS_FILE = "items.jsonl"
MANIFEST_FILE = "manifest.json"

# The two modes every model runs, named in specification section 7.2 as changed by the mode
# naming decision: `lowest` is off where a model allows it and its lowest level where it does
# not, so no chart ever claims "off" for a model that is still thinking.
LOWEST_MODE = "lowest"
HIGH_MODE = "high"
MODES = (LOWEST_MODE, HIGH_MODE)

LICENCE = "Generated from the config seed for this repository. No third-party content."


@cache
def _generators():
    """The sibling generators module, loaded by path because a field note is not a package."""
    return load_sibling(Path(__file__).parent / "generators.py")


def tasks_of(config: ExperimentConfig) -> tuple[str, ...]:
    return tuple(str(task) for task in config.parameters["tasks"])


def items_per_task(config: ExperimentConfig) -> int:
    return int(config.parameters["items_per_task"])


def _items_path(folder: Path) -> Path:
    return folder / TASKS_DIR / ITEMS_FILE


def _manifest_path(folder: Path) -> Path:
    return folder / TASKS_DIR / MANIFEST_FILE


def _lines(items) -> str:
    body = "\n".join(
        json.dumps(item.as_dict(), sort_keys=True, ensure_ascii=False) for item in items
    )
    return body + "\n"


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_items(config: ExperimentConfig, folder: Path):
    """Generate every item and write `tasks/items.jsonl` and its manifest."""
    generators = _generators()
    items = generators.build_items(config.seed, tasks_of(config), items_per_task(config))
    text = _lines(items)
    out = folder / TASKS_DIR
    out.mkdir(parents=True, exist_ok=True)
    _items_path(folder).write_text(text, encoding="utf-8", newline="\n")
    _manifest_path(folder).write_text(
        json.dumps(
            {
                "experiment": config.experiment,
                "seed": config.seed,
                "tasks": list(tasks_of(config)),
                "items_per_task": items_per_task(config),
                "items": len(items),
                "sha256": _checksum(text),
                "licence": LICENCE,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return items


def load_items(config: ExperimentConfig, folder: Path):
    """The committed items, or None when they are missing or no longer match the config.

    A mismatch means the config changed after the items were committed. Returning None makes
    the caller rebuild, so a run can never use questions the config no longer describes.
    """
    items_path, manifest_path = _items_path(folder), _manifest_path(folder)
    if not (items_path.exists() and manifest_path.exists()):
        return None
    text = items_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {
        "seed": config.seed,
        "tasks": list(tasks_of(config)),
        "items_per_task": items_per_task(config),
        "sha256": _checksum(text),
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        return None
    generators = _generators()
    return tuple(
        generators.Item.from_dict(json.loads(line)) for line in text.splitlines() if line.strip()
    )


def read_items(folder: Path):
    """Every committed item, without checking it against a config. Used by the analysis."""
    generators = _generators()
    text = _items_path(folder).read_text(encoding="utf-8")
    return tuple(
        generators.Item.from_dict(json.loads(line)) for line in text.splitlines() if line.strip()
    )


def _check_modes(config: ExperimentConfig) -> None:
    for model in config.models:
        if set(model.modes) != set(MODES):
            raise PlanError(
                f"Model '{model.display_label}' must define exactly the modes "
                f"{', '.join(MODES)}; it defines {', '.join(sorted(model.modes))}. Both modes "
                "are compared against each other, so a missing one would leave a gap in the grid."
            )


def plan_calls(config: ExperimentConfig, folder: Path) -> list[PlannedCall]:
    """Every planned call: one per model, mode, and item.

    The same item is sent to the same model in both modes, which is what makes the comparison
    paired and lets the analysis use a paired confidence interval.
    """
    _check_modes(config)
    items = load_items(config, folder)
    if items is None:
        items = build_items(config, folder)

    calls: list[PlannedCall] = []
    for item in items:
        cell = {"task": item.task, "item_index": item.index}
        for model in config.models:
            for mode in MODES:
                calls.append(
                    PlannedCall(
                        call_id=make_call_id(model_label=model.display_label, mode=mode, cell=cell),
                        model_label=model.display_label,
                        mode=mode,
                        cell=cell,
                        # No system prompt: the reasoning setting is then the only difference
                        # between the two modes, which is the whole point of the design.
                        request=build_request(
                            model,
                            mode,
                            prompt=item.prompt,
                            metadata={"experiment": config.experiment, "task": item.task},
                        ),
                    )
                )
    return calls


def dataset_sources(config: ExperimentConfig, folder: Path) -> list[DatasetSource]:
    """What went into the items, recorded in run_metadata.json."""
    items_path = _items_path(folder)
    checksum = None
    if items_path.exists():
        checksum = f"sha256:{_checksum(items_path.read_text(encoding='utf-8'))}"
    return [
        DatasetSource(
            name="S1 E10 generated task items",
            version=f"seed {config.seed}, {items_per_task(config)} items per task",
            licence=LICENCE,
            url=None,
            checksum=checksum,
        )
    ]


if __name__ == "__main__":
    here = Path(__file__).parent
    built = build_items(load_config(here / "config.yaml"), here)
    print(f"Built {len(built)} items across {len({item.task for item in built})} task families.")
    print(f"Written to {here / TASKS_DIR}")
