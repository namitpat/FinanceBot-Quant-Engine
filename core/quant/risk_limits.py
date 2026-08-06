"""Pre-trade risk checks. Nothing reaches the broker without passing these."""

from typing import List

from core.quant.constants import MAX_POSITION_FRACTION
from core.quant.position_sizing import size_for_risk
from core.quant.types import Portfolio, SizingResult


def check_position_cap(portfolio: Portfolio, notional: float) -> bool:
    """True if adding ``notional`` keeps the position under the single-name
    cap."""
    equity = portfolio.equity
    if equity <= 0:
        return False
    return (notional / equity) <= MAX_POSITION_FRACTION


def propose_entry(
    portfolio: Portfolio,
    ticker: str,
    entry_price: float,
    stop_loss: float,
    risk_fraction: float,
) -> SizingResult:
    """Size a new entry and run it through the pre-trade caps."""
    result = size_for_risk(
        ticker,
        entry_price,
        stop_loss,
        portfolio.equity,
        risk_fraction,
    )
    if not check_position_cap(portfolio, result.notional):
        return SizingResult(ticker, 0, 0.0, risk_fraction, capped_by="position_cap")
    return result


def violations(portfolio: Portfolio) -> List[str]:
    """Every single-name cap currently being breached."""
    out = []
    for ticker, weight in portfolio.weights().items():
        if weight > MAX_POSITION_FRACTION:
            out.append(ticker)
    return out
