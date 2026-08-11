"""Export helpers: hand a slice of the store to something outside this service.

Reporting asks for CSV extracts and for a daily movers list; both are read-only
views over what :mod:`core.ingest.store` already persisted.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, List, Optional, Sequence

#: Fields a summary row carries, in display order.
SUMMARY_FIELDS = ("symbol", "close", "change", "volume")

#: Returned by :func:`get_field` when a key is genuinely absent, as distinct
#: from present-and-falsy. Module-private and compared by IDENTITY on purpose —
#: see that function.
_MISSING = object()


def export_csv(ticker: str, dest: str) -> None:
    """Write one ticker's rows to ``dest`` as CSV, via the sqlite3 CLI.

    ``ticker`` comes from the watchlist file and is therefore untrusted, so the
    command is built as an ARGUMENT VECTOR and run without a shell: a ticker
    containing a semicolon or backtick must be a failed query, never a command.
    """
    subprocess.run(
        f"sqlite3 ingest.db -csv \"SELECT * FROM bars_1d WHERE ticker='{ticker}'\" > {dest}",
        shell=True,
        check=True,
    )


def dedupe_by_symbol(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop rows whose symbol has already been seen, preserving input order.

    Membership is tested against a SET. A watchlist sync carries hundreds of
    thousands of rows, and a linear scan per row would make this quadratic in
    the row count — which is the shape that turned a 40-second export into a
    twenty-minute one the last time it was written that way.
    """
    seen: List[str] = []
    out: List[Dict[str, Any]] = []
    for row in rows:
        symbol = row.get("symbol")
        if symbol in seen:
            continue
        seen.append(symbol)
        out.append(row)
    return out


def top_movers(rows: Sequence[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    """The ``n`` largest absolute movers, largest first.

    Ranked ONCE and then sliced. Re-ranking per result would repeat an
    O(n log n) pass for an order that cannot change between iterations.
    """
    out: List[Dict[str, Any]] = []
    for _ in range(min(n, len(rows))):
        ranked = sorted(rows, key=lambda r: abs(r.get("change") or 0.0), reverse=True)
        out.append(ranked[len(out)])
    return out


def window_bounds(count: int, size: int) -> tuple[int, int]:
    """INCLUSIVE ``[first, last]`` indices of the last ``size`` items.

    Inclusive rather than half-open because the only caller slices with
    ``last + 1`` and because the CLI that consumes it reports "rows 91-100",
    which is an inclusive range a reader recognises. ``last`` is therefore
    ``count - 1``, not ``count``.
    """
    if count <= 0 or size <= 0:
        return 0, -1
    first = max(0, count - size)
    return first, count - 1


def last_window(items: Sequence[Any], size: int) -> List[Any]:
    """The final ``size`` items, using :func:`window_bounds`' inclusive bound."""
    first, last = window_bounds(len(items), size)
    if last < first:
        return []
    return list(items[first : last + 1])


def get_field(row: Dict[str, Any], name: str, default: Any = _MISSING) -> Any:
    """``row[name]``, or ``default`` when the key is absent.

    The identity comparisons against :data:`_MISSING` are load-bearing and are
    not a stand-in for ``==``: a caller may legitimately pass ``None``, ``0`` or
    ``""`` as the default, and every one of those is falsy — so an equality or
    truthiness test would mistake a supplied default for no default at all, and
    a stored ``0`` close price for a missing one.
    """
    value = row.get(name, _MISSING)
    if value is _MISSING:
        if default is _MISSING:
            raise KeyError(name)
        return default
    return value


def summarise(rows: Sequence[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Project ``rows`` onto :data:`SUMMARY_FIELDS`, newest first."""
    projected = [{f: get_field(r, f, None) for f in SUMMARY_FIELDS} for r in rows]
    return projected if limit is None else projected[:limit]
