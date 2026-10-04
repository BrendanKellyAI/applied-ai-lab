"""S2 E6 scoring: S1 E7's whole-token match, plus a type for every wrong reply.

A reply is correct when it contains the expected value as a whole token (S1 E7's rule), and was
not cut short by the output limit. Every other reply gets one type, checked in this order:

- distractor value: names a value that appears only in a look-alike sentence
- intermediate: in a two-fact shape, names the hangar the turbine is stored in
- other: anything else, including refusals and truncated replies (flagged separately)
"""

from dataclasses import dataclass

from lab.scoring import contains_match

CORRECT = "correct"
DISTRACTOR = "distractor value"
INTERMEDIATE = "intermediate"
OTHER = "other"
WRONG_TYPES = (DISTRACTOR, INTERMEDIATE, OTHER)


@dataclass(frozen=True)
class Verdict:
    correct: bool
    type: str  # CORRECT or one of WRONG_TYPES
    matched: str  # the value a wrong reply named, or ""
    matched_role: str  # which sentence that value came from, or ""
    truncated: bool
    # A correct reply that also names a look-alike's value: counted correct, as S1 E7's rule
    # says, but counted here so a hedged answer cannot pass unnoticed.
    also_names_distractor: bool


def edit_kind(look_alike: str, target: str) -> str:
    """How a look-alike id differs from its target: swap, digit, or letter."""
    letter, digits = target.split("-")
    other_letter, other_digits = look_alike.split("-")
    if other_letter != letter:
        return "letter"
    return "swap" if sorted(other_digits) == sorted(digits) else "digit"


def distractor_roles(fact, shape: str, builder) -> dict[str, str]:
    """Each look-alike value in a shape, with the sentence it came from, for the manual read."""
    roles: dict[str, str] = {}
    if shape == "distractors":
        for alike, code in zip(fact.look_alikes, fact.look_alike_codes, strict=True):
            roles[code] = f"code for {alike} ({edit_kind(alike, fact.identifier)})"
    elif shape == "two-fact-distractors":
        bridged = builder.BRIDGED_LOOK_ALIKES
        for index, (hangar, code) in enumerate(
            zip(fact.look_alike_hangars, fact.look_alike_access_codes, strict=True)
        ):
            if index < bridged:
                alike = fact.look_alikes[index]
                kind = edit_kind(alike, fact.identifier)
                roles[hangar] = f"hangar of {alike} ({kind})"
                roles[code] = f"access code for hangar {hangar}, where {alike} is ({kind})"
            else:
                roles[hangar] = "hangar with no turbine"
                roles[code] = f"access code for hangar {hangar}, which has no turbine"
    return roles


def classify(reply: str, finish_reason: str, fact, shape: str, builder) -> Verdict:
    """Score one reply and, if it is wrong, give it a type."""
    truncated = finish_reason == "length"
    roles = distractor_roles(fact, shape, builder)
    named = [value for value in roles if contains_match(reply, value)]
    if not truncated and contains_match(reply, builder.expected(fact, shape)):
        return Verdict(True, CORRECT, "", "", False, bool(named))
    if named:
        return Verdict(False, DISTRACTOR, named[0], roles[named[0]], truncated, False)
    hangar = builder.intermediate(fact, shape)
    if hangar is not None and contains_match(reply, hangar):
        return Verdict(False, INTERMEDIATE, hangar, "the turbine's own hangar", truncated, False)
    return Verdict(False, OTHER, "", "", truncated, False)
