"""An experiment's cost before any call: input tokens counted from the real prompts, outputs at
an expected size and at the ceiling of each output limit.

Similar example arms are counted with random examples of the same number, since the real ones
need embeddings first; examples are of similar length, so the count is close. Judge prompts are
counted with the target replies standing in for the arms' replies. Prompt caching is not
counted, so a fixed examples prefix costs less than shown.
"""

from collections.abc import Sequence

from lab.adapt.build_tasks.estimate import StageCost, stage_cost
from lab.adapt.experiment import Experiment
from lab.adapt.items import ReplyItem
from lab.adapt.requests import Inputs, arm_requests, facts_requests, style_requests
from lab.prices import PricesFile
from lab.providers.base import GenerationRequest
from lab.rag.estimate import chat_tokens

EXPECTED_OUTPUT = {"a": 45, "b": 170}
FACTS_TOKENS = 30
STYLE_TOKENS = 10


def _inputs(requests: Sequence[GenerationRequest]) -> int:
    return sum(chat_tokens(r.system or "") + chat_tokens(r.prompt) for r in requests)


def estimate_experiment(
    experiment: Experiment, inputs: Inputs, prices: PricesFile | None
) -> list[StageCost]:
    costs = []
    for arm in experiment.arms:
        if arm.external:
            continue
        counted = arm
        if arm.examples.selection == "similar":
            examples = arm.examples.model_copy(update={"selection": "random"})
            counted = arm.model_copy(update={"examples": examples})
        requests = list(arm_requests(experiment, counted, inputs).values())
        expected = len(requests) * EXPECTED_OUTPUT[experiment.task]
        costs.append(
            stage_cost(
                f"answer {arm.name}",
                experiment.model_for(arm),
                len(requests),
                _inputs(requests),
                expected,
                prices,
            )
        )
    if experiment.task == "b":
        costs += _judge_costs(experiment, inputs, prices)
    return costs


def _judge_costs(
    experiment: Experiment, inputs: Inputs, prices: PricesFile | None
) -> list[StageCost]:
    assert experiment.judge is not None
    stand_in = {i.id: i.target_reply for i in inputs.items if isinstance(i, ReplyItem)}
    facts = list(facts_requests(experiment, inputs, stand_in, "all").values())
    n_arms = len(experiment.arms)
    style = list(style_requests(experiment, inputs, stand_in, stand_in, "all").values())
    n_pairwise = n_arms - 1
    return [
        stage_cost(
            "facts judge",
            experiment.judge,
            len(facts) * n_arms,
            _inputs(facts) * n_arms,
            len(facts) * n_arms * FACTS_TOKENS,
            prices,
        ),
        stage_cost(
            "style judge",
            experiment.judge,
            len(style) * n_pairwise,
            _inputs(style) * n_pairwise,
            len(style) * n_pairwise * STYLE_TOKENS,
            prices,
        ),
    ]
