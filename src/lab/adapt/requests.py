"""Every request an experiment sends, built before any call so the estimate counts the same
prompts the run sends."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from lab.adapt.build_tasks.prompts_b import CHECK_SYSTEM, facts_prompt
from lab.adapt.build_tasks.task_b import for_fact_check
from lab.adapt.definitions import Definitions
from lab.adapt.examples import Embed, fixed_examples, similar_examples
from lab.adapt.experiment import Arm, Experiment
from lab.adapt.items import ReplyItem, TriageItem, reply_items, triage_items
from lab.adapt.output import output_format
from lab.adapt.prompts import (
    reply_examples,
    reply_prompt,
    reply_system,
    triage_examples,
    triage_prompt,
    triage_system,
    with_examples,
)
from lab.providers.base import GenerationRequest
from lab.rag.waves import request_for

STYLE_SYSTEM = (
    "You compare two replies to the same customer question against a house style guide. Judge "
    "style only: both replies may be assumed correct. Do not explain your reasoning. Reply with "
    "one JSON object and nothing else."
)


@dataclass(frozen=True)
class Inputs:
    """The frozen data an experiment reads."""

    definitions: Definitions
    style_guide: str
    items: Sequence[TriageItem] | Sequence[ReplyItem]
    train: Sequence[TriageItem] | Sequence[ReplyItem]


def load_inputs(experiment: Experiment) -> Inputs:
    data = experiment.data_folder
    definitions = Definitions.load(data / "routes.yaml")
    style_guide = (data / "style-guide.md").read_text(encoding="utf-8")
    if experiment.task == "a":
        items = triage_items(data, experiment.split, experiment.limit)
        train = triage_items(data, "train")
    else:
        items = reply_items(data, experiment.split, experiment.limit)
        train = reply_items(data, "train")
    return Inputs(definitions, style_guide, items, train)


def _text(item: TriageItem | ReplyItem) -> str:
    return item.message if isinstance(item, TriageItem) else item.question


def examples_for(arm: Arm, inputs: Inputs, embed: Embed | None) -> list[str | None]:
    """Each item's examples block, in item order, or None where the arm shows none."""
    spec = arm.examples
    if spec.n == 0:
        return [None] * len(inputs.items)
    render = triage_examples if isinstance(inputs.train[0], TriageItem) else reply_examples
    if spec.selection == "random":
        block = render(fixed_examples(spec, inputs.train))
        return [block] * len(inputs.items)
    if embed is None:
        raise ValueError(f"arm {arm.name} chooses similar examples, which needs embeddings")
    chosen = similar_examples(
        spec,
        [_text(i) for i in inputs.items],
        inputs.train,
        [_text(t) for t in inputs.train],
        embed,
    )
    return [render(c) for c in chosen]


def arm_requests(
    experiment: Experiment, arm: Arm, inputs: Inputs, embed: Embed | None = None
) -> dict[str, GenerationRequest]:
    """Item id to request, for a prompted arm."""
    assert arm.instructions is not None
    spec = experiment.model_for(arm)
    if experiment.task == "a":
        system = triage_system(arm.instructions, inputs.definitions)
        fmt = output_format(arm.output, inputs.definitions)
    else:
        system = reply_system(arm.instructions, inputs.style_guide)
        fmt = None
    out = {}
    for item, block in zip(inputs.items, examples_for(arm, inputs, embed), strict=True):
        prompt = triage_prompt(item) if isinstance(item, TriageItem) else reply_prompt(item)
        request = request_for(
            spec,
            system=with_examples(system, block),
            prompt=prompt,
            episode=experiment.episode,
            stage=f"answer-{arm.name}",
        )
        out[item.id] = request.model_copy(update={"output_format": fmt})
    return out


def facts_requests(
    experiment: Experiment, inputs: Inputs, replies: Mapping[str, str], arm: str
) -> dict[str, GenerationRequest]:
    """Task B: the facts judge, for answerable items only. A not found item keeps its facts
    when it uses the fixed sentence, which the code checks."""
    assert experiment.judge is not None
    out = {}
    for item in inputs.items:
        assert isinstance(item, ReplyItem)
        if item.kind == "not_found" or item.id not in replies:
            continue
        reply = for_fact_check(replies[item.id], item.source_ref)
        out[item.id] = request_for(
            experiment.judge,
            system=CHECK_SYSTEM,
            prompt=facts_prompt(item.question, item.answer, reply),
            episode=experiment.episode,
            stage=f"facts-{arm}",
        )
    return out


def style_prompt(guide: str, question: str, first: str, second: str) -> str:
    return (
        f"House style guide:\n{guide}\n\nCustomer question: {question}\n\n"
        f"Reply 1:\n{first}\n\nReply 2:\n{second}\n\n"
        "Which reply follows the house style guide better? Reply "
        '{"better": "1", "2" or "tie"}'
    )


def style_requests(
    experiment: Experiment,
    inputs: Inputs,
    arm_replies: Mapping[str, str],
    reference_replies: Mapping[str, str],
    arm: str,
) -> dict[str, GenerationRequest]:
    """Task B: the pairwise style judge, each pair in both orders. Keys are id:order, where
    order "ar" shows the arm first and "ra" the reference first."""
    assert experiment.judge is not None
    out = {}
    for item in inputs.items:
        if item.id not in arm_replies or item.id not in reference_replies:
            continue
        a, r = arm_replies[item.id], reference_replies[item.id]
        for order, (first, second) in (("ar", (a, r)), ("ra", (r, a))):
            out[f"{item.id}:{order}"] = request_for(
                experiment.judge,
                system=STYLE_SYSTEM,
                prompt=style_prompt(inputs.style_guide, item.question, first, second),
                episode=experiment.episode,
                stage=f"style-{arm}",
            )
    return out
