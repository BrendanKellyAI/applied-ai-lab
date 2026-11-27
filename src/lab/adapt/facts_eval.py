"""S4 E8: generate the training pairs, judge the closed-book answers, and score every arm.

Answers are judged by Season 2's judge, with its fixed instructions, shown no passages: a
closed-book model was given none. Season 2 counted an answer right only when it was correct
and faithful to its passages; a closed-book answer has no passages to be faithful to, so E8
counts the judge's `correct` alone, for every arm, the Season 2 reference included. Season 2's
own measure is reported alongside for the reference.

The reference arm makes no call: its verdicts are read from Season 2's run log.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lab.adapt.build_tasks.config import Split
from lab.adapt.build_tasks.estimate import StageCost, stage_cost
from lab.adapt.facts import pair_requests, training_passages
from lab.adapt.run import read_texts, write_jsonl
from lab.config import ProviderLimits
from lab.prices import PricesFile
from lab.providers.base import GenerationRequest, GenerationResult
from lab.rag.config import ModelSpec
from lab.rag.corpus import Item, Library, load_items
from lab.rag.estimate import chat_tokens
from lab.rag.judge import JudgeParseError, Verdict, judge_instructions, judge_prompt, parse_verdict
from lab.rag.score import Proportion
from lab.rag.waves import planned, request_for, run_wave
from lab.runner import Runner, RunSummary

EXPECTED_PAIR_TOKENS = 70
EXPECTED_VERDICT_TOKENS = 60


def _resolve(folder: Path, path: Path) -> Path:
    return path if path.is_absolute() else folder / path


class PairsConfig(BaseModel):
    """How the training pairs are made: the generator, and pairs a passage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(min_length=1)
    data: Path
    generator: ModelSpec
    per_passage: int = Field(gt=0)
    out: Path
    limits: dict[str, ProviderLimits] = Field(default_factory=dict)
    folder: Path = Path(".")

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    @property
    def data_folder(self) -> Path:
        return _resolve(self.folder, self.data)

    @property
    def out_path(self) -> Path:
        return _resolve(self.folder, self.out)


class FactsArm(BaseModel):
    """A closed-book model's predictions file, or a Season 2 run log of judge verdicts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    predictions: Path | None = None
    s2_judge_log: Path | None = None
    note: str = ""

    @model_validator(mode="after")
    def _one_source(self) -> Self:
        if (self.predictions is None) == (self.s2_judge_log is None):
            raise ValueError(f"arm {self.name}: give predictions or s2_judge_log, not both")
        return self


class FactsExperiment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str = Field(min_length=1)
    split: Split = "test"
    data: Path
    judge: ModelSpec
    arms: tuple[FactsArm, ...] = Field(min_length=1)
    reference: str
    limits: dict[str, ProviderLimits] = Field(default_factory=dict)
    folder: Path = Path(".")

    @model_validator(mode="after")
    def _reference_is_an_arm(self) -> Self:
        names = [a.name for a in self.arms]
        if len(set(names)) != len(names):
            raise ValueError("arm names must be unique")
        if self.reference not in names:
            raise ValueError(f"reference arm {self.reference!r} is not an arm")
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate({**raw, "folder": path.parent})

    @property
    def results(self) -> Path:
        return self.folder / "results"

    def items(self) -> tuple[Item, ...]:
        return load_items(_resolve(self.folder, self.data) / f"{self.split}.jsonl")

    def path(self, relative: Path) -> Path:
        return _resolve(self.folder, relative)

    def verdicts_path(self, arm: str) -> Path:
        return self.results / arm / f"judge-{self.split}.jsonl"


# Pairs


def estimate_pairs(config: PairsConfig, library: Library, prices: PricesFile | None) -> StageCost:
    requests = pair_requests(
        training_passages(library), config.per_passage, config.generator, config.episode
    )
    inputs = sum(chat_tokens(r.system or "") + chat_tokens(r.prompt) for r in requests.values())
    expected = len(requests) * config.per_passage * EXPECTED_PAIR_TOKENS
    return stage_cost("pairs", config.generator, len(requests), inputs, expected, prices)


def _wave(
    runner: Runner, requests: Mapping[str, GenerationRequest], stage: str, condition: str, raw: Path
) -> tuple[dict[str, GenerationResult], RunSummary]:
    calls = [
        planned(r, stage=stage, item_id=key, condition=condition) for key, r in requests.items()
    ]
    return run_wave(runner, calls, raw)


def run_pairs(
    runner: Runner, config: PairsConfig, library: Library
) -> tuple[dict[str, str | None], RunSummary]:
    passages = training_passages(library)
    requests = pair_requests(passages, config.per_passage, config.generator, config.episode)
    raw = config.out_path.parent / "raw-pairs.jsonl"
    results, summary = _wave(runner, requests, "pairs", "pairs", raw)
    return {key: (results[key].text if key in results else None) for key in requests}, summary


# Judging


def judge_requests(
    experiment: FactsExperiment, items: Sequence[Item], answers: Mapping[str, str]
) -> dict[str, GenerationRequest]:
    """Season 2's judge, shown no passages: the closed-book model was given none."""
    return {
        item.id: request_for(
            experiment.judge,
            system=judge_instructions(),
            prompt=judge_prompt(item, [], answers[item.id]),
            episode=experiment.episode,
            stage="judge",
        )
        for item in items
        if item.id in answers
    }


def estimate_judge(experiment: FactsExperiment, prices: PricesFile | None) -> list[StageCost]:
    items = experiment.items()
    stand_in = {i.id: i.answer for i in items}
    requests = judge_requests(experiment, items, stand_in)
    inputs = sum(chat_tokens(r.system or "") + chat_tokens(r.prompt) for r in requests.values())
    out = []
    for arm in experiment.arms:
        if arm.predictions is None:
            continue
        out.append(
            stage_cost(
                f"judge {arm.name}",
                experiment.judge,
                len(requests),
                inputs,
                len(requests) * EXPECTED_VERDICT_TOKENS,
                prices,
            )
        )
    return out


def run_judge(runner: Runner, experiment: FactsExperiment) -> dict[str, dict]:
    items = experiment.items()
    summaries = {}
    for arm in experiment.arms:
        if arm.predictions is None:
            continue
        answers = read_texts(experiment.path(arm.predictions))
        requests = judge_requests(experiment, items, answers)
        raw = experiment.results / "raw" / f"raw-judge-{arm.name}-{experiment.split}.jsonl"
        results, summary = _wave(runner, requests, f"judge-{arm.name}", arm.name, raw)
        rows = [{"id": key, "text": results[key].text} for key in requests if key in results]
        write_jsonl(experiment.verdicts_path(arm.name), rows)
        summaries[arm.name] = {
            "made": summary.made,
            "cached": summary.cached,
            "failed": summary.failed,
        }
    return summaries


# Scoring


def s2_verdict_texts(log: Path) -> dict[str, str]:
    """The judge's reply per item, from a Season 2 run log (raw-judge.jsonl)."""
    out = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result = row.get("result") or {}
        if result.get("text") is not None:
            out[row["cell"]["item"]] = result["text"]
    return out


def verdict_texts(experiment: FactsExperiment, arm: FactsArm) -> dict[str, str]:
    if arm.s2_judge_log is not None:
        return s2_verdict_texts(experiment.path(arm.s2_judge_log))
    path = experiment.verdicts_path(arm.name)
    return read_texts(path) if path.exists() else {}


def read_verdicts(texts: Mapping[str, str]) -> dict[str, Verdict | None]:
    out: dict[str, Verdict | None] = {}
    for key, text in texts.items():
        try:
            out[key] = parse_verdict(text)
        except JudgeParseError:
            out[key] = None
    return out


class FactsScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    answerable: bool
    judged: bool
    correct: bool
    faithful: bool
    declined: bool

    @property
    def right(self) -> bool:
        return self.answerable and self.correct

    @property
    def declined_right(self) -> bool:
        return not self.answerable and self.declined

    @property
    def confident_wrong(self) -> bool:
        """An answer given, not a decline, that the judge found wrong."""
        return self.judged and not self.declined and not self.correct


def score(items: Sequence[Item], verdicts: Mapping[str, Verdict | None]) -> list[FactsScore]:
    """An item with no verdict, or one the judge's reply cannot be read for, counts as neither
    right nor declined, and is counted as unjudged."""
    out = []
    for item in items:
        v = verdicts.get(item.id)
        out.append(
            FactsScore(
                id=item.id,
                type=item.type,
                answerable=item.answerable,
                judged=v is not None,
                correct=bool(v and v.correct),
                faithful=bool(v and v.faithful),
                declined=bool(v and v.declined),
            )
        )
    return out


def _proportion(count: int, total: int) -> dict:
    return Proportion.of(count, total).model_dump()


def summarise(scores: Sequence[FactsScore]) -> dict:
    answerable = [s for s in scores if s.answerable]
    unanswerable = [s for s in scores if not s.answerable]
    by_type: dict[str, dict] = {}
    for kind in sorted({s.type for s in scores}):
        group = [s for s in scores if s.type == kind]
        by_type[kind] = {
            "items": len(group),
            "right": sum(s.right for s in group),
            "declined": sum(s.declined for s in group),
            "confident_wrong": sum(s.confident_wrong for s in group),
        }
    return {
        "items": len(scores),
        "unjudged": sum(not s.judged for s in scores),
        "right": _proportion(sum(s.right for s in answerable), len(answerable)),
        "right_and_faithful": _proportion(
            sum(s.right and s.faithful for s in answerable), len(answerable)
        ),
        "declined_unanswerable": _proportion(
            sum(s.declined_right for s in unanswerable), len(unanswerable)
        ),
        "declined_answerable": _proportion(sum(s.declined for s in answerable), len(answerable)),
        "confident_wrong": _proportion(sum(s.confident_wrong for s in scores), len(scores)),
        "by_type": by_type,
    }


def analyse(experiment: FactsExperiment) -> dict:
    items = experiment.items()
    arms = {}
    for arm in experiment.arms:
        scores = score(items, read_verdicts(verdict_texts(experiment, arm)))
        arms[arm.name] = {
            "source": "season 2 run log" if arm.s2_judge_log else "closed book, judged here",
            **summarise(scores),
            "per_item": [s.model_dump() for s in scores],
        }
    return {
        "episode": experiment.episode,
        "split": experiment.split,
        "items": len(items),
        "reference": experiment.reference,
        "primary_metric": "right",
        "arms": arms,
    }


def write_analysis(experiment: FactsExperiment, result: dict) -> Path:
    out = experiment.results / f"analysis-facts-{experiment.split}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    return out
