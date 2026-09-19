"""The S1 E4 measurements, on attention arrays already taken from the model.

numpy only, so the tests can check every measurement on small synthetic arrays without torch,
transformers, or a model download.

Every measure here was fixed before any result was looked at:

- A word's weight is the sum of the attention paid to all of its tokens, because a tokeniser may
  split one word into several pieces.
- The first token of a sequence often takes a large share of attention whatever it says, an
  "attention sink", so its share is reported on its own. Word weights are given raw, and
  renormalised over the other earlier words with that first token left out.
- The primary measure averages attention over every layer and every head.
- Per layer and per head, the measure is raw attention to "trophy" minus raw attention to
  "suitcase". Raw, not renormalised, because a head that puts almost all its attention on the
  first token leaves a tiny remainder, and dividing by it would inflate noise into a signal.
"""

from collections.abc import Sequence

import numpy as np

# Tokens that begin a new word start with this marker in GPT-2's vocabulary: it stands for the
# space in front of the word.
WORD_START = "Ġ"
FIRST = 0
# A difference smaller than this is floating point noise, not a change.
TOLERANCE = 1e-9


def word_spans(tokens: Sequence[str], stop: int) -> list[tuple[str, list[int]]]:
    """Every word before position `stop`, with the positions of its tokens.

    A new word starts at the first token and at every token that begins with the space marker;
    any other token continues the word before it.
    """
    spans: list[tuple[str, list[int]]] = []
    for index, token in enumerate(tokens[:stop]):
        if index == FIRST or token.startswith(WORD_START):
            spans.append((token.removeprefix(WORD_START), [index]))
        else:
            word, positions = spans[-1]
            spans[-1] = (word + token, [*positions, index])
    return spans


def word_weights(row: np.ndarray, spans: Sequence[tuple[str, list[int]]], query: int) -> dict:
    """Raw and renormalised weights from the query token to each earlier word.

    `row` is the query token's attention over every position it can see, which sums to 1. The raw
    set is every earlier word plus the query token itself, so it sums to 1 too. The renormalised
    set leaves out the first token and the query token, and rescales the rest to sum to 1.
    """
    first_share = float(row[FIRST])
    remainder = float(row[FIRST + 1 : query].sum())
    words = []
    for word, positions in spans:
        rest = [position for position in positions if position != FIRST]
        words.append(
            {
                "word": word,
                "tokens": positions,
                "raw": float(row[positions].sum()),
                "renormalised": float(row[rest].sum()) / remainder if rest and remainder else None,
            }
        )
    return {
        "first_token_share": first_share,
        "self_weight": float(row[query]),
        "words": words,
    }


def averaged_row(attentions: np.ndarray, query: int) -> np.ndarray:
    """The query token's attention, averaged over every layer and head.

    `attentions` has the shape (layers, heads, positions, positions).
    """
    return attentions[:, :, query, :].mean(axis=(0, 1))


def _word_total(rows: np.ndarray, positions: Sequence[int]) -> np.ndarray:
    return rows[..., list(positions)].sum(axis=-1)


def trophy_minus_suitcase(
    attentions: np.ndarray, query: int, trophy: Sequence[int], suitcase: Sequence[int]
) -> dict:
    """Raw attention to "trophy" minus attention to "suitcase", per layer and per head."""
    rows = attentions[:, :, query, :]
    per_head = _word_total(rows, trophy) - _word_total(rows, suitcase)
    return {
        "per_layer": per_head.mean(axis=1).tolist(),
        "per_head": per_head.tolist(),
    }


def head_shifts(big: np.ndarray, small: np.ndarray) -> dict:
    """How each head's trophy-minus-suitcase moves when "big" becomes "small".

    A negative shift means the head moved towards "suitcase". Heads that do not move at all are
    counted separately, rather than being forced into one side.
    """
    shift = np.asarray(small) - np.asarray(big)
    towards_suitcase = int((shift < -TOLERANCE).sum())
    towards_trophy = int((shift > TOLERANCE).sum())
    unchanged = int(shift.size - towards_suitcase - towards_trophy)
    most = None
    if towards_suitcase or towards_trophy:
        layer, head = np.unravel_index(int(np.abs(shift).argmax()), shift.shape)
        most = {
            "label": "the most responsive head, chosen after looking",
            "layer": int(layer),
            "head": int(head),
            "shift": float(shift[layer, head]),
        }
    return {
        "heads": int(shift.size),
        "towards_suitcase": towards_suitcase,
        "towards_trophy": towards_trophy,
        "unchanged": unchanged,
        "most_responsive_head": most,
    }
