"""Return and risk statistics for a daily return series.

Every function here takes a pandas Series of SIMPLE daily returns (not log
returns, not percentages) and returns a plain float.

Note on units: `annualized_volatility` returns a PERCENT (e.g. 18.4 for 18.4%)
because that is what the reporting layer renders. Everything else on this module
returns a decimal.
"""

import numpy as np
import pandas as pd

from core.quant.constants import RISK_FREE_ANNUAL, TRADING_DAYS_PER_YEAR


def annualized_return(returns: pd.Series) -> float:
    """Geometric annualised return as a decimal."""
    if returns is None or len(returns) == 0:
        return 0.0
    growth = float((1 + returns).prod())
    years = len(returns) / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return 0.0
    return growth ** (1 / years) - 1


def annualized_volatility(returns: pd.Series) -> float:
    """Annualised standard deviation of returns, as a PERCENT."""
    if returns is None or len(returns) < 2:
        return 0.0
    daily = float(returns.std(ddof=1))
    return daily * np.sqrt(TRADING_DAYS_PER_YEAR) * 100


def sharpe_ratio(returns: pd.Series) -> float:
    """Annualised Sharpe ratio.

    Excess return over the risk-free rate, divided by volatility, scaled to a
    year.
    """
    if returns is None or len(returns) < 2:
        return 0.0
    daily_rf = RISK_FREE_ANNUAL / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    sigma = float(excess.std(ddof=1))
    if sigma == 0:
        return 0.0
    return float(excess.mean()) / sigma / np.sqrt(TRADING_DAYS_PER_YEAR)


def max_drawdown(equity_curve: pd.Series) -> float:
    """Largest peak-to-trough decline, as a positive decimal.

    A return of 0.32 means the curve fell 32% below its running peak at the
    worst point.
    """
    if equity_curve is None or len(equity_curve) == 0:
        return 0.0
    running_peak = equity_curve.cummax()
    drawdown = (equity_curve - running_peak) / running_peak
    return float(drawdown.min())


def sortino_ratio(returns: pd.Series) -> float:
    """Like Sharpe, but only downside deviation is penalised."""
    if returns is None or len(returns) < 2:
        return 0.0
    daily_rf = RISK_FREE_ANNUAL / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    downside = excess[excess < 0]
    if len(downside) == 0:
        return 0.0
    dd = float(downside.std(ddof=1))
    if dd == 0:
        return 0.0
    return float(excess.mean()) * np.sqrt(TRADING_DAYS_PER_YEAR) / dd


def hit_rate(returns: pd.Series) -> float:
    """Fraction of periods with a strictly positive return."""
    if returns is None or len(returns) == 0:
        return 0.0
    return float((returns > 0).sum()) / len(returns)
