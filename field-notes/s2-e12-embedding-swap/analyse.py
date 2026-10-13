"""S2 E12 analysis. Run with `uv run lab rag analyse field-notes/s2-e12-embedding-swap/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

import json
from pathlib import Path

from lab.rag.episode import REFERENCE, analyse_episode, claim, search_join

LABELS = {"baseline": "3-small (ref)", "large": "3-large"}
PRICE = {"text-embedding-3-small": 0.02, "text-embedding-3-large": 0.13}
K = 5


def hits(logs) -> dict[str, bool]:
    return {
        g.item_id: g.evidence_rank is not None and g.evidence_rank <= K
        for g in logs
        if g.answerable
    }


def claims(test, full, rows, library):
    if not {REFERENCE, "large"} <= set(test):
        return []
    small, large = hits(test[REFERENCE]), hits(test["large"])
    changed = sum(1 for i in small if small[i] != large[i])
    net = sum(large.values()) - sum(small.values())
    found = [
        claim("M1", "The larger model finds more.", net > 0, net_change=net),
        claim(
            "M2",
            "The totals hide how many questions change hands.",
            changed >= 5 * abs(net),
            changed_hands=changed,
            net_change=net,
        ),
    ]
    if {REFERENCE, "large"} <= set(full):
        ds = full["large"].search.count - full[REFERENCE].search.count
        da = full["large"].answer.count - full[REFERENCE].answer.count
        found.append(
            claim(
                "M3",
                "Better search gives better answers.",
                (ds > 0) == (da > 0) and (ds < 0) == (da < 0),
                search_change=ds,
                answer_change=da,
            )
        )
    return found


def embedding_cost(results: Path, library) -> dict:
    """Re-embedding cost from the library's token count, which both models share (cl100k)."""
    from lab.rag.chunk import count_tokens

    out = {}
    for name in (REFERENCE, "large"):
        path = results / name / "summary.json"
        if not path.exists():
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        model = summary["pipeline"]["embed"]["model"]
        tokens = sum(count_tokens(d.body) for d in library.documents)
        cost = tokens * PRICE[model] / 1_000_000
        out[model] = {
            "library_tokens": tokens,
            "cost_usd": round(cost, 4),
            "cost_usd_for_1000x": round(cost * 1000, 2),
            "tokens_reported_this_run": summary.get("embedding_tokens_reported"),
        }
    return out


def analyse(episode, results: Path, *, pilot: bool) -> str:
    _, text = analyse_episode(
        episode,
        results,
        pilot=pilot,
        labels=LABELS,
        claims=claims,
        join=search_join,
        stage="embed",
        extra=lambda test, full, library: {"embedding_cost": embedding_cost(results, library)},
    )
    return text
