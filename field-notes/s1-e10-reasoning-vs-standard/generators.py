"""Generates the four S1 E10 task families, with known correct answers.

Every item is built from the config seed, so nothing here can have appeared in a model's
training data and no third-party text is involved. That is why the items themselves are
committed to the repository: they are wholly ours, and a reader should be able to read every
question rather than take the results on trust.

The four families run from a control that needs no reasoning to a search problem that does:

  extraction         a generated operations log with one invented fact, and a lookup question
  arithmetic         word problems needing two or three operations
  state-tracking     twelve to twenty sequential changes to stock across five warehouses
  constraint-puzzle  a seven-job ordering puzzle with exactly one valid order, brute forced

State tracking and the puzzles were made harder after the pilot, in which every model answered
every item correctly with reasoning at its lowest setting. A task that every model already gets
right cannot show what reasoning adds.

Nothing in this module touches the network or the clock.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from itertools import permutations

# Specification section 7.3: every prompt ends with this line, whatever the task.
ANSWER_INSTRUCTION = "Give your final answer on the last line in the form ANSWER: <value>"

EXTRACTION = "extraction"
ARITHMETIC = "arithmetic"
STATE_TRACKING = "state-tracking"
CONSTRAINT_PUZZLE = "constraint-puzzle"

# Short enough to fit a chart axis, in the order the tasks are meant to be read.
TASK_NAMES = {
    EXTRACTION: "Extraction",
    ARITHMETIC: "Short\narithmetic",
    STATE_TRACKING: "State\ntracking",
    CONSTRAINT_PUZZLE: "Constraint\npuzzles",
}

INTEGER = "integer"
ORDERED_LIST = "ordered-list"

# How many times a generator may draw again before giving up on a distinct item.
MAX_ATTEMPTS = 400


class GeneratorError(RuntimeError):
    """A task family could not produce the number of distinct items asked for."""


@dataclass(frozen=True)
class Item:
    """One generated question with its known correct answer."""

    task: str
    index: int
    prompt: str
    answer: str
    answer_kind: str

    def as_dict(self) -> dict:
        return {
            "task": self.task,
            "index": self.index,
            "prompt": self.prompt,
            "answer": self.answer,
            "answer_kind": self.answer_kind,
        }

    @classmethod
    def from_dict(cls, entry: dict) -> "Item":
        return cls(
            task=str(entry["task"]),
            index=int(entry["index"]),
            prompt=str(entry["prompt"]),
            answer=str(entry["answer"]),
            answer_kind=str(entry["answer_kind"]),
        )


# --------------------------------------------------------------------------------------------
# T1 Extraction: a generated operations log with one invented fact.
# --------------------------------------------------------------------------------------------

SITES = (
    "Ardrossan",
    "Balmore",
    "Crosshill",
    "Dunmore",
    "Eastgate",
    "Fairhaven",
    "Glenlochy",
    "Hartwell",
)
SHIFTS = ("early", "late", "night", "weekend")
SYSTEMS = ("coolant", "feedwater", "lubrication", "hydraulic", "ventilation", "condensate")
# Identifier letters, leaving out I, O, and Q, which read as digits in a four-digit answer.
IDENTIFIER_LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"

PASSAGE_TEMPLATES = (
    "The {shift} shift at {site} logged {count} routine inspections.",
    "Pressure in the {system} loop held at {pressure} kilopascals throughout.",
    "Bay {bay} was closed for {hours} hours while an access panel was refitted.",
    "The standby generator ran for {minutes} minutes during its scheduled test.",
    "Vibration on the {system} pump stayed inside the agreed band.",
    "A spare {system} filter was drawn from stores and fitted without incident.",
    "The duty engineer signed off {count} work orders before handover.",
    "Ambient temperature in the turbine hall reached {temperature} degrees.",
    "No alarms were raised on the {system} system during the shift.",
    "Stock of {system} fluid at {site} was topped up to its usual level.",
    "The {shift} handover note recorded nothing outstanding.",
    "Access to bay {bay} was restored once the inspection was complete.",
)
# Sentences of filler around the fact. Short on purpose: extraction is the control task, and a
# long document would test context length, which is what S1 E7 measures.
PASSAGE_SENTENCES = 11


def _fill(template: str, rng: random.Random) -> str:
    return template.format(
        shift=rng.choice(SHIFTS),
        site=rng.choice(SITES),
        system=rng.choice(SYSTEMS),
        count=rng.randint(3, 19),
        pressure=rng.randrange(200, 900, 5),
        bay=rng.randint(1, 8),
        hours=rng.randint(2, 9),
        minutes=rng.randrange(20, 95, 5),
        temperature=rng.randint(14, 31),
    )


def _extraction_item(rng: random.Random) -> tuple[str, str]:
    identifier = f"{rng.choice(IDENTIFIER_LETTERS)}-{rng.randint(100, 999)}"
    code = f"{rng.randint(1000, 9999)}"
    sentences = [
        _fill(template, rng) for template in rng.sample(PASSAGE_TEMPLATES, PASSAGE_SENTENCES)
    ]
    # Embedded rather than first or last, so the answer is never the opening or closing line.
    sentences.insert(
        rng.randint(1, PASSAGE_SENTENCES - 1),
        f"The calibration code for pump {identifier} is {code}.",
    )
    passage = " ".join(sentences)
    prompt = (
        f"{passage}\n\n"
        f"Question: what is the calibration code for pump {identifier}?\n"
        "Answer with the four-digit code only.\n"
        f"{ANSWER_INSTRUCTION}"
    )
    return prompt, code


# --------------------------------------------------------------------------------------------
# T2 Short arithmetic: two or three operations.
# --------------------------------------------------------------------------------------------

ArithmeticTemplate = Callable[[random.Random], tuple[str, int] | None]


def _pallets(rng: random.Random) -> tuple[str, int] | None:
    pallets, per = rng.randint(3, 9), rng.choice((12, 24, 36, 48))
    stores, damaged = rng.choice((2, 3, 4)), rng.randint(1, 60)
    remaining = pallets * per - damaged
    if remaining <= 0 or remaining % stores:
        return None
    return (
        f"A depot takes in {pallets} pallets holding {per} units each. {damaged} units are "
        f"found damaged and removed. The rest are shared equally between {stores} stores. "
        "How many units does each store receive?",
        remaining // stores,
    )


def _shift_hours(rng: random.Random) -> tuple[str, int] | None:
    first_days, first_hours = rng.randint(2, 6), rng.randint(6, 12)
    second_days, second_hours = rng.randint(2, 6), rng.randint(4, 10)
    if first_hours == second_hours:
        return None
    return (
        f"A maintenance crew works {first_hours} hours a day for {first_days} days, then "
        f"{second_hours} hours a day for {second_days} days. How many hours does the crew "
        "work in total?",
        first_days * first_hours + second_days * second_hours,
    )


def _tank(rng: random.Random) -> tuple[str, int] | None:
    capacity = rng.randrange(400, 2000, 50)
    per_hour, hours = rng.randrange(20, 120, 10), rng.randint(3, 9)
    added = rng.randrange(50, 400, 25)
    remaining = capacity - per_hour * hours + added
    if remaining <= 0 or remaining > capacity:
        return None
    return (
        f"A tank starts the day holding {capacity} litres. {per_hour} litres are drawn off "
        f"every hour for {hours} hours, and then {added} litres are added. How many litres "
        "are in the tank?",
        remaining,
    )


def _crates(rng: random.Random) -> tuple[str, int] | None:
    crates, weight = rng.randint(12, 60), rng.randint(3, 25)
    removed = rng.randint(2, 11)
    if removed >= crates:
        return None
    return (
        f"A pallet holds {crates} crates, each weighing {weight} kilograms. {removed} crates "
        "are taken off for inspection. What is the total weight in kilograms of the crates "
        "still on the pallet?",
        (crates - removed) * weight,
    )


def _spares(rng: random.Random) -> tuple[str, int] | None:
    boxes, per_box = rng.randint(4, 15), rng.randint(6, 24)
    used_per_week, weeks = rng.randint(3, 20), rng.randint(2, 5)
    remaining = boxes * per_box - used_per_week * weeks
    if remaining <= 0:
        return None
    return (
        f"A store room holds {boxes} boxes of spare seals, with {per_box} seals in each box. "
        f"The site uses {used_per_week} seals a week for {weeks} weeks. How many seals are "
        "left?",
        remaining,
    )


ARITHMETIC_TEMPLATES: tuple[ArithmeticTemplate, ...] = (
    _pallets,
    _shift_hours,
    _tank,
    _crates,
    _spares,
)


def _arithmetic_item(rng: random.Random, template: ArithmeticTemplate) -> tuple[str, str] | None:
    drawn = template(rng)
    if drawn is None:
        return None
    question, answer = drawn
    prompt = f"{question}\nAnswer with a whole number only.\n{ANSWER_INSTRUCTION}"
    return prompt, str(answer)


# --------------------------------------------------------------------------------------------
# T3 Long state tracking: twelve to twenty sequential changes across five warehouses.
# --------------------------------------------------------------------------------------------

WAREHOUSES = ("Aldridge", "Brindle", "Colwyn", "Dunmore", "Elgin")
MIN_CHANGES = 12
MAX_CHANGES = 20
# Spelled out in the prompt, so the count reads naturally.
NUMBER_WORDS = {3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven"}


def _state_tracking_item(rng: random.Random) -> tuple[str, str] | None:
    stock = {name: rng.randrange(40, 240, 5) for name in WAREHOUSES}
    opening = dict(stock)
    changes = [_one_change(rng, stock) for _ in range(rng.randint(MIN_CHANGES, MAX_CHANGES))]
    asked = rng.choice(WAREHOUSES)
    lines = "\n".join(f"{number}. {text}" for number, text in enumerate(changes, start=1))
    opening_text = ", ".join(f"{name} {count} units" for name, count in opening.items())
    prompt = (
        f"{NUMBER_WORDS[len(WAREHOUSES)]} warehouses start the day with these stock levels: "
        f"{opening_text}.\n\n"
        f"The following changes happen in order:\n{lines}\n\n"
        f"Question: how many units are in {asked} at the end?\n"
        "Answer with a whole number only.\n"
        f"{ANSWER_INSTRUCTION}"
    )
    return prompt, str(stock[asked])


def _one_change(rng: random.Random, stock: dict[str, int]) -> str:
    """Apply one change to `stock` and describe it. Stock never goes below zero.

    Stock only leaves a warehouse that holds enough of it. When none does, the change becomes an
    arrival, so a long sequence never has to be thrown away and drawn again.
    """
    kind = rng.choice(("move", "arrive", "ship"))
    amount = rng.randrange(5, 90, 5)
    sources = [name for name in WAREHOUSES if stock[name] >= amount]
    if kind == "arrive" or not sources:
        where = rng.choice(WAREHOUSES)
        stock[where] += amount
        return f"{amount} units arrive at {where}."
    source = rng.choice(sources)
    stock[source] -= amount
    if kind == "ship":
        return f"{amount} units are shipped out from {source}."
    destination = rng.choice([name for name in WAREHOUSES if name != source])
    stock[destination] += amount
    return f"{amount} units are moved from {source} to {destination}."


# --------------------------------------------------------------------------------------------
# T4 Constraint puzzles: exactly one valid order, checked by brute force.
# --------------------------------------------------------------------------------------------

JOBS = (
    "audit",
    "balancing",
    "calibration",
    "descaling",
    "emissions",
    "flushing",
    "greasing",
    "hosing",
)
# Seven jobs give 5,040 possible orders, against 120 for five, which the pilot showed every
# model could solve at its lowest reasoning setting.
PUZZLE_SIZE = 7

# A constraint is a sentence and the test it stands for.
Constraint = tuple[str, Callable[[tuple[str, ...]], bool]]


def _candidate_constraints(order: tuple[str, ...], rng: random.Random) -> list[Constraint]:
    """Every constraint that is true of `order`, hardest first so puzzles need real search.

    Position constraints come last, because a puzzle solved by reading off the positions
    would test nothing. They are still in the pool, which guarantees that a unique set always
    exists: together they pin the order completely.
    """
    positions = {job: index for index, job in enumerate(order)}
    relations: list[Constraint] = []
    for first, second in permutations(order, 2):
        gap = positions[second] - positions[first]
        if gap == 1:
            relations.append(
                (
                    f"{first.capitalize()} is immediately before {second}.",
                    _immediately(first, second),
                )
            )
        if gap == 2:
            relations.append(
                (
                    f"Exactly one job runs between {first} and {second}, in that order.",
                    _gap_of(first, second, 2),
                )
            )
        if gap > 0:
            relations.append(
                (f"{first.capitalize()} runs somewhere before {second}.", _before(first, second))
            )
    negatives: list[Constraint] = [
        (f"{job.capitalize()} is not job {slot + 1}.", _not_at(job, slot))
        for job in order
        for slot in range(PUZZLE_SIZE)
        if positions[job] != slot
    ]
    positives: list[Constraint] = [
        (f"{job.capitalize()} is job {positions[job] + 1}.", _at(job, positions[job]))
        for job in order
    ]
    rng.shuffle(relations)
    rng.shuffle(negatives)
    rng.shuffle(positives)
    return [*relations, *negatives, *positives]


def _immediately(first: str, second: str) -> Callable[[tuple[str, ...]], bool]:
    return lambda order: order.index(second) - order.index(first) == 1


def _gap_of(first: str, second: str, gap: int) -> Callable[[tuple[str, ...]], bool]:
    return lambda order: order.index(second) - order.index(first) == gap


def _before(first: str, second: str) -> Callable[[tuple[str, ...]], bool]:
    return lambda order: order.index(first) < order.index(second)


def _not_at(job: str, slot: int) -> Callable[[tuple[str, ...]], bool]:
    return lambda order: order.index(job) != slot


def _at(job: str, slot: int) -> Callable[[tuple[str, ...]], bool]:
    return lambda order: order.index(job) == slot


def _solutions(jobs: tuple[str, ...], constraints: list[Constraint]) -> list[tuple[str, ...]]:
    """Brute force over every order of the jobs, so uniqueness is checked, not assumed."""
    return [
        candidate
        for candidate in permutations(sorted(jobs))
        if all(test(candidate) for _, test in constraints)
    ]


def _minimal_constraints(
    jobs: tuple[str, ...], candidates: list[Constraint]
) -> list[Constraint] | None:
    """Clues taken in order until one solution is left, then pruned of any it can spare.

    The orders still possible are narrowed as each clue is added, rather than every order being
    checked again from scratch, which matters at 5,040 orders. A clue that rules nothing out is
    skipped, so it never reaches the reader.
    """
    remaining = list(permutations(sorted(jobs)))
    chosen: list[Constraint] = []
    for candidate in candidates:
        narrowed = [order for order in remaining if candidate[1](order)]
        if len(narrowed) == len(remaining):
            continue
        chosen.append(candidate)
        remaining = narrowed
        if len(remaining) == 1:
            break
    else:
        return None
    for constraint in list(chosen):
        without = [kept for kept in chosen if kept is not constraint]
        if len(_solutions(jobs, without)) == 1:
            chosen = without
    return chosen


def _constraint_puzzle_item(rng: random.Random) -> tuple[str, str] | None:
    jobs = tuple(rng.sample(JOBS, PUZZLE_SIZE))
    order = tuple(rng.sample(jobs, PUZZLE_SIZE))
    chosen = _minimal_constraints(jobs, _candidate_constraints(order, rng))
    if chosen is None:
        return None
    clues = "\n".join(f"- {sentence}" for sentence, _ in chosen)
    names = ", ".join(sorted(jobs))
    prompt = (
        f"{NUMBER_WORDS[PUZZLE_SIZE]} maintenance jobs are run one after another, as job 1 "
        f"through to job {PUZZLE_SIZE}. The jobs are: {names}.\n\n"
        f"These statements are all true:\n{clues}\n\n"
        "Exactly one order fits every statement. Work out that order.\n"
        f"Answer with the {NUMBER_WORDS[PUZZLE_SIZE].lower()} job names from first to last, "
        "separated by commas.\n"
        f"{ANSWER_INSTRUCTION}"
    )
    return prompt, ", ".join(order)


# --------------------------------------------------------------------------------------------
# Building a whole task family.
# --------------------------------------------------------------------------------------------


SINGLE_DRAW = {
    EXTRACTION: _extraction_item,
    STATE_TRACKING: _state_tracking_item,
    CONSTRAINT_PUZZLE: _constraint_puzzle_item,
}


def _draw(task: str, rng: random.Random, accepted: int) -> tuple[str, str] | None:
    """One attempt at the next item of `task`, or None when the draw is unusable.

    `accepted` is how many items the family already has, so the arithmetic templates are cycled
    over the items that are kept rather than over the attempts. A template that rejects most of
    its draws, such as the one that needs the units to divide evenly, would otherwise appear far
    less often than the rest.
    """
    if task == ARITHMETIC:
        return _arithmetic_item(rng, ARITHMETIC_TEMPLATES[accepted % len(ARITHMETIC_TEMPLATES)])
    return SINGLE_DRAW[task](rng)


def _answer_kind(task: str) -> str:
    return ORDERED_LIST if task == CONSTRAINT_PUZZLE else INTEGER


def build_task(task: str, seed: int, count: int) -> tuple[Item, ...]:
    """`count` distinct items of one task family, generated from the seed.

    Each family gets its own stream of random numbers, keyed by name, so changing the number of
    items in one family leaves the others byte for byte the same.
    """
    if task not in TASK_NAMES:
        raise GeneratorError(f"Unknown task '{task}'. Known tasks: {', '.join(TASK_NAMES)}")
    rng = random.Random(f"{seed}:{task}")
    items: list[Item] = []
    seen: set[str] = set()
    attempts = 0
    while len(items) < count:
        attempts += 1
        if attempts > MAX_ATTEMPTS + count:
            raise GeneratorError(
                f"Only {len(items)} distinct '{task}' items after {attempts} attempts; "
                f"{count} were asked for. Widen the generator's ranges or ask for fewer."
            )
        drawn = _draw(task, rng, len(items))
        if drawn is None or drawn[0] in seen:
            continue
        seen.add(drawn[0])
        items.append(
            Item(
                task=task,
                index=len(items),
                prompt=drawn[0],
                answer=drawn[1],
                answer_kind=_answer_kind(task),
            )
        )
    return tuple(items)


def build_items(seed: int, tasks: tuple[str, ...], items_per_task: int) -> tuple[Item, ...]:
    """Every item of every task family, in the order the tasks are listed in the config."""
    return tuple(item for task in tasks for item in build_task(task, seed, items_per_task))
