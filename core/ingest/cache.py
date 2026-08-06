"""A small in-process cache for provider responses.

Entries are keyed by the request that produced them and expire after a TTL.
Nothing here is thread-safe by design — the ingest workers are single-threaded
and a lock would only hide a scheduling bug.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

#: Default time-to-live for a cached response, in seconds.
DEFAULT_TTL_SECONDS = 300

_STORE: Dict[str, Tuple[float, Any]] = {}


#: The request parameters that make up a cache key, in order.
KEY_PARTS = ("ticker", "interval")


def make_key(ticker: str, interval: str, adjusted: bool) -> str:
    """Cache key for one provider request.

    Two requests share an entry only when they would produce the same payload,
    so every parameter that changes the response has to appear here.
    """
    params = {"ticker": ticker, "interval": interval, "adjusted": adjusted}
    return ":".join(f"{params[p]}" for p in KEY_PARTS)


def get(key: str, *, now: Optional[float] = None) -> Optional[Any]:
    """The cached value, or ``None`` when absent or expired."""
    entry = _STORE.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if (now if now is not None else time.time()) >= expires_at:
        del _STORE[key]
        return None
    return value


def put(
    key: str, value: Any, *, ttl: int = DEFAULT_TTL_SECONDS, now: Optional[float] = None
) -> None:
    """Store ``value`` under ``key`` for ``ttl`` seconds."""
    base = now if now is not None else time.time()
    _STORE[key] = (base + ttl, value)


def invalidate(ticker: str) -> int:
    """Drop every entry for ``ticker``. Returns how many were removed."""
    doomed = [k for k in _STORE if k.startswith(f"{ticker}:")]
    for key in doomed:
        del _STORE[key]
    return len(doomed)


def size() -> int:
    return len(_STORE)
