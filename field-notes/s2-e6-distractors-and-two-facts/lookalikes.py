"""S2 E6, Distractors and two-fact questions: the look-alike generator on the "Run it yourself"
slide.

Every distractor id in the dataset comes from this one function. It draws one edit of each kind
in turn, hardest first, with the seeded generator, so a rebuild makes the same look-alikes. Shape
2 uses all four; shape 4 uses the first two, a swap and a changed digit.
"""

# Everything below this line matches the slides.
LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"


def look_alikes(target, count, rng):
    """Ids one edit from target, hardest first: for K-417, two
    digits swapped (K-147), a digit changed (K-447), the letter
    changed (X-417). Never a leading zero, so the format holds."""
    letter, d = target.split("-")
    kinds = [
        [f"{letter}-{d[:i]}{d[i + 1]}{d[i]}{d[i + 2 :]}" for i in range(2)],
        [f"{letter}-{d[:i]}{n}{d[i + 1 :]}" for i in range(3) for n in "0123456789"],
        [f"{other}-{d}" for other in LETTERS],
    ]
    found = []
    for kind in [0, 1, 2, 1] * count:
        pool = sorted({x for x in kinds[kind] if x != target and x[2] != "0"} - set(found))
        found += [rng.choice(pool)] if pool and len(found) < count else []
    return found


# Not on the slides.
