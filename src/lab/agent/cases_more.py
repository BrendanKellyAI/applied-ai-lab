"""Sequences (E7) and long cases (E8).

Sequences: one customer, three to five cases in order. A later case's expected outcome depends
on an earlier one, through one of three links:
  preference     the customer states a time preference once (it is not in the database), and
                 every later booking must respect it
  goodwill       an earlier case pays a goodwill refund, so a later one cannot have another
  repair_failed  the same fault comes back after a repair; the third report gets a replacement
Expected outcomes assume every earlier case in the sequence ended as expected. Whether a run
records earlier outcomes in the database, or leaves them to the agent's memory, is E7's design.

Long cases: one household message about several appliances, with a long case history, needing
20 or more tool calls.
"""

from datetime import timedelta

from lab.agent.case_draw import fault_words
from lab.agent.case_model import Appliance, CaseFacts
from lab.agent.cases import WANTS_WORDS, CaseBuilder
from lab.agent.world import RECALLS, add_past_case

LINKS = ("preference", "goodwill", "repair_failed")
PREFERENCE_WORDS = {"morning": "mornings only", "afternoon": "afternoons only"}


class SequenceBuilder:
    def __init__(self, builder: CaseBuilder) -> None:
        self.b = builder
        self.d = builder.d
        self.rng = builder.rng
        self.policy = builder.policy

    def _free_customer(self) -> dict[str, object]:
        """A customer with no preference on record, so a stated one lives only in the chat."""
        while True:
            customer = self.d.customer()
            if not customer["contact_pref"]:
                return customer

    def sequence(self, number: int, split: str) -> list[CaseFacts]:
        link = LINKS[number % len(LINKS)]
        customer = self._free_customer()
        length = self.rng.randint(3, 5)
        steps = getattr(self, f"_{link}")(customer, length)
        sequence_id = f"S{split[0].upper()}-{number + 1:02d}"
        return [
            facts.model_copy(
                update={
                    "case_id": f"{sequence_id}-{position}",
                    "split": split,
                    "sequence_id": sequence_id,
                    "sequence_position": position,
                    "tags": (link, *facts.tags),
                }
            )
            for position, facts in enumerate(steps, start=1)
        ]

    def _routine(self, customer: dict[str, object], **facts: object) -> Appliance:
        return self.b._in_cover(customer, wants="repair", **facts)

    def _preference(self, customer: dict[str, object], length: int) -> list[CaseFacts]:
        time_of_day = self.rng.choice(("morning", "afternoon"))
        steps = []
        for position in range(length):
            appliance = self._routine(customer)
            say = self.b._basic_say(appliance)
            if position == 0:
                say.append(
                    f"You say that from now on you can only do {PREFERENCE_WORDS[time_of_day]}."
                )
            steps.append(self._case(customer, appliance, say, time_of_day=time_of_day))
        return steps

    def _goodwill(self, customer: dict[str, object], length: int) -> list[CaseFacts]:
        steps, used = [], False
        goodwill_positions = {0, self.rng.randint(1, length - 1)}
        for position in range(length):
            if position in goodwill_positions:
                product = self.b._product()
                delivered = self.d.delivered_out_of_cover_by(product, "none", 1, 90)
                appliance = self.d.appliance(
                    customer, product, delivered, wants="refund", goodwill_in_last_year=used
                )
                used = True
            else:
                appliance = self._routine(customer)
            steps.append(self._case(customer, appliance, self.b._basic_say(appliance)))
        return steps

    def _repair_failed(self, customer: dict[str, object], length: int) -> list[CaseFacts]:
        repeat = self._routine(customer)
        steps = []
        for position in range(length):
            if position < 3:
                appliance = repeat.model_copy(update={"earlier_repairs_same_fault": position})
                say = self.b._basic_say(appliance)
                if position:
                    say.append(
                        "You say the engineer repaired this exact fault before, but it is back."
                    )
            else:
                appliance = self._routine(customer)
                say = self.b._basic_say(appliance)
            steps.append(self._case(customer, appliance, say))
        return steps

    def _case(
        self,
        customer: dict[str, object],
        appliance: Appliance,
        say: list[str],
        time_of_day: str | None = None,
    ) -> CaseFacts:
        stated = PREFERENCE_WORDS[time_of_day] if time_of_day else None
        return self.b._case("sequence", customer, (appliance,), say, stated_earlier=stated)


class LongCaseBuilder:
    """One household, several appliances, a long history."""

    def __init__(self, builder: CaseBuilder) -> None:
        self.b = builder
        self.d = builder.d
        self.rng = builder.rng
        self.policy = builder.policy

    def long_case(self, number: int, split: str) -> CaseFacts:
        customer = self.d.customer()
        appliances = [self._appliance(customer, slot) for slot in range(self.rng.randint(4, 6))]
        self._history(customer, appliances)
        say = [f"You write about {len(appliances)} Halvard appliances in one message."]
        for appliance in appliances:
            say.append(
                f"Your {appliance.product} (order {appliance.order_id}): "
                f"{fault_words(appliance.fault, self.rng)}. {WANTS_WORDS[appliance.wants]}"
            )
        facts = self.b._case("long", customer, tuple(appliances), say)
        return facts.model_copy(
            update={"case_id": f"L{split[0].upper()}-{number + 1:02d}", "split": split}
        )

    def _appliance(self, customer: dict[str, object], slot: int) -> Appliance:
        choice = (slot + self.rng.randint(0, 4)) % 5
        product = self.b._product()
        if choice == 0:
            delivered = self.d.delivered_out_of_cover_by(product, "none", 91, 900)
            return self.d.appliance(customer, product, delivered, wants="repair")
        if choice == 1:
            product = self.rng.choice([r[0] for r in RECALLS])
            return self.b._in_cover(customer, product=product, recalled=True, wants="repair")
        if choice == 2:
            return self.d.appliance(
                customer, product, self.d.delivered_days_ago(8, 100), wants="refund"
            )
        return self.b._in_cover(customer, product=product, wants="repair")

    def _history(self, customer: dict[str, object], appliances: list[Appliance]) -> None:
        """Ten to twenty older closed cases across the household's older appliances."""
        older = [a for a in appliances if (self.policy.as_of - a.delivered).days > 90]
        for _ in range(self.rng.randint(10, 20) if older else 0):
            appliance = self.rng.choice(older)
            age = (self.policy.as_of - appliance.delivered).days
            other_faults = [
                f for f in ("noise", "error_code", "door_or_lid") if f != appliance.fault
            ]
            add_past_case(
                self.d.world,
                customer_id=str(customer["customer_id"]),
                serial=appliance.serial,
                fault=self.rng.choice(other_faults),
                opened=self.policy.as_of - timedelta(days=self.rng.randint(30, age - 1)),
                status="closed",
                outcome="repair_booked",
                summary="An unrelated fault, repaired under the warranty.",
            )
