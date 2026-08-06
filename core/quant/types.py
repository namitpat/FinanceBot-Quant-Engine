"""Small value objects passed between the quant modules.

Deliberately plain dataclasses: these cross module boundaries constantly and a
heavier abstraction would just get in the way of reading a stack trace.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Position:
    """One open position.

    ``quantity`` is signed: negative means short. ``entry_price`` and
    ``last_price`` are in account currency per share.
    """

    ticker: str
    quantity: float
    entry_price: float
    last_price: float

    @property
    def notional(self) -> float:
        return abs(self.quantity) * self.last_price

    @property
    def unrealised_pnl(self) -> float:
        return self.quantity * (self.last_price - self.entry_price)


@dataclass
class Portfolio:
    """A set of positions plus uninvested cash."""

    cash: float
    positions: List[Position] = field(default_factory=list)

    @property
    def equity(self) -> float:
        return self.cash + sum(p.notional for p in self.positions)

    def weights(self) -> Dict[str, float]:
        """Current weight of each holding as a fraction of total equity."""
        total = self.equity
        if total <= 0:
            return {}
        return {p.ticker: p.notional / total for p in self.positions}


@dataclass
class SizingResult:
    """What the sizer decided, and why."""

    ticker: str
    shares: int
    notional: float
    risk_fraction: float
    capped_by: Optional[str] = None
