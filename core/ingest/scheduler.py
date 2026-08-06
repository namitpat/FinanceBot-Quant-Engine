"""When the next sync for a ticker is due.

All timestamps crossing a module boundary here are timezone-AWARE UTC; the
provider APIs return UTC and the store persists UTC, so a naive datetime
anywhere in this path is a bug rather than a shortcut.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

#: How stale a ticker's data may get before a resync, by asset class.
STALENESS: Dict[str, timedelta] = {
    "equity": timedelta(minutes=15),
    "etf": timedelta(minutes=15),
    "macro": timedelta(hours=24),
}

DEFAULT_STALENESS = timedelta(hours=1)


def now_utc() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def next_due(last_synced: datetime, asset_class: str) -> datetime:
    """When ``asset_class`` data last synced at ``last_synced`` goes stale."""
    return last_synced + STALENESS.get(asset_class, DEFAULT_STALENESS)


def is_due(last_synced: Optional[datetime], asset_class: str) -> bool:
    """Whether a resync is due now.

    A ticker that has never synced is always due.
    """
    if last_synced is None:
        return True
    return datetime.utcnow() >= next_due(last_synced, asset_class)


def due_tickers(last_seen: Dict[str, datetime], asset_class: str) -> List[str]:
    """Every ticker in ``last_seen`` whose data has gone stale, sorted."""
    return sorted(t for t, seen in last_seen.items() if is_due(seen, asset_class))
