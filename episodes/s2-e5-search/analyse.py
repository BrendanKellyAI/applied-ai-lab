"""S2 E5 analysis. Run with `uv run lab rag analyse episodes/s2-e5-search/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

from pathlib import Path

from lab.rag.analysis import below, of_type, recall
from lab.rag.episode import REFERENCE, analyse_episode, claim, load_results, search_join

HERE = Path(__file__).parent
HYBRIDS = ("hybrid-20", "hybrid-50", "hybrid-all")
LABELS = {"baseline": "Vector (ref)", "keyword": "Keyword (BM25)", "hybrid-all": "Hybrid, all",
          "hybrid-50": "Hybrid, top 50", "hybrid-20": "Hybrid, top 20"}
K = 5


def choose(dev) -> str | None:
    """The hybrid with the highest dev recall at 5; a tie goes to the shallower fusion."""
    present = [h for h in HYBRIDS if h in dev]
    if not present:
        return None
    return max(present, key=lambda h: (recall([g for g in dev[h] if g.answerable], K).count,
                                       -HYBRIDS.index(h)))


def look_alike_above(logs) -> int:
    return sum(1 for g in of_type(logs, "identifier", "distractor") if g.distractor_above)


def claims(test, full, rows, library):
    def r(name, *types):
        logs = test[name]
        return recall(of_type(logs, *types) if types else [g for g in logs if g.answerable], K)

    dev = load_results(HERE / "results-dev", list(LABELS))
    chosen = choose(dev)
    found = [
        claim("S1", "Keyword search finds identifier codes that vector search misses.",
              below(r(REFERENCE, "identifier"), r("keyword", "identifier")),
              keyword=r("keyword", "identifier").model_dump(),
              vector=r(REFERENCE, "identifier").model_dump()),
        claim("S2", "Vector search finds paraphrases that keyword search misses.",
              below(r("keyword", "paraphrase"), r(REFERENCE, "paraphrase")),
              keyword=r("keyword", "paraphrase").model_dump(),
              vector=r(REFERENCE, "paraphrase").model_dump()),
        claim("S3", "Fusing the full rankings does not beat vector search.",
              r("hybrid-all").count <= r(REFERENCE).count,
              hybrid_all=r("hybrid-all").model_dump(), vector=r(REFERENCE).model_dump()),
    ]
    if chosen:
        found.append(claim(
            "S4",
            "Fusing only the top of each ranking keeps vector's strengths and adds keyword's.",
            r(chosen).count >= r(REFERENCE).count
            and below(r(REFERENCE, "identifier"), r(chosen, "identifier")),
            chosen=chosen, overall=r(chosen).model_dump(),
            identifier=r(chosen, "identifier").model_dump()))
    if chosen in full and REFERENCE in full:
        ds = full[chosen].search.count - full[REFERENCE].search.count
        da = full[chosen].answer.count - full[REFERENCE].answer.count
        found.append(claim("S5", "Better search gives better answers.",
                           (ds > 0) == (da > 0) and (ds < 0) == (da < 0),
                           search_change=ds, answer_change=da))
    for name in test:
        rows[name]["look_alike_above"] = look_alike_above(test[name])
    return found


def analyse(episode, results: Path, *, pilot: bool) -> str:
    _, text = analyse_episode(episode, results, pilot=pilot, labels=LABELS, claims=claims,
                              join=search_join, stage="search")
    return text
