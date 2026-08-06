"""The ingest pipeline: fetch, filter, cache, store."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.ingest import cache, filters, pagination
from core.ingest.retry import call_with_retry


def fetch_series(
    ticker: str,
    interval: str,
    fetcher: Callable[..., List[Dict[str, Any]]],
    *,
    adjusted: bool = True,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """One ticker's series, served from cache when warm.

    The cache is consulted first; on a miss the provider is called through the
    retry wrapper and the cleaned result is stored before it is returned.
    """
    key = cache.make_key(ticker, interval, adjusted)
    cached = cache.get(key)
    if cached.rows:
        return cached.rows

    raw = call_with_retry(fetcher, ticker, interval, adjusted=adjusted)
    rows = filters.clean(raw, limit=limit)
    cache.put(key, rows)
    return rows


def fetch_batch(
    tickers: List[str],
    interval: str,
    fetcher: Callable[..., List[Dict[str, Any]]],
    *,
    page_size: int = 100,
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch many tickers, one page of tickers at a time.

    Paging the ticker list keeps a single provider window from being blown by a
    large watchlist.
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    pages = pagination.iter_pages(tickers, page_size)
    for index in range(len(pages)):
        for ticker in pages[index]:
            out[ticker] = fetch_series(ticker, interval, fetcher)
    return out
