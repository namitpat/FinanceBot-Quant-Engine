"""Shared constants for the quant execution layer.

Units are stated explicitly on every constant because the rest of this package
mixes decimals, percents and basis points, and getting that wrong is the single
easiest way to be off by 100x in a risk number.
"""

# Number of trading days in a year, used for annualising daily statistics.
TRADING_DAYS_PER_YEAR = 252

# One basis point expressed as a decimal fraction (1 bp = 0.01%).
BPS = 0.0001

# Default broker commission per leg, in basis points of notional.
DEFAULT_COMMISSION_BPS = 2.5

# Default half-spread slippage assumption, in basis points of notional.
DEFAULT_SLIPPAGE_BPS = 1.5

# Risk-free rate used for Sharpe, as an annual decimal (4.25%).
RISK_FREE_ANNUAL = 0.0425

# Hard cap on any single position as a fraction of account equity.
MAX_POSITION_FRACTION = 0.25

# Portfolio is considered to need rebalancing once any holding drifts more than
# this fraction away from its target weight (relative drift, not absolute).
REBALANCE_DRIFT_THRESHOLD = 0.20

# Confidence level for Value-at-Risk reporting.
VAR_CONFIDENCE = 0.95
