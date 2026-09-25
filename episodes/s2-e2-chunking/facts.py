"""The invented facts and questions for S2 E2, generated from the seed in config.yaml.

Every fact is about a place that does not exist, so no model can have seen it in training, and
every question names that place, so each question has exactly one right answer in the corpus.

Run from the repository root to regenerate facts.json, which is committed:

    uv run python episodes/s2-e2-chunking/facts.py
"""

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CONFIG = HERE / "config.yaml"
FACTS_FILE = HERE / "facts.json"

PLACE_STARTS = (
    "Carrig", "Kil", "Bally", "Drum", "Ard", "Glen", "Inish", "Knock", "Lis", "Rath",
    "Tulla", "Clon", "Dun", "Mulla", "Tober", "Cashel", "Derry", "Ennis",
)
PLACE_ENDS = (
    "more", "rane", "beg", "nagh", "owen", "keel", "darra", "finn", "lough", "corr",
    "mullen", "brack", "garve", "tully", "screen",
)
FIRST_NAMES = (
    "Orla", "Declan", "Maeve", "Cathal", "Nuala", "Fergal", "Aoife", "Tadhg", "Sorcha",
    "Ronan", "Grainne", "Eamon", "Brid", "Colm", "Ailbhe", "Donagh",
)
SURNAMES = (
    "Venn", "Quill", "Harrow", "Tolan", "Sleat", "Moran", "Vesey", "Crean", "Lusk",
    "Parle", "Garvan", "Hoey", "Rooke", "Cadden", "Mahony",
)
BOATS = ("Grey Heron", "Slow Tide", "Margaret Rose", "Silver Eel", "Kittiwake", "Lady Anne")
DOGS = ("Pilot", "Bramble", "Captain", "Sixpence", "Rua", "Tinker", "Marley", "Fenn")
COLOURS = ("blue", "green", "red", "yellow", "black", "copper")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

# (fact, question) templates. {place} is the distinctive subject; the rest is the answer.
ONE_SENTENCE = (
    ("The lighthouse at {place} was painted by a woman named {name}.",
     "Who painted the lighthouse at {place}?"),
    ("The chapel bell at {place} was cast from {number} melted horseshoes.",
     "How many horseshoes were melted to cast the chapel bell at {place}?"),
    ("The ferry that crosses to {place} is called the {boat}.",
     "What is the ferry that crosses to {place} called?"),
    ("The oldest oak in {place} was planted by a schoolmaster named {name}.",
     "Who planted the oldest oak in {place}?"),
    ("The weekly market in {place} is held every {weekday} in the tannery yard.",
     "On which day is the weekly market in {place} held?"),
    ("The well at {place} was sealed in the year {year} after a winter flood.",
     "In what year was the well at {place} sealed?"),
)
# The first sentence names the subject; the second holds the answer and cannot stand alone.
TWO_SENTENCE = (
    ("The harbourmaster at {place} kept a ledger of every ship.",
     "She stored it in a {colour} tin under the stairs.",
     "Where did the harbourmaster at {place} store her ledger?"),
    ("The baker in {place} won first prize at the county fair.",
     "His recipe called for {number} duck eggs.",
     "How many duck eggs did the prize recipe of the baker in {place} call for?"),
    ("The postmistress of {place} kept a dog that met every train.",
     "It was a terrier called {dog}.",
     "What was the name of the dog kept by the postmistress of {place}?"),
    ("The blacksmith at {place} made a new gate for the churchyard.",
     "He hung it in the spring of {year}.",
     "In what year did the blacksmith at {place} hang the churchyard gate?"),
    ("The ferryman at {place} carried a lantern on every crossing.",
     "He had bought it from a pedlar named {name}.",
     "From whom did the ferryman at {place} buy his lantern?"),
)


@dataclass(frozen=True)
class Fact:
    fact_id: str
    kind: str  # "one" or "two"
    novel_index: int
    place: str
    sentences: tuple[str, ...]
    question: str

    @property
    def text(self) -> str:
        return " ".join(self.sentences)


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _places(rng: random.Random, count: int) -> list[str]:
    options = [start + end for start in PLACE_STARTS for end in PLACE_ENDS]
    if count > len(options):
        raise ValueError(f"Only {len(options)} place names can be made; {count} were asked for")
    return rng.sample(options, count)


def _slots(rng: random.Random, place: str) -> dict[str, str]:
    return {
        "place": place,
        "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(SURNAMES)}",
        "number": str(rng.randint(12, 97)),
        "boat": rng.choice(BOATS),
        "weekday": rng.choice(WEEKDAYS),
        "year": str(rng.randint(1790, 1889)),
        "colour": rng.choice(COLOURS),
        "dog": rng.choice(DOGS),
    }


def make_facts(seed: int, novels: int, one_per_novel: int, two_per_novel: int) -> list[Fact]:
    """Every fact, in novel order, one-sentence facts first. The same seed gives the same list."""
    rng = random.Random(seed)
    places = iter(_places(rng, novels * (one_per_novel + two_per_novel)))
    facts: list[Fact] = []
    one_count = two_count = 0
    for novel in range(novels):
        for _ in range(one_per_novel):
            fact, question = ONE_SENTENCE[one_count % len(ONE_SENTENCE)]
            slots = _slots(rng, next(places))
            facts.append(
                Fact(f"one-{one_count:02d}", "one", novel, slots["place"],
                     (fact.format(**slots),), question.format(**slots))
            )
            one_count += 1
        for _ in range(two_per_novel):
            first, second, question = TWO_SENTENCE[two_count % len(TWO_SENTENCE)]
            slots = _slots(rng, next(places))
            facts.append(
                Fact(f"two-{two_count:02d}", "two", novel, slots["place"],
                     (first.format(**slots), second.format(**slots)), question.format(**slots))
            )
            two_count += 1
    return facts


def facts_from_config(config: dict, novels: int = 6) -> list[Fact]:
    return make_facts(
        config["seed"],
        novels,
        config["one_sentence_facts_per_novel"],
        config["two_sentence_facts_per_novel"],
    )


def save(facts: list[Fact], path: Path = FACTS_FILE) -> None:
    rows = [asdict(fact) for fact in facts]
    path.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def load(path: Path = FACTS_FILE) -> list[Fact]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Fact(**{**row, "sentences": tuple(row["sentences"])}) for row in rows]


if __name__ == "__main__":
    generated = facts_from_config(load_config())
    save(generated)
    print(f"Wrote {len(generated)} facts to {FACTS_FILE}")
