"""S4 E10: judge the decline set and score every check, each tuned model against the base.

General ability is scored by Season 1 E10's own code (its metrics.py, loaded from the field
note), format bleed by code (lab.adapt.regression.bleed_kind), and declines by Season 2's judge
shown the reference's passages. Only the decline set makes calls.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.adapt.build_tasks.estimate import StageCost, stage_cost
from lab.adapt.facts_eval import _wave, read_verdicts
from lab.adapt.regression import (
    REFERENCE_CHUNKER,
    bleed_kind,
    general_items,
    judge_requests_with_passages,
)
from lab.adapt.run import read_texts, write_jsonl
from lab.config import ProviderLimits
from lab.experiments import load_sibling
from lab.prices import PricesFile
from lab.rag.chunk import chunk_library
from lab.rag.compare import paired
from lab.rag.config import ModelSpec
from lab.rag.corpus import load_library
from lab.rag.estimate import chat_tokens
from lab.rag.score import Proportion
from lab.runner import Runner

EXPECTED_VERDICT_TOKENS = 60
SETS = ("general", "bleed", "declines")


class RegressionArm(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    # The eval job's arm folder, holding predictions-<set>.jsonl.
    results: Path
    note: str = ""


class RegressionExperiment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(min_length=1)
    library: Path
    s1_items: Path
    s1_metrics: Path
    s2_log: Path
    judge: ModelSpec
    baseline: str
    arms: tuple[RegressionArm, ...] = Field(min_length=2)
    limits: dict[str, ProviderLimits] = Field(default_factory=dict)
    folder: Path = Path(".")

    @model_validator(mode="after")
    def _baseline_is_an_arm(self) -> Self:
        names = [a.name for a in self.arms]
        if len(set(names)) != len(names) or self.baseline not in names:
            raise ValueError("arm names must be unique and include the baseline")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    def path(self, relative: Path) -> Path:
        return relative if relative.is_absolute() else self.folder / relative

    @property
    def results(self) -> Path:
        return self.folder / "results"

    def predictions(self, arm: RegressionArm, name: str) -> dict[str, str]:
        return read_texts(self.path(arm.results) / f"predictions-{name}.jsonl")

    def verdicts_path(self, arm: str) -> Path:
        return self.results / arm / "judge-declines.jsonl"


def _decline_context(experiment: RegressionExperiment):
    library = load_library(experiment.path(experiment.library))
    items = [i for i in library.test if not i.answerable]
    chunks = {c.chunk_id: c for c in chunk_library(library.documents, REFERENCE_CHUNKER)}
    prompts = {}
    for line in experiment.path(experiment.s2_log).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        prompts[row["item_id"]] = row["prompt_chunks"]
    return items, chunks, prompts


def _requests(experiment: RegressionExperiment, answers: Mapping[str, str]) -> dict:
    items, chunks, prompts = _decline_context(experiment)
    return judge_requests_with_passages(
        experiment.judge, experiment.episode, items, answers, prompts, chunks
    )


def estimate(experiment: RegressionExperiment, prices: PricesFile | None) -> list[StageCost]:
    items, _, _ = _decline_context(experiment)
    stand_in = {i.id: i.answer for i in items}
    requests = _requests(experiment, stand_in)
    inputs = sum(chat_tokens(r.system or "") + chat_tokens(r.prompt) for r in requests.values())
    return [
        stage_cost(
            f"judge {arm.name}",
            experiment.judge,
            len(requests),
            inputs,
            len(requests) * EXPECTED_VERDICT_TOKENS,
            prices,
        )
        for arm in experiment.arms
    ]


def run(runner: Runner, experiment: RegressionExperiment) -> dict[str, dict]:
    summaries = {}
    for arm in experiment.arms:
        requests = _requests(experiment, experiment.predictions(arm, "declines"))
        raw = experiment.results / "raw" / f"raw-judge-{arm.name}.jsonl"
        results, summary = _wave(runner, requests, f"judge-{arm.name}", arm.name, raw)
        rows = [{"id": k, "text": results[k].text} for k in requests if k in results]
        write_jsonl(experiment.verdicts_path(arm.name), rows)
        summaries[arm.name] = {
            "made": summary.made,
            "cached": summary.cached,
            "failed": summary.failed,
        }
    return summaries


def per_item(experiment: RegressionExperiment, arm: RegressionArm) -> dict[str, dict[str, bool]]:
    """For each check, item id to the outcome that counts: general right, bleed found, and
    declined."""
    metrics = load_sibling(experiment.path(experiment.s1_metrics))
    expected = general_items(experiment.path(experiment.s1_items))
    general = experiment.predictions(arm, "general")
    right = {
        key: metrics.score(general.get(key) or "", item["answer"], item["answer_kind"])[0]
        for key, item in expected.items()
    }
    bleed = {k: bleed_kind(t) is not None for k, t in experiment.predictions(arm, "bleed").items()}
    verdicts = read_verdicts(
        read_texts(experiment.verdicts_path(arm.name))
        if experiment.verdicts_path(arm.name).exists()
        else {}
    )
    items, _, _ = _decline_context(experiment)
    declined = {i.id: bool(verdicts.get(i.id) and verdicts[i.id].declined) for i in items}
    return {"general": right, "bleed": bleed, "declines": declined}


def bleed_kinds(experiment: RegressionExperiment, arm: RegressionArm) -> dict[str, int]:
    kinds = [bleed_kind(t) for t in experiment.predictions(arm, "bleed").values()]
    return {k: kinds.count(k) for k in ("triage", "house_reply")}


def analyse(experiment: RegressionExperiment) -> dict:
    outcomes = {arm.name: per_item(experiment, arm) for arm in experiment.arms}
    base = outcomes[experiment.baseline]
    arms = {}
    for arm in experiment.arms:
        checks = {}
        for name in SETS:
            values = outcomes[arm.name][name]
            checks[name] = Proportion.of(sum(values.values()), len(values)).model_dump()
            if arm.name != experiment.baseline:
                pair = paired(values, base[name])
                checks[name] |= {"against_base": pair}
        arms[arm.name] = {
            "checks": checks,
            "bleed_kinds": bleed_kinds(experiment, arm),
            "per_item": outcomes[arm.name],
        }
    return {"episode": experiment.episode, "baseline": experiment.baseline, "arms": arms}


def write_analysis(experiment: RegressionExperiment, result: dict) -> Path:
    out = experiment.results / "analysis-regression.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    return out
