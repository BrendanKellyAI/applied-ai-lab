"""Scoring for S2 E5, fixed before the run: counts, intervals, the hindsight cut-off, and every
claim's verdict against the pass marks in config.yaml. Nothing here calls a model or the network.
"""

from collections.abc import Sequence

from lab.scoring import wilson_interval


def count(hits: int, n: int) -> dict:
    rate, low, high = wilson_interval(hits, n)
    return {"hits": hits, "n": n, "rate": rate, "low": low, "high": high}


def tally(rows: Sequence[dict], test) -> dict:
    return count(sum(1 for row in rows if test(row)), len(rows))


def x_of_n(entry: dict) -> str:
    return (f"{entry['hits']} of {entry['n']} ({entry['low']:.0%} to {entry['high']:.0%})")


def verdict(holds: bool) -> str:
    return "Held" if holds else "Failed"


# Test C, part 1 -----------------------------------------------------------------------------


def best_cutoff(answerable: Sequence[float], unanswerable: Sequence[float]) -> dict:
    """The one score cut-off that best separates the groups, chosen with hindsight: a question
    scoring at or above it is called answerable. Every midpoint between neighbouring scores is
    tried, plus one below and one above all of them; on a tie the lowest cut-off wins."""
    scores = sorted(set(answerable) | set(unanswerable))
    cuts = ([scores[0] - 1e-6]
            + [(a + b) / 2 for a, b in zip(scores, scores[1:], strict=False)]
            + [scores[-1] + 1e-6])
    best = None
    for cut in cuts:
        missed = sum(1 for s in answerable if s < cut) + sum(1 for s in unanswerable if s >= cut)
        if best is None or missed < best["misclassified"]:
            best = {"cutoff": cut, "misclassified": missed}
    n = len(answerable) + len(unanswerable)
    return {**best, "n": n, "accuracy": (n - best["misclassified"]) / n,
            "answerable_range": [min(answerable), max(answerable)],
            "unanswerable_range": [min(unanswerable), max(unanswerable)]}


# Claims -------------------------------------------------------------------------------------


def claim(holds: bool, measured: str, mark: str) -> dict:
    return {"verdict": verdict(holds), "measured": measured, "pass_mark": mark}


def claims_a(summary: dict, marks: dict) -> dict:
    fresh, stale = summary["fresh"], summary["stale"]
    gap = abs(stale["recall"]["hits"] - fresh["recall"]["hits"])
    n = fresh["recall"]["n"]
    return {
        "A1": claim(gap <= marks["a1_max_recall_gap"],
                    f"stale {stale['recall']['hits']} of {n}, fresh {fresh['recall']['hits']} "
                    f"of {n}; gap {gap}",
                    f"gap of {marks['a1_max_recall_gap']} or fewer"),
        "A2": claim(stale["current"]["hits"] <= marks["a2_max_stale_current"]
                    and stale["old"]["hits"] >= marks["a2_min_stale_old"],
                    f"current value {stale['current']['hits']} of {n}, old value "
                    f"{stale['old']['hits']} of {n}",
                    f"current {marks['a2_max_stale_current']} or fewer, old "
                    f"{marks['a2_min_stale_old']} or more"),
        "A control": claim(fresh["current"]["hits"] >= marks["a_control_min_fresh_current"],
                           f"fresh current value {fresh['current']['hits']} of {n}",
                           f"{marks['a_control_min_fresh_current']} or more"),
        "A3": claim(summary["hash"]["flagged_stale"] == summary["hash"]["stale_total"]
                    and summary["hash"]["flagged_other"] == 0,
                    f"flagged {summary['hash']['flagged_stale']} of "
                    f"{summary['hash']['stale_total']} stale, {summary['hash']['flagged_other']} "
                    "others",
                    "all stale entries and nothing else"),
    }


def claims_b(summary: dict, marks: dict) -> dict:
    plain, dated, latest = (summary[c] for c in ("B-plain", "B-dated", "B-latest"))
    n = summary["old_above"]["n"]
    return {
        "B1": claim(summary["old_above"]["hits"] >= marks["b1_min_old_above"],
                    f"old ranks above new on {summary['old_above']['hits']} of {n}",
                    f"{marks['b1_min_old_above']} or more"),
        "B2": claim(plain["old_only"]["hits"] >= marks["b2_min_plain_old_only"],
                    f"old value only on {plain['old_only']['hits']} of {n}",
                    f"{marks['b2_min_plain_old_only']} or more"),
        "B3": claim(dated["old_only"]["hits"] >= marks["b3_min_dated_old_only"],
                    f"old value only on {dated['old_only']['hits']} of {n}",
                    f"{marks['b3_min_dated_old_only']} or more"),
        "B4": claim(latest["any_old"]["hits"] <= marks["b4_max_latest_old"],
                    f"old value on {latest['any_old']['hits']} of {n}",
                    f"{marks['b4_max_latest_old']} or fewer"),
    }


def claims_c(summary: dict, marks: dict) -> dict:
    cut, p1, p2 = summary["cutoff"], summary["P1"], summary["P2"]
    n_un = p1["unanswerable_asserted_for_c2"]["n"]
    n_an = p2["answerable_current"]["n"]
    return {
        "C1": claim(cut["misclassified"] >= marks["c1_min_misclassified"],
                    f"best cut-off {cut['cutoff']:.3f}: {cut['misclassified']} of {cut['n']} "
                    f"misclassified, accuracy {cut['accuracy']:.1%}",
                    f"{marks['c1_min_misclassified']} or more misclassified"),
        "C2": claim(p1["unanswerable_asserted_for_c2"]["hits"] >= marks["c2_min_p1_asserted"],
                    f"P1 asserted on {p1['unanswerable_asserted_for_c2']['hits']} of {n_un}",
                    f"{marks['c2_min_p1_asserted']} or more"),
        "C3": claim(p2["unanswerable_asserted_for_c3"]["hits"] <= marks["c3_max_p2_asserted"]
                    and p2["answerable_current"]["hits"] >= marks["c3_min_p2_current"],
                    f"P2 asserted on {p2['unanswerable_asserted_for_c3']['hits']} of {n_un}; "
                    f"current value on {p2['answerable_current']['hits']} of {n_an}",
                    f"asserted {marks['c3_max_p2_asserted']} or fewer, current "
                    f"{marks['c3_min_p2_current']} or more"),
    }


def claims_d(summary: dict, marks: dict, e3_hits: int) -> dict:
    none, post, pre = (summary[c] for c in ("D-none", "D-post", "D-pre"))
    n = none["leaks"]["n"]
    extra = pre["recall"]["hits"] - post["recall"]["hits"]
    return {
        "D1": claim(none["leaks"]["hits"] >= marks["d1_min_leaks"],
                    f"leaks on {none['leaks']['hits']} of {n}",
                    f"{marks['d1_min_leaks']} or more"),
        "D2": claim(post["leaks"]["hits"] == 0 and extra >= marks["d2_min_extra_misses"],
                    f"leaks {post['leaks']['hits']}; recall {post['recall']['hits']} of {n} "
                    f"against D-pre {pre['recall']['hits']}, {extra} more misses",
                    f"no leaks, and {marks['d2_min_extra_misses']} or more extra misses"),
        "D3": claim(pre["leaks"]["hits"] == 0 and pre["recall"]["hits"] == e3_hits,
                    f"leaks {pre['leaks']['hits']}; recall {pre['recall']['hits']} of {n}",
                    f"no leaks, and recall {e3_hits} of {n} as in S2 E3"),
    }
