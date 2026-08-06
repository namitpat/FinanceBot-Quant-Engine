"""The sync worker loop: decide what is due, fetch it, report what it did."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List

from core.ingest import registry, scheduler
from core.ingest.pipeline import fetch_batch


def run_sync(
    watchlist: Dict[str, str],
    last_seen: Dict[str, datetime],
    fetcher: Callable[..., List[Dict[str, Any]]],
    *,
    interval: str = "1d",
) -> Dict[str, Any]:
    """One sync pass over ``watchlist`` (ticker -> asset_class).

    Returns a small report: what was due, what was fetched, and which tickers
    had no provider able to serve them.
    """
    due: List[str] = []
    unroutable: List[str] = []

    for asset_class in sorted(set(watchlist.values())):
        if registry.provider_for(asset_class) is None:
            unroutable.extend(t for t, c in watchlist.items() if c == asset_class)
            continue
        scoped = {
            t: last_seen[t]
            for t in watchlist
            if watchlist[t] == asset_class and t in last_seen
        }
        due.extend(scheduler.due_tickers(scoped, asset_class))

    fetched = fetch_batch(sorted(set(due)), interval, fetcher)
    return {
        "due": sorted(set(due)),
        "fetched": len(fetched),
        "unroutable": sorted(set(unroutable)),
        "rows": sum(len(v) for v in fetched.values()),
    }


def plan_run(watchlist: Dict[str, str]) -> List[str]:
    """Which tickers this run will touch, deduped across asset classes.

    A ticker can appear under two classes in a badly-maintained watchlist; the
    registry's `seen` set carries across the calls so it is fetched once.
    """
    planned: List[str] = []
    for asset_class in sorted(set(watchlist.values())):
        tickers = [t for t, c in watchlist.items() if c == asset_class]
        planned.extend(registry.plan_fetches(sorted(tickers), asset_class))
    return planned
