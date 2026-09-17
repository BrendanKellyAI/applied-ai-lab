"""Loading experiment-specific code from a field note folder."""

import hashlib
import importlib.util
from collections.abc import Callable
from pathlib import Path

from lab.config import ConfigError, ExperimentConfig
from lab.plan import PlannedCall

PlanFunction = Callable[[ExperimentConfig, Path], list[PlannedCall]]

DATASET_MODULE = "build_dataset.py"
PLAN_FUNCTION = "plan_calls"


def _load_module(path: Path) -> object:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"lab_field_note_{digest}", path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_plan_function(config_path: Path) -> PlanFunction:
    """The field note's `plan_calls(config, folder)`, defined in its build_dataset.py."""
    module_path = config_path.parent / DATASET_MODULE
    if not module_path.exists():
        raise ConfigError(
            f"{module_path} not found. Each field note needs {DATASET_MODULE} defining "
            f"{PLAN_FUNCTION}(config, folder)."
        )
    plan = getattr(_load_module(module_path), PLAN_FUNCTION, None)
    if not callable(plan):
        raise ConfigError(f"{module_path} must define {PLAN_FUNCTION}(config, folder)")
    return plan


def results_dir(config_path: Path) -> Path:
    return config_path.parent / "results"
