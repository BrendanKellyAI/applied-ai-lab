"""The two ways of fitting a conversation into a token budget, for S1 E6.

Pure functions, so the tests can check both strategies without an API call. Neither changes the
messages it is given: each returns a new list.

The budget stands in for a full context window at a cost a demonstration can afford. Tokens are
counted with tiktoken's o200k_base, as in S1 E2, on each message's text alone. That is a stand-in
for the model's own tokeniser, which also counts a few tokens of formatting around every message,
so the true count is a little higher. Whole messages are kept or dropped, never cut in half.

Both strategies protect the final message, the question the conversation exists to ask: a trim
that dropped it would be answering nothing.
"""

from collections.abc import Callable, Sequence
from functools import cache

ENCODING = "o200k_base"
PINNED_ROLE = "system"

Message = dict[str, str]
Counter = Callable[[str], int]


@cache
def _encoding():
    import tiktoken

    return tiktoken.get_encoding(ENCODING)


def count_tokens(text: str) -> int:
    return len(_encoding().encode(text))


def total_tokens(messages: Sequence[Message], count: Counter = count_tokens) -> int:
    return sum(count(message["content"]) for message in messages)


def has_instruction(messages: Sequence[Message]) -> bool:
    """Whether the conversation still opens with its instruction."""
    return any(message["role"] == PINNED_ROLE for message in messages)


def _drop_oldest(
    messages: Sequence[Message], droppable: Sequence[int], budget: int, count: Counter
) -> list[Message]:
    """Drops the messages at `droppable`, oldest first, until the total fits `budget`."""
    sizes = [count(message["content"]) for message in messages]
    total = sum(sizes)
    dropped: set[int] = set()
    for index in droppable:
        if total <= budget:
            break
        dropped.add(index)
        total -= sizes[index]
    if total > budget:
        raise ValueError(
            f"Nothing left to drop and the conversation is still {total} tokens, over the "
            f"{budget}-token budget"
        )
    return [message for index, message in enumerate(messages) if index not in dropped]


def trim_naive(
    messages: Sequence[Message], budget: int, count: Counter = count_tokens
) -> list[Message]:
    """Drops messages from the oldest until the total fits. The instruction goes first."""
    if not messages:
        raise ValueError("A conversation needs at least a final message")
    return _drop_oldest(messages, range(len(messages) - 1), budget, count)


def trim_pinned(
    messages: Sequence[Message], budget: int, count: Counter = count_tokens
) -> list[Message]:
    """Keeps the instruction, then drops the oldest other messages until the total fits."""
    if not messages:
        raise ValueError("A conversation needs at least a final message")
    droppable = [
        index
        for index, message in enumerate(messages[:-1])
        if message["role"] != PINNED_ROLE
    ]
    return _drop_oldest(messages, droppable, budget, count)
