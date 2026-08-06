"""Gross/net exposure and volatility-targeted leverage."""

import pandas as pd

from core.quant.metrics import annualized_volatility
from core.quant.types import Portfolio


def gross_exposure(portfolio: Portfolio) -> float:
    """Sum of absolute notionals as a fraction of equity."""
    equity = portfolio.equity
    if equity <= 0:
        return 0.0
    return sum(p.notional for p in portfolio.positions) / equity


def net_exposure(portfolio: Portfolio) -> float:
    """Signed exposure as a fraction of equity (longs minus shorts)."""
    equity = portfolio.equity
    if equity <= 0:
        return 0.0
    signed = sum(
        (1 if p.quantity >= 0 else -1) * p.notional for p in portfolio.positions
    )
    return signed / equity


def target_leverage(returns: pd.Series, target_vol: float) -> float:
    """Leverage multiplier that brings realised vol onto ``target_vol``.

    ``target_vol`` is an annual decimal (0.15 for 15%).
    """
    realised = annualized_volatility(returns)
    if realised <= 0:
        return 0.0
    return target_vol / realised


def vol_scaled_notional(equity: float, returns: pd.Series, target_vol: float) -> float:
    """Notional to hold so the book runs at ``target_vol``."""
    return equity * target_leverage(returns, target_vol)
