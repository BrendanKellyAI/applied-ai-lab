"""A mock for the fixed pipeline: perfect triage from the case's facts, and a stock reply.

Shows the best the pipeline can do when triage is never wrong, and drives its tests and dry
runs with no spend. Withheld products and faults stay unknown, as they would to real triage.
"""

import json
from collections.abc import Callable, Mapping

from lab.agent.case_model import CaseFacts
from lab.providers.base import GenerationRequest


def perfect_triage(cases: Mapping[str, CaseFacts]) -> Callable[[GenerationRequest], str]:
    def respond(request: GenerationRequest) -> str:
        if not request.prompt.startswith("Customer message:"):
            return "Thank you for your message. We have recorded the decision on your case."
        facts = cases[request.metadata["case_id"]]
        appliance = facts.appliances[0]
        route = "warranty_claim"
        if appliance.wants == "refund":
            route = "return_refund"
        if appliance.formal_complaint:
            route = "complaint"
        label = {
            "route": route,
            "safety": appliance.safety,
            "product": None if "product" in facts.withhold else appliance.product,
            "fault": None if "fault" in facts.withhold else appliance.fault,
        }
        return json.dumps(label)

    return respond
