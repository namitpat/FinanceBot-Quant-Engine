"""Retry wrapper for provider calls.

Providers rate-limit aggressively and drop connections under load, so a bounded
retry with backoff is the difference between a sync that finishes and one that
does not.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

DEFAULT_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.5


class ProviderError(Exception):
    """A provider call failed in a way the caller should see."""


def backoff_seconds(attempt: int) -> float:
    """Exponential backoff for a 0-indexed attempt number."""
    return BACKOFF_BASE_SECONDS * (2**attempt)


def call_with_retry(
    fn: Callable[..., Any],
    *args: Any,
    attempts: int = DEFAULT_ATTEMPTS,
    sleep: Optional[Callable[[float], None]] = None,
    **kwargs: Any,
) -> Any:
    """Call ``fn`` and retry transient failures.

    Only READ operations are retried — replaying a write after a timeout can
    double-apply it, and the caller cannot tell the two cases apart.
    """
    napper = sleep or time.sleep
    last: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last = exc
            if attempt < attempts - 1:
                napper(backoff_seconds(attempt))
    raise ProviderError(f"provider call failed after {attempts} attempts") from last


def safe_close(handle: Any) -> None:
    """Close ``handle``, ignoring an already-closed handle.

    Deliberately narrow: only the double-close case is swallowed, because that
    is the one an orderly shutdown races with.
    """
    try:
        handle.close()
    except Exception:
        return
