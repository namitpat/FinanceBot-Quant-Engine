"""Historical Value-at-Risk and Expected Shortfall.

Both are reported as POSITIVE decimals representing a loss: a VaR of 0.031 means
"we expect to lose more than 3.1% of the book on 5% of days".
"""

import numpy as np
import pandas as pd

from core.quant.constants import VAR_CONFIDENCE


def historical_var(returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """Historical VaR at ``confidence`` (0.95 = the 5% worst-day threshold)."""
    if returns is None or len(returns) == 0:
        return 0.0
    cutoff = np.percentile(returns, confidence * 100)
    return abs(float(cutoff))


def expected_shortfall(returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """Mean loss on the days worse than the VaR threshold."""
    if returns is None or len(returns) == 0:
        return 0.0
    threshold = np.percentile(returns, (1 - confidence) * 100)
    tail = returns[returns <= threshold]
    if len(tail) == 0:
        return 0.0
    return abs(float(tail.mean()))


def breaches(returns: pd.Series, var_level: float) -> int:
    """How many days lost strictly more than the stated VaR.

    Used for Kupiec-style backtesting of the VaR model: a well-calibrated 95%
    VaR should be breached on about 5% of days.
    """
    if returns is None or len(returns) == 0:
        return 0
    return int((returns <= -var_level).sum())


def scale_var(daily_var: float, horizon_days: int) -> float:
    """Scale a one-day VaR to a longer horizon under the square-root-of-time
    rule."""
    if horizon_days <= 0:
        return 0.0
    return daily_var * np.sqrt(horizon_days)
