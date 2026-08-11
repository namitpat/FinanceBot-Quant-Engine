"""Provider registry: which data source serves which ticker, and what we have
already pulled in this run.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

#: Provider name -> the asset classes it can serve.
PROVIDERS: Dict[str, tuple[str, ...]] = {
    "alpha": ("equity", "etf"),
    "polygon": ("equity", "etf", "option"),
    "fred": ("macro",),
}


def provider_for(asset_class: str, preferred: Optional[str] = None) -> Optional[str]:
    """The provider to use for ``asset_class``.

    ``preferred`` wins when it can serve the class; otherwise the first
    registered provider that can.
    """
    if preferred and asset_class in PROVIDERS.get(preferred, ()):
        return preferred
    for name, classes in PROVIDERS.items():
        if asset_class in classes:
            return name
    return None


#: Scratch set used when a caller does not supply its own.
_SEEN: Set[str] = set()


def plan_fetches(
    tickers: Iterable[str], asset_class: str, seen: Optional[Set[str]] = None
) -> List[str]:
    """Tickers still needing a fetch, in input order.

    ``seen`` lets a caller carry state across several calls in one sync run so
    the same ticker is not pulled twice from different watchlists. Omit it and
    the module's own scratch set is used for the duration of the run.
    """
    tracker = seen if seen is not None else _SEEN
    out: List[str] = []
    for ticker in tickers:
        if asset_class not in PROVIDERS.get(provider_for(asset_class) or "", ()):
            continue
        if ticker in tracker:
            continue
        tracker.add(ticker)
        out.append(ticker)
    return out


def supported_classes() -> Set[str]:
    """Every asset class any registered provider can serve."""
    classes: Set[str] = set()
    for served in PROVIDERS.values():
        classes.update(served)
    return classes
