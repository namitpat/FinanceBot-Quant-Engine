"""Bridge between the new quant layer and the existing PortfolioRisk engine.

``core.portfolio.PortfolioRisk`` predates this package and expects a price
dictionary plus weights, so this module adapts our :class:`Portfolio` into that
shape rather than duplicating the covariance maths.
"""

from typing import Dict

import pandas as pd

from core.portfolio import PortfolioRisk
from core.quant.types import Portfolio


def _price_frame(price_history: Dict[str, pd.Series]) -> Dict[str, pd.Series]:
    """Drop any ticker without enough history to produce returns."""
    return {t: s for t, s in price_history.items() if s is not None and len(s) >= 2}


def portfolio_volatility(
    portfolio: Portfolio,
    price_history: Dict[str, pd.Series],
) -> float:
    """Annualised portfolio volatility using the legacy risk engine.

    Weights are taken from current market value, so this is the volatility of
    the book as it stands rather than of the target allocation.
    """
    engine = PortfolioRisk()
    prices = _price_frame(price_history)

    weights = portfolio.weights()
    weight_list = [weights.get(p.ticker, 0.0) for p in portfolio.positions]

    return engine.compute_portfolio_volatility(prices, weight_list)


def marginal_contribution(
    portfolio: Portfolio,
    price_history: Dict[str, pd.Series],
    bump: float = 0.01,
) -> Dict[str, float]:
    """Change in portfolio vol from bumping each weight by ``bump``.

    A crude finite-difference risk attribution: useful for spotting which
    holding is actually driving the book's volatility.
    """
    base = portfolio_volatility(portfolio, price_history)
    out: Dict[str, float] = {}
    for position in portfolio.positions:
        original = position.quantity
        position.quantity = original * (1 + bump)
        out[position.ticker] = portfolio_volatility(portfolio, price_history) - base
        position.quantity = original
    return out
