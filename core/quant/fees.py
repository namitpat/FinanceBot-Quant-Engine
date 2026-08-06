"""Transaction cost model: commission plus slippage.

All functions take a notional in account currency and return a cost in the same
currency.
"""

from core.quant.constants import BPS, DEFAULT_COMMISSION_BPS, DEFAULT_SLIPPAGE_BPS


def commission(notional: float, bps: float = DEFAULT_COMMISSION_BPS) -> float:
    """Broker commission for a single leg."""
    return abs(notional) * bps * BPS


def slippage(notional: float, bps: float = DEFAULT_SLIPPAGE_BPS) -> float:
    """Expected slippage for a single leg."""
    return abs(notional) * bps * BPS


def round_trip_cost(notional: float) -> float:
    """Total cost of entering AND exiting a position of this size.

    A round trip is two legs, so both commission and slippage are incurred on
    the way in and again on the way out.
    """
    return commission(notional) + slippage(notional)


def net_of_costs(gross_pnl: float, notional: float) -> float:
    """Gross P&L less the full round-trip cost of the trade."""
    return gross_pnl - round_trip_cost(notional)


def break_even_move(entry_price: float) -> float:
    """Price move per share needed just to cover costs on a round trip."""
    if entry_price <= 0:
        return 0.0
    return round_trip_cost(entry_price)
