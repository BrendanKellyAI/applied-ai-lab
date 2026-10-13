"""S2 E10 analysis. Run with
`uv run lab rag analyse episodes/s2-e10-grounding-and-citations/config.yaml`.

Reads committed results only; no key, no call. Citations are checked in code against the
evidence labels: a citation is supported if the cited passage holds an evidence span.
"""

import json
import re
from pathlib import Path

from lab.rag.analysis import below
from lab.rag.corpus import load_library
from lab.rag.episode import REFERENCE, analyse_episode, claim
from lab.rag.judge_check import chunk_lookup
from lab.rag.score import Proportion, holds

HERE = Path(__file__).parent
LABELS = {"baseline": "Plain (ref)", "grounded-cite": "Grounded, citing"}
MARKER = re.compile(r"\[P(\d+)(?:\s*[-–,]\s*P?(\d+))?\]")


# slide: S2 E10
def cited(answer, n_passages):
    """The passage numbers an answer cites, from markers like
    [P2] or [P2-P3]; numbers outside the prompt are ignored."""
    found = set()
    for first, last in MARKER.findall(answer):
        lo, hi = int(first), int(last or first)
        found.update(range(lo, hi + 1))
    return sorted(n for n in found if 1 <= n <= n_passages)


def citation_report(logs, library, pipeline) -> dict:
    chunks = chunk_lookup(library, pipeline)
    items = {i.id: i for i in library.test}
    answered = [g for g in logs if g.answer and g.verdict and not g.verdict.declined]
    citing = [g for g in answered if cited(g.answer.text, len(g.prompt_chunks))]
    total = supported = only_unsupported = right = right_cites_evidence = 0
    for g in answered:
        if not g.answerable:
            continue
        item = items[g.item_id]
        numbers = cited(g.answer.text, len(g.prompt_chunks))
        good = [n for n in numbers
                if any(holds(chunks[g.prompt_chunks[n - 1]], s) for s in item.evidence)]
        total += len(numbers)
        supported += len(good)
        if numbers and not good:
            only_unsupported += 1
        if g.verdict.correct:
            right += 1
            right_cites_evidence += bool(good)
    return {
        "answered": len(answered),
        "citing": Proportion.of(len(citing), len(answered)).model_dump(),
        "citations": total,
        "supported_citations": Proportion.of(supported, total).model_dump(),
        "answers_citing_only_unsupported": only_unsupported,
        "right_citing_evidence": Proportion.of(right_cites_evidence, right).model_dump(),
    }


def faithful(logs) -> Proportion:
    group = [g for g in logs if g.answerable and g.verdict and not g.verdict.declined]
    return Proportion.of(sum(1 for g in group if g.verdict.faithful), len(group))


def handled(logs) -> Proportion:
    good = 0
    for g in logs:
        v = g.verdict
        if v is not None:
            good += (v.correct and v.faithful) if g.answerable else v.declined
    return Proportion.of(good, len(logs))


def summary_pipeline(results: Path, name: str) -> dict:
    return json.loads((results / name / "summary.json").read_text(encoding="utf-8"))["pipeline"]


def make(results: Path):
    library = load_library(HERE.parents[1] / "datasets" / "halvard")
    cache: dict = {}

    def cites(test, name):
        if name not in cache:
            cache[name] = citation_report(test[name], library, summary_pipeline(results, name))
        return cache[name]

    def claims(test, full, rows, lib):
        if not {REFERENCE, "grounded-cite"} <= set(full):
            return []
        g = cites(test, "grounded-cite")
        ref, gc = full[REFERENCE], full["grounded-cite"]
        return [
            claim("G1", "Asked to cite, the model cites.", g["citing"]["rate"] >= 0.90,
                  citing=g["citing"]),
            claim("G2", "A right answer cites the right passage.",
                  g["right_citing_evidence"]["rate"] >= 0.80, right=g["right_citing_evidence"]),
            claim("G3", "Grounding makes answers more faithful.",
                  faithful(test["grounded-cite"]).rate > faithful(test[REFERENCE]).rate,
                  grounded=faithful(test["grounded-cite"]).model_dump(),
                  reference=faithful(test[REFERENCE]).model_dump()),
            claim("G4", "Grounding does not cost right answers.", not below(gc.answer, ref.answer),
                  grounded=gc.answer.model_dump(), reference=ref.answer.model_dump()),
        ]

    def join(full):
        from lab.rag.episode import load_results

        test = load_results(results, [REFERENCE, "grounded-cite"])
        if "grounded-cite" not in full:
            return {"rule": "", "passed": [], "joined": None}
        g = cites(test, "grounded-cite")
        ok = (g["citing"]["rate"] >= 0.90
              and not below(full["grounded-cite"].answer, full[REFERENCE].answer)
              and not below(handled(test["grounded-cite"]), handled(test[REFERENCE])))
        return {"rule": "cites at least 90%, answer and handled share not below the reference's",
                "passed": ["grounded-cite"] if ok else [],
                "joined": "grounded-cite" if ok else None, "candidate": "grounded-cite",
                "handled": {n: handled(test[n]).model_dump() for n in (REFERENCE, "grounded-cite")}}

    def extra(test, full, lib):
        return {n: cites(test, n) for n in test if n in full}

    return claims, join, extra


def analyse(episode, results: Path, *, pilot: bool) -> str:
    claims, join, extra = make(results)
    _, text = analyse_episode(episode, results, pilot=pilot, labels=LABELS, claims=claims,
                              join=join, stage="cite", extra=extra)
    return text
