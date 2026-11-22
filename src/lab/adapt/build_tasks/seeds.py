"""Task A seeds: the label, hard case and persona of every item, drawn in code from the seed.

The label is decided here, before any call, so it is right by construction. Each split draws
its own seeds, with exact counts of safety and hard case items, in a shuffled order that
depends only on the seed and the split.
"""

import math
import random
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from lab.adapt.build_tasks.config import Split, TaskAConfig
from lab.adapt.definitions import Definitions, Label

SAFETY_FAULTS = ("burning_or_smoke", "electric_shock")
SAFETY_ROUTES = ("warranty_claim", "return_refund", "complaint")
ANGRY_ROUTES = ("warranty_claim", "return_refund", "servicing_booking", "delivery")
# The faults that make sense for each route; None means no fault is described.
ROUTE_FAULTS: dict[str, tuple[str | None, ...]] = {
    "warranty_claim": (
        "no_power",
        "leak",
        "noise",
        "not_heating",
        "not_cooling",
        "error_code",
        "connectivity",
        "door_or_lid",
        "poor_performance",
    ),
    "return_refund": (None, "damaged_on_arrival", "no_power", "leak", "noise", "poor_performance"),
    "delivery": (None,),
    "servicing_booking": (None, None, "noise", "poor_performance"),
    "spare_part": (None, None, "door_or_lid"),
    "how_to_use": (None, None, "error_code", "connectivity"),
    "complaint": (None, "no_power", "leak", "noise", "poor_performance", "damaged_on_arrival"),
    "other": (None,),
}
# Routes on which a message may name no product at all, and how often.
NO_PRODUCT_SHARE = {"delivery": 0.2, "complaint": 0.3, "how_to_use": 0.1}

PLAIN = "plain"
SAFETY = "safety"


class Seed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    split: Split
    label: Label
    # PLAIN, SAFETY or a hard case name from routes.yaml.
    kind: str
    # The other product named in a two_products item, or the unsold product an
    # unknown_product item names.
    also_named: str | None
    tone: str
    habit: str
    channel: str
    name: str
    length: tuple[int, int]


def seed_count(size: int, overgenerate: float) -> int:
    return math.ceil(size * (1 + overgenerate))


def kinds_for(n: int, definitions: Definitions, rng: random.Random) -> list[str]:
    """Exact counts of each hard case and of safety items, the rest plain, shuffled.

    played_down_safety items count towards the safety share."""
    kinds: list[str] = []
    for name, case in definitions.hard_cases.items():
        kinds += [name] * round(n * case.share)
    safety_total = round(n * definitions.safety.share)
    kinds += [SAFETY] * max(0, safety_total - kinds.count("played_down_safety"))
    kinds += [PLAIN] * (n - len(kinds))
    rng.shuffle(kinds)
    return kinds


def draw_seeds(
    split: Split,
    n: int,
    config: TaskAConfig,
    definitions: Definitions,
    seed: int,
) -> list[Seed]:
    rng = random.Random(f"{seed}:task-a:{split}")
    return [
        _seed(f"A-{split}-{index:05d}", split, kind, config, definitions, rng)
        for index, kind in enumerate(kinds_for(n, definitions, rng))
    ]


def _seed(
    seed_id: str,
    split: Split,
    kind: str,
    config: TaskAConfig,
    definitions: Definitions,
    rng: random.Random,
) -> Seed:
    label, also_named = _label(kind, config, definitions, rng)
    label.check_against(definitions)
    personas = config.personas
    tone = "frustrated" if kind == "angry_not_complaint" else rng.choice(personas.tone)
    return Seed(
        id=seed_id,
        split=split,
        label=label,
        kind=kind,
        also_named=also_named,
        tone=tone,
        habit=rng.choice(personas.habit),
        channel=rng.choice(personas.channel),
        name=rng.choice(personas.name),
        length=rng.choice(config.length_bands),
    )


def _label(
    kind: str, config: TaskAConfig, definitions: Definitions, rng: random.Random
) -> tuple[Label, str | None]:
    products = definitions.products
    if kind in (SAFETY, "played_down_safety"):
        route = rng.choice(SAFETY_ROUTES)
        fault = rng.choice(SAFETY_FAULTS)
        return Label(route=route, safety=True, product=rng.choice(products), fault=fault), None
    if kind == "unknown_product":
        unsold = rng.choice(config.unsold_products)
        return Label(route="other", safety=False, product=None, fault=None), unsold
    if kind == "angry_not_complaint":
        return _ordinary(rng.choice(ANGRY_ROUTES), products, rng), None
    route = _weighted_route(config.route_weights, rng)
    if kind == "two_products":
        route = route if route != "other" else "warranty_claim"
        label = _ordinary(route, products, rng, always_product=True)
        other = rng.choice([p for p in products if p != label.product])
        return label, other
    return _ordinary(route, products, rng), None


def _ordinary(
    route: str, products: Sequence[str], rng: random.Random, *, always_product: bool = False
) -> Label:
    fault = rng.choice(ROUTE_FAULTS[route])
    if (
        route == "other"
        or not always_product
        and fault is None
        and rng.random() < NO_PRODUCT_SHARE.get(route, 0.0)
    ):
        product = None
    else:
        product = rng.choice(products)
    return Label(route=route, safety=False, product=product, fault=fault)


def _weighted_route(weights: dict[str, float], rng: random.Random) -> str:
    routes = list(weights)
    return rng.choices(routes, weights=[weights[r] for r in routes], k=1)[0]
