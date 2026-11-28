"""The invented Halvard case world: customers, orders, appliances, recalls, history and slots.

Drawn in code from a fixed seed, with no model calls, and written as CSV beside schema.sql.
Case building (cases.py) later adds planted history rows that particular cases need.
"""

import csv
import random
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

from lab.agent.policy import Policy

WORLD_DIR = Path(__file__).resolve().parents[3] / "datasets" / "halvard-cases" / "world"

# The eight regions the Season 2 corpus names (POL-WAR@2, "Warranty repairs in this region").
REGIONS = (
    "Scotland North",
    "Scotland South",
    "North of England",
    "Midlands",
    "Wales and West",
    "London and South East",
    "Northern Ireland",
    "Island Areas",
)
# Two letter serial prefix and three digit model number per product. Invented.
PRODUCT_CODES = {
    "Brio kettle": ("BK", 200),
    "Tessa dishwasher": ("TD", 450),
    "Orrin heat pump": ("OH", 900),
    "Lumen smart thermostat": ("LT", 120),
    "Keel washing machine": ("KW", 610),
    "Ashby tumble dryer": ("AD", 380),
    "Vale fridge freezer": ("VF", 720),
    "Corra induction hob": ("CH", 540),
    "Fenwick cooker hood": ("FH", 260),
    "Mira robot vacuum": ("MR", 330),
}
# Invented names from many cultures. Pairs are drawn at random, so no row names a real person.
FIRST_NAMES = (
    "Aisha",
    "Bram",
    "Chiara",
    "Dmitri",
    "Eilidh",
    "Farid",
    "Grace",
    "Hamza",
    "Ines",
    "Jonas",
    "Kemi",
    "Lars",
    "Mei",
    "Niamh",
    "Oluwaseun",
    "Priya",
    "Quentin",
    "Rhian",
    "Sanjay",
    "Tomasz",
    "Uma",
    "Viktor",
    "Wen",
    "Ximena",
    "Yusuf",
    "Zara",
    "Aled",
    "Beatriz",
    "Callum",
    "Deepa",
    "Emre",
    "Fiona",
    "Gareth",
    "Hana",
    "Idris",
    "Joanna",
    "Kofi",
    "Leila",
    "Mateo",
    "Nadia",
)
SURNAMES = (
    "Abernethy", "Baptiste", "Castellano", "Dlamini", "Evans", "Fitzgerald", "Gupta", "Haddad",
    "Ivanova", "Jansen", "Kowalski", "Lindqvist", "Mbeki", "Nakamura", "O'Rourke", "Petrovic",
    "Quinlan", "Rahman", "Sorensen", "Takahashi", "Umeh", "Varga", "Whitlock", "Xu", "Yilmaz",
    "Zielinski", "Agarwal", "Brennan", "Chaudhry", "Delacroix", "Eriksen", "Fairbairn", "Gallo",
    "Hughes", "Iqbal", "Jovanovic", "Kerr", "Lucchese", "MacLeod", "Novak",
)  # fmt: skip
CONTACT_PREFERENCES = ("mornings only", "afternoons only", "email only, no calls")
PLAN_WEIGHTS = {"none": 85, "extended_care": 10, "extended_care_plus": 5}
SLOT_HOURS = (8, 13)
SLOT_WINDOW_HOURS = 5
SLOTS_PER_REGION = 40


@dataclass(frozen=True)
class WorldSizes:
    # One customer per case, so no case inherits history planted for another.
    customers: int = 700
    orders: int = 1500
    retailer_appliances: int = 150
    past_cases: int = 900


@dataclass
class World:
    """Rows for every read table, keyed by table name, in insertion order."""

    tables: dict[str, list[dict[str, object]]] = field(default_factory=dict)

    def rows(self, table: str) -> list[dict[str, object]]:
        return self.tables.setdefault(table, [])


def serial_for(product: str, number: int) -> str:
    prefix, model = PRODUCT_CODES[product]
    return f"{prefix}{model // 10}-{number:05d}"


def model_code(product: str) -> str:
    prefix, model = PRODUCT_CODES[product]
    return f"HV-{prefix}-{model}"


DEFAULT_SIZES = WorldSizes()


def build_world(policy: Policy, seed: int, sizes: WorldSizes = DEFAULT_SIZES) -> World:
    rng = random.Random(seed)
    world = World()
    _products(world, policy)
    _customers(world, rng, sizes.customers)
    serials = _serial_numbers(rng, sizes.orders + sizes.retailer_appliances)
    _orders(world, rng, policy, sizes.orders, serials[: sizes.orders])
    _retailer(world, rng, policy, sizes.retailer_appliances, serials[sizes.orders :])
    _recalls(world)
    _past_cases(world, rng, policy, sizes.past_cases)
    _slots(world, rng, policy)
    return world


def _products(world: World, policy: Policy) -> None:
    for product in policy.cover_months:
        world.rows("products").append(
            {"product": product, "model_code": model_code(product), "line": policy.lines[product]}
        )


def _customers(world: World, rng: random.Random, count: int) -> None:
    for index in range(1, count + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(SURNAMES)
        handle = f"{first}.{last}".lower().replace("'", "")
        world.rows("customers").append(
            {
                "customer_id": f"C-{index:04d}",
                "name": f"{first} {last}",
                "email": f"{handle}.{index}@example.test",
                "region": rng.choice(REGIONS),
                "contact_pref": rng.choice(CONTACT_PREFERENCES) if rng.random() < 0.1 else "",
            }
        )


def _serial_numbers(rng: random.Random, count: int) -> list[int]:
    return rng.sample(range(10000, 99999), count)


def _delivery_date(rng: random.Random, policy: Policy) -> date:
    """Spread over seven years before as_of, weighted towards recent deliveries."""
    days_back = int(rng.triangular(1, 7 * 365, 300))
    return policy.as_of - timedelta(days=days_back)


def _orders(
    world: World, rng: random.Random, policy: Policy, count: int, numbers: list[int]
) -> None:
    customers = world.rows("customers")
    products = list(policy.cover_months)
    for index, number in enumerate(numbers, start=1):
        product = rng.choice(products)
        delivered = _delivery_date(rng, policy)
        plan = rng.choices(list(PLAN_WEIGHTS), weights=list(PLAN_WEIGHTS.values()))[0]
        world.rows("orders").append(
            {
                "order_id": f"H-{100000 + index}",
                "customer_id": rng.choice(customers)["customer_id"],
                "product": product,
                "serial": serial_for(product, number),
                "order_date": (delivered - timedelta(days=rng.randint(2, 21))).isoformat(),
                "delivery_date": delivered.isoformat(),
                "price": policy.prices[product],
                "plan": plan,
            }
        )


def _retailer(
    world: World, rng: random.Random, policy: Policy, count: int, numbers: list[int]
) -> None:
    customers = world.rows("customers")
    for number in numbers[:count]:
        product = rng.choice(list(policy.cover_months))
        world.rows("retailer_appliances").append(
            {
                "serial": serial_for(product, number),
                "product": product,
                "customer_id": rng.choice(customers)["customer_id"],
                "receipt_date": _delivery_date(rng, policy).isoformat(),
                "price": policy.prices[product],
            }
        )


# Three invented recall batches: serial number ranges on three products.
RECALLS = (
    ("Ashby tumble dryer", 30000, 34999, "invented: thermal cut-out may fail to reset"),
    ("Corra induction hob", 60000, 62999, "invented: control panel may not respond"),
    ("Mira robot vacuum", 45000, 47999, "invented: battery may swell"),
)


def _recalls(world: World) -> None:
    for product, low, high, reason in RECALLS:
        world.rows("recalls").append(
            {
                "product": product,
                "serial_from": serial_for(product, low),
                "serial_to": serial_for(product, high),
                "reason": reason,
            }
        )


def is_recalled(product: str, serial: str) -> bool:
    return any(
        product == name and serial_for(name, low) <= serial <= serial_for(name, high)
        for name, low, high, _ in RECALLS
    )


BACKGROUND_FAULTS = ("no_power", "leak", "noise", "not_heating", "error_code", "poor_performance")


def _past_cases(world: World, rng: random.Random, policy: Policy, count: int) -> None:
    """Closed background history. Cases needing a particular history get planted rows later."""
    orders = world.rows("orders")
    for _ in range(count):
        order = rng.choice(orders)
        delivered = date.fromisoformat(str(order["delivery_date"]))
        span = max((policy.as_of - delivered).days - 30, 1)
        opened = delivered + timedelta(days=rng.randint(1, span))
        fault = rng.choice(BACKGROUND_FAULTS)
        add_past_case(
            world,
            customer_id=str(order["customer_id"]),
            serial=str(order["serial"]),
            fault=fault,
            opened=opened,
            status="closed",
            outcome="repair_booked",
            summary=f"Reported {fault.replace('_', ' ')}; a warranty repair was completed.",
        )


def add_past_case(
    world: World,
    *,
    customer_id: str,
    serial: str | None,
    fault: str | None,
    opened: date,
    status: str,
    outcome: str | None,
    summary: str,
    goodwill_amount: float | None = None,
) -> str:
    rows = world.rows("past_cases")
    case_ref = f"PC-{len(rows) + 1:05d}"
    rows.append(
        {
            "case_ref": case_ref,
            "customer_id": customer_id,
            "serial": serial or "",
            "fault": fault or "",
            "opened": opened.isoformat(),
            "status": status,
            "outcome": outcome or "",
            "goodwill_amount": "" if goodwill_amount is None else goodwill_amount,
            "summary": summary,
        }
    )
    return case_ref


def _slots(world: World, rng: random.Random, policy: Policy) -> None:
    for region_index, region in enumerate(REGIONS):
        day = policy.as_of + timedelta(days=1)
        for slot in range(SLOTS_PER_REGION):
            hour = SLOT_HOURS[slot % 2]
            if slot % 2 == 0 and slot:
                day += timedelta(days=rng.choice((1, 1, 2)))
            world.rows("service_slots").append(
                {
                    "slot_id": f"S-{region_index + 1}-{slot + 1:03d}",
                    "region": region,
                    "starts": datetime.combine(day, time(hour)).isoformat(),
                    "window_hours": SLOT_WINDOW_HOURS,
                    "taken": 0,
                }
            )


READ_TABLES = (
    "customers",
    "products",
    "orders",
    "retailer_appliances",
    "recalls",
    "past_cases",
    "service_slots",
)


def write_csv(world: World, directory: Path = WORLD_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for table in READ_TABLES:
        rows = world.rows(table)
        path = directory / f"{table}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        written.append(path)
    return written


def load_database(target: Path | str, directory: Path = WORLD_DIR) -> sqlite3.Connection:
    """A fresh database from schema.sql and the world CSVs. ':memory:' for a throwaway copy."""
    # Shared across threads only as a template, copied under a lock (env.fresh_database).
    connection = sqlite3.connect(target, check_same_thread=False)
    connection.executescript((directory / "schema.sql").read_text(encoding="utf-8"))
    for table in READ_TABLES:
        with (directory / f"{table}.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            continue
        columns = list(rows[0])
        marks = ", ".join("?" for _ in columns)
        connection.executemany(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})",  # noqa: S608
            [[_blank_to_null(row[c]) for c in columns] for row in rows],
        )
    connection.commit()
    return connection


def _blank_to_null(value: str) -> str | None:
    return None if value == "" else value
