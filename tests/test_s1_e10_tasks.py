"""The S1 E10 task generators and call plan (specification sections 7.3 and 7.4).

Every generated item is checked against an independent solver written here, so a mistake in a
generator cannot quietly publish a question with the wrong answer. The constraint puzzles are
re-solved by brute force from the published prompt alone, which is the strongest form of the
check the specification asks for: exactly one valid solution.
"""

import json
import re
from itertools import permutations
from pathlib import Path

import pytest

from lab.config import load_config
from lab.experiments import load_sibling
from lab.plan import PlanError, ensure_unique_call_ids

FIELD_NOTE = Path("field-notes/s1-e10-reasoning-vs-standard")
CONFIG_PATH = FIELD_NOTE / "config.yaml"

ITEMS_PER_TASK = 30
MODELS = 3
MODES = 2


@pytest.fixture(scope="module")
def generators():
    return load_sibling(FIELD_NOTE / "generators.py")


@pytest.fixture(scope="module")
def builder():
    return load_sibling(FIELD_NOTE / "build_dataset.py")


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def items(generators, config):
    return generators.build_items(config.seed, tuple(config.parameters["tasks"]), ITEMS_PER_TASK)


def _of(items, task):
    return [item for item in items if item.task == task]


# --------------------------------------------------------------------------------------------
# Independent solvers, written from the published prompt rather than from the generator.
# --------------------------------------------------------------------------------------------

ARITHMETIC_SOLVERS = (
    (
        re.compile(
            r"(\d+) pallets holding (\d+) units each\. (\d+) units are found damaged and "
            r"removed\. The rest are shared equally between (\d+) stores"
        ),
        lambda p, u, d, s: (p * u - d) // s,
    ),
    (
        re.compile(r"(\d+) hours a day for (\d+) days, then (\d+) hours a day for (\d+) days"),
        lambda h1, d1, h2, d2: h1 * d1 + h2 * d2,
    ),
    (
        re.compile(
            r"holding (\d+) litres\. (\d+) litres are drawn off every hour for (\d+) hours, "
            r"and then (\d+) litres are added"
        ),
        lambda capacity, rate, hours, added: capacity - rate * hours + added,
    ),
    (
        re.compile(r"(\d+) crates, each weighing (\d+) kilograms\. (\d+) crates are taken off"),
        lambda crates, weight, removed: (crates - removed) * weight,
    ),
    (
        re.compile(
            r"(\d+) boxes of spare seals, with (\d+) seals in each box\. The site uses (\d+) "
            r"seals a week for (\d+) weeks"
        ),
        lambda boxes, per, used, weeks: boxes * per - used * weeks,
    ),
)


def solve_arithmetic(prompt: str) -> tuple[int, int]:
    """The answer worked out again from the prompt, plus which template it came from."""
    for index, (pattern, solve) in enumerate(ARITHMETIC_SOLVERS):
        found = pattern.search(prompt)
        if found is not None:
            return solve(*(int(number) for number in found.groups())), index
    raise AssertionError(f"No solver matched this prompt:\n{prompt}")


OPENING = re.compile(r"(\w+) (\d+) units")
ARRIVE = re.compile(r"^(\d+) units arrive at (\w+)\.$")
SHIP = re.compile(r"^(\d+) units are shipped out from (\w+)\.$")
MOVE = re.compile(r"^(\d+) units are moved from (\w+) to (\w+)\.$")
CHANGE_LINE = re.compile(r"^\d+\. (.*)$")
ASKED = re.compile(r"how many units are in (\w+) at the end")


def solve_state_tracking(prompt: str) -> int:
    """Replay the changes named in the prompt and read off the warehouse that was asked about."""
    header, rest = prompt.split("\n\n", 1)
    stock = {name: int(count) for name, count in OPENING.findall(header.split(":", 1)[1])}
    for line in rest.splitlines():
        numbered = CHANGE_LINE.match(line.strip())
        if numbered is None:
            continue
        change = numbered.group(1)
        if (found := ARRIVE.match(change)) is not None:
            stock[found.group(2)] += int(found.group(1))
        elif (found := SHIP.match(change)) is not None:
            stock[found.group(2)] -= int(found.group(1))
        elif (found := MOVE.match(change)) is not None:
            stock[found.group(2)] -= int(found.group(1))
            stock[found.group(3)] += int(found.group(1))
        else:
            raise AssertionError(f"Unreadable change: {change}")
    return stock[ASKED.search(prompt).group(1)]


CLUES = (
    (re.compile(r"^(\w+) is immediately before (\w+)\.$"), "immediately"),
    (re.compile(r"^Exactly one job runs between (\w+) and (\w+), in that order\.$"), "gap"),
    (re.compile(r"^(\w+) runs somewhere before (\w+)\.$"), "before"),
    (re.compile(r"^(\w+) is not job (\d)\.$"), "not-at"),
    (re.compile(r"^(\w+) is job (\d)\.$"), "at"),
)


def _holds(kind: str, first: str, second: str, order: tuple[str, ...]) -> bool:
    if kind == "immediately":
        return order.index(second) - order.index(first) == 1
    if kind == "gap":
        return order.index(second) - order.index(first) == 2
    if kind == "before":
        return order.index(first) < order.index(second)
    if kind == "not-at":
        return order.index(first) != int(second) - 1
    return order.index(first) == int(second) - 1


def solve_puzzle(prompt: str) -> list[tuple[str, ...]]:
    """Every order that fits the clues in the prompt, found by brute force."""
    jobs = tuple(
        name.strip() for name in re.search(r"The jobs are: (.+?)\.", prompt).group(1).split(",")
    )
    block = prompt.split("These statements are all true:\n", 1)[1].split("\n\n", 1)[0]
    clues = []
    for line in block.splitlines():
        sentence = line.removeprefix("- ").strip()
        for pattern, kind in CLUES:
            if (found := pattern.match(sentence)) is not None:
                clues.append((kind, found.group(1).lower(), found.group(2)))
                break
        else:
            raise AssertionError(f"Unreadable clue: {sentence}")
    return [
        candidate
        for candidate in permutations(jobs)
        if all(_holds(kind, first, second, candidate) for kind, first, second in clues)
    ]


# --------------------------------------------------------------------------------------------


class TestDeterminism:
    def test_the_same_seed_gives_the_same_items(self, generators, config, items):
        again = generators.build_items(
            config.seed, tuple(config.parameters["tasks"]), ITEMS_PER_TASK
        )
        assert [item.as_dict() for item in again] == [item.as_dict() for item in items]

    def test_a_different_seed_gives_different_items(self, generators, config, items):
        other = generators.build_items(
            config.seed + 1, tuple(config.parameters["tasks"]), ITEMS_PER_TASK
        )
        assert [item.prompt for item in other] != [item.prompt for item in items]

    def test_a_family_does_not_shift_when_another_changes_size(self, generators, config):
        tasks = tuple(config.parameters["tasks"])
        few = generators.build_task(tasks[0], config.seed, 5)
        many = generators.build_task(tasks[0], config.seed, 30)
        assert [item.prompt for item in many[:5]] == [item.prompt for item in few]

    def test_the_committed_items_match_a_fresh_build(self, builder, config, tmp_path):
        builder.build_items(config, tmp_path)
        built = (tmp_path / "tasks" / "items.jsonl").read_text(encoding="utf-8")
        committed = (FIELD_NOTE / "tasks" / "items.jsonl").read_text(encoding="utf-8")
        assert built == committed


class TestEveryItem:
    def test_every_task_has_the_items_asked_for(self, config, items):
        for task in config.parameters["tasks"]:
            assert len(_of(items, task)) == ITEMS_PER_TASK

    def test_no_two_items_share_a_prompt(self, items):
        assert len({item.prompt for item in items}) == len(items)

    def test_every_prompt_ends_with_the_answer_instruction(self, generators, items):
        for item in items:
            assert item.prompt.endswith(generators.ANSWER_INSTRUCTION)

    def test_every_item_is_indexed_from_zero_within_its_task(self, config, items):
        for task in config.parameters["tasks"]:
            assert [item.index for item in _of(items, task)] == list(range(ITEMS_PER_TASK))

    def test_an_unknown_task_is_refused(self, generators):
        with pytest.raises(generators.GeneratorError, match="Unknown task"):
            generators.build_task("nonsense", 1, 1)


class TestExtraction:
    def test_the_answer_appears_in_the_passage(self, generators, items):
        for item in _of(items, generators.EXTRACTION):
            assert f"is {item.answer}." in item.prompt

    def test_the_question_names_the_pump_the_fact_describes(self, generators, items):
        for item in _of(items, generators.EXTRACTION):
            pump = re.search(r"calibration code for pump ([A-Z]-\d{3}) is", item.prompt).group(1)
            assert f"what is the calibration code for pump {pump}?" in item.prompt

    def test_the_fact_is_never_the_first_or_last_sentence(self, generators, items):
        for item in _of(items, generators.EXTRACTION):
            passage = item.prompt.split("\n\n")[0]
            sentences = [part for part in passage.split(". ") if part]
            assert "calibration code" not in sentences[0]
            assert "calibration code" not in sentences[-1]

    def test_the_answer_is_four_digits(self, generators, items):
        for item in _of(items, generators.EXTRACTION):
            assert re.fullmatch(r"\d{4}", item.answer)


class TestArithmetic:
    def test_every_answer_survives_an_independent_solver(self, generators, items):
        for item in _of(items, generators.ARITHMETIC):
            expected, _ = solve_arithmetic(item.prompt)
            assert int(item.answer) == expected

    def test_every_answer_is_positive(self, generators, items):
        for item in _of(items, generators.ARITHMETIC):
            assert int(item.answer) > 0

    def test_all_five_templates_are_used(self, generators, items):
        used = {solve_arithmetic(item.prompt)[1] for item in _of(items, generators.ARITHMETIC)}
        assert used == set(range(len(ARITHMETIC_SOLVERS)))


class TestStateTracking:
    def test_every_answer_survives_an_independent_replay(self, generators, items):
        for item in _of(items, generators.STATE_TRACKING):
            assert int(item.answer) == solve_state_tracking(item.prompt)

    def test_every_item_has_six_to_eight_changes(self, generators, items):
        for item in _of(items, generators.STATE_TRACKING):
            changes = [line for line in item.prompt.splitlines() if CHANGE_LINE.match(line)]
            assert generators.MIN_CHANGES <= len(changes) <= generators.MAX_CHANGES

    def test_stock_never_goes_negative_at_any_step(self, generators, items):
        for item in _of(items, generators.STATE_TRACKING):
            assert solve_state_tracking(item.prompt) >= 0


class TestConstraintPuzzles:
    def test_every_puzzle_has_exactly_one_solution(self, generators, items):
        for item in _of(items, generators.CONSTRAINT_PUZZLE):
            assert len(solve_puzzle(item.prompt)) == 1

    def test_the_recorded_answer_is_that_solution(self, generators, items):
        for item in _of(items, generators.CONSTRAINT_PUZZLE):
            (only,) = solve_puzzle(item.prompt)
            assert ", ".join(only) == item.answer

    def test_every_puzzle_orders_five_jobs(self, generators, items):
        for item in _of(items, generators.CONSTRAINT_PUZZLE):
            assert len(item.answer.split(", ")) == generators.PUZZLE_SIZE

    def test_no_clue_is_redundant(self, generators, items):
        """Dropping any one clue must allow more than one order, or the clue was not needed."""
        for item in _of(items, generators.CONSTRAINT_PUZZLE):
            block = item.prompt.split("These statements are all true:\n", 1)[1].split("\n\n", 1)[0]
            clues = block.splitlines()
            for dropped in clues:
                thinner = item.prompt.replace(f"{dropped}\n", "", 1)
                assert len(solve_puzzle(thinner)) > 1


class TestCommittedFiles:
    def test_building_writes_items_and_a_manifest(self, builder, config, tmp_path):
        builder.build_items(config, tmp_path)
        manifest = json.loads((tmp_path / "tasks" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["seed"] == config.seed
        assert manifest["items"] == ITEMS_PER_TASK * len(config.parameters["tasks"])

    def test_committed_items_are_loaded_rather_than_rebuilt(self, builder, config):
        loaded = builder.load_items(config, FIELD_NOTE)
        assert loaded is not None
        assert len(loaded) == ITEMS_PER_TASK * len(config.parameters["tasks"])

    def test_missing_items_are_reported_as_none(self, builder, config, tmp_path):
        assert builder.load_items(config, tmp_path) is None

    def test_a_tampered_items_file_is_reported_as_none(self, builder, config, tmp_path):
        builder.build_items(config, tmp_path)
        path = tmp_path / "tasks" / "items.jsonl"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        assert builder.load_items(config, tmp_path) is None

    def test_a_config_with_a_different_seed_is_reported_as_none(self, builder, config, tmp_path):
        builder.build_items(config, tmp_path)
        changed = config.model_copy(update={"seed": config.seed + 1})
        assert builder.load_items(changed, tmp_path) is None

    def test_dataset_sources_records_the_licence_and_checksum(self, builder, config):
        (source,) = builder.dataset_sources(config, FIELD_NOTE)
        assert "No third-party content" in source.licence
        assert source.checksum.startswith("sha256:")
        assert source.url is None


class TestPlan:
    def test_the_grid_is_every_item_by_model_by_mode(self, builder, config):
        calls = builder.plan_calls(config, FIELD_NOTE)
        assert len(calls) == ITEMS_PER_TASK * len(config.parameters["tasks"]) * MODELS * MODES

    def test_call_identifiers_are_unique(self, builder, config):
        ensure_unique_call_ids(builder.plan_calls(config, FIELD_NOTE))

    def test_every_call_carries_its_task_and_item(self, builder, config):
        for call in builder.plan_calls(config, FIELD_NOTE):
            assert set(call.cell) == {"task", "item_index"}

    def test_the_same_prompt_goes_to_both_modes(self, builder, config):
        calls = builder.plan_calls(config, FIELD_NOTE)
        prompts: dict[tuple[str, str, int], set[str]] = {}
        for call in calls:
            key = (call.model_label, str(call.cell["task"]), int(call.cell["item_index"]))
            prompts.setdefault(key, set()).add(call.request.prompt)
        assert all(len(shared) == 1 for shared in prompts.values())

    def test_no_system_prompt_is_sent(self, builder, config):
        assert all(call.request.system is None for call in builder.plan_calls(config, FIELD_NOTE))

    def test_high_mode_shows_thinking_and_lowest_does_not(self, builder, config):
        for call in builder.plan_calls(config, FIELD_NOTE):
            assert call.request.show_thinking == (call.mode == builder.HIGH_MODE)

    def test_items_are_built_when_they_are_missing(self, builder, config, tmp_path):
        calls = builder.plan_calls(config, tmp_path)
        assert (tmp_path / "tasks" / "items.jsonl").exists()
        assert len(calls) == ITEMS_PER_TASK * len(config.parameters["tasks"]) * MODELS * MODES

    def test_a_model_missing_a_mode_is_refused(self, builder, config):
        first = config.models[0]
        broken = config.model_copy(
            update={
                "models": [
                    first.model_copy(update={"modes": {"lowest": first.modes["lowest"]}}),
                    *config.models[1:],
                ]
            }
        )
        with pytest.raises(PlanError, match="must define exactly the modes"):
            builder.plan_calls(broken, FIELD_NOTE)
