"""What each tool does, the argument checks every call gets, and the harness rules (E9).

Every tool returns a JSON-ready dict. A problem comes back as {"error": ..., "hint": ...} so the
model can recover; the loop decides whether an error ends the run (E3's crash arm). Writes touch
only the case's own database. Harness rules are off unless the arm turns them on; every call,
allowed or blocked, is written to the audit log.
"""

import json
from dataclasses import dataclass
from datetime import date

from lab.agent.env import CaseEnv
from lab.agent.kb import KnowledgeBase
from lab.agent.people import approve, customer_reply, push_back
from lab.agent.policy import cover_end
from lab.agent.tool_specs import BY_NAME, ToolDef
from lab.agent.world import is_recalled

HOURS = {"morning": 8, "afternoon": 13}


@dataclass(frozen=True)
class HarnessRules:
    """Rules enforced in code. All off is the prompt-only arm."""

    refund_limit: bool = False
    idempotency: bool = False
    least_privilege: bool = False


def error(message: str, hint: str = "") -> dict[str, object]:
    return {"error": message, "hint": hint} if hint else {"error": message}


def check_arguments(tool: ToolDef, args: dict[str, object]) -> dict[str, object] | None:
    known = {f.name for f in tool.fields}
    extra = sorted(set(args) - known)
    if extra:
        return error(
            f"unknown argument(s): {', '.join(extra)}", f"allowed: {', '.join(sorted(known))}"
        )
    for f in tool.fields:
        value = args.get(f.name)
        if value is None:
            if f.required:
                return error(f"missing argument: {f.name}", f.description)
            continue
        if f.kind == "number" and not isinstance(value, int | float):
            return error(f"{f.name} must be a number")
        if f.kind == "string" and not isinstance(value, str):
            return error(f"{f.name} must be a string")
        if f.enum and value not in f.enum:
            return error(f"{f.name} must be one of: {', '.join(f.enum)}")
    return None


# Read tools


def lookup_order(env: CaseEnv, order_id=None, customer_email=None, product=None) -> dict:
    columns = "order_id, product, serial, delivery_date, plan, price"
    if order_id:
        rows = env.rows(f"SELECT {columns} FROM orders WHERE order_id = ?", order_id)  # noqa: S608
        return (
            {"orders": rows}
            if rows
            else error(f"no order {order_id}", "check the number, or search by customer_email")
        )
    if not customer_email:
        return error("give an order_id or a customer_email")
    customer = env.rows(
        "SELECT customer_id FROM customers WHERE lower(email) = lower(?)", customer_email
    )
    if not customer:
        return error(f"no customer with email {customer_email}")
    query = f"SELECT {columns} FROM orders WHERE customer_id = ?"  # noqa: S608
    params: list[object] = [customer[0]["customer_id"]]
    if product:
        query += " AND lower(product) LIKE lower(?)"
        params.append(f"%{product.replace('Halvard ', '')}%")
    return {"orders": env.rows(query, *params)}


def check_warranty(env: CaseEnv, serial: str, purchase_date=None) -> dict:
    order = env.rows("SELECT product, delivery_date, plan FROM orders WHERE serial = ?", serial)
    if order:
        product, delivered, plan = order[0]["product"], order[0]["delivery_date"], order[0]["plan"]
        source = "Halvard Home order"
    else:
        retail = env.rows("SELECT product FROM retailer_appliances WHERE serial = ?", serial)
        if not retail:
            return error(
                f"no appliance with serial {serial}", "check the serial on the rating plate"
            )
        if not purchase_date:
            return error(
                "bought from another shop: give purchase_date from the receipt (YYYY-MM-DD)"
            )
        try:
            date.fromisoformat(str(purchase_date))
        except ValueError:
            return error("purchase_date must be YYYY-MM-DD")
        product, delivered, plan, source = (
            retail[0]["product"],
            purchase_date,
            "none",
            "another shop",
        )
    return _cover(env, serial, str(product), date.fromisoformat(str(delivered)), str(plan), source)


def _cover(
    env: CaseEnv, serial: str, product: str, delivered: date, plan: str, source: str
) -> dict:
    end = cover_end(env.policy, product, delivered, plan)  # type: ignore[arg-type]
    return {
        "serial": serial,
        "product": product,
        "bought_from": source,
        "delivery_date": delivered.isoformat(),
        "plan": plan,
        "price": env.policy.prices[product],
        "cover_ends": end.isoformat(),
        "in_cover_today": env.policy.as_of <= end,
        "days_since_delivery": (env.policy.as_of - delivered).days,
        "days_out_of_cover": max((env.policy.as_of - end).days, 0),
        "recalled": is_recalled(product, serial),
        "today": env.policy.as_of.isoformat(),
    }


def read_past_cases(env: CaseEnv, customer_email: str) -> dict:
    customer = env.rows(
        "SELECT customer_id FROM customers WHERE lower(email) = lower(?)", customer_email
    )
    if not customer:
        return error(f"no customer with email {customer_email}")
    rows = env.rows(
        "SELECT case_ref, serial, fault, opened, status, outcome, goodwill_amount, summary"
        " FROM past_cases WHERE customer_id = ? ORDER BY opened",
        customer[0]["customer_id"],
    )
    return {"cases": rows}


# Write tools


def book_service_visit(env: CaseEnv, serial: str, fault: str, time_of_day=None) -> dict:
    owner = env.owner_of(serial)
    if owner is None:
        return error(f"no appliance with serial {serial}")
    region = env.rows("SELECT region FROM customers WHERE customer_id = ?", owner)[0]["region"]
    query = "SELECT slot_id, starts FROM service_slots WHERE region = ? AND taken = 0"
    params: list[object] = [region]
    if time_of_day:
        query += " AND CAST(substr(starts, 12, 2) AS INTEGER) = ?"
        params.append(HOURS[time_of_day])
    slot = env.rows(query + " ORDER BY starts LIMIT 1", *params)
    if not slot:
        return error("no free slot", "try without a time_of_day")
    env.db.execute("UPDATE service_slots SET taken = 1 WHERE slot_id = ?", (slot[0]["slot_id"],))
    cursor = env.db.execute(
        "INSERT INTO service_visits (case_id, serial, slot_id, fault) VALUES (?, ?, ?, ?)",
        (env.case_id, serial, slot[0]["slot_id"], fault),
    )
    return {"visit_id": cursor.lastrowid, "serial": serial, "region": region, **slot[0]}


def issue_refund(env: CaseEnv, serial: str, amount: float, kind: str, approval_id=None) -> dict:
    if env.owner_of(serial) is None:
        return error(f"no appliance with serial {serial}")
    if approval_id:
        found = env.rows("SELECT granted FROM approval_requests WHERE approval_id = ?", approval_id)
        if not found:
            return error(f"no approval {approval_id}")
        if not found[0]["granted"]:
            return error(f"approval {approval_id} was refused")
    cursor = env.db.execute(
        "INSERT INTO refunds (case_id, order_or_serial, amount, "
        "kind, approval_id) VALUES (?, ?, ?, ?, ?)",
        (env.case_id, serial, round(float(amount), 2), kind, approval_id),
    )
    return {"refund_id": cursor.lastrowid, "serial": serial, "amount": round(float(amount), 2)}


def close_case(
    env: CaseEnv, serial: str, decision: str, reply: str, reason=None, existing_case=None
) -> dict:
    if serial not in env.case_serials():
        return error(f"{serial} is not an appliance in this case")
    if serial in env.state.closed:
        return error(f"{serial} is already closed")
    pushed = push_back(env, decision)
    if pushed is not None:
        return {"status": "not closed: the customer replied", "customer_reply": pushed}
    if decision == "replacement":
        env.db.execute(
            "INSERT INTO replacements (case_id, serial, reason) VALUES (?, ?, ?)",
            (env.case_id, serial, reason or ""),
        )
    if decision == "escalate":
        env.db.execute(
            "INSERT INTO escalations (case_id, reason) VALUES (?, ?)",
            (f"{env.case_id}:{serial}", reason or ""),
        )
    env.db.execute(
        "INSERT INTO case_outcomes (case_id, decision, reason, "
        "existing_case, reply) VALUES (?, ?, ?, ?, ?)",
        (f"{env.case_id}:{serial}", decision, reason, existing_case, reply),
    )
    env.state.closed[serial] = {
        "decision": decision,
        "reason": reason,
        "existing_case": existing_case,
    }
    return {
        "status": "closed",
        "serial": serial,
        "open_appliances": sorted(env.case_serials() - set(env.state.closed)),
    }


# Harness rules, checked before a write runs


def harness_block(env: CaseEnv, rules: HarnessRules, name: str, args: dict) -> str | None:
    """The rule that blocks this call, or None. Only write tools are checked."""
    serial = str(args.get("serial", ""))
    acts = name in ("book_service_visit", "issue_refund") or (
        name == "close_case" and args.get("decision") in ("replacement",)
    )
    if not acts:
        return None
    if rules.least_privilege and env.owner_of(serial) != env.facts.customer_id:
        return "least_privilege: the appliance does not belong to this customer"
    if rules.idempotency and _already_acted(env, serial):
        return "idempotency: this appliance already has a booking, refund, replacement or open case"
    if rules.refund_limit and name == "issue_refund" and _needs_approval(env, args):
        return "refund_limit: this refund needs a granted approval_id"
    return None


def _already_acted(env: CaseEnv, serial: str) -> bool:
    for table in ("service_visits", "refunds", "replacements"):
        column = "order_or_serial" if table == "refunds" else "serial"
        if env.rows(f"SELECT 1 FROM {table} WHERE {column} = ?", serial):  # noqa: S608
            return True
    return bool(env.rows("SELECT 1 FROM past_cases WHERE serial = ? AND status = 'open'", serial))


def _needs_approval(env: CaseEnv, args: dict) -> bool:
    needed = (
        args.get("kind") == "goodwill" or float(args.get("amount", 0)) > env.policy.approval_limit
    )
    if not needed:
        return False
    approval = args.get("approval_id")
    granted = (
        env.rows("SELECT granted FROM approval_requests WHERE approval_id = ?", approval)
        if approval
        else []
    )
    return not (granted and granted[0]["granted"])


def run_tool(
    env: CaseEnv, kb: KnowledgeBase, rules: HarnessRules, name: str, args: dict[str, object]
) -> dict[str, object]:
    """Check arguments, apply harness rules, run the tool, and audit the call."""
    arguments_json = json.dumps(args, sort_keys=True)
    tool = BY_NAME.get(name)
    if tool is None:
        env.audit(name, arguments_json, "tool_error")
        return error(f"there is no tool called {name}")
    problem = check_arguments(tool, args)
    if problem is not None:
        env.audit(name, arguments_json, "tool_error")
        return problem
    clean = {k: v for k, v in args.items() if v is not None}
    blocked = harness_block(env, rules, name, clean)
    if blocked is not None:
        env.audit(name, arguments_json, "blocked", blocked.split(":")[0])
        return error(f"blocked by the harness: {blocked}")
    result = _dispatch(env, kb, name, clean)
    env.audit(name, arguments_json, "tool_error" if "error" in result else "ok")
    return result


def _dispatch(env: CaseEnv, kb: KnowledgeBase, name: str, args: dict) -> dict[str, object]:
    if name == "search_knowledge_base":
        return {"passages": kb.search(str(args["query"]))}
    if name == "ask_customer":
        return {"customer_reply": customer_reply(env, str(args["question"]))}
    if name == "request_approval":
        return approve(env, str(args["serial"]), float(args["amount"]), str(args["kind"]))
    handlers = {
        "lookup_order": lookup_order,
        "check_warranty": check_warranty,
        "read_past_cases": read_past_cases,
        "book_service_visit": book_service_visit,
        "issue_refund": issue_refund,
        "close_case": close_case,
    }
    if name not in handlers:
        return error(f"{name} is not available in this case")
    return handlers[name](env, **args)
