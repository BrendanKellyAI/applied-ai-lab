"""Helpers for drawing cases: planted appliances with exact dates, fault wording, and outcomes.

Every case gets its own planted appliance (an order, or a retailer purchase) with dates chosen
so its rule applies exactly, rather than hoping a random world holds enough edge cases.
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from lab.agent.case_model import Appliance, ExpectedOutcome
from lab.agent.policy import Claim, Plan, Policy, add_months, cover_end, decide
from lab.agent.world import RECALLS, World, is_recalled, serial_for

# The faults each product can plausibly have (S4 Task A fault codes), safety faults apart.
PRODUCT_FAULTS: dict[str, tuple[str, ...]] = {
    "Brio kettle": ("no_power", "leak", "not_heating", "noise", "error_code"),
    "Tessa dishwasher": ("leak", "not_heating", "error_code", "door_or_lid", "poor_performance"),
    "Orrin heat pump": ("not_heating", "noise", "error_code", "connectivity", "no_power"),
    "Lumen smart thermostat": ("connectivity", "no_power", "error_code"),
    "Keel washing machine": ("leak", "noise", "door_or_lid", "error_code", "poor_performance"),
    "Ashby tumble dryer": ("not_heating", "noise", "no_power", "door_or_lid", "poor_performance"),
    "Vale fridge freezer": ("not_cooling", "leak", "noise", "door_or_lid", "error_code"),
    "Corra induction hob": ("no_power", "not_heating", "error_code"),
    "Fenwick cooker hood": ("noise", "no_power", "poor_performance"),
    "Mira robot vacuum": ("no_power", "connectivity", "poor_performance", "noise"),
}
FAULT_WORDS = {
    "no_power": "it will not switch on at all",
    "leak": "it is leaking water onto the floor",
    "noise": "it has started making a loud grinding noise",
    "not_heating": "it no longer heats up properly",
    "not_cooling": "it is not keeping food cold",
    "error_code": "it keeps showing error code E{code}",
    "connectivity": "it will not connect to the app or the wifi any more",
    "door_or_lid": "the door will not close and latch properly",
    "poor_performance": "it still runs but does a poor job",
    "damaged_on_arrival": "it arrived with a large dent in the side panel",
    "burning_or_smoke": "there was a burning smell and a little smoke coming from it",
    "electric_shock": "it gave me a tingle, like a small shock, when I touched it",
}
SAFETY_FAULTS = ("burning_or_smoke", "electric_shock")
PREFERENCE_TIME = {"mornings only": "morning", "afternoons only": "afternoon"}


@dataclass
class Drawer:
    """Draws planted appliances into the world, never reusing a serial number."""

    world: World
    policy: Policy
    rng: random.Random
    used_numbers: set[int] = field(default_factory=set)
    order_counter: int = 0
    used_customers: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        for table in ("orders", "retailer_appliances"):
            for row in self.world.rows(table):
                self.used_numbers.add(int(str(row["serial"]).split("-")[1]))
        self.order_counter = len(self.world.rows("orders"))

    def customer(self) -> dict[str, object]:
        """A customer no earlier case has used, so planted history never crosses cases."""
        free = [
            c for c in self.world.rows("customers") if c["customer_id"] not in self.used_customers
        ]
        if not free:
            raise ValueError("every customer is already in a case; enlarge the world")
        chosen = self.rng.choice(free)
        self.used_customers.add(str(chosen["customer_id"]))
        return chosen

    def serial(self, product: str, *, recalled: bool = False) -> str:
        while True:
            number = self._recall_number(product) if recalled else self.rng.randint(10000, 99999)
            serial = serial_for(product, number)
            if number not in self.used_numbers and is_recalled(product, serial) == recalled:
                self.used_numbers.add(number)
                return serial

    def _recall_number(self, product: str) -> int:
        low, high = next((lo, hi) for name, lo, hi, _ in RECALLS if name == product)
        return self.rng.randint(low, high)

    def fault(self, product: str) -> str:
        return self.rng.choice(PRODUCT_FAULTS[product])

    # Delivery dates that put a claim exactly where a rule applies.

    def delivered_days_ago(self, low: int, high: int) -> date:
        return self.policy.as_of - timedelta(days=self.rng.randint(low, high))

    def delivered_in_cover(self, product: str, plan: Plan, *, after_refund_window: bool) -> date:
        """In cover on as_of, and past the 100 day refund window if asked."""
        latest = cover_end(self.policy, product, self.policy.as_of, plan)
        cover_days = (latest - self.policy.as_of).days
        low = self.policy.early_refund_days + 1 if after_refund_window else 8
        return self.delivered_days_ago(low, max(low, min(cover_days - 1, 6 * 365)))

    def delivered_out_of_cover_by(self, product: str, plan: Plan, low: int, high: int) -> date:
        days_out = self.rng.randint(low, high)
        months = self.policy.cover_months[product] + self.policy.plan_months[plan]
        return add_months(self.policy.as_of - timedelta(days=days_out), -months)

    def plant_order(
        self,
        customer: dict[str, object],
        product: str,
        delivered: date,
        *,
        plan: Plan = "none",
        recalled: bool = False,
    ) -> tuple[str, str]:
        self.order_counter += 1
        order_id = f"H-{100000 + self.order_counter}"
        serial = self.serial(product, recalled=recalled)
        self.world.rows("orders").append(
            {
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "product": product,
                "serial": serial,
                "order_date": (delivered - timedelta(days=self.rng.randint(2, 21))).isoformat(),
                "delivery_date": delivered.isoformat(),
                "price": self.policy.prices[product],
                "plan": plan,
            }
        )
        return order_id, serial

    def plant_retailer(self, customer: dict[str, object], product: str, bought: date) -> str:
        serial = self.serial(product)
        self.world.rows("retailer_appliances").append(
            {
                "serial": serial,
                "product": product,
                "customer_id": customer["customer_id"],
                "receipt_date": bought.isoformat(),
                "price": self.policy.prices[product],
            }
        )
        return serial

    def appliance(
        self,
        customer: dict[str, object],
        product: str,
        delivered: date,
        *,
        plan: Plan = "none",
        recalled: bool = False,
        **facts: object,
    ) -> Appliance:
        order_id, serial = self.plant_order(
            customer, product, delivered, plan=plan, recalled=recalled
        )
        return Appliance(
            serial=serial,
            product=product,
            source="halvard",
            order_id=order_id,
            delivered=delivered,
            price=self.policy.prices[product],
            plan=plan,
            recalled=recalled,
            **{"fault": self.fault(product), **facts},  # type: ignore[arg-type]
        )


def expected_for(
    policy: Policy, appliance: Appliance, region: str, preference: str | None
) -> ExpectedOutcome:
    claim = Claim(
        product=appliance.product,
        delivered=appliance.delivered,
        price=appliance.price,
        plan=appliance.plan,
        fault=appliance.fault,
        wants=appliance.wants,
        safety=appliance.safety,
        formal_complaint=appliance.formal_complaint,
        exclusion=appliance.exclusion,
        cosmetic_reported_after_days=(policy.as_of - appliance.delivered).days,
        recalled=appliance.recalled,
        earlier_repairs_same_fault=appliance.earlier_repairs_same_fault,
        open_case_ref=appliance.open_case_ref,
        goodwill_in_last_year=appliance.goodwill_in_last_year,
        identifiable=appliance.identifiable,
    )
    outcome = decide(policy, claim)
    booked = outcome.decision == "repair_booked"
    return ExpectedOutcome(
        serial=appliance.serial,
        decision=outcome.decision,
        reason=outcome.reason,
        amount=outcome.amount,
        approval_needed=outcome.approval_needed,
        existing_case=outcome.existing_case,
        visit_region=region if booked else None,
        visit_time_of_day=PREFERENCE_TIME.get(preference or "") if booked else None,  # type: ignore[arg-type]
    )


def fault_words(fault: str, rng: random.Random) -> str:
    return FAULT_WORDS[fault].format(code=rng.randint(10, 49))
