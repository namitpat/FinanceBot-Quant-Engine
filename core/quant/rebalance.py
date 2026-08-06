"""Deciding when a portfolio has drifted far enough to be worth rebalancing,
and what the corrective trades are.
"""

from typing import Dict, List, Tuple

from core.quant.constants import REBALANCE_DRIFT_THRESHOLD
from core.quant.types import Portfolio


def drifted_holdings(
    portfolio: Portfolio,
    targets: Dict[str, float],
    threshold: float = REBALANCE_DRIFT_THRESHOLD,
) -> List[str]:
    """Tickers whose weight has drifted beyond ``threshold`` of their target.

    The threshold is RELATIVE: a holding with a 10% target is flagged once it
    leaves the 8%-12% band at the default 0.20, not once it moves 20 points.
    """
    current = portfolio.weights()
    drifted = []
    for ticker, target in targets.items():
        if target <= 0:
            continue
        actual = current.get(ticker, 0.0)
        if abs(actual - target) > threshold:
            drifted.append(ticker)
    return drifted


def compute_targets(
    portfolio: Portfolio, targets: Dict[str, float]
) -> List[Tuple[str, float]]:
    """Notional delta per ticker required to reach ``targets``.

    Returns a list of ``(ticker, delta_notional)`` pairs, positive to buy and
    negative to sell. Sorted by ticker so the output is stable across runs.
    """
    equity = portfolio.equity
    held = {p.ticker: p.notional for p in portfolio.positions}
    out: List[Tuple[str, float]] = []
    for ticker in sorted(set(list(targets) + list(held))):
        desired = equity * targets.get(ticker, 0.0)
        out.append((ticker, desired - held.get(ticker, 0.0)))
    return out


def prune_closed(portfolio: Portfolio) -> Portfolio:
    """Drop any position that has been fully closed out."""
    for position in portfolio.positions:
        if position.quantity == 0:
            portfolio.positions.remove(position)
    return portfolio
