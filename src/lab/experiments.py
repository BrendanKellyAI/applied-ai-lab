"""Loading experiment-specific code from a field note folder."""

import hashlib
import importlib.util
from collections.abc import Callable, Sequence
from pathlib import Path

from lab.config import ConfigError, ExperimentConfig
from lab.metadata import DatasetSource
from lab.plan import PlannedCall
from lab.raw_log import RunRecord

PlanFunction = Callable[[ExperimentConfig, Path], list[PlannedCall]]
# analyse(config, folder, records) -> text to print. It writes summary.csv and charts itself.
AnalyseFunction = Callable[[ExperimentConfig, Path, Sequence[RunRecord]], str]

DatasetSourcesFunction = Callable[[ExperimentConfig, Path], list[DatasetSource]]

DATASET_MODULE = "build_dataset.py"
PLAN_FUNCTION = "plan_calls"
SOURCES_FUNCTION = "dataset_sources"
ANALYSE_MODULE = "analyse.py"
ANALYSE_FUNCTION = "analyse"


def _load_module(path: Path) -> object:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"lab_field_note_{digest}", path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_callable(config_path: Path, module_name: str, function: str, signature: str) -> object:
    module_path = config_path.parent / module_name
    if not module_path.exists():
        raise ConfigError(
            f"{module_path} not found. Each field note needs {module_name} defining "
            f"{function}{signature}."
        )
    found = getattr(_load_module(module_path), function, None)
    if not callable(found):
        raise ConfigError(f"{module_path} must define {function}{signature}")
    return found


def load_plan_function(config_path: Path) -> PlanFunction:
    """The field note's `plan_calls(config, folder)`, defined in its build_dataset.py."""
    return _load_callable(config_path, DATASET_MODULE, PLAN_FUNCTION, "(config, folder)")


def dataset_sources(config_path: Path) -> DatasetSourcesFunction:
    """The field note's optional `dataset_sources(config, folder)`, for run metadata.

    A field note with no dataset of its own does not have to define it.
    """
    found = getattr(_load_module(config_path.parent / DATASET_MODULE), SOURCES_FUNCTION, None)
    if not callable(found):
        return lambda config, folder: []
    return found


def load_analyse_function(config_path: Path) -> AnalyseFunction:
    """The field note's `analyse(config, folder, records)`, defined in its analyse.py."""
    return _load_callable(
        config_path, ANALYSE_MODULE, ANALYSE_FUNCTION, "(config, folder, records)"
    )


def results_dir(config_path: Path) -> Path:
    return config_path.parent / "results"
