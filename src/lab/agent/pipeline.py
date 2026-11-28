"""E1's fixed pipeline: the same steps for every case, decided in code, not by a model.

1. Triage the message with the Season 4 reference (gpt-6-luna, the definitions prompt).
2. Find the appliance: each order number in the message, else the customer's one order for
   the triaged product. It cannot ask the customer or read photos, so if that fails it escalates.
3. Check the warranty and read past cases.
4. Decide with the policy code, from what the records show and what triage found. It cannot
   see an exclusion or a time preference stated in the message.
5. Act through the same tools as the agent, then one model call writes the reply.
Runs through the same tools, audit log and scorer as the agent, so the arms compare directly.
"""

import json
import re
from datetime import date, timedelta
from functools import cache

from lab.adapt.definitions import Definitions
from lab.adapt.output import parse_triage
from lab.adapt.prompts import triage_system
from lab.agent.caller import ModelCaller
from lab.agent.case_model import CaseFacts
from lab.agent.config import Arm
from lab.agent.env import CaseEnv
from lab.agent.kb import REPO, KeywordKB
from lab.agent.loop import CaseRun, ToolEvent, Turn, _end_state
from lab.agent.policy import Claim, Outcome, decide
from lab.agent.tools import HarnessRules, run_tool
from lab.providers.base import GenerationRequest, GenerationResult

ORDER = re.compile(r"H-\d{6}")
ROUTES = REPO / "datasets" / "halvard-tasks" / "routes.yaml"
REPLY_SYSTEM = (
    "Write a short, polite reply from Halvard Home (an invented appliance maker) to a customer, "
    "telling them the decision below and what happens next. British English, under 80 words."
)


@cache
def definitions() -> Definitions:
    return Definitions.load(ROUTES)


class Pipeline:
    def __init__(self, facts: CaseFacts, message: str, arm: Arm, caller: ModelCaller) -> None:
        self.facts = facts
        self.message = message
        self.arm = arm
        self.caller = caller
        self.env = CaseEnv.open(facts)
        self.email = str(self.env.customer()["email"])
        self.turns: list[Turn] = []
        self.events: list[ToolEvent] = []

    def _model(self, system: str, prompt: str, max_tokens: int) -> GenerationResult:
        request = GenerationRequest(
            provider=self.arm.model.provider,
            model=self.arm.model.model,
            system=system,
            prompt=prompt,
            max_output_tokens=max_tokens,
            reasoning=self.arm.model.reasoning,
            metadata={"case_id": self.facts.case_id, "arm": self.arm.name},
        )
        result, source = self.caller(request)
        self.turns.append(
            Turn(
                index=len(self.turns),
                request_hash=result.request_hash,
                source=source,
                text=result.text,
                tool_calls=(),
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                finish_reason=result.finish_reason,
            )
        )
        return result

    def _tool(self, name: str, **args: object) -> dict[str, object]:
        result = run_tool(self.env, KeywordKB(), HarnessRules(), name, dict(args))
        outcome = "ok" if "error" not in result else "tool_error"
        self.events.append(
            ToolEvent(
                turn=len(self.turns),
                call_id=f"p{len(self.events)}",
                name=name,
                arguments_json=json.dumps(args, sort_keys=True),
                result_json=json.dumps(result, default=str),
                outcome=outcome,
            )
        )
        return result

    def run(self) -> CaseRun:
        triage = parse_triage(
            self._model(
                triage_system("definitions", definitions()),
                f"Customer message:\n{self.message}",
                200,
            ).text,
            definitions(),
        ).label
        if triage is not None and (triage.route == "complaint" or triage.safety):
            # Rules 1 and 2 come before identifying the appliance: escalate every appliance.
            reason = "formal_complaint" if triage.route == "complaint" else "safety_incident"
            for serial in sorted(self.env.case_serials()):
                self._close(serial, Outcome("escalate", reason))
            return self._finish()
        orders = self._orders(triage.product if triage else None)
        for serial in self.env.case_serials():
            if serial not in {o["serial"] for o in orders}:
                self._close(serial, Outcome("escalate", "facts_unknown"))
        cases = self._tool("read_past_cases", customer_email=self.email).get("cases", [])
        for order in orders:
            self._handle(order, triage, cases)
        return self._finish()

    def _finish(self) -> CaseRun:
        run = CaseRun(
            case_id=self.facts.case_id,
            arm=self.arm.name,
            repeat=0,
            stop_reason="closed" if self.env.all_closed() else "no_tool_call",
            turns=tuple(self.turns),
            events=tuple(self.events),
            end_state=_end_state(self.env),
        )
        self.env.db.close()
        return run

    def _orders(self, product: str | None) -> list[dict[str, object]]:
        found = []
        for number in dict.fromkeys(ORDER.findall(self.message)):
            found += self._tool("lookup_order", order_id=number).get("orders", [])
        if not found and product:
            listed = self._tool("lookup_order", customer_email=self.email, product=product)
            orders = listed.get("orders", [])
            found = orders if len(orders) == 1 else []
        return [o for o in found if o["serial"] in self.env.case_serials()]

    def _handle(self, order: dict, triage, cases: list[dict]) -> None:
        serial = str(order["serial"])
        cover = self._tool("check_warranty", serial=serial)
        fault = (triage.fault if triage else None) or "error_code"
        outcome = decide(self.env.policy, self._claim(order, cover, triage, fault, cases))
        if outcome.decision == "repair_booked":
            self._tool("book_service_visit", serial=serial, fault=fault)
        if outcome.decision == "refund":
            refund = {"serial": serial, "amount": outcome.amount, "kind": outcome.reason}
            if outcome.approval_needed:
                approval = self._tool(
                    "request_approval", **refund, reason="Policy gives this refund."
                )
                refund["approval_id"] = approval.get("approval_id")
            self._tool("issue_refund", **refund)
        self._close(serial, outcome)

    def _claim(self, order: dict, cover: dict, triage, fault: str, cases: list[dict]) -> Claim:
        serial = str(order["serial"])
        since = (
            self.env.policy.as_of - timedelta(days=self.env.policy.goodwill_once_days)
        ).isoformat()
        same = [c for c in cases if c["serial"] == serial and c["fault"] == fault]
        route = triage.route if triage else "warranty_claim"
        return Claim(
            product=str(order["product"]),
            delivered=date.fromisoformat(str(order["delivery_date"])),
            price=float(order["price"]),
            plan=order["plan"],  # type: ignore[arg-type]
            fault=fault,
            wants="refund" if route == "return_refund" else "repair",
            safety=bool(triage and triage.safety),
            formal_complaint=route == "complaint",
            cosmetic_reported_after_days=int(cover.get("days_since_delivery", 0)),
            recalled=bool(cover.get("recalled")),
            earlier_repairs_same_fault=sum(
                1 for c in same if c["status"] == "closed" and c["outcome"] == "repair_booked"
            ),
            open_case_ref=next((str(c["case_ref"]) for c in same if c["status"] == "open"), None),
            goodwill_in_last_year=any(
                c["goodwill_amount"] and str(c["opened"]) >= since for c in cases
            ),
        )

    def _close(self, serial: str, outcome: Outcome) -> None:
        reply = self._model(
            REPLY_SYSTEM, f"Decision: {outcome.decision}. Reason: {outcome.reason}.", 200
        ).text
        args = {"serial": serial, "decision": outcome.decision, "reason": outcome.reason,
                "existing_case": outcome.existing_case, "reply": reply or "Thank you."}  # fmt: skip
        result = self._tool("close_case", **args)
        if "not closed" in str(result.get("status", "")):
            self._tool("close_case", **args)


def run_pipeline(facts: CaseFacts, message: str, arm: Arm, caller: ModelCaller) -> CaseRun:
    return Pipeline(facts, message, arm, caller).run()
