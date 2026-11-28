"""One case's world: a fresh database, the case's facts, and what the run has done so far.

Each case runs against its own in-memory copy of the world database, copied from a template
built once, so cases never see each other's writes and a run can be repeated exactly.
"""

import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path

from lab.agent.case_model import CaseFacts
from lab.agent.policy import Policy, load_policy
from lab.agent.world import WORLD_DIR, load_database

_TEMPLATE_LOCK = threading.Lock()
_TEMPLATES: dict[Path, sqlite3.Connection] = {}


def fresh_database(world_dir: Path = WORLD_DIR) -> sqlite3.Connection:
    """A private in-memory copy of the world, made from a template loaded once per process."""
    with _TEMPLATE_LOCK:
        template = _TEMPLATES.get(world_dir)
        if template is None:
            template = load_database(":memory:", world_dir)
            _TEMPLATES[world_dir] = template
        copy = sqlite3.connect(":memory:", check_same_thread=False)
        template.backup(copy)
    copy.row_factory = sqlite3.Row
    return copy


@dataclass
class CaseState:
    """What the agent has done in this case, beyond the database rows."""

    closed: dict[str, dict[str, object]] = field(default_factory=dict)
    questions: list[tuple[str, str]] = field(default_factory=list)
    pushed_back: bool = False
    turn: int = 0


@dataclass
class CaseEnv:
    facts: CaseFacts
    db: sqlite3.Connection
    policy: Policy
    state: CaseState = field(default_factory=CaseState)

    @classmethod
    def open(cls, facts: CaseFacts, world_dir: Path = WORLD_DIR) -> "CaseEnv":
        return cls(facts=facts, db=fresh_database(world_dir), policy=load_policy())

    @property
    def case_id(self) -> str:
        return self.facts.case_id

    def customer(self) -> sqlite3.Row:
        row = self.db.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (self.facts.customer_id,)
        ).fetchone()
        assert row is not None
        return row

    def owner_of(self, serial: str) -> str | None:
        """The customer an appliance belongs to, from orders or retailer purchases."""
        for table in ("orders", "retailer_appliances"):
            row = self.db.execute(
                f"SELECT customer_id FROM {table} WHERE serial = ?",  # noqa: S608
                (serial,),
            ).fetchone()
            if row is not None:
                return str(row["customer_id"])
        return None

    def case_serials(self) -> set[str]:
        return {a.serial for a in self.facts.appliances}

    def all_closed(self) -> bool:
        return self.case_serials() <= set(self.state.closed)

    def audit(self, tool: str, arguments_json: str, outcome: str, rule: str | None = None) -> None:
        self.db.execute(
            "INSERT INTO audit_log (case_id, turn, tool, arguments_json, outcome, blocked_rule)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (self.case_id, self.state.turn, tool, arguments_json, outcome, rule),
        )

    def rows(self, query: str, *args: object) -> list[dict[str, object]]:
        return [dict(row) for row in self.db.execute(query, args).fetchall()]
