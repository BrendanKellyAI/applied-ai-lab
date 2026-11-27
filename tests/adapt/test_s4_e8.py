"""S4 E8: the configs, jobs and claims match the pre-registration."""

from pathlib import Path

import pytest
import yaml

from lab.adapt.facts_eval import FactsExperiment, PairsConfig
from lab.adapt.tune_config import TuneConfig
from lab.experiments import load_sibling

EPISODES = Path(__file__).parents[2] / "episodes"
E8 = EPISODES / "s4-e8-can-fine-tuning-teach-facts"
E5_SHORT = EPISODES / "s4-e5-does-fine-tuning-beat-a-good-prompt" / "tune-short.yaml"
claims = load_sibling(E8 / "claims.py")


def test_pairs_config_is_the_cheapest_generator_at_four_a_passage():
    spec = PairsConfig.load(E8 / "pairs.yaml")
    assert spec.generator.model == "gemini-3.1-flash-lite" and spec.per_passage == 4
    assert spec.out_path == E8 / "pairs" / "pairs.jsonl"
    assert (spec.data_folder / "manifest.json").exists()


def test_base_job_is_eval_only_with_e5s_settings():
    job = TuneConfig.load(E8 / "tune-base.yaml")
    e5 = TuneConfig.load(E5_SHORT)
    assert (job.task, job.arm, job.train_size) == ("facts", "e8-base-closed", 0)
    assert (job.base_model, job.base_revision) == (e5.base_model, e5.base_revision)
    assert job.lora == e5.lora and job.training == e5.training
    assert job.eval_splits == ("dev", "test") and job.max_new_tokens == 160


@pytest.mark.parametrize(("name", "split"), [("config.dev.yaml", "dev"), ("config.yaml", "test")])
def test_configs_judge_with_season_twos_judge(name, split):
    experiment = FactsExperiment.load(E8 / name)
    assert experiment.split == split and experiment.judge.model == "gemini-3.6-flash"
    assert len(experiment.items()) == (100 if split == "dev" else 520)
    names = [a.name for a in experiment.arms]
    assert names[:2] == ["e8-base-closed", "e8-tuned-closed"]
    if split == "test":
        reference = experiment.arms[2]
        assert reference.name == experiment.reference == "e8-reference"
        assert reference.s2_judge_log is not None
        assert experiment.path(reference.s2_judge_log).exists()


def test_preregistration_states_every_claim():
    text = (E8 / "PREREGISTRATION.md").read_text(encoding="utf-8")
    spec = yaml.safe_load((E8 / "claims.yaml").read_text(encoding="utf-8"))
    for claim_id, claim in spec["claims"].items():
        assert f"**{claim_id}. {claim['title']}.**" in text
        assert claim["measure"] in claims.MEASURES


def _item(i: int, answerable: bool, correct: bool, declined: bool) -> dict:
    return {"id": f"i{i}", "type": "t", "answerable": answerable, "judged": True,
            "correct": correct, "faithful": False, "declined": declined}  # fmt: skip


def test_claims_on_synthetic_arms():
    spec = claims.load_claims_file()
    knows = [_item(i, True, True, False) for i in range(20)] + [
        _item(100 + i, False, True, True) for i in range(20)
    ]
    guesses = [_item(i, True, False, False) for i in range(20)] + [
        _item(100 + i, False, False, False) for i in range(20)
    ]
    held = {c.id: c.held for c in claims.evaluate(
        {"e8-base-closed": guesses, "e8-tuned-closed": knows, "e8-reference": knows}, spec
    )}  # fmt: skip
    assert held == {"C1": True, "C2": False, "C3": False, "C4": False}
    flipped = {c.id: c for c in claims.evaluate(
        {"e8-base-closed": knows, "e8-tuned-closed": guesses, "e8-reference": knows}, spec
    )}  # fmt: skip
    assert [flipped[k].held for k in ("C1", "C2", "C3", "C4")] == [False, True, True, True]
    assert claims.verdict(flipped["C1"]) == "Failed" and claims.verdict(flipped["C2"]) == "Held"


def test_tuned_job_trains_on_every_kept_pair():
    from lab.adapt.facts import load_pairs
    from lab.adapt.tune import train_subset

    job = TuneConfig.load(E8 / "tune-tuned.yaml")
    base = TuneConfig.load(E8 / "tune-base.yaml")
    assert (job.task, job.arm) == ("facts", "e8-tuned-closed")
    assert job.train_size == len(load_pairs(E8 / "pairs" / "pairs.jsonl")) == 1724
    assert len(train_subset(job)) == 1724
    ignore = {"arm", "train_size"}
    assert job.model_dump(exclude=ignore) == base.model_dump(exclude=ignore)
