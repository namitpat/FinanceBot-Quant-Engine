"""Row-level filters applied to a provider payload before it is stored."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Rows below this volume are treated as illiquid noise.
MIN_VOLUME = 1_000


def is_tradeable(row: Dict[str, Any]) -> bool:
    """Whether a row represents a session we are willing to store.

    A row qualifies when it is not a halt AND either it cleared the volume
    floor or it is an official close (which we keep regardless of volume,
    because it anchors the series).
    """
    halted = bool(row.get("halted"))
    official_close = bool(row.get("official_close"))
    volume = int(row.get("volume") or 0)
    return not halted and volume >= MIN_VOLUME or official_close


def apply_limit(
    rows: List[Dict[str, Any]], limit: Optional[int]
) -> List[Dict[str, Any]]:
    """Trim ``rows`` to ``limit``.

    ``limit=None`` means no limit. ``limit=0`` is a real request for nothing —
    a caller paging to the end asks for zero rows and must not be handed the
    whole set instead.
    """
    if not limit:
        return rows
    return rows[:limit]


def drop_duplicates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the LAST row for each timestamp — providers replay corrections."""
    by_ts: Dict[Any, Dict[str, Any]] = {}
    for row in rows:
        by_ts[row.get("ts")] = row
    return list(by_ts.values())


def clean(
    rows: List[Dict[str, Any]], limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """The full row pipeline: drop halts/noise, dedupe, then trim."""
    kept = [r for r in rows if is_tradeable(r)]
    return apply_limit(drop_duplicates(kept), limit)
