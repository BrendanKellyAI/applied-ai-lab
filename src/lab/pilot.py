"""Choosing which planned calls to run: pilot sampling, provider filter, and call order."""

import random
from collections import defaultdict
from collections.abc import Sequence

from lab.config import ExperimentConfig, FilterPilot, PilotConfig, StratifiedPilot
from lab.plan import PlanError, PlannedCall, ensure_unique_call_ids


def select_calls(
    calls: Sequence[PlannedCall],
    config: ExperimentConfig,
    *,
    pilot: bool = False,
    provider: str | None = None,
) -> list[PlannedCall]:
    """Return the calls to run, in the order to run them.

    The pilot is chosen from the whole grid before the provider filter is applied, so a reader
    with one key runs exactly the owner's pilot calls for that provider.
    """
    ensure_unique_call_ids(calls)
    selected = _pilot_sample(calls, config.pilot, config.seed) if pilot else list(calls)
    if provider is not None:
        if provider not in config.providers:
            known = ", ".join(sorted(config.providers))
            raise PlanError(f"Provider '{provider}' is not in this config. Choose from: {known}")
        selected = [call for call in selected if call.request.provider == provider]
    if config.call_order == "shuffled":
        selected = random.Random(config.seed).sample(selected, len(selected))
    return selected


def _pilot_sample(calls: Sequence[PlannedCall], pilot: PilotConfig, seed: int) -> list[PlannedCall]:
    if isinstance(pilot, FilterPilot):
        chosen = _filter_sample(calls, pilot)
    else:
        chosen = _stratified_sample(calls, pilot, seed)
    chosen_ids = {call.call_id for call in chosen}
    return [call for call in calls if call.call_id in chosen_ids]


def _filter_sample(calls: Sequence[PlannedCall], pilot: FilterPilot) -> list[PlannedCall]:
    chosen = [call for call in calls if any(_matches(call, rule) for rule in pilot.include)]
    if not chosen:
        raise PlanError("Pilot include rules matched no calls; check keys and values in config")
    return chosen


def _matches(call: PlannedCall, rule: dict) -> bool:
    descriptor = call.descriptor()
    return all(key in descriptor and descriptor[key] == value for key, value in rule.items())


def _stratified_sample(
    calls: Sequence[PlannedCall], pilot: StratifiedPilot, seed: int
) -> list[PlannedCall]:
    """One call per stratum first, then random extras up to the target fraction."""
    rng = random.Random(seed)
    keys = ["model", *(key for key in pilot.strata if key != "model")]
    groups: dict[tuple[str, ...], list[PlannedCall]] = defaultdict(list)
    for call in calls:
        groups[_stratum(call, keys)].append(call)

    chosen = [rng.choice(groups[stratum]) for stratum in sorted(groups)]
    chosen_ids = {call.call_id for call in chosen}
    remaining = [call for call in calls if call.call_id not in chosen_ids]
    target = max(1, round(pilot.fraction * len(calls)))
    extra_count = min(max(0, target - len(chosen)), len(remaining))
    return [*chosen, *rng.sample(remaining, extra_count)]


def _stratum(call: PlannedCall, keys: Sequence[str]) -> tuple[str, ...]:
    descriptor = call.descriptor()
    missing = [key for key in keys if key not in descriptor]
    if missing:
        raise PlanError(f"Pilot strata {missing} are not keys of call cells")
    return tuple(str(descriptor[key]) for key in keys)
