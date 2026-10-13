"""S2 E8 analysis. Run with `uv run lab rag analyse episodes/s2-e8-filters/config.yaml`.

Reads committed results only; no key, no call. The claims are those in PREREGISTRATION.md.
"""

from pathlib import Path

from lab.rag.analysis import below, of_type
from lab.rag.episode import REFERENCE, analyse_episode, claim
from lab.rag.score import Proportion

LABELS = {"baseline": "No filter (ref)", "before": "Before ranking", "after": "After ranking",
          "before-access": "Before, access only", "before-status": "Before, status only"}
K = 5


def leaks(logs) -> Proportion:
    public = [g for g in logs if g.asker == "public"]
    return Proportion.of(sum(1 for g in public if g.leaks), len(public))


def short_prompts(logs) -> int:
    return sum(1 for g in logs if len(g.prompt_chunks) < K)


def declined(logs, *types) -> Proportion:
    group = of_type(logs, *types)
    return Proportion.of(sum(1 for g in group if g.verdict and g.verdict.declined), len(group))


def right(logs, *types) -> Proportion:
    group = of_type(logs, *types)
    return Proportion.of(
        sum(1 for g in group if g.verdict and g.verdict.correct and g.verdict.faithful), len(group)
    )


def join(full) -> dict:
    ref = full[REFERENCE]
    passed = [n for n, v in full.items() if n != REFERENCE and below(v.leaks, ref.leaks)
              and v.answer.count >= ref.answer.count]
    return {"rule": "leaks below the reference's interval, answer not lower",
            "passed": passed, "joined": passed[0] if passed else None}


def claims(test, full, rows, library):
    for name, logs in test.items():
        rows[name]["short_prompts"] = short_prompts(logs)
    found = [
        claim("F1", "A filter before ranking stops every leak.", leaks(test["before"]).count == 0,
              before=leaks(test["before"]).model_dump(),
              reference=leaks(test[REFERENCE]).model_dump()),
        claim("F2", "A filter after ranking also stops leaks, but starves the prompt.",
              leaks(test["after"]).count == 0
              and short_prompts(test["after"]) > short_prompts(test["before"]),
              after_leaks=leaks(test["after"]).count, after_short=short_prompts(test["after"]),
              before_short=short_prompts(test["before"])),
        claim("F3", "The status rule removes the old versions from the prompt.",
              rows["before-status"]["superseded_slots"] == 0
              and not any(c.split("@")[0] in _withdrawn(library) for g in test["before-status"]
                          for c in g.prompt_chunks),
              superseded_slots=rows["before-status"]["superseded_slots"]),
    ]
    if "before" in full and REFERENCE in full:
        unanswerable = ("restricted_public", "deleted")
        f4b, f4r = declined(test["before"], *unanswerable), declined(test[REFERENCE], *unanswerable)
        f5b, f5r = right(test["before"], "version"), right(test[REFERENCE], "version")
        found += [
            claim("F4", "With nothing it should not see, the model declines.", below(f4r, f4b),
                  before=f4b.model_dump(), reference=f4r.model_dump()),
            claim("F5", "Without the old version beside it, the model gives the current value.",
                  below(f5r, f5b), before=f5b.model_dump(), reference=f5r.model_dump()),
        ]
    return found


def _withdrawn(library) -> set[str]:
    return {d.doc_id for d in library.documents if d.status == "deleted"}


def analyse(episode, results: Path, *, pilot: bool) -> str:
    _, text = analyse_episode(episode, results, pilot=pilot, labels=LABELS, claims=claims,
                              join=join, stage="filter",
                              chart_types=("restricted_staff", "version", "policy_single"))
    return text
