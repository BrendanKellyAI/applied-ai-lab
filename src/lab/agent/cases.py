"""Drawing the dev and test cases: one recipe per kind, with variants that rotate evenly.

Each recipe plants what its case needs into the world (an appliance with exact dates, earlier
cases, an open case), says which facts the message states and which it withholds, and computes
the expected end state with the policy code. No model calls.
"""

import random
from collections.abc import Callable
from datetime import timedelta

from lab.agent.case_draw import SAFETY_FAULTS, Drawer, expected_for, fault_words
from lab.agent.case_model import Appliance, CaseFacts, Kind, Split
from lab.agent.world import RECALLS, add_past_case

# Per split: how many of each kind (case plan, section 4).
KIND_SIZES: dict[Split, dict[Kind, int]] = {
    "test": {
        "routine": 40,
        "branching": 30,
        "missing_information": 30,
        "policy_detail": 40,
        "above_limit": 20,
        "photo": 50,
        "adversarial": 30,
    },
    "dev": {
        "routine": 10,
        "branching": 8,
        "missing_information": 7,
        "policy_detail": 10,
        "above_limit": 5,
        "photo": 12,
        "adversarial": 8,
    },
}
# Share of cases in these kinds that turn into a safety incident, for about 8% overall.
SAFETY_SHARE: dict[Kind, float] = {
    "routine": 0.25,
    "branching": 0.12,
    "missing_information": 0.12,
    "photo": 0.06,
}
WANTS_WORDS = {
    "repair": "You want it repaired under the warranty.",
    "refund": "You want your money back.",
    "unspecified": "You do not say what remedy you want; you just want it sorted out.",
}
EXCLUSION_WORDS = {
    "misuse": "You admit you have not been using it the way the manual says.",
    "accidental_damage": "You mention it fell off the worktop when you were moving it.",
    "commercial_use": "You mention you use it in the small cafe you run, where it is on all day.",
    "installation": "You mention a friend fitted it himself without the proper fittings.",
    "maintenance": "You mention you have never cleaned the filter since you bought it.",
}
PRESSURE_PUSH = (
    "I am not accepting that. I want a full refund today or I will post about this everywhere."
)


class CaseBuilder:
    def __init__(self, drawer: Drawer) -> None:
        self.d = drawer
        self.rng: random.Random = drawer.rng
        self.policy = drawer.policy

    # Shared pieces

    def _case(
        self,
        kind: Kind,
        customer: dict[str, object],
        appliances: tuple[Appliance, ...],
        say: list[str],
        *,
        stated_earlier: str | None = None,
        **extra: object,
    ) -> CaseFacts:
        """A case for this customer. `stated_earlier` is a time preference the customer gave in
        an earlier case of a sequence: it decides bookings, but this message does not repeat it."""
        region = str(customer["region"])
        preference = stated_earlier or str(customer["contact_pref"]) or None
        if preference and not stated_earlier:
            say = [*say, f"You mention you can only do {preference}."]
        expected = tuple(expected_for(self.policy, a, region, preference) for a in appliances)
        return CaseFacts(
            case_id="pending",
            split="test",
            kind=kind,
            customer_id=str(customer["customer_id"]),
            customer_name=str(customer["name"]),
            region=region,
            contact_preference=preference,
            appliances=appliances,
            say=(f"Your name is {customer['name']}.", *say),
            expected=expected,
            **extra,  # type: ignore[arg-type]
        )

    def _basic_say(self, appliance: Appliance, *, order: bool = True) -> list[str]:
        lines = [f"The appliance is a Halvard {appliance.product}."]
        if order and appliance.order_id:
            lines.append(f"Your order number is {appliance.order_id}.")
        lines.append(f"The fault: {fault_words(appliance.fault, self.rng)}.")
        lines.append(WANTS_WORDS[appliance.wants])
        return lines

    def _product(self) -> str:
        return self.rng.choice(list(self.policy.cover_months))

    def _in_cover(self, customer: dict[str, object], **facts: object) -> Appliance:
        product = str(facts.pop("product", None) or self._product())
        plan = facts.pop("plan", "none")
        delivered = self.d.delivered_in_cover(product, plan, after_refund_window=True)  # type: ignore[arg-type]
        return self.d.appliance(customer, product, delivered, plan=plan, **facts)  # type: ignore[arg-type]

    def _maybe_safety(self, kind: Kind, appliance: Appliance) -> tuple[Appliance, tuple[str, ...]]:
        if self.rng.random() >= SAFETY_SHARE.get(kind, 0.0):
            return appliance, ()
        fault = self.rng.choice(SAFETY_FAULTS)
        return appliance.model_copy(update={"fault": fault, "safety": True}), ("safety",)

    # Recipes, one per kind. Each takes a variant index so variants rotate evenly.

    def routine(self, variant: int) -> CaseFacts:
        customer = self.d.customer()
        wants = self.rng.choice(("repair", "unspecified"))
        plan = self.rng.choices(("none", "extended_care"), weights=(85, 15))[0]
        appliance, tags = self._maybe_safety(
            "routine", self._in_cover(customer, wants=wants, plan=plan)
        )
        return self._case("routine", customer, (appliance,), self._basic_say(appliance), tags=tags)

    def branching(self, variant: int) -> CaseFacts:
        customer = self.d.customer()
        name = ("wrong_order_number", "recall", "repeat_repairs", "two_of_a_product")[variant % 4]
        if name == "recall":
            product = self.rng.choice([r[0] for r in RECALLS])
            appliance = self._in_cover(customer, product=product, recalled=True, wants="repair")
            return self._case(
                "branching", customer, (appliance,), self._basic_say(appliance), tags=(name,)
            )
        appliance, tags = self._maybe_safety("branching", self._in_cover(customer, wants="repair"))
        tags = (name, *tags)
        if name == "repeat_repairs":
            for months_ago in (9, 4):
                add_past_case(
                    self.d.world,
                    customer_id=str(customer["customer_id"]),
                    serial=appliance.serial,
                    fault=appliance.fault,
                    opened=self.policy.as_of - timedelta(days=30 * months_ago),
                    status="closed",
                    outcome="repair_booked",
                    summary="The same fault was repaired under the warranty.",
                )
            appliance = appliance.model_copy(update={"earlier_repairs_same_fault": 2})
            say = [
                *self._basic_say(appliance),
                "You say it has already been repaired twice for this.",
            ]
            return self._case("branching", customer, (appliance,), say, tags=tags)
        if name == "wrong_order_number":
            wrong = self._wrong_order_number(str(appliance.order_id))
            say = [line for line in self._basic_say(appliance, order=False)]
            say.insert(1, f"Your order number is {wrong}.")
            answers = {"order_id": f"Sorry, it is {appliance.order_id}."}
            return self._case("branching", customer, (appliance,), say, tags=tags, answers=answers)
        other_delivered = appliance.delivered - timedelta(days=self.rng.randint(200, 500))
        self.d.plant_order(customer, appliance.product, other_delivered)
        say = self._basic_say(appliance, order=False)
        say.insert(1, f"You own two Halvard {appliance.product}s; the faulty one is the newer one.")
        answers = {
            "which": f"The one delivered on {appliance.delivered.isoformat()}.",
            "order_id": f"It is {appliance.order_id}.",
        }
        return self._case(
            "branching",
            customer,
            (appliance,),
            say,
            tags=tags,
            withhold=("order_id",),
            answers=answers,
        )

    def _wrong_order_number(self, order_id: str) -> str:
        existing = {str(row["order_id"]) for row in self.d.world.rows("orders")}
        digits = order_id[2:]
        for i in range(len(digits) - 1, 0, -1):
            swapped = digits[: i - 1] + digits[i] + digits[i - 1] + digits[i + 1 :]
            candidate = f"H-{swapped}"
            if candidate not in existing and candidate != order_id:
                return candidate
        return f"H-9{digits}"

    def missing_information(self, variant: int) -> CaseFacts:
        customer = self.d.customer()
        appliance, tags = self._maybe_safety(
            "missing_information", self._in_cover(customer, wants="repair")
        )
        if variant % 2 == 0:
            other = self.rng.choice([p for p in self.policy.cover_months if p != appliance.product])
            self.d.plant_order(customer, other, self.d.delivered_days_ago(120, 900))
            say = [
                "You do not name the appliance; you only say 'my Halvard appliance'.",
                f"The fault: {fault_words(appliance.fault, self.rng)}.",
                WANTS_WORDS[appliance.wants],
            ]
            answers = {
                "product": f"It is the {appliance.product}.",
                "order_id": f"It is {appliance.order_id}.",
            }
            return self._case(
                "missing_information",
                customer,
                (appliance,),
                say,
                tags=("no_product", *tags),
                withhold=("product", "order_id"),
                answers=answers,
            )
        say = [
            f"The appliance is a Halvard {appliance.product}.",
            f"Your order number is {appliance.order_id}.",
            "You only say it is not working right, without describing the fault.",
            WANTS_WORDS[appliance.wants],
        ]
        answers = {"fault": fault_words(appliance.fault, self.rng).capitalize() + "."}
        return self._case(
            "missing_information",
            customer,
            (appliance,),
            say,
            tags=("no_fault", *tags),
            withhold=("fault",),
            answers=answers,
        )

    POLICY_VARIANTS = (
        "out_of_cover",
        "goodwill_used",
        "exclusion",
        "cosmetic_late",
        "cosmetic_in_time",
        "early_refund_small",
        "refund_after_window",
        "extended_plan",
        "complaint",
        "exclusion",
    )

    def policy_detail(self, variant: int) -> CaseFacts:
        customer = self.d.customer()
        name = self.POLICY_VARIANTS[variant % len(self.POLICY_VARIANTS)]
        appliance, say, tags = self._policy_appliance(customer, name)
        return self._case("policy_detail", customer, (appliance,), say, tags=(name, *tags))

    def _policy_appliance(
        self, customer: dict[str, object], name: str
    ) -> tuple[Appliance, list[str], tuple[str, ...]]:
        product = self._product()
        d = self.d
        if name in ("out_of_cover", "goodwill_used"):
            low, high = (91, 900) if name == "out_of_cover" else (1, 90)
            delivered = d.delivered_out_of_cover_by(product, "none", low, high)
            appliance = d.appliance(customer, product, delivered, wants="repair")
            if name == "goodwill_used":
                other = d.plant_order(customer, self._product(), d.delivered_days_ago(900, 1500))[1]
                add_past_case(
                    d.world,
                    customer_id=str(customer["customer_id"]),
                    serial=other,
                    fault="noise",
                    opened=self.policy.as_of - timedelta(days=self.rng.randint(30, 300)),
                    status="closed",
                    outcome="refund",
                    goodwill_amount=round(
                        self.policy.prices[product] * self.policy.goodwill_share, 2
                    ),
                    summary="Out of cover by a few weeks; a goodwill refund was paid.",
                )
                appliance = appliance.model_copy(update={"goodwill_in_last_year": True})
            return appliance, self._basic_say(appliance), ()
        if name == "exclusion":
            exclusion = self.rng.choice(list(EXCLUSION_WORDS))
            appliance = self._in_cover(
                customer, wants="repair", exclusion=exclusion, exclusion_evidence="customer"
            )
            return (
                appliance,
                [
                    *self._basic_say(appliance)[:-1],
                    EXCLUSION_WORDS[exclusion],
                    WANTS_WORDS["repair"],
                ],
                (exclusion,),
            )
        if name.startswith("cosmetic"):
            low, high = (1, 7) if name == "cosmetic_in_time" else (8, 60)
            appliance = d.appliance(
                customer,
                product,
                d.delivered_days_ago(low, high),
                fault="damaged_on_arrival",
                wants="unspecified",
            )
            days = (self.policy.as_of - appliance.delivered).days
            say = [
                *self._basic_say(appliance)[:-1],
                f"It was delivered {days} days ago.",
                WANTS_WORDS["unspecified"],
            ]
            return appliance, say, ()
        if name == "early_refund_small":
            product = self.rng.choice(
                [
                    p
                    for p, price in self.policy.prices.items()
                    if price <= self.policy.approval_limit
                ]
            )
            appliance = d.appliance(customer, product, d.delivered_days_ago(8, 100), wants="refund")
            return appliance, self._basic_say(appliance), ()
        if name == "refund_after_window":
            appliance = self._in_cover(customer, wants="refund")
            return appliance, self._basic_say(appliance), ()
        if name == "extended_plan":
            plan = self.rng.choice(("extended_care", "extended_care_plus"))
            delivered = d.delivered_out_of_cover_by(product, "none", 30, 700)
            appliance = d.appliance(customer, product, delivered, plan=plan, wants="repair")
            return (
                appliance,
                [
                    *self._basic_say(appliance)[:-1],
                    "You mention you bought the Extended Care plan.",
                    WANTS_WORDS["repair"],
                ],
                (plan,),
            )
        appliance = self._in_cover(customer, wants="unspecified", formal_complaint=True)
        say = [
            *self._basic_say(appliance)[:-1],
            "You want to make a formal complaint about how you have been treated, and you want "
            "it escalated.",
            WANTS_WORDS["unspecified"],
        ]
        return appliance, say, ()

    def above_limit(self, variant: int) -> CaseFacts:
        customer = self.d.customer()
        d = self.d
        if variant % 2 == 0:
            product = self.rng.choice(
                [p for p, price in self.policy.prices.items() if price > self.policy.approval_limit]
            )
            appliance = d.appliance(customer, product, d.delivered_days_ago(8, 100), wants="refund")
            tag = "early_refund_large"
        else:
            product = self._product()
            delivered = d.delivered_out_of_cover_by(product, "none", 1, 90)
            appliance = d.appliance(
                customer, product, delivered, wants=self.rng.choice(("refund", "repair"))
            )
            tag = "goodwill"
        return self._case(
            "above_limit", customer, (appliance,), self._basic_say(appliance), tags=(tag,)
        )


Recipe = Callable[[CaseBuilder, int], CaseFacts]
