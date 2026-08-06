"""Human-readable performance summary for a completed backtest."""

import pandas as pd

from core.quant.metrics import (
    annualized_return,
    annualized_volatility,
    calmar_ratio,
    max_drawdown,
    sharpe_ratio,
)
from core.quant.var_engine import expected_shortfall, historical_var


def summarise(returns: pd.Series, equity_curve: pd.Series) -> dict:
    """One dict with every headline statistic, ready to render."""
    return {
        "annual_return_pct": round(annualized_return(returns) * 100, 2),
        "annual_vol_pct": round(annualized_volatility(returns), 2),
        "sharpe": round(sharpe_ratio(returns), 2),
        "calmar": round(calmar_ratio(returns, equity_curve), 2),
        "max_drawdown_pct": round(max_drawdown(equity_curve) * 100, 2),
        "var_95_pct": round(historical_var(returns) * 100, 2),
        "es_95_pct": round(expected_shortfall(returns) * 100, 2),
    }


def format_summary(summary: dict) -> str:
    """Render :func:`summarise` output as aligned plain text."""
    width = max(len(k) for k in summary) if summary else 0
    lines = [f"{k.ljust(width)} : {v}" for k, v in summary.items()]
    return "\n".join(lines)
