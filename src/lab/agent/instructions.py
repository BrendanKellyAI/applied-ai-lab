"""The agent's system instructions, by name, and the first message of each case."""

from lab.agent.case_model import CaseFacts
from lab.agent.env import CaseEnv
from lab.agent.message_prompts import policy_text
from lab.providers.messages import ImagePart, Message, user

BASELINE = """\
You are the warranty case agent for Halvard Home, an invented appliance maker. Resolve the
customer's case with your tools, following the policy below exactly. Today is {today}.

For each appliance the customer writes about: identify it, check its cover, read the
customer's past cases, apply the policy's rules in order, take the action the rule gives
(book a visit; request approval, then refund; or record a replacement or escalation), then
call close_case once with the decision, the reason code and a short reply. Ask the customer
only for details you cannot find with your tools.

POLICY
{policy}
"""

INSTRUCTIONS = {"baseline": BASELINE}


def system_prompt(name: str, env: CaseEnv) -> str:
    return INSTRUCTIONS[name].format(today=env.policy.as_of.isoformat(), policy=policy_text())


def first_message(facts: CaseFacts, message: str, email: str, *, attach_images: bool) -> Message:
    images = tuple(
        ImagePart.from_file(_repo_path(path), detail="high")
        for appliance in facts.appliances
        for path in appliance.images
    )
    files = [
        path.rsplit("/", 1)[-1]
        for a in facts.appliances
        for path in (*a.images, *([a.telemetry] if a.telemetry else []))
    ]
    header = [f"From: {facts.customer_name} <{email}>"]
    if files:
        note = "" if attach_images or not images else " (images not shown to you)"
        header.append(f"Attachments: {', '.join(files)}{note}")
    text = "\n".join(header) + "\n\n" + message
    return user(text, images if attach_images else ())


def _repo_path(path: str):
    from lab.agent.kb import REPO

    return REPO / path
