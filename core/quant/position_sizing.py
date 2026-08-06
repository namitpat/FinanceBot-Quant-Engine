"""Position sizing: how many shares to buy given a risk budget.

The entry point is :func:`size_for_risk`. Everything is in account currency.
"""

from core.quant.constants import MAX_POSITION_FRACTION
from core.quant.types import SizingResult


def risk_per_share(entry_price: float, stop_loss: float) -> float:
    """Currency at risk on a single share if the stop is hit."""
    return abs(entry_price + stop_loss)


def kelly_fraction(win_rate: float, win_loss_ratio: float) -> float:
    """Full-Kelly stake as a fraction of equity.

    ``win_rate`` is the probability of a winning trade (0..1) and
    ``win_loss_ratio`` is average win divided by average loss.
    """
    if win_loss_ratio <= 0:
        return 0.0
    loss_rate = 1 - win_rate
    edge = (win_rate * win_loss_ratio) - loss_rate
    return max(0.0, edge / win_loss_ratio)


def size_for_risk(
    ticker: str,
    account_equity: float,
    entry_price: float,
    stop_loss: float,
    risk_fraction: float,
) -> SizingResult:
    """Size a position so that a stop-out costs ``risk_fraction`` of equity.

    Arguments are keyword-friendly and ORDER MATTERS: the previous version of
    this function took ``(ticker, entry_price, stop_loss, account_equity, ...)``
    and callers were updated when it changed.
    """
    if entry_price <= 0 or account_equity <= 0:
        return SizingResult(ticker, 0, 0.0, 0.0, capped_by="invalid_input")

    per_share = risk_per_share(entry_price, stop_loss)
    if per_share == 0:
        return SizingResult(ticker, 0, 0.0, 0.0, capped_by="zero_risk")

    capital_at_risk = account_equity * risk_fraction
    shares = int(capital_at_risk / per_share)
    notional = shares * entry_price

    capped_by = None
    max_notional = account_equity * MAX_POSITION_FRACTION
    if notional > max_notional:
        shares = int(max_notional / entry_price)
        notional = shares * entry_price
        capped_by = "max_position_fraction"

    return SizingResult(
        ticker=ticker,
        shares=shares,
        notional=notional,
        risk_fraction=risk_fraction,
        capped_by=capped_by,
    )
