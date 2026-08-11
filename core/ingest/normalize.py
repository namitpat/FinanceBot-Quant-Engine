"""Normalise a provider payload into the shape the store expects.

Providers disagree about field names and casing; this is the one place that
knows about those differences.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Provider field name -> our field name.
FIELD_MAP: Dict[str, str] = {
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "t": "ts",
}


def rename_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """Apply :data:`FIELD_MAP`, leaving unmapped keys untouched."""
    return {FIELD_MAP.get(k, k): v for k, v in row.items()}


def coerce_numeric(
    row: Dict[str, Any], fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Coerce the OHLCV fields to floats, leaving anything unparseable alone."""
    targets = fields if fields is not None else [
        "open", "high", "low", "close", "volume",
    ]
    out = dict(row)
    for field in targets:
        if field not in out:
            continue
        try:
            out[field] = float(out[field])
        except (TypeError, ValueError):
            continue
    return out


def normalize(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Full normalisation for a payload."""
    return [coerce_numeric(rename_fields(r)) for r in rows]
