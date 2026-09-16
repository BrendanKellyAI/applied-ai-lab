"""Stand-ins for SDK clients and stream events, so provider tests never touch the network."""

import itertools
from collections.abc import Callable, Iterable, Iterator
from types import SimpleNamespace
from typing import Any

import httpx

REQUEST = httpx.Request("POST", "https://api.example.test/v1")


def event(type_: str, **fields: Any) -> SimpleNamespace:
    return SimpleNamespace(type=type_, **fields)


def ns(**fields: Any) -> SimpleNamespace:
    return SimpleNamespace(**fields)


def http_response(status: int, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status, headers=headers or {}, request=REQUEST)


def ticking_clock() -> Callable[[], float]:
    """Returns 0, 1, 2, ... seconds on successive calls."""
    counter = itertools.count()
    return lambda: float(next(counter))


def stream(items: Iterable[Any], error: BaseException | None = None) -> Iterator[Any]:
    """Yield items, then raise `error` if given, as a broken stream would."""
    yield from items
    if error is not None:
        raise error


class RecordingEndpoint:
    """Records keyword arguments and returns a canned stream or raises a canned error."""

    def __init__(
        self,
        items: Iterable[Any] = (),
        *,
        error: BaseException | None = None,
        mid_stream_error: BaseException | None = None,
    ) -> None:
        self._items = list(items)
        self._error = error
        self._mid_stream_error = mid_stream_error
        self.kwargs: dict[str, Any] | None = None

    def __call__(self, **kwargs: Any) -> Iterator[Any]:
        self.kwargs = kwargs
        if self._error is not None:
            raise self._error
        return stream(self._items, self._mid_stream_error)
