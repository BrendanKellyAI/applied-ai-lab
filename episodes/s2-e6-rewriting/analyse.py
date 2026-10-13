"""S2 E6 analysis. Run with `uv run lab rag analyse episodes/s2-e6-rewriting/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

import json
from pathlib import Path

from lab.rag.analysis import below, of_type, recall
from lab.rag.episode import REFERENCE, analyse_episode, claim, load_results, search_join

HERE = Path(__file__).parent
MODES = ("resolve-followup", "rewrite", "split")
TARGET = ("followup", "two_part", "bridge")
LABELS = {"baseline": "As typed (ref)", "rewrite": "Rewrite", "split": "Split",
          "resolve-followup": "Resolve follow-up"}
K = 5


def choose(dev) -> str | None:
    """The mode with the highest dev recall on the target types; ties in MODES order."""
    present = [m for m in MODES if m in dev]
    if not present:
        return None
    return max(present, key=lambda m: (recall(of_type(dev[m], *TARGET), K).count,
                                       -MODES.index(m)))


def rewrite_cost(results: Path) -> dict:
    out = {}
    for mode in MODES:
        path = results / mode / "summary.json"
        if path.exists():
            calls = json.loads(path.read_text(encoding="utf-8"))["calls"].get("rewrite", [])
            out[mode] = calls
    return out


def claims(test, full, rows, library):
    def r(name, *types):
        return recall(of_type(test[name], *types), K)

    other = sorted({g.type for g in test[REFERENCE] if g.answerable} - set(TARGET))
    chosen = choose(load_results(HERE / "results-dev", list(LABELS)))
    found = [
        claim("R1", "Resolving a follow-up finds its passage.",
              below(r(REFERENCE, "followup"), r("resolve-followup", "followup")),
              resolved=r("resolve-followup", "followup").model_dump(),
              reference=r(REFERENCE, "followup").model_dump()),
        claim("R2", "Splitting a two-part question finds both parts.",
              below(r(REFERENCE, "two_part"), r("split", "two_part")),
              split=r("split", "two_part").model_dump(),
              reference=r(REFERENCE, "two_part").model_dump()),
        claim("R3", "No one-shot rewrite solves a bridge question.",
              all(r(n, "bridge").count <= 5 for n in test),
              bridge={n: r(n, "bridge").count for n in test}),
        claim("R4", "Rewriting every question does not hurt the questions that did not need it.",
              not below(r("rewrite", *other), r(REFERENCE, *other)),
              rewrite=r("rewrite", *other).model_dump(),
              reference=r(REFERENCE, *other).model_dump()),
    ]
    if chosen in full and REFERENCE in full:
        ds = full[chosen].search.count - full[REFERENCE].search.count
        da = full[chosen].answer.count - full[REFERENCE].answer.count
        found.append(claim("R5", "Better search gives better answers.",
                           (ds > 0) == (da > 0) and (ds < 0) == (da < 0),
                           chosen=chosen, search_change=ds, answer_change=da))
    return found


def analyse(episode, results: Path, *, pilot: bool) -> str:
    report, text = analyse_episode(
        episode, results, pilot=pilot, labels=LABELS, claims=claims, join=search_join,
        stage="rewrite", chart_types=TARGET,
        extra=lambda test, full, library: {"rewrite_calls": rewrite_cost(results)},
    )
    return text
