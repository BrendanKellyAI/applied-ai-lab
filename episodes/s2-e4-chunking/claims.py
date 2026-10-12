"""S2 E4's pre-registered rules, applied to run logs. See PREREGISTRATION.md.

- `choose_full`: which fixed and which structure chunker run in full, chosen on dev.
- `evaluate`: claims C1 to C5 on test.
- `join`: whether a full condition joins the reference system.
- `mcnemar`: the paired comparison, reported beside the joining rule; it decides nothing.
"""

from collections.abc import Mapping, Sequence
from math import comb
from typing import Any

from pydantic import BaseModel, ConfigDict

from lab.rag.analysis import below, of_type, recall
from lab.rag.log import ItemLog
from lab.rag.score import SeasonNumbers

REFERENCE = "baseline"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    statement: str
    held: bool
    detail: dict[str, Any]


def chunk_size(chunker: Any) -> int:
    """The size a chunker cuts to: its window, or its section cap."""
    return chunker.size if chunker.kind == "fixed" else chunker.max_tokens


def policy_recall(logs: Sequence[ItemLog], marks: Mapping[str, Any], k: int):
    return recall(of_type(logs, *marks["policy_types"]), k)


def cut_items(logs: Sequence[ItemLog]) -> int:
    """Answerable items with an evidence span that no chunk holds whole."""
    return sum(
        1 for g in logs if g.answerable and any(s.kind == "evidence" and s.cut for s in g.spans)
    )


def choose_full(
    dev: Mapping[str, Sequence[ItemLog]],
    chunkers: Mapping[str, Any],
    marks: Mapping[str, Any],
    k: int,
) -> dict[str, str]:
    """The fixed and the structure condition with the highest dev policy recall at 5. A tie goes
    to the smaller chunks; then to no overlap, the cheaper index; then to the name, so the
    choice never depends on file order."""

    def key(name: str):
        chunker = chunkers[name]
        overlap = getattr(chunker, "overlap", 0)
        return (-policy_recall(dev[name], marks, k).count, chunk_size(chunker), overlap, name)

    kinds = {"fixed": [], "structure": []}
    for name in dev:
        kinds[chunkers[name].kind].append(name)
    return {kind: min(names, key=key) for kind, names in kinds.items() if names}


def _fixed_name(size: int, overlap: int) -> str:
    return REFERENCE if (size, overlap) == (256, 0) else f"fixed-{size}-{overlap}"


def c1(test, marks, k) -> Claim:
    long = policy_recall(test[marks["c1_long"]], marks, k)
    ref = policy_recall(test[marks["c1_reference"]], marks, k)
    return Claim(
        id="C1",
        statement="Long chunks dilute a fact.",
        held=below(long, ref),
        detail={"long": long.model_dump(), "reference": ref.model_dump()},
    )


def c2(test, chunkers) -> Claim:
    sizes = sorted({c.size for c in chunkers.values() if c.kind == "fixed"})
    pairs = {}
    for size in sizes:
        plain, overlapped = _fixed_name(size, 0), _fixed_name(size, size // 4)
        if plain in test and overlapped in test:
            pairs[size] = {"no_overlap": cut_items(test[plain]),
                           "overlap": cut_items(test[overlapped])}
    return Claim(
        id="C2",
        statement="Overlap stops facts being cut.",
        held=bool(pairs) and all(p["overlap"] < p["no_overlap"] for p in pairs.values()),
        detail={"cut_items_by_size": pairs},
    )


def c3(test, marks, k) -> Claim:
    heading = marks["c3_heading_type"]
    pairs = []
    for with_h, without in marks["c3_pairs"]:
        a, b = recall(of_type(test[with_h], heading), k), recall(of_type(test[without], heading), k)
        pairs.append({"with": with_h, "without": without, "with_count": a.count,
                      "without_count": b.count, "total": a.total})
    best = max((p["with"] for p in pairs), key=lambda n: recall(of_type(test[n], heading), k).count)
    best_p = recall(of_type(test[best], heading), k)
    ref_p = recall(of_type(test[REFERENCE], heading), k)
    return Claim(
        id="C3",
        statement="The heading carries the fact.",
        held=all(p["with_count"] > p["without_count"] for p in pairs),
        detail={"pairs": pairs, "strong_form": below(ref_p, best_p), "best": best,
                "best_recall": best_p.model_dump(), "reference": ref_p.model_dump()},
    )


def c4(test, chunkers, marks, k) -> Claim:
    def best(kind: str):
        names = [n for n in test if chunkers[n].kind == kind]
        name = max(names, key=lambda n: policy_recall(test[n], marks, k).count)
        return name, policy_recall(test[name], marks, k)

    (fixed, fp), (structure, sp) = best("fixed"), best("structure")
    return Claim(
        id="C4",
        statement="Following the document's structure beats cutting blind.",
        held=sp.count > fp.count,
        detail={"best_fixed": fixed, "fixed": fp.model_dump(),
                "best_structure": structure, "structure": sp.model_dump()},
    )


def _sign(x: int) -> int:
    return (x > 0) - (x < 0)


def c5(numbers: Mapping[str, SeasonNumbers]) -> Claim:
    ref = numbers[REFERENCE]
    rows = {}
    for name, n in numbers.items():
        if name == REFERENCE:
            continue
        rows[name] = {"search_change": n.search.count - ref.search.count,
                      "answer_change": n.answer.count - ref.answer.count}
    return Claim(
        id="C5",
        statement="Better search gives better answers.",
        held=bool(rows) and all(
            _sign(r["search_change"]) == _sign(r["answer_change"]) for r in rows.values()
        ),
        detail=rows,
    )


def evaluate(test, chunkers, full_numbers, marks, k) -> list[Claim]:
    return [c1(test, marks, k), c2(test, chunkers), c3(test, marks, k),
            c4(test, chunkers, marks, k), c5(full_numbers)]


def join(full_numbers: Mapping[str, SeasonNumbers]) -> dict[str, Any]:
    """Which full condition joins the reference: search above (intervals apart) and answer not
    lower; of those, the higher search number. None if no condition passes."""
    ref = full_numbers[REFERENCE]
    passed = {
        name: n for name, n in full_numbers.items()
        if name != REFERENCE and below(ref.search, n.search) and n.answer.count >= ref.answer.count
    }
    joined = max(passed, key=lambda n: (passed[n].search.count, passed[n].answer.count),
                 default=None)
    return {"passed": sorted(passed), "joined": joined}


def mcnemar(reference: Sequence[ItemLog], other: Sequence[ItemLog], k: int) -> dict[str, Any]:
    """Search hits on the same answerable items: found only by each, and an exact two-sided
    McNemar p-value (a binomial test on the items where the two differ)."""
    def hit(g: ItemLog) -> bool:
        return g.evidence_rank is not None and g.evidence_rank <= k

    ref = {g.item_id: hit(g) for g in reference if g.answerable}
    oth = {g.item_id: hit(g) for g in other if g.answerable}
    only_other = sum(1 for i in ref if oth[i] and not ref[i])
    only_ref = sum(1 for i in ref if ref[i] and not oth[i])
    n, low = only_other + only_ref, min(only_other, only_ref)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(low + 1)) / 2**n) if n else 1.0
    return {"only_other": only_other, "only_reference": only_ref, "p_value": p}
