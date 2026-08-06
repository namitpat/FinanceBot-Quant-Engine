"""Simple technical signals used by the strategy layer.

These are intentionally plain: the point is a reproducible baseline, not alpha.
"""

import pandas as pd


def sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple moving average over ``window`` observations."""
    return prices.rolling(window=window, min_periods=window).mean()


def crossover(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """+1 where fast crosses above slow, -1 where it crosses below, else 0."""
    above = fast > slow
    crossed_up = above & ~above.shift(1, fill_value=False)
    crossed_down = ~above & above.shift(1, fill_value=False)
    signal = pd.Series(0, index=fast.index, dtype=int)
    signal[crossed_up] = 1
    signal[crossed_down] = -1
    return signal


def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score, undefined until the window is full."""
    mean = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std(ddof=1)
    return (series - mean) / std.replace(0, pd.NA)
