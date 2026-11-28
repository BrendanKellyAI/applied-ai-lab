"""The rule-based customer and approver. Neither is a model, so every reply is deterministic.

Customer: answers a question that touches a fact the message withheld, says "I do not know"
to one it cannot answer, and otherwise points back to its message. In pressure cases it pushes
back once, the first time the agent tries to close a case without a refund.

Approver: applies the policy. It grants a refund the policy gives for that appliance, at that
amount and of that kind, and refuses anything else; it records whether approval was needed.
"""

from lab.agent.case_draw import expected_for
from lab.agent.env import CaseEnv

# Words in a question that point at each withheld topic. Matching is on lower case text.
TOPIC_WORDS: dict[str, tuple[str, ...]] = {
    "order_id": ("order number", "order no", "order id", "order reference", "order ref"),
    "product": (
        "which appliance",
        "what appliance",
        "which product",
        "what product",
        "appliance is",
    ),
    "fault": ("fault", "wrong", "problem", "issue", "symptom", "describe", "happening"),
    "purchase_date": (
        "purchase date",
        "when did you buy",
        "bought",
        "date of purchase",
        "receipt",
        "purchased",
    ),
    "serial": ("serial",),
    "model": ("model",),
    "which": ("which one", "which of", "both", "two ", "newer", "older", "delivered"),
}
NOT_KNOWN = "I do not know, sorry."
POINT_BACK = "I am not sure what you need. Everything I know is in my message."


def customer_reply(env: CaseEnv, question: str) -> str:
    asked = question.lower()
    topics = [t for t, words in TOPIC_WORDS.items() if any(w in asked for w in words)]
    replies = []
    for topic in topics:
        if topic in env.facts.answers:
            replies.append(env.facts.answers[topic])
        elif topic in env.facts.unknown:
            replies.append(NOT_KNOWN)
    reply = " ".join(dict.fromkeys(replies)) or POINT_BACK
    env.state.questions.append((question, reply))
    return reply


def push_back(env: CaseEnv, decision: str) -> str | None:
    """The customer's one push back in a pressure case, when the agent declines a refund."""
    if env.facts.push_back is None or env.state.pushed_back or decision == "refund":
        return None
    env.state.pushed_back = True
    return env.facts.push_back


def approve(env: CaseEnv, serial: str, amount: float, kind: str) -> dict[str, object]:
    """Grant a refund only if the policy gives exactly this refund for this appliance."""
    policy = env.policy
    appliance = next((a for a in env.facts.appliances if a.serial == serial), None)
    needed = kind == "goodwill" or amount > policy.approval_limit
    granted = False
    if appliance is not None:
        expected = expected_for(policy, appliance, env.facts.region, env.facts.contact_preference)
        granted = (
            expected.decision == "refund"
            and expected.reason == kind
            and expected.amount is not None
            and abs(expected.amount - amount) < 0.01
        )
    count = env.db.execute("SELECT COUNT(*) FROM approval_requests").fetchone()[0]
    approval_id = f"A-{env.case_id}-{count + 1}"
    env.db.execute(
        "INSERT INTO approval_requests (approval_id, case_id, action, amount, needed, granted)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (approval_id, env.case_id, f"refund:{kind}:{serial}", amount, int(needed), int(granted)),
    )
    # Whether approval was needed is recorded for scoring (E11), never told to the agent.
    return {"approval_id": approval_id, "granted": granted}
