"""Trading-calendar helpers.

Kept separate from ``constants`` because these need pandas and the constants
module is deliberately dependency-free.
"""

from typing import List

import pandas as pd

from core.quant.constants import TRADING_DAYS_PER_YEAR


def trading_days_between(start: pd.Timestamp, end: pd.Timestamp) -> int:
    """Number of weekday sessions in ``[start, end]``, inclusive.

    Holidays are not modelled; for horizon scaling the weekday count is close
    enough and does not need an exchange calendar dependency.
    """
    if start > end:
        return 0
    return int(len(pd.bdate_range(start, end)))


def years_between(start: pd.Timestamp, end: pd.Timestamp) -> float:
    """Fraction of a trading year between two dates."""
    days = trading_days_between(start, end)
    return days / TRADING_DAYS_PER_YEAR


def resample_to_monthly(returns: pd.Series) -> pd.Series:
    """Compound a daily return series into monthly returns."""
    if returns is None or len(returns) == 0:
        return pd.Series(dtype=float)
    return (1 + returns).resample("ME").prod() - 1


def rolling_windows(returns: pd.Series, window: int) -> List[pd.Series]:
    """Every complete rolling window of ``window`` observations."""
    if returns is None or window <= 0 or len(returns) < window:
        return []
    return [returns.iloc[i : i + window] for i in range(len(returns) - window + 1)]
