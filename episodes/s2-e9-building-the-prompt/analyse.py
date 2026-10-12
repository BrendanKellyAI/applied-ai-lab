"""S2 E9 analysis. Run with `uv run lab rag analyse episodes/s2-e9-building-the-prompt/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

from pathlib import Path

from lab.rag.analysis import below
from lab.rag.episode import REFERENCE, analyse_episode, claim
from lab.rag.score import Proportion

LABELS = {"baseline": "Top 5, plain (ref)", "allow-not-found": "Not found allowed",
          "k-3": "Top 3", "ends": "Best at the ends", "k-8": "Top 8"}


def handled(logs) -> Proportion:
    """Answerable items judged correct and faithful, plus unanswerable items declined."""
    good = 0
    for g in logs:
        v = g.verdict
        if v is None:
            continue
        good += (v.correct and v.faithful) if g.answerable else v.declined
    return Proportion.of(good, len(logs))


def join_rule(test):
    def join(full) -> dict:
        shares = {n: handled(test[n]) for n in full}
        passed = [n for n in full if n != REFERENCE and below(shares[REFERENCE], shares[n])]
        joined = max(passed, key=lambda n: shares[n].count, default=None)
        return {"rule": "share of the 520 handled right above the reference's interval",
                "shares": {n: s.model_dump() for n, s in shares.items()},
                "passed": passed, "joined": joined}

    return join


def claims(test, full, rows, library):
    if not {REFERENCE, "allow-not-found", "k-3", "ends"} <= set(full):
        return []
    ref, nf, k3, ends = (full[n] for n in (REFERENCE, "allow-not-found", "k-3", "ends"))
    shorter = 1 - rows["k-3"]["median_prompt_tokens"] / rows[REFERENCE]["median_prompt_tokens"]
    return [
        claim("P1", "Allowing 'not found' makes the model decline when it should.",
              below(ref.not_found, nf.not_found), allow=nf.not_found.model_dump(),
              reference=ref.not_found.model_dump()),
        claim("P2", "Allowing 'not found' does not cost right answers.",
              not below(nf.answer, ref.answer), allow=nf.answer.model_dump(),
              reference=ref.answer.model_dump()),
        claim("P3", "Three passages answer as well as five, for less.",
              not below(k3.answer, ref.answer) and shorter >= 0.30,
              k3=k3.answer.model_dump(), prompt_shorter_by=round(shorter, 3)),
        claim("P4", "Passage order does not matter at this length.",
              not below(ends.answer, ref.answer) and not below(ref.answer, ends.answer),
              ends=ends.answer.model_dump(), reference=ref.answer.model_dump()),
    ]


def analyse(episode, results: Path, *, pilot: bool) -> str:
    from lab.rag.episode import load_results

    test = load_results(results, [c.name for c in episode.conditions])
    _, text = analyse_episode(episode, results, pilot=pilot, labels=LABELS, claims=claims,
                              join=join_rule(test), stage="prompt")
    return text
