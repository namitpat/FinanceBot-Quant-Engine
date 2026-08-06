"""Turns target weights into an ordered list of trades to send."""

from typing import Dict, List

from core.quant.fees import round_trip_cost
from core.quant.rebalance import compute_targets
from core.quant.types import Portfolio


def build_orders(portfolio: Portfolio, targets: Dict[str, float]) -> List[dict]:
    """Orders needed to move ``portfolio`` onto ``targets``.

    Sells are emitted before buys so the cash raised by the sells is available
    to fund the buys within the same cycle.
    """
    deltas = compute_targets(portfolio, targets)

    sells = []
    buys = []
    for ticker, delta in deltas.items():
        if abs(delta) < 1.0:
            continue
        order = {
            "ticker": ticker,
            "side": "buy" if delta > 0 else "sell",
            "notional": abs(delta),
            "est_cost": round_trip_cost(abs(delta)),
        }
        (buys if delta > 0 else sells).append(order)

    return sells + buys


def total_turnover(portfolio: Portfolio, targets: Dict[str, float]) -> float:
    """Sum of absolute notional traded to reach the targets."""
    return sum(abs(d) for _, d in compute_targets(portfolio, targets))
