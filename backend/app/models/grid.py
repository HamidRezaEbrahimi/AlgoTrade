# app/models/grid.py
"""
Grid Model — 25-level grid between 30-day S/R.

Grid is NEVER an entry signal on its own.
Used only for position sizing and capital distribution.
Disabled if range < 4%.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class GridLevel(BaseModel):
    """Single grid level with price and allocation."""

    index: int
    price: Decimal
    allocation_pct: Decimal      # % of total capital for this level
    is_active: bool = True
    order_id: str | None = None  # Linked order (if placed)


class GridConfig(BaseModel):
    """Grid configuration for a symbol."""

    symbol: str
    support: Decimal             # 30-day support level
    resistance: Decimal          # 30-day resistance level
    range_pct: Decimal           # (resistance - support) / support × 100
    is_enabled: bool = True      # Disabled if range_pct < 4%
    total_levels: int = 25
    levels: list[GridLevel] = Field(default_factory=list)

    def calculate_levels(self) -> None:
        """Generate 25 equally-spaced levels between S/R."""
        if self.range_pct < Decimal("4.0"):
            self.is_enabled = False
            self.levels = []
            return

        self.is_enabled = True
        step = (self.resistance - self.support) / self.total_levels
        alloc = Decimal("100") / self.total_levels

        self.levels = [
            GridLevel(
                index=i,
                price=self.support + step * i,
                allocation_pct=alloc,
            )
            for i in range(self.total_levels)
        ]
