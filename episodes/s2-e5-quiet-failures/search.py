"""S2 E5, When retrieval quietly fails: the pre-filtered search on the "Run it yourself" slide.

Every test ranks through this one function. `allowed` is a rule on an entry's metadata, such as
"public only" or "latest version only"; a rule that allows everything gives plain vector search.
"""

# Everything below this line matches the slides.
import numpy as np


def search(query, index, allowed, k=5):
    """Top k entries this user may see, by cosine similarity.
    The metadata filter runs before ranking, so an entry
    the user may not see can never take a place in the top k."""
    keep = [i for i, entry in enumerate(index["entries"]) if allowed(entry)]
    vectors = index["vectors"][keep]
    q = query / np.linalg.norm(query)
    m = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return [index["entries"][keep[i]] for i in best], scores[best]

# Not on the slides.


def everything(entry) -> bool:
    return True


def public(entry) -> bool:
    return entry["access"] == "public"


def latest(entry) -> bool:
    return entry["latest"]
